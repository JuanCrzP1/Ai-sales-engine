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
    app = create_app(service, lab, access=BusinessAccess(service, BusinessMembersStore(engine)), verifier=Tokens(), conversations=store)
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
        assert columns == {column.name for column in table.columns}, table.name
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
    assert activity == {"conversations": 2, "conversations_today": 2, "messages_today": 3, "test_conversations": 1}
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
