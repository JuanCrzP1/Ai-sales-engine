"""La bandeja de conversaciones: cada chat queda guardado con su negocio y su canal, y cada usuario solo ve los de sus negocios.

Las conversaciones del área de pruebas también se guardan, con el canal `prueba` y los datos de pago ocultos.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin_api.main import create_app
from app.business_config_application.access import BusinessAccess
from app.domain.business_config.access import Principal
from app.domain.business_config.ai_settings import AICredentials, AssistantTurn, KeyCheck
from app.domain.business_config.conversations import NewMessage
from app.domain.business_config.payment_data import REDACTED_PAYMENT_VALUE, payment_values
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import (
    build_assistant_lab_service,
    build_business_config_service,
    create_business_config_engine,
    create_local_schema,
)
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.notification_store import NotificationStore
from app.infrastructure.business_config.tables import business_members, conversation_entries, conversations, tenants
from app.infrastructure.config.config_service import ConfigService
from app.infrastructure.config.legacy_store_migration import import_prepared, prepare_tenant

ROOT_DIR = Path(__file__).resolve().parents[1]
MIGRATION = ROOT_DIR / "project" / "db" / "migrations" / "0004_conversations.sql"
ANA = Principal(user_id="usuario-ana", email="ana@example.com")
BETO = Principal(user_id="usuario-beto", email="beto@example.com")
TOKENS = {"token-de-ana": ANA, "token-de-beto": BETO}
KEY = "sk-or-v1-clave-ficticia-de-ana-000000001"


class Tokens:
    def verify(self, token: str) -> Principal | None:
        return TOKENS.get(token)


class Runner:
    """El motor de mentira: repite el primer dato de pago del negocio, como haría al cerrar una venta."""

    def reply(self, *, tenant_slug, sections, credentials, session_id, message):
        values = payment_values(sections)
        return AssistantTurn(reply=f"Puedes pagar a {values[0]}" if values else "Hola", intent="buy")

    def reset(self, *, tenant_slug, session_id):
        return None


class Verifier:
    def verify(self, credentials):
        return KeyCheck(True, "La clave funciona.")


def _as(user: str) -> dict[str, str]:
    return {"Authorization": f"Bearer token-de-{user}"}


@pytest.fixture
def platform(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'plataforma.sqlite3').as_posix()}")
    create_local_schema(engine)
    key = Fernet.generate_key().decode()
    service = build_business_config_service(engine, secrets_key=key)
    for slug in ("restaurant", "clinic", "saas"):
        import_prepared(service, prepare_tenant(ConfigService(), slug))
    with engine.begin() as conn:
        ids = {row.slug: row.id for row in conn.execute(select(tenants.c.slug, tenants.c.id))}
        for slug, user in (("restaurant", ANA), ("clinic", ANA), ("saas", BETO)):
            conn.execute(business_members.insert().values(tenant_id=ids[slug], user_id=user.user_id, role="owner", created_at=datetime.now(timezone.utc)))
    store = ConversationStore(engine)
    lab = build_assistant_lab_service(engine, service, secrets_key=key, verifier=Verifier(), runner=Runner())
    app = create_app(
        service, lab, access=BusinessAccess(service, BusinessMembersStore(engine)), verifier=Tokens(), conversations=store, notifications=NotificationStore(engine)
    )
    yield engine, store, lab, TestClient(app)
    engine.dispose()


# ---------------------------------------------------------------------------
# Almacén
# ---------------------------------------------------------------------------

def test_each_contact_has_one_thread_per_channel_that_keeps_its_order(platform):
    _engine, store, _lab, _client = platform
    first = store.record("restaurant", channel="whatsapp", contact_ref="+573001112233", contact_name="Laura", messages=[NewMessage("customer", "Hola, ¿tienen mesa?"), NewMessage("assistant", "¡Claro! ¿Para cuántos?", "info")])
    second = store.record("restaurant", channel="whatsapp", contact_ref="+573001112233", contact_name=None, messages=[NewMessage("customer", "Para 4"), NewMessage("assistant", "Listo, te espero.")])
    other_channel = store.record("restaurant", channel="instagram", contact_ref="laura.ig", contact_name="Laura", messages=[NewMessage("customer", "Hola")])
    assert first == second != other_channel
    summary, messages = store.thread(first)
    assert [(item.author, item.body) for item in messages] == [
        ("customer", "Hola, ¿tienen mesa?"), ("assistant", "¡Claro! ¿Para cuántos?"), ("customer", "Para 4"), ("assistant", "Listo, te espero."),
    ]
    assert (summary.business_slug, summary.channel, summary.contact_name, summary.message_count) == ("restaurant", "whatsapp", "Laura", 4)
    assert summary.last_message_preview == "Listo, te espero."
    assert messages[0].intent is None and messages[1].intent == "info"


def test_the_store_only_accepts_known_channels_and_authors(platform):
    _engine, store, _lab, _client = platform
    with pytest.raises(ValueError):
        store.record("restaurant", channel="fax", contact_ref="1", contact_name=None, messages=[NewMessage("customer", "Hola")])
    with pytest.raises(ValueError):
        store.record("restaurant", channel="web", contact_ref="1", contact_name=None, messages=[NewMessage("robot", "Hola")])


def test_the_migration_matches_the_tables():
    sql = MIGRATION.read_text(encoding="utf-8")
    for table in (conversations, conversation_entries):
        body = re.search(rf"CREATE TABLE IF NOT EXISTS {table.name} \((.*?)\n\);", sql, re.S).group(1)
        columns = {match.group(1) for match in re.finditer(r"^\s+([a-z_]+)\s+[A-Z]+", body, re.M)} - {"constraint"}
        # La 0005 agregó a `conversations` las columnas del traspaso a una persona.
        added_later = {"needs_human", "handoff_requested_at"} if table is conversations else set()
        assert columns == {column.name for column in table.columns} - added_later, table.name
    assert "REFERENCES tenants(id) ON DELETE CASCADE" in sql and "REFERENCES conversations(id) ON DELETE CASCADE" in sql


# ---------------------------------------------------------------------------
# La bandeja por usuario
# ---------------------------------------------------------------------------

def test_the_inbox_shows_the_chats_of_all_my_businesses_and_where_each_comes_from(platform):
    _engine, store, _lab, client = platform
    store.record("restaurant", channel="whatsapp", contact_ref="+571", contact_name="Laura", messages=[NewMessage("customer", "Hola restaurante")])
    store.record("clinic", channel="telegram", contact_ref="99", contact_name="Pedro", messages=[NewMessage("customer", "Hola clínica")])
    store.record("saas", channel="whatsapp", contact_ref="+572", contact_name="Cliente de Beto", messages=[NewMessage("customer", "Hola saas")])

    mine = client.get("/api/conversations", headers=_as("ana")).json()
    assert {(item["business"]["slug"], item["channel"], item["contact_name"]) for item in mine} == {("restaurant", "whatsapp", "Laura"), ("clinic", "telegram", "Pedro")}
    assert all(item["business"]["name"] for item in mine)
    assert [item["contact_name"] for item in client.get("/api/conversations?business=clinic", headers=_as("ana")).json()] == ["Pedro"]
    assert [item["channel"] for item in client.get("/api/conversations?channel=whatsapp", headers=_as("ana")).json()] == ["whatsapp"]
    assert [item["contact_name"] for item in client.get("/api/conversations", headers=_as("beto")).json()] == ["Cliente de Beto"]


def test_a_chat_of_someone_else_answers_like_one_that_does_not_exist(platform):
    _engine, store, _lab, client = platform
    theirs = store.record("saas", channel="whatsapp", contact_ref="+572", contact_name="Cliente de Beto", messages=[NewMessage("customer", "Mi número es 3001234567")])
    response = client.get(f"/api/conversations/{theirs}", headers=_as("ana"))
    missing = client.get("/api/conversations/00000000-0000-0000-0000-000000000000", headers=_as("ana"))
    assert (response.status_code, response.json()) == (missing.status_code, missing.json()) == (404, {"code": "not_found", "message": "Esa conversación no existe.", "issues": []})
    assert "3001234567" not in response.text
    assert client.get("/api/conversations?business=saas", headers=_as("ana")).status_code == 404
    assert client.get("/api/conversations/no-es-un-id", headers=_as("ana")).status_code == 404
    assert client.get(f"/api/conversations/{theirs}", headers=_as("beto")).json()["messages"][0]["body"] == "Mi número es 3001234567"


def test_the_inbox_needs_a_session_and_valid_filters(platform):
    _engine, _store, _lab, client = platform
    assert client.get("/api/conversations").status_code == 401
    assert client.get("/api/conversations?channel=fax", headers=_as("ana")).status_code == 422


def test_the_home_shows_what_happened_today(platform):
    _engine, store, _lab, client = platform
    store.record("restaurant", channel="whatsapp", contact_ref="+571", contact_name="Laura", messages=[NewMessage("customer", "Hola"), NewMessage("assistant", "Hola, ¿en qué te ayudo?")])
    store.record("restaurant", channel="prueba", contact_ref="a" * 32, contact_name="Prueba en el panel", messages=[NewMessage("customer", "Hola")])
    activity = client.get("/api/businesses/restaurant/activity", headers=_as("ana")).json()
    assert activity == {"conversations": 2, "conversations_today": 2, "messages_today": 3, "test_conversations": 1, "waiting_human": 0}
    tomorrow = store.activity("restaurant", since=datetime.now(timezone.utc) + timedelta(days=1))
    assert (tomorrow.conversations, tomorrow.conversations_since, tomorrow.messages_since) == (2, 0, 0)
    assert client.get("/api/businesses/restaurant/activity", headers=_as("beto")).status_code == 404


# ---------------------------------------------------------------------------
# El área de pruebas también queda en la bandeja
# ---------------------------------------------------------------------------

def test_the_playground_chats_are_saved_as_tests_without_payment_data(platform):
    _engine, _store, lab, client = platform
    assert client.put("/api/businesses/restaurant/ai", headers=_as("ana"), json={"model": None, "api_key": KEY}).status_code == 200
    reply = client.post("/api/businesses/restaurant/playground", headers=_as("ana"), json={"message": "¿Cómo pago?", "source": "published"}).json()
    sections = lab._configs.compile_sections("restaurant", 1)
    secret = payment_values(sections)[0]
    assert secret in reply["reply"], "el cliente de la prueba sí ve el dato, como lo vería un cliente real"

    [conversation] = client.get("/api/conversations?business=restaurant", headers=_as("ana")).json()
    assert (conversation["channel"], conversation["contact_name"], conversation["message_count"]) == ("prueba", "Prueba en el panel", 2)
    thread = client.get(f"/api/conversations/{conversation['id']}", headers=_as("ana")).json()
    assert [(item["author"], item["body"]) for item in thread["messages"]] == [("customer", "¿Cómo pago?"), ("assistant", f"Puedes pagar a {REDACTED_PAYMENT_VALUE}")]
    assert secret not in str(thread) and secret not in str(conversation)


def test_if_the_inbox_fails_the_playground_still_answers(platform, monkeypatch):
    _engine, store, _lab, client = platform
    client.put("/api/businesses/restaurant/ai", headers=_as("ana"), json={"model": None, "api_key": KEY})

    def broken(*_args, **_kwargs):
        raise RuntimeError("base caída")

    monkeypatch.setattr(ConversationStore, "record", broken)
    response = client.post("/api/businesses/restaurant/playground", headers=_as("ana"), json={"message": "Hola", "source": "published"})
    assert response.status_code == 200 and response.json()["reply"]
    assert isinstance(AICredentials("openrouter", None, KEY), AICredentials)


# ---------------------------------------------------------------------------
# Pasar a una persona: la conversación queda marcada y el equipo recibe un aviso
# ---------------------------------------------------------------------------

def _handoff(store, slug="restaurant", contact="+571", name="Laura"):
    return store.record(
        slug, channel="whatsapp", contact_ref=contact, contact_name=name,
        messages=[NewMessage("customer", "Quiero hablar con alguien"), NewMessage("assistant", "Te paso con un asesor.")], handoff=True,
    )


def test_a_handoff_marks_the_conversation_and_notifies_once_per_wait(platform):
    engine, store, _lab, client = platform
    conversation = _handoff(store)
    _handoff(store)  # El cliente sigue escribiendo mientras espera: no se repite el aviso.
    summary, _messages = store.thread(conversation)
    assert summary.needs_human and summary.handoff_requested_at is not None

    body = client.get("/api/notifications", headers=_as("ana")).json()
    assert body["unread"] == 1
    [item] = body["items"]
    assert (item["kind"], item["title"], item["body"], item["conversation_id"], item["read"]) == (
        "handoff", "Laura pidió hablar con una persona", "Quiero hablar con alguien", conversation, False,
    )
    assert item["business"] == {"slug": "restaurant", "name": summary.business_name}

    resolved = client.post(f"/api/conversations/{conversation}/handoff/resolve", headers=_as("ana")).json()
    assert resolved["needs_human"] is False
    _handoff(store)  # Una espera nueva sí avisa otra vez.
    assert client.get("/api/notifications", headers=_as("ana")).json()["unread"] == 2


def test_each_person_marks_their_own_notifications_and_never_sees_others(platform):
    engine, store, _lab, client = platform
    with engine.begin() as conn:
        restaurant = conn.execute(select(tenants.c.id).where(tenants.c.slug == "restaurant")).scalar_one()
        conn.execute(business_members.insert().values(tenant_id=restaurant, user_id="usuario-carla", role="owner", created_at=datetime.now(timezone.utc)))
    TOKENS["token-de-carla"] = Principal(user_id="usuario-carla", email="carla@example.com")
    try:
        _handoff(store)
        _handoff(store, slug="saas", contact="+579", name="Cliente de Beto")
        assert client.post("/api/notifications/read", headers=_as("ana"), json={}).json() == {"marked": 1}
        assert client.get("/api/notifications", headers=_as("ana")).json()["unread"] == 0
        assert client.get("/api/notifications", headers=_as("carla")).json()["unread"] == 1, "lo leído es de cada persona"
        assert [item["title"] for item in client.get("/api/notifications", headers=_as("beto")).json()["items"]] == ["Cliente de Beto pidió hablar con una persona"]
        theirs = client.get("/api/notifications", headers=_as("beto")).json()["items"][0]["id"]
        assert client.post("/api/notifications/read", headers=_as("ana"), json={"ids": [theirs]}).json() == {"marked": 0}
        assert client.get("/api/notifications", headers=_as("beto")).json()["unread"] == 1
    finally:
        TOKENS.pop("token-de-carla")


def test_the_inbox_filters_who_waits_for_a_person_and_only_the_owner_resolves(platform):
    _engine, store, _lab, client = platform
    waiting = _handoff(store)
    store.record("restaurant", channel="web", contact_ref="w1", contact_name="Pedro", messages=[NewMessage("customer", "Hola")])
    assert [item["contact_name"] for item in client.get("/api/conversations?waiting_human=true", headers=_as("ana")).json()] == ["Laura"]
    assert client.get("/api/businesses/restaurant/activity", headers=_as("ana")).json()["waiting_human"] == 1
    assert client.post(f"/api/conversations/{waiting}/handoff/resolve", headers=_as("beto")).status_code == 404
    assert store.thread(waiting)[0].needs_human
    assert client.get("/api/notifications").status_code == 401


def test_the_playground_handoff_reaches_the_team_as_a_test(platform, monkeypatch):
    _engine, _store, _lab, client = platform
    monkeypatch.setattr(Runner, "reply", lambda self, **_kwargs: AssistantTurn(reply="Te paso con un asesor.", intent="support", handoff=True))
    client.put("/api/businesses/restaurant/ai", headers=_as("ana"), json={"model": None, "api_key": KEY})
    client.post("/api/businesses/restaurant/playground", headers=_as("ana"), json={"message": "Quiero una persona", "source": "published"})
    [conversation] = client.get("/api/conversations?waiting_human=true", headers=_as("ana")).json()
    assert conversation["channel"] == "prueba"
    assert client.get("/api/notifications", headers=_as("ana")).json()["items"][0]["title"] == "Prueba: Prueba en el panel pidió hablar con una persona"


def test_the_handoff_migration_matches_the_tables():
    from app.infrastructure.business_config.tables import notification_reads, notifications

    sql = (ROOT_DIR / "project" / "db" / "migrations" / "0005_handoff_notifications.sql").read_text(encoding="utf-8")
    for table in (notifications, notification_reads):
        body = re.search(rf"CREATE TABLE IF NOT EXISTS {table.name} \((.*?)\n\);", sql, re.S).group(1)
        columns = {match.group(1) for match in re.finditer(r"^\s+([a-z_]+)\s+[A-Z]+", body, re.M)} - {"constraint", "primary"}
        assert columns == {column.name for column in table.columns}, table.name
    assert "ADD COLUMN IF NOT EXISTS needs_human" in sql and "ADD COLUMN IF NOT EXISTS handoff_requested_at" in sql


def test_a_local_database_from_before_receives_the_new_columns(tmp_path):
    from sqlalchemy import inspect, text

    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'vieja.sqlite3').as_posix()}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE conversations (id CHAR(32) PRIMARY KEY, tenant_id CHAR(32), channel TEXT, contact_ref TEXT, contact_name TEXT, status TEXT, started_at DATETIME, last_message_at DATETIME, last_message_preview TEXT, message_count INTEGER)"))
    create_local_schema(engine)
    assert {"needs_human", "handoff_requested_at"} <= {column["name"] for column in inspect(engine).get_columns("conversations")}
    engine.dispose()


def test_the_engine_says_when_the_assistant_passes_the_chat_to_a_person():
    from types import SimpleNamespace

    from app.application.ai_pipeline import AIPipeline
    from app.domain.business_config.ai_settings import AICredentials as Credentials
    from app.domain.conversation.memory import MemoryDomainService
    from app.infrastructure.persistence.memory_repository import MemoryRepository
    from pipeline_harness import reply

    def answer(text):
        pipeline = AIPipeline(memory_service=MemoryDomainService(MemoryRepository()), ai_loader=lambda _slug: Credentials("openrouter", None, KEY))
        pipeline.runtime.generate = lambda prompt, *, user_message, bot_config=None: reply(text)
        _reply, _ai_used, metadata = pipeline.run(
            tenant=SimpleNamespace(slug="restaurant", name="restaurant", id="restaurant"), user_message="Necesito ayuda con mi pedido",
            user_id="cliente-1", bot_config=None, conversation_history=[], faq_results=[], yaml_config=None, include_metadata=True,
        )
        return metadata

    assert answer("Claro, te paso con un asesor de nuestro equipo.").get("handoff") is True
    assert not answer("Claro, ¿qué pedido es?").get("handoff")
