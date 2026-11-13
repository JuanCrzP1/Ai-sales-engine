"""
Datos de pago sensibles según el contrato (links, números, cuentas y referencias): detección, redacción y su paso por el motor.

- Unitaria de `app/domain/business_config/payment_data.py`. Que ningún documento del contrato contenga estos valores lo prueban
  `test_business_config_contract.py` y la migración.
- Motor, con lo publicado de cada negocio: los datos nunca llegan a la IA (ni desde la configuración ni desde el historial) ni al registro
  `conversation_trace`, pero el cliente los recibe al elegir el método. Si la IA repitiera el marcador, el cliente no lo vería.

Las aserciones cuentan coincidencias: si una falla, el informe no muestra los datos de pago (ver `conftest.py`).
"""
from __future__ import annotations

import pytest

import app.application.pipeline.common as pipeline_common
from app.application.pipeline.ai_execution import ejecutar_pago, without_payment_placeholder
from app.application.runtime import load_tenant_runtime_yaml
from app.domain.business_config.payment_data import (
    REDACTED_PAYMENT_VALUE,
    iter_payment_blocks,
    payment_values,
    redact_payment_values,
)
from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService
from pipeline_harness import TENANTS, reply, run_conversation


def test_redaction_replaces_exact_values_longest_first():
    runtime = {
        "pricing": {
            "plans": [{"payment": {"link": "https://pagos.example/abc", "transfer": {"enabled": False, "methods": [{"type": "nequi", "number": "3001112233"}]}}}],
            "catalog": {"payment": {"transfer": {"enabled": True, "methods": [{"type": "breb", "reference": "300"}, {"type": "bank", "account_number": "3001112233-9"}]}}},
        }
    }
    # Los métodos desactivados también se protegen; los valores muy cortos no se tocan.
    assert payment_values(runtime) == ["https://pagos.example/abc", "3001112233-9", "3001112233"]
    text = "Link https://pagos.example/abc, cuenta 3001112233-9, nequi 3001112233, código 300."
    assert redact_payment_values(text, runtime) == (
        f"Link {REDACTED_PAYMENT_VALUE}, cuenta {REDACTED_PAYMENT_VALUE}, nequi {REDACTED_PAYMENT_VALUE}, código 300."
    )
    assert redact_payment_values("sin datos", {}) == "sin datos"


# ---------------------------------------------------------------------------
# El motor: la IA nunca los ve, el cliente sí los recibe
# ---------------------------------------------------------------------------

def _first_transfer_method(runtime: dict) -> tuple[str, str]:
    for block in iter_payment_blocks(runtime["pricing"]):
        transfer = block.get("transfer") or {}
        for method in transfer.get("methods") or [] if transfer.get("enabled") else []:
            value = next((str(method[field]) for field in ("number", "account_number", "reference") if method.get(field)), "")
            if value:
                return method["type"], value
    raise AssertionError("el negocio no tiene transferencias activas")


@pytest.mark.parametrize("slug", TENANTS)
def test_payment_values_never_reach_the_ai_but_reach_the_customer(monkeypatch, slug):
    runtime = load_tenant_runtime_yaml(slug)
    secrets = payment_values(runtime)
    method, value = _first_transfer_method(runtime)
    assert secrets and value in secrets

    turns = [
        ("¿Cuánto cuesta?", reply("Te cuento los precios.")),
        (f"Quiero pagar por {method}", reply("Listo.", "buy", payment_method=method)),
        ("¿Me repites el dato?", reply("Claro, revisa el mensaje anterior.")),
    ]
    results = run_conversation(slug, turns, user_id="pagos")
    prompts = [prompt for turn_prompts, _ in results for prompt in turn_prompts]

    assert prompts
    for prompt in prompts:
        leaked = [secret for secret in secrets if secret in prompt]
        assert not leaked, f"{slug}: {len(leaked)} datos de pago en el prompt"
    # La IA sabe qué medios hay para guiar la elección, sin ningún dato de pago.
    assert "Medios de pago: " in prompts[0]
    assert value in results[1][1], "el cliente debe recibir el dato de pago al elegir el método"


def test_payment_value_in_conversation_history_is_redacted_from_the_prompt():
    """El motor le entregó al cliente su dato de pago: en la conversación que ve la IA solo aparece el marcador."""
    from app.infrastructure.ai.prompting.history import recent_messages

    runtime = load_tenant_runtime_yaml("asesor_ai_prod")
    _method, value = _first_transfer_method(runtime)
    runtime["conversation_state"] = "active"
    runtime["memory_context"] = {"last_ai_response": f"Puedes transferir usando {value}.", "last_intent": "buy"}
    runtime["conversation_history"] = [{"role": "user", "text": "Por nequi"}, {"role": "assistant", "text": f"Puedes transferir usando {value}."}]

    prompt, _metadata, _context = PromptBuilderService().build(
        client_config_id="asesor_ai_prod", user_message="¿Ya te llegó?", yaml_config=runtime, faq_results=[], progression_rules=None
    )
    messages = recent_messages(runtime)
    assert value not in prompt and value not in str(messages)
    assert messages[-1]["content"] == f"Puedes transferir usando {REDACTED_PAYMENT_VALUE}."


def test_conversation_trace_log_never_stores_payment_values(monkeypatch):
    method, value = _first_transfer_method(load_tenant_runtime_yaml("saas"))
    traces: list[dict] = []

    class _CaptureLogger:
        def info(self, event, extra=None, **_kwargs):
            if event == "conversation_trace":
                traces.append(extra or {})

    monkeypatch.setattr(pipeline_common, "logger", _CaptureLogger())
    (_, response), = run_conversation("saas", [(f"Pago por {method}", reply("Listo.", "buy", payment_method=method))], user_id="log")

    assert value in response
    assert traces and value not in traces[-1]["ai_response"]
    assert REDACTED_PAYMENT_VALUE in traces[-1]["ai_response"]


# ---------------------------------------------------------------------------
# Si la IA repite el marcador, el cliente no lo ve
# ---------------------------------------------------------------------------

def test_the_placeholder_becomes_the_real_payment_data_when_the_method_is_known():
    runtime = load_tenant_runtime_yaml("saas")
    method, value = _first_transfer_method(runtime)
    answer = without_payment_placeholder(f"Claro, transfiere a {REDACTED_PAYMENT_VALUE}.", runtime, method)
    assert answer == ejecutar_pago(runtime, method)
    assert value in answer and REDACTED_PAYMENT_VALUE not in answer


def test_without_a_method_the_customer_is_asked_instead_of_receiving_a_cut_sentence():
    """Antes se quitaba la frase del marcador y quedaba algo como «Cuando lo hagas, avísame» sin el número (13 nov 2026)."""
    runtime = load_tenant_runtime_yaml("saas")
    answer = without_payment_placeholder(f"Te cuento cómo pagar. El número es {REDACTED_PAYMENT_VALUE}. Cuando lo hagas, avísame.", runtime, "")
    assert answer == "¿Con qué medio prefieres pagar: pago en línea, Nequi, Daviplata, transferencia a Bancolombia o Bre-B?"


def test_if_the_method_cannot_be_known_the_customer_is_asked_with_the_names_of_the_methods():
    runtime = load_tenant_runtime_yaml("saas")
    method, _value = _first_transfer_method(runtime)
    answer = without_payment_placeholder(f"Paga en {REDACTED_PAYMENT_VALUE}", runtime, "")
    assert answer.startswith("¿Con qué medio prefieres pagar") and method in answer.lower()
    assert REDACTED_PAYMENT_VALUE not in answer
    assert without_payment_placeholder("Sin marcador.", runtime, "") == "Sin marcador."


@pytest.mark.parametrize("slug", TENANTS)
def test_the_customer_never_receives_the_placeholder_from_the_real_flow(slug):
    (_prompts, response), = run_conversation(slug, [("¿A qué número pago?", reply(f"Paga al {REDACTED_PAYMENT_VALUE}. Gracias."))], user_id="marcador")
    assert REDACTED_PAYMENT_VALUE not in response


# ---------------------------------------------------------------------------
# La acción de pago y la red de seguridad, con la conversación real del 13 de noviembre de 2026 (Telegram, Asesor Comercial):
# el cliente pidió el Nequi otra vez, la IA no dijo el medio y al cliente le llegó «Cuando lo hagas, avísame» sin el número.
# ---------------------------------------------------------------------------

def _nequi(slug: str = "saas") -> str:
    return next(value for method, value in [_first_transfer_method(load_tenant_runtime_yaml(slug))] if method == "nequi")


def test_the_assistant_sends_the_payment_details_again_when_the_customer_asks_with_the_action():
    number = _nequi()
    turns = [
        ("Quiero pagar por nequi", reply("Listo.", "buy", payment_method="nequi", send_payment="nequi")),
        ("Espérame un momento", reply("Claro, tómate tu tiempo.", "info")),
        ("Se me borró el Nequi, me lo envías de nuevo", reply("¡Claro! Te los envío otra vez.", "info", send_payment="nequi")),
    ]
    (prompts1, first), (_p2, waiting), (prompts3, again) = run_conversation("saas", turns, user_id="reenvio-accion")
    assert first.startswith("💳 *Datos para pagar*") and number in first
    assert waiting == "Claro, tómate tu tiempo."
    assert again == first
    # La IA sabe que puede enviarlos, y en esta conversación sabe que ya los envió.
    assert "metadata.send_payment" in prompts1[0] and "nunca digas que no puedes" in prompts1[0]
    assert "Ya le enviaste los datos para pagar por Nequi" in prompts3[0]


@pytest.mark.parametrize(
    ("message", "how"),
    [("Pero se me borró el Nequi me lo envías de nuevo", "el cliente lo nombra"), ("Me lo envías de nuevo porfa", "venían pagando por Nequi")],
)
def test_if_the_assistant_forgets_the_action_the_system_still_sends_the_right_details(message, how):
    number = _nequi()
    turns = [
        ("Quiero pagar por nequi", reply("Listo.", "buy", payment_method="nequi")),
        ("Espérame un momento", reply("Claro, tómate tu tiempo.", "info")),
        (message, reply(f"Claro, el número es {REDACTED_PAYMENT_VALUE}. Cuando lo hagas, avísame para continuar.", "info")),
    ]
    *_before, (_prompts, answer) = run_conversation("saas", turns, user_id=f"red-{how}")
    assert answer.startswith("💳 *Datos para pagar*") and number in answer, how
    assert "Cuando lo hagas, avísame para continuar." != answer


def test_the_details_never_repeat_while_the_customer_keeps_talking_about_the_same_payment():
    turns = [
        ("Quiero pagar por nequi", reply("Listo.", "buy", payment_method="nequi")),
        ("¿Y cuando lo haga qué necesito hacer?", reply("Cuando pagues, envíame aquí la captura del comprobante.", "buy", payment_method="nequi")),
        ("¿Y en cuánto lo confirman?", reply("Nuestro equipo lo revisa en unos minutos.", "buy", payment_method="nequi")),
        ("Mejor por link", reply("Listo.", "buy", payment_method="link")),
    ]
    (_a, first), (_b, next_step), (_c, follow_up), (_d, by_link) = run_conversation("saas", turns, user_id="sin-repetir")
    assert first.startswith("💳 *Datos para pagar*")
    assert next_step == "Cuando pagues, envíame aquí la captura del comprobante."
    assert follow_up == "Nuestro equipo lo revisa en unos minutos."
    # Cambiar de medio sí envía los datos del nuevo.
    assert by_link.startswith("💳 *Datos para pagar*") and "*Pago en línea*" in by_link
