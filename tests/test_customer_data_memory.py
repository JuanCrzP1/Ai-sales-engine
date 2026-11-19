"""Los datos que el cliente ya dio (`domain/conversation/customer_data.py`): el asesor los anota, el motor los recuerda y se los dice
en cada mensaje para que no se los vuelva a pedir.

La IA del asesor es simulada (`pipeline_harness`): aquí se prueba qué se guarda, qué ve el asesor después y que los datos de contacto
y de pago no se repiten. Si el asesor real anota bien y deja de pedir lo ya dado se mide con la IA real (`experiments/quality_lab`).
"""
from __future__ import annotations

import logging

from app.application.runtime import load_tenant_runtime_yaml
from app.domain.business_config.payment_data import payment_values
from app.domain.conversation import customer_data
from app.domain.conversation.memory import MemoryDomainService
from app.application.pipeline.turn_persistence import save_customer_data
from app.infrastructure.persistence.memory_repository import MemoryRepository
from app.infrastructure.ai.structured_output import parse_structured_output
from pipeline_harness import reads, reply, run_conversation

SLUG, CUSTOMER = "saas", "573001112233"
PHONE = "3001234567"


def _section(prompt: str) -> str:
    """«ESTA CONVERSACIÓN»: lo que el motor le dice al asesor de esta conversación."""
    return prompt[prompt.rindex("ESTA CONVERSACIÓN"):]


# ---------------------------------------------------------------------------------------------------- el orden de lo que anota


def test_each_data_keeps_one_name_and_contact_data_keeps_no_value():
    tidy = customer_data.tidy({"Nombre": " Juan  Camilo ", "phone": PHONE, "Email": "juan@correo.com", "Negocio": "tienda de ropa", "vacío": ""})
    assert tidy == {"nombre": "Juan Camilo", "teléfono": "dado", "correo": "dado", "negocio": "tienda de ropa"}


def test_a_long_number_is_kept_as_given_but_a_price_is_not_a_number_to_hide():
    tidy = customer_data.tidy({"referido por": f"mi primo {PHONE}", "presupuesto": "1.320.000"})
    assert tidy == {"referido por": "dado", "presupuesto": "1.320.000"}


def test_what_is_not_data_is_ignored_and_values_are_short():
    assert customer_data.tidy(["nombre"]) == {} and customer_data.tidy(None) == {}
    long_value = customer_data.tidy({"negocio": "x" * 200})["negocio"]
    assert len(long_value) == customer_data.MAX_VALUE_CHARS


def test_a_correction_wins_and_the_limit_only_stops_new_data():
    assert customer_data.merge({"nombre": "Juan"}, {"nombre": "Juan Camilo"}) == {"nombre": "Juan Camilo"}
    full = {f"dato {number}": "sí" for number in range(customer_data.MAX_ITEMS)}
    merged = customer_data.merge(full, {"dato 0": "no", "otro": "sí"})
    assert merged["dato 0"] == "no" and "otro" not in merged and len(merged) == customer_data.MAX_ITEMS


def test_the_advisor_reads_them_as_a_sentence():
    assert customer_data.described({}) == ""
    assert customer_data.described({"nombre": "Camila"}) == "su nombre (Camila)"
    assert customer_data.described({"nombre": "Camila", "teléfono": "dado", "negocio": "tienda de ropa"}) == (
        "su nombre (Camila), su teléfono y su negocio (tienda de ropa)"
    )


def test_the_parser_reads_customer_data_and_nothing_else_from_it():
    raw = '{"intent": "buy", "metadata": {"customer_data": {"nombre": "Camila", "ciudad": "", "otros": {"a": 1}}}, "response": "Listo"}'
    assert parse_structured_output(raw)["ai_metadata"]["customer_data"] == {"nombre": "Camila"}
    no_data = '{"intent": "buy", "metadata": {"customer_data": "Camila"}, "response": "Listo"}'
    assert parse_structured_output(no_data)["ai_metadata"]["customer_data"] == {}


# ---------------------------------------------------------------------------------------------------- de un mensaje al siguiente


def test_the_next_message_reminds_the_advisor_what_the_customer_already_gave():
    turns = [
        (f"Soy Juan Camilo, tengo una tienda de ropa, mi número es {PHONE}", reply(
            "¡Hola, Juan Camilo! ¿Qué plan te interesa?", customer_data={"nombre": "Juan Camilo", "teléfono": PHONE, "negocio": "tienda de ropa"},
        ), reads()),
        ("Quiero el plan básico", reply("¡Perfecto! Te cuento cómo empezar.", "buy"), reads()),
    ]
    (first_prompts, _), (second_prompts, _) = run_conversation(SLUG, turns, user_id="datos-dados")
    assert "Datos que ya te dio" not in first_prompts[-1]
    section = _section(second_prompts[-1])
    assert ("Datos que ya te dio el cliente: su nombre (Juan Camilo), su teléfono y su negocio (tienda de ropa). Ya los tienes: "
            "pídele solo lo que todavía falte.") in section
    # El teléfono no se le repite al asesor: lo ve en el chat, no junto a los medios de pago.
    assert PHONE not in second_prompts[-1]


def test_what_was_given_before_stays_when_the_next_message_gives_something_new():
    turns = [
        ("Soy Camila", reply("¡Hola, Camila!", customer_data={"nombre": "Camila"}), reads()),
        ("Vivo en Medellín", reply("¡Qué bien!", customer_data={"ciudad": "Medellín"}), reads()),
        ("¿Cuánto vale?", reply("Te cuento.", customer_data={}), reads()),
    ]
    *_rest, (last_prompts, _) = run_conversation(SLUG, turns, user_id="datos-suman")
    assert "su nombre (Camila) y su ciudad (Medellín)" in _section(last_prompts[-1])


def test_without_data_given_the_advisor_gets_no_reminder():
    turns = [("Hola", reply("¡Hola! ¿En qué te ayudo?"), reads()), ("¿Cuánto vale?", reply("Te cuento."), reads())]
    *_rest, (last_prompts, _) = run_conversation(SLUG, turns, user_id="sin-datos")
    assert "Datos que ya te dio" not in last_prompts[-1]


# ---------------------------------------------------------------------------------------------------- lo mínimo de datos personales


def _saved(raw: dict) -> dict:
    memory = MemoryDomainService(MemoryRepository())
    save_customer_data(memory, tenant_slug=SLUG, user_id=CUSTOMER, metadata={"customer_data": raw}, runtime_yaml=load_tenant_runtime_yaml(SLUG))
    return memory.get_customer_data(tenant_slug=SLUG, user_id=CUSTOMER)


def test_a_value_with_the_business_payment_data_is_never_kept():
    runtime = load_tenant_runtime_yaml(SLUG)
    payment = next(value for value in payment_values(runtime) if not value.isdigit())
    assert _saved({"nombre": "Camila", "referencia": f"pagué en {payment}"}) == {"nombre": "Camila"}


def test_a_phone_like_the_business_payment_number_still_counts_as_given():
    """El teléfono del cliente se guarda como «dado» antes de revisar los datos de pago: aunque coincida con el Nequi del negocio, el
    asesor sabe que ya lo dio y nunca ve el número."""
    runtime = load_tenant_runtime_yaml(SLUG)
    assert PHONE in payment_values(runtime)
    assert _saved({"teléfono": PHONE}) == {"teléfono": "dado"}


def test_the_log_says_which_data_was_given_never_what_it_is(caplog):
    with caplog.at_level(logging.INFO, logger="assistant"):
        _saved({"nombre": "Camila", "negocio": "tienda de ropa"})
    (record,) = [record for record in caplog.records if record.getMessage() == "datos_del_cliente"]
    assert record.datos == ["negocio", "nombre"]
    assert "Camila" not in str(record.__dict__) and "tienda de ropa" not in str(record.__dict__)


def test_starting_the_conversation_over_forgets_them():
    repository = MemoryRepository()
    memory = MemoryDomainService(repository)
    memory.set_customer_data(tenant_slug=SLUG, user_id=CUSTOMER, data={"nombre": "Camila"})
    memory.reset_conversation(tenant_slug=SLUG, user_id=CUSTOMER)
    assert memory.get_customer_data(tenant_slug=SLUG, user_id=CUSTOMER) == {}


def test_a_memory_without_customer_data_keeps_working():
    """Un almacenamiento sin estos datos (otra implementación de la memoria) no rompe el turno: el asesor responde sin el recordatorio."""
    memory = MemoryDomainService(object())
    assert memory.get_customer_data(tenant_slug=SLUG, user_id=CUSTOMER) == {}
    save_customer_data(memory, tenant_slug=SLUG, user_id=CUSTOMER, metadata={"customer_data": {"nombre": "Camila"}}, runtime_yaml={})
