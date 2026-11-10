"""
Datos de pago sensibles según el contrato (links, números, cuentas y referencias): detección, redacción y su paso por el motor.

- Unitaria de `app/domain/business_config/payment_data.py`. Que ningún documento del contrato contenga estos valores lo prueban
  `test_business_config_contract.py` y la migración.
- Motor, con YAML o con el contrato: los datos nunca llegan a la IA (ni desde la configuración ni desde el historial) ni al registro
  `conversation_trace`, pero el cliente los recibe al elegir el método. Si la IA repitiera el marcador, el cliente no lo vería.

Las aserciones cuentan coincidencias: si una falla, el informe no muestra los datos de pago (ver `conftest.py`).
"""
from __future__ import annotations

import pytest

import app.application.pipeline.common as pipeline_common
from app.application.pipeline.ai_execution import ejecutar_pago, without_payment_placeholder
from app.application.runtime import load_tenant_runtime_yaml
from app.application.runtime import tenant_runtime_loader as loader
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


def _use_source(monkeypatch, source: str, slug: str) -> None:
    if source == "contract":
        monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, slug)
    else:
        monkeypatch.delenv(loader.CONTRACT_TENANTS_ENV, raising=False)


@pytest.mark.parametrize("source", ["yaml", "contract"])
@pytest.mark.parametrize("slug", TENANTS)
def test_payment_values_never_reach_the_ai_but_reach_the_customer(monkeypatch, slug, source):
    _use_source(monkeypatch, source, slug)
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
        assert not leaked, f"{slug}/{source}: {len(leaked)} datos de pago en el prompt"
    # El método sigue siendo visible para que la IA guíe la elección, sin su dato.
    assert "TRANSFER_METHODS:" in prompts[0] and f"- {method}:" in prompts[0]
    assert value in results[1][1], "el cliente debe recibir el dato de pago al elegir el método"


def test_payment_value_in_conversation_history_is_redacted_from_the_prompt():
    runtime = load_tenant_runtime_yaml("asesor_ai_prod")
    _method, value = _first_transfer_method(runtime)
    runtime["conversation_state"] = "active"
    runtime["memory_context"] = {"last_ai_response": f"Puedes transferir usando {value}.", "last_intent": "buy"}

    prompt, _metadata, _context = PromptBuilderService().build(
        client_config_id="asesor_ai_prod", user_message="¿Ya te llegó?", yaml_config=runtime, faq_results=[], progression_rules=None
    )
    assert value not in prompt
    assert f"Puedes transferir usando {REDACTED_PAYMENT_VALUE}." in prompt


@pytest.mark.parametrize("source", ["yaml", "contract"])
def test_conversation_trace_log_never_stores_payment_values(monkeypatch, source):
    _use_source(monkeypatch, source, "saas")
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


def test_without_a_method_the_sentences_with_the_placeholder_are_dropped():
    runtime = load_tenant_runtime_yaml("saas")
    answer = without_payment_placeholder(f"Te cuento cómo pagar. El número es {REDACTED_PAYMENT_VALUE}. ¿Te sirve?", runtime, "")
    assert answer == "Te cuento cómo pagar. ¿Te sirve?"


def test_if_nothing_is_left_the_customer_is_asked_for_the_payment_method():
    runtime = load_tenant_runtime_yaml("saas")
    method, _value = _first_transfer_method(runtime)
    answer = without_payment_placeholder(f"Paga en {REDACTED_PAYMENT_VALUE}", runtime, "")
    assert answer.startswith("¿Con qué medio prefieres pagar") and method in answer
    assert REDACTED_PAYMENT_VALUE not in answer
    assert without_payment_placeholder("Sin marcador.", runtime, "") == "Sin marcador."


@pytest.mark.parametrize("slug", TENANTS)
def test_the_customer_never_receives_the_placeholder_from_the_real_flow(slug):
    (_prompts, response), = run_conversation(slug, [("¿A qué número pago?", reply(f"Paga al {REDACTED_PAYMENT_VALUE}. Gracias."))], user_id="marcador")
    assert REDACTED_PAYMENT_VALUE not in response
