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
from app.application.pipeline.payment_delivery import PaymentDelivery, payment_problem, remembered_message
from app.application.pipeline.payment_reading import PaymentReading, read_customer_message
from app.application.pipeline.response_postprocessor import without_model_artifacts
from app.domain.business_config.payment_data import (
    REDACTED_PAYMENT_VALUE,
    iter_payment_blocks,
    mask_invented_numbers,
    mask_own_markers,
    payment_values,
    redact_payment_values,
)
from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService
from pipeline_harness import TENANTS, reads, reply, run_conversation, run_with_document


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
        (f"Quiero pagar por {method}", reply("Listo.", "buy", send_payment=method)),
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
    (_, response), = run_conversation("saas", [(f"Pago por {method}", reply("Listo.", "buy", send_payment=method))], user_id="log")

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
# Un asesor, no un bot de preguntas frecuentes (AI-first). El chat real en producción (13 nov 2026, Asesor Comercial): «Y puedo
# trasferir» → le llegó solo la cuenta de Bancolombia; «Y Nequi no» → solo la de Nequi; «Cómo así» → el mismo bloque otra vez. Unas
# reglas de palabras cambiaban lo que decía el asesor por la plantilla. Ahora:
# - el asesor (la IA) siempre habla y los datos van debajo de su mensaje;
# - qué pide el cliente lo entiende el lector de pagos (otra llamada a la IA, corta), no reglas de palabras;
# - el código solo cuida el dato y no deja salir algo falso sobre los pagos.
# Aquí el asesor y el lector tienen respuestas fijas: se prueba lo que hace el motor con lo que ellos dicen. Qué tan bien entienden se
# mide con la IA real (`experiments/quality_lab`).
# ---------------------------------------------------------------------------

def _nequi(slug: str = "saas") -> str:
    return next(value for method, value in [_first_transfer_method(load_tenant_runtime_yaml(slug))] if method == "nequi")


def _details(answer: str) -> str:
    """El mensaje con los datos de pago que va debajo de lo que dice el asesor (o "")."""
    start = min((answer.find(mark) for mark in ("💳 *Datos para pagar*", "💵 *Cómo pagar*") if mark in answer), default=-1)
    return answer[start:] if start >= 0 else ""


def _said(answer: str) -> str:
    """Lo que dice el asesor encima de los datos de pago."""
    details = _details(answer)
    return (answer[: -len(details)] if details else answer).strip()


WANTS_NEQUI = reads(True, "Nequi")
FIRST = ("Te pago por Nequi", reply("¡Perfecto! Ahí abajo te dejo los datos de Nequi.", "buy"), WANTS_NEQUI)


def test_when_the_customer_should_get_the_details_they_arrive_below_what_the_advisor_says():
    number = _nequi()
    (prompts, answer), = run_conversation("saas", [FIRST], user_id="recibe-datos")
    assert _said(answer) == "¡Perfecto! Ahí abajo te dejo los datos de Nequi."
    assert _details(answer).startswith("💳 *Datos para pagar*\n\n*Nequi*\n") and number in _details(answer)
    # El asesor lo sabe antes de responder (lo entendió el lector), y nunca ve el número.
    assert "Con este mensaje el cliente recibe los datos para pagar por Nequi" in prompts[0] and number not in prompts[0]
    assert len(prompts) == 1


def test_asking_about_a_method_is_answered_by_the_advisor_without_details():
    """«Y puedo trasferir», «Y Nequi no»: preguntar no es pedir los datos. Responde el asesor y sigue guiando."""
    can_i = "¡Claro! Puedes pagar por transferencia a Bancolombia 🙌. ¿Me compartes tu nombre para dejar lista tu activación?"
    turns = [
        ("Y puedo trasferir", reply(can_i, "info"), reads()),
        ("Y Nequi no", reply("Sí, también recibimos Nequi. ¿Con cuál prefieres pagar?", "info"), reads()),
    ]
    (prompts, transfer), (prompts_nequi, nequi) = run_conversation("saas", turns, user_id="pregunta-medio")
    assert transfer == can_i and nequi == "Sí, también recibimos Nequi. ¿Con cuál prefieres pagar?"
    assert "Con este mensaje el cliente no recibe datos de pago" in prompts[0]
    # Un dato del negocio que viene al caso: el medio que nombra sí lo recibe (un modelo pequeño llegó a decir «no ofrecemos Nequi»).
    assert "El cliente nombra Nequi: el negocio sí lo recibe." in prompts_nequi[0]


def test_the_advisor_cannot_push_details_the_customer_did_not_ask_for():
    """Con la IA real (13 nov 2026): «Quiero el plan básico» → el asesor enviaba el Nequi sin que el cliente hubiera elegido medio.
    Con varios medios, se le pide otra respuesta; si insiste, los datos no salen."""
    pushy = reply("Te dejo abajo los datos para pagar por Nequi.", "buy", send_payment="nequi")
    turns = [("Quiero el plan básico", [pushy, reply("¡Genial! ¿Con cuál medio prefieres pagar?", "buy")], reads())]
    (prompts, answer), = run_conversation("saas", turns, user_id="sin-pedir")
    assert answer == "¡Genial! ¿Con cuál medio prefieres pagar?" and len(prompts) == 2
    assert "ibas a enviarle los datos para pagar por Nequi y el cliente no los ha pedido" in prompts[1]
    (_p, insisted), = run_conversation("saas", [("Quiero el plan básico", [pushy, pushy], reads())], user_id="sin-pedir-insiste")
    assert insisted == "Te dejo abajo los datos para pagar por Nequi." and not _details(insisted)


def test_details_already_sent_are_not_repeated_unless_the_customer_asks():
    """«Cómo así» → el mismo bloque otra vez (producción, 13 nov 2026). Lo que ya salió no se repite si el cliente no lo pidió: se le
    pide al asesor que responda a lo que dijo el cliente; si lo pide otra vez, sale otra vez."""
    again = reply("Aquí tienes los datos de Nequi.", "info", send_payment="nequi")
    turns = [
        FIRST,
        ("Cómo así", [again, reply("Te explico: arriba tienes el número de Nequi. Pagas ahí y me envías la captura.", "info")], reads()),
        ("Ya voy a pagar", [again, again], reads()),
        ("Se me borró el Nequi, me lo envías de nuevo", reply("¡Claro! Aquí lo tienes otra vez.", "info"), reads(True)),
    ]
    (_a, first), (prompts, explained), (_c, going), (_d, resent) = run_conversation("saas", turns, user_id="sin-repetir")
    assert explained == "Te explico: arriba tienes el número de Nequi. Pagas ahí y me envías la captura."
    assert "Ya le enviaste los datos para pagar por Nequi" in prompts[0]
    assert "ibas a enviarle otra vez los datos para pagar por Nequi; ya los tiene y no los pidió" in prompts[1]
    # Si insiste, los datos no se repiten.
    assert going == "Aquí tienes los datos de Nequi." and not _details(going)
    # Sin nombrar el medio: el que venían usando.
    assert _said(resent) == "¡Claro! Aquí lo tienes otra vez." and _details(resent) == _details(first)


def test_without_the_reader_the_advisor_action_is_trusted():
    """Si el lector no responde (sin clave, un error del proveedor), decide el asesor solo con su acción."""
    number = _nequi()
    turns = [
        ("Quiero pagar por nequi", reply("Listo, ahí van.", "buy", send_payment="nequi")),
        ("Me lo envías de nuevo", reply("Claro, otra vez.", "info", send_payment="nequi")),
        ("Gracias", reply("Con gusto.", "info")),
    ]
    (_a, first), (_b, again), (_c, thanks) = run_conversation("saas", turns, user_id="sin-lector")
    assert _said(first) == "Listo, ahí van." and number in _details(first)
    assert _details(again) == _details(first) and thanks == "Con gusto."


def test_a_false_refusal_never_reaches_the_customer():
    """El chat real (13 nov 2026, 07:58): «Pero envíame el Nequi» → «No puedo enviarte el número de Nequi directamente. Te paso con
    alguien del equipo». Es falso: se le pide otra respuesta; si insiste, salen los datos sin esa frase y el chat no pasa a una
    persona por eso."""
    number = _nequi()
    refusal = reply("No puedo enviarte el número de Nequi directamente. Te paso con alguien del equipo.", "info", handoff="persona")
    fixed = reply("¡Claro! Ahí abajo te lo dejo.", "info")
    turns = [("Pero envíame el Nequi", [refusal, fixed], WANTS_NEQUI)]
    (prompts, answer), = run_conversation("saas", turns, user_id="negativa")
    assert _said(answer) == "¡Claro! Ahí abajo te lo dejo." and number in _details(answer)
    assert "decía que no puedes dar los datos de pago o que no tienes acceso a ellos, y sí puedes" in prompts[1]
    (insisted, context), = run_conversation("saas", [("Pero envíame el Nequi", [refusal, refusal], WANTS_NEQUI)], user_id="negativa-insiste", with_context=True)
    assert insisted == _details(answer) and "No puedo" not in insisted
    assert not context.get("handoff")
    # Sin saber el medio, se le pregunta al cliente con cuál.
    unknown = reply("No puedo darte el número de cuenta.", "info")
    (_p, question), = run_conversation("saas", [("¿A qué número te consigno?", [unknown, unknown], reads(True))], user_id="negativa-sin-medio")
    assert question == "¿Con qué medio prefieres pagar: pago en línea, Nequi, Daviplata, transferencia a Bancolombia o Bre-B?"


def test_a_refusal_about_something_else_is_left_alone():
    turns = [("¿Me lo pueden llevar a Medellín?", reply("No puedo enviarlo a Medellín, solo hacemos entregas en Bogotá.", "info"), reads())]
    (prompts, answer), = run_conversation("restaurant", turns, user_id="negativa-de-envio")
    assert answer == "No puedo enviarlo a Medellín, solo hacemos entregas en Bogotá." and len(prompts) == 1


def test_if_the_ai_denies_a_method_the_business_has_the_truth_goes_out():
    """Con la IA real (13 nov 2026): «Y Nequi no» → «Nequi no es un medio que manejamos en este momento» (falso), y lo repitió cuatro
    turnos. Se le pide otra respuesta; si insiste, sale la verdad."""
    denial = reply("Nequi no es un medio que manejamos en este momento. Puedes transferir a Bancolombia.", "info")
    turns = [("Y Nequi no", [denial, reply("Sí, también recibimos Nequi. ¿Prefieres ese?", "info")], reads())]
    (prompts, answer), = run_conversation("saas", turns, user_id="niega")
    assert answer == "Sí, también recibimos Nequi. ¿Prefieres ese?"
    assert "decía que el negocio no recibe Nequi, y sí lo recibe" in prompts[1]
    (_p, insisted), = run_conversation("saas", [("Y Nequi no", [denial, denial], reads())], user_id="niega-insiste")
    assert insisted == "Sí, claro: también recibimos Nequi. ¿Quieres que te envíe los datos para pagar?"
    # Negar lo que el negocio no tiene se respeta.
    other = [("¿Y PayPal no?", reply("No manejamos PayPal; puedes pagar por Nequi o Daviplata.", "info"), reads())]
    (prompts, kept), = run_conversation("saas", other, user_id="niega-paypal")
    assert kept == "No manejamos PayPal; puedes pagar por Nequi o Daviplata." and len(prompts) == 1


def test_the_marker_marks_where_the_details_go_and_never_reaches_the_customer():
    number = _nequi()
    placed = reply(f"Listo, Juan. Te dejo los datos:\n\n{REDACTED_PAYMENT_VALUE}\n\nCuando pagues me avisas.", "buy")
    (_p, answer), = run_conversation("saas", [("Te pago por Nequi", placed, WANTS_NEQUI)], user_id="marcador-lugar")
    assert answer == f"Listo, Juan. Te dejo los datos:\n\n{_details(answer).split(chr(10) * 2 + 'Cuando pagues me avisas.')[0]}\n\nCuando pagues me avisas."
    assert number in answer and REDACTED_PAYMENT_VALUE not in answer
    # Un modelo pequeño a veces escribe su propia plantilla con marcadores suyos: esos renglones no salen.
    own = reply("Aquí van los datos:\n\nTitular: [Nombre del negocio]\nNúmero de cuenta: [número de cuenta]\n\n¿Me confirmas tu nombre?", "buy")
    (_p, cleaned), = run_conversation("saas", [("Te pago por Nequi", own, WANTS_NEQUI)], user_id="marcador-propio")
    assert _said(cleaned) == "Aquí van los datos:\n\n¿Me confirmas tu nombre?" and number in _details(cleaned) and "[" not in cleaned
    # Si ya tiene los datos y la IA los nombra al explicar, el dato real va dentro de su frase.
    explains = reply(f"Te envié los datos de Nequi: {REDACTED_PAYMENT_VALUE}. Paga ahí y me mandas el comprobante.", "info")
    _first, (_p, inline) = run_conversation("saas", [FIRST, ("Cómo así", explains, reads())], user_id="marcador-frase")
    assert inline == f"Te envié los datos de Nequi: {number}. Paga ahí y me mandas el comprobante."
    # Lo que algunos modelos dejan cuando intentan «llamar una función» tampoco sale.
    assert without_model_artifacts('Claro, aquí van.\n<function_calls>\n[{"name": "set_metadata"}]\n</function_calls>') == "Claro, aquí van."


def test_an_invented_number_never_reaches_the_customer():
    """Con la IA real (13 nov 2026): «Puedes pagar por Nequi al número que te compartí: 310 123 4567». La IA no ve los datos de pago:
    un número largo que no leyó en ninguna parte es inventado, y un cliente podría pagar ahí."""
    number = _nequi()
    invented = reply("Puedes pagar por Nequi al número que te compartí: 310 123 4567. Envíame el comprobante.", "info")
    _first, (_p, answer) = run_conversation("saas", [FIRST, ("Se me borró el número", invented, reads(True))], user_id="numero-inventado")
    assert "310 123 4567" not in answer and number in _details(answer) and _said(answer) == "Envíame el comprobante."
    # Un número que la IA sí leyó (el teléfono que dio el cliente) o un precio no se tocan.
    known = "el cliente dijo: mi teléfono es 3001234567"
    assert mask_invented_numbers("Anoté tu teléfono 300 123 4567. Son COP 1.320.000 al año.", known) == "Anoté tu teléfono 300 123 4567. Son COP 1.320.000 al año."
    assert mask_invented_numbers("La cuenta es 123-456789-01.", known) == f"La cuenta es {REDACTED_PAYMENT_VALUE}."
    assert mask_own_markers("Usa este número [número de Nequi] o el [link de pago].") == f"Usa este número {REDACTED_PAYMENT_VALUE} o el {REDACTED_PAYMENT_VALUE}."
    assert mask_own_markers("Lista: [1] uno") == "Lista: [1] uno"


def test_a_reported_payment_goes_to_the_team_when_the_reader_understands_it():
    """«Ya te consigné»: un pago avisado lo verifica el equipo, lo marque o no el asesor. Y si el asesor lo marca sin que el cliente lo
    diga («Ya voy a pagar»; pasó con la IA real), el chat no pasa al equipo."""
    turns = [
        FIRST,
        ("Ya voy a pagar", reply("¡Perfecto! Quedo atento.", "buy", payment_status="reportado"), reads()),
        ("ya te consigné", reply("¡Gracias!", "info"), reads(paid=True)),
    ]
    _first, (going, going_context), (_paid, paid_context) = run_conversation("saas", turns, user_id="pago-avisado", with_context=True)
    assert going == "¡Perfecto! Quedo atento." and not going_context.get("handoff")
    assert paid_context.get("handoff") is True and paid_context.get("handoff_reason") == "payment_review"


def test_the_ai_remembers_what_it_said_and_a_marker_never_the_details():
    """En su historial la IA ve lo que dijo ella y el marcador donde fueron los datos: no ve el mensaje con los datos (lo copiaría
    como si lo hubiera escrito) ni puede «recordar» un número (lo inventaría)."""
    runtime = load_tenant_runtime_yaml("saas")
    sent = PaymentDelivery("Te dejo los datos.", "💳 DATOS", "nequi", tail="Me avisas.")
    assert remembered_message(sent, runtime) == f"Te dejo los datos.\n\n{REDACTED_PAYMENT_VALUE}\n\nMe avisas."
    assert remembered_message(PaymentDelivery("", "💳 DATOS", "nequi"), runtime) == f"Te dejo aquí los datos para pagar por Nequi.\n\n{REDACTED_PAYMENT_VALUE}"


def test_the_word_limit_is_for_the_advisor_and_the_details_always_arrive_complete():
    number = _nequi()
    long_text = "¡Perfecto! " + " ".join(["Te cuento que el plan incluye la implementación acompañada."] * 20)
    (_p, answer), = run_conversation("saas", [("Te pago por Nequi", reply(long_text, "buy"), WANTS_NEQUI)], user_id="largo-con-datos")
    assert len(_said(answer).split()) < len(long_text.split()) and number in _details(answer)
    assert _details(answer).endswith("✅")


# ---------------------------------------------------------------------------
# Cualquier medio, de cualquier país, y varias cuentas del mismo medio
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("method", ["link", "nequi", "daviplata", "bank", "breb"])
def test_every_configured_method_reaches_the_customer(method):
    runtime = load_tenant_runtime_yaml("saas")
    expected = ejecutar_pago(runtime, method)
    assert expected, f"saas tiene {method}"
    said = {"link": "link de pago", "bank": "transferencia a Bancolombia", "breb": "Bre-B"}.get(method, method)
    (_p, answer), = run_conversation("saas", [(f"Envíame los datos de {said}", reply("Claro, ahí van.", "info"), reads(True, said))], user_id=f"medio-{method}")
    assert answer == f"Claro, ahí van.\n\n{expected}" and REDACTED_PAYMENT_VALUE not in answer


def _two_banks(document):
    for profile in document["payments"]:
        banks = [method for method in profile["transfer_methods"] if method["type"] == "bank"]
        if banks:
            second = {**banks[0], "bank": "Davivienda", "account_type": "corriente", "holder": "Software Norte S.A.S."}
            banks[0]["holder"] = "Software Norte S.A.S."
            profile["transfer_methods"].append(second)


def test_with_two_banks_the_customer_gets_the_one_he_names_or_both(monkeypatch, tmp_path):
    turns = [
        ("Envíame la cuenta de Davivienda", reply("Claro.", "info"), reads(True, "transferencia a Davivienda")),
        ("Mejor por Bancolombia", reply("Listo.", "buy"), reads(True, "Bancolombia")),
        ("Pásame los datos para pagar por transferencia bancaria", reply("Claro.", "buy"), reads(True, "transferencia bancaria")),
    ]
    (_a, davivienda), (_b, bancolombia), (_c, both) = run_with_document(monkeypatch, tmp_path / "dos-bancos", "saas", _two_banks, turns)
    assert "*Davivienda*\nCuenta corriente\n" in davivienda and "Bancolombia" not in davivienda
    assert "A nombre de: Software Norte S.A.S." in davivienda
    assert "*Bancolombia*\nCuenta de ahorros\n" in bancolombia and "Davivienda" not in bancolombia
    assert both.startswith("Claro.\n\n💳 *Datos para pagar*\n\n*Transferencia bancaria*\n")
    assert "*Bancolombia*\nCuenta de ahorros\n" in both and "*Davivienda*\nCuenta corriente\n" in both and both.count("A nombre de:") == 2


def test_with_two_banks_the_question_names_both(monkeypatch, tmp_path):
    turns = [("¿A qué cuenta pago?", reply(f"Paga a {REDACTED_PAYMENT_VALUE}.", "info"))]
    (_prompts, answer), = run_with_document(monkeypatch, tmp_path / "pregunta", "saas", _two_banks, turns)
    assert "transferencia a Bancolombia o Davivienda" in answer and answer.startswith("¿Con qué medio prefieres pagar")


def _peru(document):
    profile = document["payments"][0]
    number = next(method["number"] for method in profile["transfer_methods"] if method.get("number"))
    reference = next(method["reference"] for method in profile["transfer_methods"] if method.get("reference"))
    profile["transfer_methods"] = [
        {"type": "yape", "number": number, "holder": "Asesor Comercial S.A.C."},
        {"type": "custom", "name": "Nu", "data_label": "Cuenta", "reference": reference},
        {"type": "cash", "instructions": "Pagas al asesor cuando te visite."},
    ]
    profile["link_enabled"] = False


def test_a_business_of_another_country_and_a_single_method(monkeypatch, tmp_path):
    turns = [
        ("Por Yape", reply("Listo, ahí van.", "buy"), reads(True, "Yape")),
        ("¿Y si te pago por Nu?", reply("También, claro.", "info"), reads(True, "Nu")),
        ("Mejor en efectivo", reply("Perfecto.", "info"), reads(True, "efectivo")),
    ]
    (_a, yape), (_b, nu), (_c, cash) = run_with_document(monkeypatch, tmp_path / "peru", "saas", _peru, turns)
    assert "*Yape*" in yape and "A nombre de: Asesor Comercial S.A.C." in yape
    assert "*Nu*\nCuenta: " in nu
    # El efectivo no pide comprobante.
    assert _details(cash).startswith("💵 *Cómo pagar*\n\n*Efectivo o contraentrega*\nPagas al asesor cuando te visite.") and "comprobante" not in cash

    def _only_nequi(document):
        for profile in document["payments"]:
            profile["transfer_methods"] = [method for method in profile["transfer_methods"] if method["type"] == "nequi"]
            profile["link_enabled"] = False

    # Con un solo medio de pago, el asesor puede enviarlo por su cuenta (una vez), sin que el cliente lo nombre.
    alone = [("Listo, quiero pagar", reply("¡Perfecto! Ahí abajo te dejo los datos.", "buy", send_payment="nequi"), reads())]
    (prompts, answer), = run_with_document(monkeypatch, tmp_path / "un-medio", "saas", _only_nequi, alone)
    assert "*Nequi*" in _details(answer) and len(prompts) == 1


# ---------------------------------------------------------------------------
# El lector de pagos: lo que se le pregunta a la IA y lo que se hace con su respuesta
# ---------------------------------------------------------------------------

class _Reader:
    def __init__(self, answer):
        self.answer, self.calls = answer, []

    def classify(self, prompt, *, user_message, bot_config=None, **_kwargs):
        self.calls.append((prompt, user_message))
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


def test_the_reader_asks_the_ai_a_short_question_and_resolves_the_method():
    runtime = load_tenant_runtime_yaml("saas")
    runtime["conversation_history"] = [{"role": "assistant", "text": f"Te dejo los datos.\n\n{_nequi()}"}]
    reader = _Reader('{"recibe_datos_de_pago": true, "medio": "transferencia a Bancolombia (ahorros)", "dice_que_ya_pago": false}')
    reading = read_customer_message(reader, bot_config=None, runtime_yaml=runtime, user_message="pásame la de ahorros")
    assert reading == PaymentReading(wants_details=True, method="bank:bancolombia", says_paid=False)
    prompt, turn = reader.calls[0]
    assert "Medios de pago del negocio: Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B, link de pago" in prompt
    # Ni el número de pago ni nada del negocio fuera de los nombres de sus medios.
    assert _nequi() not in turn and REDACTED_PAYMENT_VALUE in turn and turn.endswith("Mensaje del cliente: «pásame la de ahorros»")
    assert len(prompt) < 2_600
    # Lo que se le cuenta al asesor.
    assert reading.for_prompt(runtime) == {"wants_details": True, "no_details_now": False, "method": "transferencia a Bancolombia", "says_paid": False}
    assert PaymentReading().for_prompt(runtime)["no_details_now"] is True


@pytest.mark.parametrize("answer", ["no es json", '{"otra": "cosa"}', RuntimeError("sin clave")])
def test_without_a_usable_answer_there_is_no_reading(answer):
    runtime = load_tenant_runtime_yaml("saas")
    assert read_customer_message(_Reader(answer), bot_config=None, runtime_yaml=runtime, user_message="hola") is None


def test_what_cannot_go_out_as_it_is():
    """`payment_problem`: por qué se le pide al asesor otra respuesta."""
    runtime = load_tenant_runtime_yaml("saas")
    assert payment_problem("Claro, con gusto.", runtime, asked=False) == {}
    assert payment_problem("No puedo enviarte el número.", runtime, asked=True) == {"refused": True}
    # «No tengo acceso a los datos» (con la IA real, al pedir el reenvío): es la misma negativa cuando ya están pagando.
    assert payment_problem("No tengo acceso a los números, pero puedo ayudarte.", runtime, asked=True, remembered="nequi") == {"refused": True}
    assert payment_problem("No tengo acceso a los datos de tu pedido anterior.", runtime, asked=False) == {}
    assert payment_problem("Lamentablemente, no recibimos pagos por Nequi.", runtime, asked=False) == {"denied": "Nequi"}
    assert payment_problem("Si no tienes Nequi, puedes usar Daviplata.", runtime, asked=False) == {}
    assert payment_problem("Te dejo el link.", runtime, send_payment="link de pago", asked=False) == {"unrequested": "pago en línea"}
    assert payment_problem(f"Te los dejo:\n{REDACTED_PAYMENT_VALUE}", runtime, asked=False, remembered="nequi") == {"unrequested": "Nequi"}
    # Si el cliente debe recibirlos, o no hubo lectura, la acción del asesor vale.
    assert payment_problem("Te dejo el link.", runtime, send_payment="link de pago", asked=True) == {}
    assert payment_problem("Te dejo el link.", runtime, send_payment="link de pago", asked=None) == {}
