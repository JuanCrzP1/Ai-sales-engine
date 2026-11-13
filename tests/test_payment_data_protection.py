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


def _run_with_context(slug: str, turns: list[tuple[str, str]], *, user_id: str) -> list[tuple[str, dict]]:
    """Como `run_conversation`, pero devuelve también lo que el motor decide del chat (por ejemplo, pasarlo a una persona)."""
    from app.application.ai_pipeline import AIPipeline
    from app.domain.conversation.memory import MemoryDomainService
    from app.infrastructure.persistence.memory_repository import MemoryRepository

    pipeline = AIPipeline(memory_service=MemoryDomainService(MemoryRepository()))
    results = []
    for message, llm_reply in turns:
        pipeline.runtime.generate = lambda prompt, *, user_message, bot_config=None, _reply=llm_reply, **_kwargs: _reply
        response, _ai_used, context = pipeline.run(
            tenant=type("T", (), {"slug": slug, "name": slug, "id": slug})(), user_message=message, user_id=user_id, bot_config=None,
            conversation_history=[], faq_results=[], yaml_config=None, include_metadata=True,
        )
        results.append((response, context if isinstance(context, dict) else {}))
    return results


def test_when_the_customer_asks_for_the_details_they_arrive_even_if_the_assistant_says_it_cannot():
    """El chat real (13 nov 2026, 07:58): «Pero envíame el Nequi» → «No puedo enviarte el número de Nequi directamente. Te paso con
    alguien del equipo». El modelo copiaba su propia respuesta vieja. Ahora salen los datos y el chat no pasa a una persona por eso."""
    number = _nequi()
    refusal = reply("No puedo enviarte el número de Nequi directamente. Te paso con alguien del equipo por este mismo chat.", "info", handoff="persona")
    turns = [
        ("Quiero pagar por nequi", reply("Listo.", "buy", payment_method="nequi")),
        ("Pero envíame el Nequi", refusal),
        ("Me lo envías de nuevo porfa", reply("No puedo enviarlo directamente.", "info")),
    ]
    (_first, _), (sent, context), (again, _ctx) = _run_with_context("saas", turns, user_id="pide-los-datos")
    assert sent.startswith("💳 *Datos para pagar*") and number in sent and "No puedo" not in sent
    assert not context.get("handoff")
    assert again == sent


def test_if_the_customer_also_asks_for_a_person_the_chat_still_goes_to_the_team():
    turns = [
        ("Quiero pagar por nequi", reply("Listo.", "buy", payment_method="nequi")),
        ("Envíame el Nequi y quiero hablar con una persona", reply("Te paso con alguien del equipo.", "info", handoff="persona")),
    ]
    _first, (sent, context) = _run_with_context("saas", turns, user_id="datos-y-persona")
    assert sent.startswith("💳 *Datos para pagar*") and context.get("handoff") is True


@pytest.mark.parametrize(
    "message",
    ["Dime este sistema cómo se llama", "Quisiera saber algo más", "¿Aceptan Nequi?", "Envíame la información del plan otra vez",
     "Dame el número de la tienda", "Envíame el número de WhatsApp", "¿Me mandas una foto del producto?"],
)
def test_other_requests_are_answered_by_the_assistant_not_with_payment_details(message):
    turns = [
        ("Quiero pagar por nequi", reply("Listo.", "buy", payment_method="nequi")),
        (message, reply("Respuesta del asistente.", "info")),
    ]
    _first, (_prompts, answer) = run_conversation("saas", turns, user_id=f"otra-cosa-{abs(hash(message))}")
    assert answer == "Respuesta del asistente."


# ---------------------------------------------------------------------------
# Cualquier medio que tenga el negocio, y varias cuentas del mismo tipo
# ---------------------------------------------------------------------------

_SAID = {"link": "el link de pago", "nequi": "el Nequi", "daviplata": "el Daviplata", "bank": "la cuenta de Bancolombia", "breb": "la llave Bre-B"}


@pytest.mark.parametrize("method", ["link", "nequi", "daviplata", "bank", "breb"])
def test_every_configured_method_reaches_the_customer_when_asked_even_if_the_assistant_refuses(method):
    runtime = load_tenant_runtime_yaml("saas")
    expected = ejecutar_pago(runtime, method)
    assert expected, f"saas tiene {method}"
    refusal = reply("No puedo enviarte esos datos directamente.", "info")
    (_prompts, answer), = run_conversation("saas", [(f"Envíame {_SAID[method]} para pagar", refusal)], user_id=f"cualquier-medio-{method}")
    assert answer == expected and REDACTED_PAYMENT_VALUE not in answer


def _two_banks(document):
    for profile in document["payments"]:
        banks = [method for method in profile["transfer_methods"] if method["type"] == "bank"]
        if banks:
            second = {**banks[0], "bank": "Davivienda", "account_type": "corriente", "holder": "Software Norte S.A.S."}
            banks[0]["holder"] = "Software Norte S.A.S."
            profile["transfer_methods"].append(second)


def test_with_two_banks_the_customer_gets_the_one_he_names_or_both(monkeypatch, tmp_path):
    from pipeline_harness import run_with_document

    turns = [
        ("Envíame la cuenta de Davivienda", reply("No puedo enviarla.", "info")),
        ("Mejor por Bancolombia", reply("Listo.", "buy", payment_method="bank")),
        ("¿Cuáles cuentas bancarias tienen? Pásame los datos para pagar por transferencia bancaria", reply("Claro.", "buy", send_payment="bank")),
    ]
    (_a, davivienda), (_b, bancolombia), (_c, both) = run_with_document(monkeypatch, tmp_path / "dos-bancos", "saas", _two_banks, turns)
    assert "*Davivienda*\nCuenta corriente\n" in davivienda and "Bancolombia" not in davivienda
    assert "A nombre de: Software Norte S.A.S." in davivienda
    assert "*Bancolombia*\nCuenta de ahorros\n" in bancolombia and "Davivienda" not in bancolombia
    assert both.startswith("💳 *Datos para pagar*\n\n*Transferencia bancaria*\n")
    assert "*Bancolombia*\nCuenta de ahorros\n" in both and "*Davivienda*\nCuenta corriente\n" in both and both.count("A nombre de:") == 2


def test_with_two_banks_the_question_names_both(monkeypatch, tmp_path):
    from pipeline_harness import run_with_document

    turns = [("¿A qué cuenta pago?", reply(f"Paga a {REDACTED_PAYMENT_VALUE}.", "info"))]
    (_prompts, answer), = run_with_document(monkeypatch, tmp_path / "pregunta", "saas", _two_banks, turns)
    assert "transferencia a Bancolombia o Davivienda" in answer and answer.startswith("¿Con qué medio prefieres pagar")


def test_a_resend_works_even_after_talking_about_something_else():
    """Laboratorio de calidad, 13 nov 2026 (Asesor Comercial): después de los datos, la IA habló de activar el servicio y el paso de
    pago dejó de estar activo; «se me borró el número, ¿me lo envías otra vez?» no sabía de qué medio era. Se recuerda el elegido."""
    number = _nequi()
    turns = [
        ("Quiero pagar por nequi", reply("Listo.", "buy", payment_method="nequi")),
        ("¿Y después qué sigue?", reply("Cuando pagues, para activar tu servicio te pido unos datos de arranque.", "info")),
        ("Se me borró el número, ¿me lo envías otra vez?", reply("Lo siento, no puedo enviar el número nuevamente.", "info")),
    ]
    *_before, (_prompts, again) = run_conversation("saas", turns, user_id="reenvio-tras-activacion")
    assert again.startswith("💳 *Datos para pagar*") and number in again


# ---------------------------------------------------------------------------
# Con la IA real, un negocio de Perú (13 nov 2026): «¿Y si te pago por Nu?» → «los datos de pago son los mismos, solo cambia el
# medio» (falso, y sin los datos de Nu); y el efectivo pedía «la captura del comprobante».
# ---------------------------------------------------------------------------

def _peru(document):
    profile = document["payments"][0]
    number = next(method["number"] for method in profile["transfer_methods"] if method.get("number"))
    reference = next(method["reference"] for method in profile["transfer_methods"] if method.get("reference"))
    profile["transfer_methods"] = [
        {"type": "yape", "number": number, "holder": "Asesor Comercial S.A.C."},
        {"type": "custom", "name": "Nu", "data_label": "Cuenta", "reference": reference},
        {"type": "cash", "instructions": "Pagas al asesor cuando te visite."},
    ]


def test_when_the_customer_switches_method_its_details_arrive_even_if_the_assistant_says_they_are_the_same(monkeypatch, tmp_path):
    from pipeline_harness import run_with_document

    turns = [
        ("Por Yape", reply("Listo.", "buy", payment_method="yape")),
        ("¿Y si te pago por Nu?", reply("Los datos de pago son los mismos, solo cambia el medio.", "info")),
        ("Mejor en efectivo", reply("Perfecto.", "info")),
    ]
    (_a, yape), (_b, nu), (_c, cash) = run_with_document(monkeypatch, tmp_path / "peru", "saas", _peru, turns)
    assert "*Yape*" in yape and "A nombre de: Asesor Comercial S.A.C." in yape
    assert "*Nu*\nCuenta: " in nu and "son los mismos" not in nu
    # El efectivo no pide comprobante.
    assert cash.startswith("💵 *Cómo pagar*\n\n*Efectivo o contraentrega*\nPagas al asesor cuando te visite.") and "comprobante" not in cash


@pytest.mark.parametrize("message", ["¿Tienen Nu?", "¿Aceptan Yape?", "No puedo pagar por Yape", "¿Nu o Yape?"])
def test_asking_about_a_method_or_refusing_it_is_not_choosing_it(monkeypatch, tmp_path, message):
    from pipeline_harness import run_with_document

    (_prompts, answer), = run_with_document(monkeypatch, tmp_path / f"no-elige-{abs(hash(message))}", "saas", _peru, [(message, reply("Respuesta del asistente.", "info"))])
    assert answer == "Respuesta del asistente."


def test_when_the_system_sends_the_details_the_method_is_remembered_even_if_the_ai_did_not_mark_it():
    """Si la IA no marcó el medio y el sistema envió los datos porque el cliente lo eligió, queda anotado: así, más adelante, «me lo
    envías de nuevo» sabe de cuál medio es aunque el paso de la conversación ya no esté."""
    from app.application.ai_pipeline import AIPipeline
    from app.domain.conversation.memory import MemoryDomainService
    from app.infrastructure.persistence.memory_repository import MemoryRepository

    memory = MemoryDomainService(MemoryRepository())
    pipeline = AIPipeline(memory_service=memory)
    pipeline.runtime.generate = lambda prompt, *, user_message, bot_config=None, **_kwargs: reply("Perfecto.", "info")
    pipeline.run(tenant=type("T", (), {"slug": "saas", "name": "saas", "id": "saas"})(), user_message="Te pago por Daviplata", user_id="recuerda-medio",
                 bot_config=None, conversation_history=[], faq_results=[], yaml_config=None, include_metadata=True)
    assert memory.get_payment_method(tenant_slug="saas", user_id="recuerda-medio") == "daviplata"


def test_details_already_sent_are_not_repeated_unless_asked_and_the_ai_can_name_them_in_its_own_words():
    """Con la IA real (13 nov 2026): «Ya voy a pagar» → la IA pidió reenviar el bloque que ya tenía. Si nadie los pidió, se respeta su
    respuesta; si la IA dice «aquí los tienes de nuevo», salen; y si los nombra al explicar, el dato real va dentro de su frase."""
    number = _nequi()
    turns = [
        ("Te pago por Nequi", reply("Listo.", "buy", payment_method="nequi")),
        ("Ya voy a pagar", reply("¡Perfecto! Cuando pagues, envíame aquí la captura del comprobante.", "buy", payment_method="nequi", send_payment="nequi")),
        ("Cómo así", reply(f"Te envié los datos de Nequi: {REDACTED_PAYMENT_VALUE}. Paga ahí y me mandas el comprobante.", "info", send_payment="nequi")),
        ("Ok", reply("Claro, aquí los tienes de nuevo.", "info", send_payment="nequi")),
    ]
    (_a, first), (_b, going), (_c, explained), (_d, again) = run_conversation("saas", turns, user_id="sin-repetir-accion")
    assert first.startswith("💳 *Datos para pagar*")
    assert going == "¡Perfecto! Cuando pagues, envíame aquí la captura del comprobante."
    assert explained == f"Te envié los datos de Nequi: {number}. Paga ahí y me mandas el comprobante."
    assert again == first


def test_when_the_ai_says_it_sends_the_details_they_really_arrive():
    """Con la IA real (13 nov 2026): «Cómo así» → «Te envío nuevamente los datos para pagar por Nequi…» sin enviarlos (marcó mal su
    acción). Si la IA dice que los envía y se sabe el medio, salen de verdad; si dice otra cosa, no."""
    number = _nequi()
    turns = [
        ("Te pago por Nequi", reply("Listo.", "buy", payment_method="nequi")),
        ("Cómo así", reply("Te envío nuevamente los datos para pagar por Nequi. Cuando pagues, me mandas el comprobante.", "info", send_payment="[dato de pago]")),
        ("Ok", reply("Perfecto, cuando pagues envíame el comprobante.", "info")),
    ]
    (_a, first), (_b, promised), (_c, plain) = run_conversation("saas", turns, user_id="promesa-cumplida")
    assert promised == first and number in promised
    assert plain == "Perfecto, cuando pagues envíame el comprobante."


def test_a_false_refusal_never_reaches_the_customer_and_the_customer_request_wins():
    """Con la IA real (13 nov 2026): «¿A qué número te consigno?» → «No puedo darte el número de cuenta…» (falso), y «me regalas la
    cuenta de bancolombia» → le llegó el link (la IA marcó otro medio). La negativa nunca sale y lo que pide el cliente gana."""
    runtime = load_tenant_runtime_yaml("saas")
    bank = next(value for value in payment_values(runtime) if value.isdigit() and len(value) == 10 and not value.startswith("3"))
    fresh = [("¿A qué número te consigno?", reply("No puedo darte el número de cuenta, pero puedo enviarte el link de pago.", "info"))]
    (_p, question), = run_conversation("saas", fresh, user_id="negativa-sin-medio")
    assert question.startswith("¿Con qué medio prefieres pagar") and "No puedo" not in question
    paying = [
        ("Te pago por Nequi", reply("Listo.", "buy", payment_method="nequi")),
        ("¿A qué número te consigno?", reply("No puedo darte el número de cuenta.", "info")),
        ("me regalas la cuenta de bancolombia", reply("Claro.", "buy", send_payment="link")),
    ]
    (_a, nequi), (_b, again), (_c, bancolombia) = run_conversation("saas", paying, user_id="negativa-con-medio")
    assert again == nequi
    assert "*Bancolombia*" in bancolombia and bank in bancolombia and "Pago en línea" not in bancolombia


def test_a_refusal_about_something_else_is_left_alone():
    turns = [("¿Me lo pueden llevar a Medellín?", reply("No puedo enviarlo a Medellín, solo hacemos entregas en Bogotá.", "info"))]
    (_p, answer), = run_conversation("restaurant", turns, user_id="negativa-de-envio")
    assert answer == "No puedo enviarlo a Medellín, solo hacemos entregas en Bogotá."
