"""La memoria del motor contra un PostgreSQL de verdad: lo que recuerda de cada cliente entre mensajes y entre servidores.

En la nube cada mensaje puede llegar a un servidor distinto (Vercel). La memoria es correcta solo si la base es la única fuente: ningún
servidor responde con lo que guardó en su RAM. Estas pruebas usan dos repositorios como si fueran dos servidores.

Necesitan una base PostgreSQL vacía para pruebas en `TEST_POSTGRES_URL` (en la integración continua la levanta un servicio; en este
equipo: `createdb ai_sales_engine_pruebas_memoria` y `TEST_POSTGRES_URL=postgresql+psycopg:///ai_sales_engine_pruebas_memoria`). Sin
ella se saltan. Crean las tablas del motor si faltan (`project/docs/postgresql_schema.sql`) y vacían las de la memoria antes de cada
prueba: nunca apuntes esta variable a una base con datos reales.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, text

from app.domain.conversation.memory import ConversationState, MemoryDomainService
from app.infrastructure.business_config.migrations import run_sql_file
from app.infrastructure.persistence.sql_memory import SQLMemoryRepository

URL = os.getenv("TEST_POSTGRES_URL", "").strip()
pytestmark = pytest.mark.skipif(not URL, reason="requiere TEST_POSTGRES_URL (una base PostgreSQL vacía para pruebas)")
SCHEMA = Path(__file__).resolve().parents[1] / "project" / "docs" / "postgresql_schema.sql"
MIGRATIONS = Path(__file__).resolve().parents[1] / "project" / "db" / "migrations"
SLUG, CUSTOMER = "memoria_pruebas", "573001112233"


@pytest.fixture(scope="module")
def engine():
    database = create_engine(URL)
    with database.begin() as conn:
        if conn.execute(text("SELECT to_regclass('public.tenants')")).scalar() is None:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            conn.exec_driver_sql(SCHEMA.read_text(encoding="utf-8"))

    # El índice de los mensajes más recientes, aplicado como lo aplica la nube.
    run_sql_file(database, MIGRATIONS / "0019_conversation_messages_recent.sql")
    yield database
    database.dispose()


@pytest.fixture(autouse=True)
def clean(engine):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM conversation_messages; DELETE FROM conversation_memory; DELETE FROM clients; DELETE FROM tenants WHERE slug LIKE 'memoria_%'"))
        conn.execute(text("INSERT INTO tenants (slug, name, status) VALUES (:slug, 'Memoria de pruebas', 'active')"), {"slug": SLUG})


def server(engine) -> SQLMemoryRepository:
    """Un servidor: su propio repositorio, con la misma base."""
    return SQLMemoryRepository(engine=engine)


def count_statements(engine):
    statements: list[str] = []

    def record(conn, cursor, statement, *args):  # noqa: ANN001 - firma de SQLAlchemy
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", record)
    return statements, lambda: event.remove(engine, "before_cursor_execute", record)


# --------------------------------------------------------------------------------------------- la base es la única fuente

def test_what_one_server_writes_is_what_the_next_one_reads(engine):
    """Producción (13 nov 2026): cada servidor respondía con lo que tenía en su RAM. Uno recordaba «Nequi» cuando el cliente ya había
    cambiado a Daviplata en otro."""
    first, second = server(engine), server(engine)
    first.set_payment_method(tenant_slug=SLUG, user_id=CUSTOMER, method="nequi")
    second.set_payment_method(tenant_slug=SLUG, user_id=CUSTOMER, method="daviplata")
    second.set_payment_status(tenant_slug=SLUG, user_id=CUSTOMER, status="reportado")
    assert first.get_payment_method(tenant_slug=SLUG, user_id=CUSTOMER) == "daviplata"
    assert first.get_payment_status(tenant_slug=SLUG, user_id=CUSTOMER) == "reportado"


def test_everything_the_engine_remembers_survives_a_change_of_server(engine):
    """Algunas cosas solo vivían en la RAM: la etapa, el modo y la hora del último mensaje se perdían al cambiar de servidor."""
    first, second = server(engine), server(engine)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    state = ConversationState(pain_detected=True, pain_timeline=["no alcanzo a responder"], stage="cierre", objections=1, last_cta="¿Empezamos?")
    writes = {
        "set_last_intent": {"intent": "buy"}, "set_detected_intent": {"intent": "buy"}, "set_last_pain": {"pain": "no alcanzo a responder"},
        "set_mode": {"mode": "cierre"}, "set_stage": {"stage": "pago"}, "set_last_response": {"response": "¡Listo!"},
        "set_conversation_state": {"state": state}, "set_last_user_message_at": {"sent_at": now},
        "set_initial_message_last_sent_at": {"sent_at": now - timedelta(minutes=5)},
        "set_op_state": {"state_dict": {"active_process": "payment", "active_option": "nequi", "pending_action": "report_payment"}},
    }
    for name, value in writes.items():
        getattr(first, name)(tenant_slug=SLUG, user_id=CUSTOMER, **value)
    first.save_message(tenant_slug=SLUG, user_id=CUSTOMER, message_text="Hola", role="user")
    read = lambda name: getattr(second, name)(tenant_slug=SLUG, user_id=CUSTOMER)  # noqa: E731
    assert (read("get_last_intent"), read("get_detected_intent"), read("get_last_pain")) == ("buy", "buy", "no alcanzo a responder")
    assert (read("get_mode"), read("get_stage"), read("get_last_response")) == ("cierre", "pago", "¡Listo!")
    assert read("get_conversation_state") == state
    assert read("get_last_user_message_at") == now and read("get_initial_message_last_sent_at") == now - timedelta(minutes=5)
    assert read("get_op_state")["active_option"] == "nequi"
    assert read("get_last_timestamp") is not None


def test_a_server_keeps_nothing_in_ram(engine):
    """Lo que se borra en la base (otro servidor, o el panel al eliminar un chat) ya no lo recuerda nadie."""
    first, second = server(engine), server(engine)
    first.set_payment_method(tenant_slug=SLUG, user_id=CUSTOMER, method="nequi")
    first.save_message(tenant_slug=SLUG, user_id=CUSTOMER, message_text="Te pago por Nequi")
    second.forget_contact(tenant_slug=SLUG, user_id=CUSTOMER)
    assert first.get_payment_method(tenant_slug=SLUG, user_id=CUSTOMER) == ""
    assert first.get_history(tenant_slug=SLUG, user_id=CUSTOMER) == []


# ----------------------------------------------------------------------------------------------- el historial más reciente

def test_the_ai_gets_the_latest_messages_not_the_first_ones(engine):
    """Producción (13 nov 2026): el historial traía los PRIMEROS 40 mensajes. En un chat de 56, la IA respondía con lo de hace rato."""
    memory = server(engine)
    for number in range(1, 51):
        memory.save_message(tenant_slug=SLUG, user_id=CUSTOMER, message_text=f"mensaje {number}", role="user" if number % 2 else "assistant")
    history = memory.get_history(tenant_slug=SLUG, user_id=CUSTOMER)
    assert history[-1] == {"role": "assistant", "text": "mensaje 50"}
    assert [item["text"] for item in history] == [f"mensaje {number}" for number in range(51 - len(history), 51)]


def test_messages_written_in_the_same_instant_keep_their_order(engine):
    memory = server(engine)
    with memory.turn(tenant_slug=SLUG, user_id=CUSTOMER):
        memory.save_message(tenant_slug=SLUG, user_id=CUSTOMER, message_text="¿Cuánto vale?", role="user")
        memory.save_message(tenant_slug=SLUG, user_id=CUSTOMER, message_text="Vale 110.000.", role="assistant")
    assert [item["text"] for item in server(engine).get_history(tenant_slug=SLUG, user_id=CUSTOMER)] == ["¿Cuánto vale?", "Vale 110.000."]


# ------------------------------------------------------------------------------------------------ una lectura por mensaje

def test_a_customer_message_reads_the_memory_once_and_writes_it_once(engine):
    """Antes cada dato se pedía por separado: unas 50 consultas por mensaje. Dentro de un turno se lee una vez al empezar y se guarda
    una vez al terminar, en una sola transacción."""
    memory = MemoryDomainService(server(engine))
    memory.repository.save_message(tenant_slug=SLUG, user_id=CUSTOMER, message_text="Hola")
    statements, stop = count_statements(engine)
    try:
        with memory.turn(tenant_slug=SLUG, user_id=CUSTOMER):
            for _ in range(10):
                memory.get_payment_method(tenant_slug=SLUG, user_id=CUSTOMER)
                memory.get_history(tenant_slug=SLUG, user_id=CUSTOMER)
                memory.get_conversation_state(tenant_slug=SLUG, user_id=CUSTOMER)
            memory.save_message(tenant_slug=SLUG, user_id=CUSTOMER, message_text="Quiero el plan")
            memory.set_payment_method(tenant_slug=SLUG, user_id=CUSTOMER, method="nequi")
            memory.set_last_intent(tenant_slug=SLUG, user_id=CUSTOMER, intent="buy")
            memory.save_message(tenant_slug=SLUG, user_id=CUSTOMER, message_text="¡Genial!", role="assistant")
            # Dentro del turno se ve lo que el mismo turno escribió.
            assert memory.get_payment_method(tenant_slug=SLUG, user_id=CUSTOMER) == "nequi"
            assert memory.get_history(tenant_slug=SLUG, user_id=CUSTOMER)[-1]["text"] == "¡Genial!"
    finally:
        stop()
    data = [statement for statement in statements if not statement.strip().upper().startswith(("BEGIN", "COMMIT", "ROLLBACK", "SELECT PG_", "SHOW"))]
    assert len(data) <= 6, data
    assert server(engine).get_payment_method(tenant_slug=SLUG, user_id=CUSTOMER) == "nequi"
    assert [item["text"] for item in server(engine).get_history(tenant_slug=SLUG, user_id=CUSTOMER)] == ["Hola", "Quiero el plan", "¡Genial!"]


def test_two_messages_at_once_do_not_erase_each_other(engine):
    """Dos mensajes del mismo cliente atendidos a la vez en dos servidores: cada uno guarda solo lo que cambió."""
    first, second = server(engine), server(engine)
    with first.turn(tenant_slug=SLUG, user_id=CUSTOMER), second.turn(tenant_slug=SLUG, user_id=CUSTOMER):
        first.set_payment_method(tenant_slug=SLUG, user_id=CUSTOMER, method="nequi")
        second.set_last_pain(tenant_slug=SLUG, user_id=CUSTOMER, pain="no alcanzo a responder")
    reader = server(engine)
    assert reader.get_payment_method(tenant_slug=SLUG, user_id=CUSTOMER) == "nequi"
    assert reader.get_last_pain(tenant_slug=SLUG, user_id=CUSTOMER) == "no alcanzo a responder"


# --------------------------------------------------------------------------------------------- si la base no responde

def test_without_database_the_engine_answers_and_does_not_split_its_memory(engine, caplog):
    """Antes, si la base fallaba, cada dato quedaba en la RAM de ese servidor: el siguiente mensaje, en otro servidor, no sabía nada y
    este sí (memoria partida). Ahora la memoria queda vacía en ese mensaje, el motor sigue respondiendo y queda el aviso."""
    broken = SQLMemoryRepository(engine=create_engine("postgresql+psycopg://nadie:nada@127.0.0.1:1/no_existe", connect_args={"connect_timeout": 1}))
    broken.set_payment_method(tenant_slug=SLUG, user_id=CUSTOMER, method="nequi")
    broken.save_message(tenant_slug=SLUG, user_id=CUSTOMER, message_text="Hola")
    assert broken.get_payment_method(tenant_slug=SLUG, user_id=CUSTOMER) == ""
    assert broken.get_history(tenant_slug=SLUG, user_id=CUSTOMER) == []
    with broken.turn(tenant_slug=SLUG, user_id=CUSTOMER):
        assert broken.get_conversation_state(tenant_slug=SLUG, user_id=CUSTOMER) == ConversationState(pain_timeline=[])
    assert any(record.message == "memoria_no_disponible" for record in caplog.records)


# ------------------------------------------------------------------------------------------------ olvidar a un cliente

def _rows(engine, table: str) -> list[str]:
    with engine.connect() as conn:
        return sorted(conn.execute(text(f"SELECT c.external_id FROM {table} x JOIN clients c ON c.id = x.client_id")).scalars().all()) if table != "clients" \
            else sorted(conn.execute(text("SELECT external_id FROM clients")).scalars().all())


def test_forgetting_a_contact_erases_their_messages_memory_and_record(engine):
    """Al eliminar un chat en el panel, el motor olvida todo de ese cliente, y solo de ese."""
    memory = server(engine)
    for customer in (CUSTOMER, "573009998877"):
        memory.save_message(tenant_slug=SLUG, user_id=customer, message_text="hola")
        memory.set_payment_method(tenant_slug=SLUG, user_id=customer, method="nequi")
    memory.forget_contact(tenant_slug=SLUG, user_id=CUSTOMER)
    for table in ("clients", "conversation_messages", "conversation_memory"):
        assert _rows(engine, table) == ["573009998877"], table


def test_forgetting_the_test_conversations_erases_only_the_prueba_contacts(engine):
    """«Probar asistente» guarda su memoria con contactos «prueba-<sesión>»: borrar las pruebas borra solo esos, nunca a un cliente."""
    memory = server(engine)
    for customer in (CUSTOMER, "prueba-aaaa", "prueba-bbbb", "pruebaxcliente"):
        memory.save_message(tenant_slug=SLUG, user_id=customer, message_text="hola")
    memory.forget_contacts_with_prefix(tenant_slug=SLUG, prefix="prueba-")
    assert _rows(engine, "clients") == [CUSTOMER, "pruebaxcliente"]
    assert _rows(engine, "conversation_messages") == [CUSTOMER, "pruebaxcliente"]


def test_forgetting_reports_a_failure_instead_of_hiding_it():
    """Si no se pudo borrar, el panel debe saberlo (y no borra el chat): aquí sí se avisa."""
    broken = SQLMemoryRepository(engine=create_engine("postgresql+psycopg://nadie:nada@127.0.0.1:1/no_existe", connect_args={"connect_timeout": 1}))
    with pytest.raises(Exception):
        broken.forget_contact(tenant_slug=SLUG, user_id=CUSTOMER)


# ------------------------------------------------------------------------------------------------ el motor completo

def _engine_turn(engine, statements_engine, message: str, reply_text: str, *, slug: str = "saas"):
    """Un mensaje atendido por el motor completo en un servidor nuevo, con la memoria en la base. Devuelve el prompt y la respuesta."""
    import json as _json

    from app.application.ai_pipeline import AIPipeline

    pipeline = AIPipeline(memory_service=MemoryDomainService(server(statements_engine)))
    prompts: list[str] = []

    def generate(prompt, *, user_message, bot_config=None, history=None, **_kwargs):
        prompts.append(str(prompt) + "\n\nHISTORIAL:\n" + "\n".join(item["content"] for item in history or []))
        return _json.dumps({"intent": "info", "metadata": {}, "response": reply_text})

    pipeline.runtime.generate = generate
    pipeline.runtime.classify = lambda *args, **kwargs: _json.dumps({"recibe_datos_de_pago": False, "medio": "", "dice_que_ya_pago": False})
    response, *_rest = pipeline.run(tenant=type("T", (), {"slug": slug, "name": slug, "id": slug})(), user_message=message, user_id=CUSTOMER,
                                    bot_config=None, conversation_history=[], faq_results=[], yaml_config=None, include_metadata=True)
    return prompts[-1], response


def test_the_engine_continues_the_conversation_on_another_server_and_sees_the_latest_messages(engine):
    """Cada mensaje en un servidor distinto, como en Vercel: el siguiente ve lo último que se habló, también pasados 40 mensajes."""
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO tenants (slug, name, status) VALUES ('saas', 'Software', 'active') ON CONFLICT (slug) DO NOTHING"))
        conn.execute(text("DELETE FROM clients WHERE tenant_id = (SELECT id FROM tenants WHERE slug = 'saas')"))
    seed = server(engine)
    for number in range(1, 45):
        seed.save_message(tenant_slug="saas", user_id=CUSTOMER, message_text=f"mensaje viejo {number}", role="user" if number % 2 else "assistant")
    _engine_turn(engine, engine, "Me interesa el plan básico", "¡Genial! ¿Cómo te llamas?")
    statements, stop = count_statements(engine)
    try:
        prompt, _reply = _engine_turn(engine, engine, "Me llamo Juan Camilo", "Gracias, Juan Camilo.")
    finally:
        stop()
    assert "Me interesa el plan básico" in prompt and "¡Genial! ¿Cómo te llamas?" in prompt
    assert "mensaje viejo 1\n" not in prompt
    # Un mensaje del motor: unas pocas consultas a la memoria (antes, unas 50).
    data = [statement for statement in statements if not statement.strip().upper().startswith(("BEGIN", "COMMIT", "ROLLBACK", "SELECT PG_", "SHOW"))]
    assert len(data) <= 6, data
    assert server(engine).get_history(tenant_slug="saas", user_id=CUSTOMER)[-2:] == [
        {"role": "user", "text": "Me llamo Juan Camilo"}, {"role": "assistant", "text": "Gracias, Juan Camilo."}]


def test_the_conversation_summary_is_shared_between_servers(engine):
    first, second = server(engine), server(engine)
    until = datetime.now(timezone.utc).replace(microsecond=0)
    first.set_summary(tenant_slug=SLUG, user_id=CUSTOMER, summary="Juan Camilo quiere el Plan Básico.", until=until)
    assert second.get_summary(tenant_slug=SLUG, user_id=CUSTOMER) == ("Juan Camilo quiere el Plan Básico.", until)
    first.save_message(tenant_slug=SLUG, user_id=CUSTOMER, message_text="Hola")
    (entry,) = second.get_history_entries(tenant_slug=SLUG, user_id=CUSTOMER)
    assert entry["text"] == "Hola" and entry["at"] is not None
