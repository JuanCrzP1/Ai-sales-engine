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
from app.infrastructure.business_config.ai_usage_store import AIUsageStore
from app.infrastructure.business_config.commerce_store import CommerceStore
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
from app.infrastructure.business_config.usage_store import UsageCounterStore
from app.infrastructure.business_config.example_businesses import import_example, load_example
from app.infrastructure.business_config.quick_reply_store import QuickReplyStore

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


class FakeMessenger:
    """El canal del cliente: lo que el equipo responde desde el panel sale por aquí."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str, str]] = []
        self.files: list[tuple] = []
        self.fail = False

    def send_text(self, business_slug, channel, contact_ref, text):
        from app.domain.business_config.channels import ChannelError

        if self.fail:
            raise ChannelError("WhatsApp no está conectado en este negocio. Conéctalo en Canales para responder desde aquí.")
        self.sent.append((business_slug, channel, contact_ref, text))
        return f"WA-AGENTE-{len(self.sent)}"

    def send_media(self, business_slug, channel, contact_ref, kind, media, caption):
        from app.domain.business_config.channels import ChannelError

        if self.fail:
            raise ChannelError("WhatsApp no está conectado en este negocio. Conéctalo en Canales para responder desde aquí.")
        self.files.append((business_slug, contact_ref, kind, media.mime_type, media.file_name, media.content, caption))
        return f"WA-ARCHIVO-{len(self.files)}"


MESSENGER = FakeMessenger()


@pytest.fixture
def platform(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'plataforma.sqlite3').as_posix()}")
    create_local_schema(engine)
    key = Fernet.generate_key().decode()
    service = build_business_config_service(engine, secrets_key=key)
    for slug in ("restaurant", "clinic", "saas"):
        import_example(service, load_example(slug))
    with engine.begin() as conn:
        ids = {row.slug: row.id for row in conn.execute(select(tenants.c.slug, tenants.c.id))}
        for slug, user in (("restaurant", ANA), ("clinic", ANA), ("saas", BETO)):
            conn.execute(business_members.insert().values(tenant_id=ids[slug], user_id=user.user_id, role="owner", created_at=datetime.now(timezone.utc)))
    store = ConversationStore(engine)
    lab = build_assistant_lab_service(engine, service, secrets_key=key, verifier=Verifier(), runner=Runner())
    app = create_app(
        service,
        lab,
        access=BusinessAccess(service, BusinessMembersStore(engine)),
        verifier=Tokens(),
        conversations=store,
        notifications=NotificationStore(engine),
        usage=UsageCounterStore(engine),
        messenger=MESSENGER,
        commerce=CommerceStore(engine),
        ai_usage=AIUsageStore(engine),
        quick_replies=QuickReplyStore(engine),
    )
    MESSENGER.sent.clear()
    MESSENGER.files.clear()
    MESSENGER.fail = False
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
        # La 0005 agregó a `conversations` las columnas del traspaso a una persona; la 0009, las de la bandeja en vivo; la 0010, la
        # etapa; la 0011, la espera del cliente y cuándo retomó la IA.
        added_later = (
            {
                "needs_human", "handoff_requested_at", "ai_paused", "handoff_reason", "unread_count", "assistant_typing_until", "updated_at",
                "stage", "customer_waiting_since", "ai_resumed_at",
            }
            if table is conversations
            else {"kind", "status", "provider_message_id", "media_id", "media_note", "updated_at"}
        )
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

    def answer(text, **model_metadata):
        pipeline = AIPipeline(memory_service=MemoryDomainService(MemoryRepository()), ai_loader=lambda _slug: Credentials("openrouter", None, KEY))
        pipeline.runtime.generate = lambda prompt, *, user_message, bot_config=None, **_kwargs: reply(text, **model_metadata)
        _reply, _ai_used, metadata = pipeline.run(
            tenant=SimpleNamespace(slug="restaurant", name="restaurant", id="restaurant"), user_message="Necesito ayuda con mi pedido",
            user_id="cliente-1", bot_config=None, conversation_history=[], faq_results=[], yaml_config=None, include_metadata=True,
        )
        return metadata

    assert answer("Claro, te paso con un asesor de nuestro equipo.").get("handoff") is True
    assert not answer("Claro, ¿qué pedido es?").get("handoff")
    # El modelo dice por qué pasa a una persona: la pidió o reclama. Un pago reportado también pasa: solo el equipo lo verifica.
    asked = answer("Listo, te paso con el equipo por este mismo chat.", handoff="persona")
    assert (asked["handoff"], asked["handoff_reason"]) == (True, "human_request")
    assert answer("Lamento lo que pasó, te paso con el equipo.", handoff="reclamo")["handoff_reason"] == "complaint"
    assert answer("Gracias, el equipo lo verifica.", payment_status="reportado")["handoff_reason"] == "payment_review"
    assert not answer("Te ayudo con eso.", handoff="cualquier cosa").get("handoff")


def test_the_live_inbox_migration_matches_the_tables():
    from app.infrastructure.business_config.tables import conversation_media

    sql = (ROOT_DIR / "project" / "db" / "migrations" / "0009_conversations_live.sql").read_text(encoding="utf-8")
    body = re.search(r"CREATE TABLE IF NOT EXISTS conversation_media \((.*?)\n\);", sql, re.S).group(1)
    columns = {match.group(1) for match in re.finditer(r"^\s+([a-z_]+)\s+[A-Z]+", body, re.M)}
    assert columns == {column.name for column in conversation_media.columns}
    added = {(table, column) for table, column in re.findall(r"ALTER TABLE (\w+) ADD COLUMN IF NOT EXISTS (\w+)", sql)}
    assert added == {
        ("conversations", name) for name in ("ai_paused", "handoff_reason", "unread_count", "assistant_typing_until", "updated_at")
    } | {("conversation_entries", name) for name in ("kind", "status", "provider_message_id", "media_id", "media_note", "updated_at")}
    for table, column in added:
        assert column in (conversations if table == "conversations" else conversation_entries).columns, (table, column)
    for index in ("conversation_entries_provider_key", "conversation_entries_live_idx", "conversation_entries_provider_idx"):
        assert f"CREATE {'UNIQUE ' if index.endswith('_key') else ''}INDEX IF NOT EXISTS {index}" in sql


# ---------------------------------------------------------------------------
# La bandeja en vivo: lo nuevo, responder desde el panel, la IA pausada, leídos y archivos
# ---------------------------------------------------------------------------

def _whatsapp_chat(store: ConversationStore, *, text: str = "Hola", message_id: str = "WA-1"):
    from app.domain.business_config.conversations import MediaFile

    return store.append(
        "restaurant", channel="whatsapp", contact_ref="573009998877", contact_name="Ana",
        message=NewMessage("customer", text, kind="image" if message_id.startswith("FOTO") else "text", provider_message_id=message_id),
        media=MediaFile("image/jpeg", b"jpeg") if message_id.startswith("FOTO") else None,
    )


def test_the_live_inbox_returns_only_what_changed_since_the_cursor(platform):
    _engine, store, _lab, client = platform
    first = _whatsapp_chat(store)
    whole = client.get(f"/api/conversations/{first.conversation_id}/live", headers=_as("ana")).json()
    assert [m["body"] for m in whole["messages"]] == ["Hola"] and whole["cursor"].endswith("Z")
    assert whole["conversation"]["unread_count"] == 1 and whole["conversation"]["can_reply"] is True
    later = datetime.now(timezone.utc) + timedelta(seconds=10)
    assert client.get(f"/api/conversations/{first.conversation_id}/live", params={"since": later.isoformat()}, headers=_as("ana")).json()["messages"] == []
    assert client.get(f"/api/conversations/{first.conversation_id}/live", params={"since": "ayer"}, headers=_as("ana")).status_code == 422
    assert client.get(f"/api/conversations/{first.conversation_id}/live", headers=_as("beto")).status_code == 404


def test_the_same_channel_message_is_saved_once(platform):
    _engine, store, _lab, _client = platform
    first, again = _whatsapp_chat(store), _whatsapp_chat(store)
    assert first.created and not again.created and first.entry_id == again.entry_id
    assert store.thread(first.conversation_id)[0].message_count == 1


def test_the_team_replies_from_the_panel_and_the_assistant_steps_aside(platform):
    _engine, store, _lab, client = platform
    chat = _whatsapp_chat(store)
    store.request_handoff(chat.conversation_id, "human_request", "Quiero un asesor")
    response = client.post(f"/api/conversations/{chat.conversation_id}/messages", json={"text": "Hola Ana, soy Juan del equipo"}, headers=_as("ana"))
    assert response.status_code == 201
    assert (response.json()["author"], response.json()["status"]) == ("agent", "sent")
    assert MESSENGER.sent == [("restaurant", "whatsapp", "573009998877", "Hola Ana, soy Juan del equipo")]
    summary = client.get(f"/api/conversations/{chat.conversation_id}/live", headers=_as("ana")).json()["conversation"]
    assert (summary["ai_paused"], summary["needs_human"]) == (True, False)
    resumed = client.post(f"/api/conversations/{chat.conversation_id}/assistant", json={"active": True}, headers=_as("ana")).json()
    assert (resumed["ai_paused"], resumed["needs_human"], resumed["handoff_reason"]) == (False, False, None)
    assert client.post(f"/api/conversations/{chat.conversation_id}/messages", json={"text": "x"}, headers=_as("beto")).status_code == 404


def test_a_reply_the_channel_does_not_deliver_is_kept_as_not_sent(platform):
    _engine, store, _lab, client = platform
    chat = _whatsapp_chat(store)
    MESSENGER.fail = True
    response = client.post(f"/api/conversations/{chat.conversation_id}/messages", json={"text": "Hola"}, headers=_as("ana"))
    assert response.status_code == 502 and "Conéctalo en Canales" in response.json()["message"]
    assert store.thread(chat.conversation_id)[1][-1].status == "failed"


def test_test_chats_and_empty_replies_cannot_be_sent(platform):
    _engine, store, _lab, client = platform
    test_chat = store.record("restaurant", channel="prueba", contact_ref="s1", contact_name="Prueba", messages=[NewMessage("customer", "Hola")])
    assert client.post(f"/api/conversations/{test_chat}/messages", json={"text": "Hola"}, headers=_as("ana")).status_code == 422
    chat = _whatsapp_chat(store)
    assert client.post(f"/api/conversations/{chat.conversation_id}/messages", json={"text": ""}, headers=_as("ana")).status_code == 422
    assert MESSENGER.sent == []


PDF = b"%PDF-1.7\n catalogo"


def _send_file(client, conversation_id, content, mime, *, name="", caption="", user="ana"):
    from urllib.parse import quote

    headers = {**_as(user), "Content-Type": mime, "X-File-Name": quote(name), "X-Caption": quote(caption)}
    return client.post(f"/api/conversations/{conversation_id}/attachments", content=content, headers=headers)


def test_the_team_sends_a_file_with_its_text_and_the_assistant_steps_aside(platform):
    _engine, store, _lab, client = platform
    chat = _whatsapp_chat(store)
    response = _send_file(client, chat.conversation_id, PDF, "application/pdf", name="../Catálogo noviembre.pdf", caption="Aquí está el catálogo, Ana 👇")
    assert response.status_code == 201, response.text
    sent = response.json()
    assert (sent["author"], sent["status"], sent["kind"], sent["body"]) == ("agent", "sent", "document", "Aquí está el catálogo, Ana 👇")
    assert MESSENGER.files == [("restaurant", "573009998877", "document", "application/pdf", "Catálogo noviembre.pdf", PDF, "Aquí está el catálogo, Ana 👇")]
    # El archivo queda en el chat, como los que llegan, y se puede abrir desde el panel.
    media = store.thread(chat.conversation_id)[1][-1].media
    assert (media.mime_type, media.file_name) == ("application/pdf", "Catálogo noviembre.pdf")
    assert client.get(f"/api/conversations/{chat.conversation_id}/media/{media.id}", headers=_as("ana")).content == PDF
    assert client.get(f"/api/conversations/{chat.conversation_id}/live", headers=_as("ana")).json()["conversation"]["ai_paused"] is True
    # Una foto sin texto también sale.
    photo = _send_file(client, chat.conversation_id, b"\xff\xd8\xff\xe0foto", "image/jpeg", name="foto.jpg")
    assert photo.status_code == 201 and photo.json()["kind"] == "image" and MESSENGER.files[-1][2] == "image"


@pytest.mark.parametrize(
    "content, mime, caption, reason",
    [
        (b"", "application/pdf", "", "vacío"),
        (b"MZ ejecutable", "application/x-msdownload", "", "no se puede enviar"),
        (b"\xff\xd8\xff foto", "application/pdf", "", "no es lo que dice ser"),
        (PDF, "application/pdf", "x" * 1025, "hasta 1024"),
    ],
)
def test_a_file_that_cannot_go_is_refused_with_the_reason(platform, content, mime, caption, reason):
    _engine, store, _lab, client = platform
    chat = _whatsapp_chat(store)
    response = _send_file(client, chat.conversation_id, content, mime, caption=caption)
    assert response.status_code == 422 and reason in response.json()["message"]
    assert MESSENGER.files == []


def test_a_file_over_4_mb_or_to_someone_else_or_to_a_test_chat_is_refused(platform):
    _engine, store, _lab, client = platform
    chat = _whatsapp_chat(store)
    too_big = _send_file(client, chat.conversation_id, b"%PDF" + b"0" * (4 * 1024 * 1024), "application/pdf")
    assert too_big.status_code == 413 and "4 MB" in too_big.json()["message"]
    assert _send_file(client, chat.conversation_id, PDF, "application/pdf", user="beto").status_code == 404
    test_chat = store.record("restaurant", channel="prueba", contact_ref="s1", contact_name="Prueba", messages=[NewMessage("customer", "Hola")])
    assert _send_file(client, test_chat, PDF, "application/pdf").status_code == 422
    assert MESSENGER.files == []


def test_the_file_of_a_quick_reply_goes_to_the_chat_from_the_server(platform):
    from urllib.parse import quote

    _engine, store, _lab, client = platform
    chat = _whatsapp_chat(store)
    upload = client.post(
        "/api/businesses/restaurant/quick-replies/files", content=PDF, headers={**_as("ana"), "Content-Type": "application/pdf", "X-File-Name": quote("Menú.pdf")}
    ).json()
    sent = client.post(f"/api/conversations/{chat.conversation_id}/quick-reply-file", json={"file_id": upload["file_id"], "caption": "El menú, Ana"}, headers=_as("ana"))
    assert sent.status_code == 201, sent.text
    assert (sent.json()["kind"], sent.json()["body"], sent.json()["media"]["file_name"]) == ("document", "El menú, Ana", "Menú.pdf")
    assert MESSENGER.files == [("restaurant", "573009998877", "document", "application/pdf", "Menú.pdf", PDF, "El menú, Ana")]
    # Solo archivos del negocio de esa conversación.
    foreign = client.post(
        "/api/businesses/clinic/quick-replies/files", content=PDF, headers={**_as("ana"), "Content-Type": "application/pdf"}
    ).json()
    refused = client.post(f"/api/conversations/{chat.conversation_id}/quick-reply-file", json={"file_id": foreign["file_id"]}, headers=_as("ana"))
    assert refused.status_code == 404 and len(MESSENGER.files) == 1


def test_a_file_the_channel_does_not_deliver_is_kept_as_not_sent(platform):
    _engine, store, _lab, client = platform
    chat = _whatsapp_chat(store)
    MESSENGER.fail = True
    response = _send_file(client, chat.conversation_id, PDF, "application/pdf", name="catalogo.pdf")
    assert response.status_code == 502 and "Conéctalo en Canales" in response.json()["message"]
    last = store.thread(chat.conversation_id)[1][-1]
    assert (last.status, last.media.file_name) == ("failed", "catalogo.pdf")


def test_opening_a_chat_marks_it_read_and_its_files_are_served_safely(platform):
    _engine, store, _lab, client = platform
    chat = _whatsapp_chat(store, text="", message_id="FOTO1")
    assert client.post(f"/api/conversations/{chat.conversation_id}/read", headers=_as("ana")).status_code == 204
    assert store.thread(chat.conversation_id)[0].unread_count == 0
    media = store.thread(chat.conversation_id)[1][0].media
    image = client.get(f"/api/conversations/{chat.conversation_id}/media/{media.id}", headers=_as("ana"))
    assert (image.status_code, image.content, image.headers["content-type"]) == (200, b"jpeg", "image/jpeg")
    assert image.headers["content-security-policy"] == "default-src 'none'; sandbox" and image.headers["x-content-type-options"] == "nosniff"
    assert client.get(f"/api/conversations/{chat.conversation_id}/media/{media.id}", headers=_as("beto")).status_code == 404


def test_a_file_that_could_run_scripts_is_only_downloaded(platform):
    from app.domain.business_config.conversations import MediaFile

    _engine, store, _lab, client = platform
    chat = store.append(
        "restaurant", channel="whatsapp", contact_ref="573009998877", contact_name="Ana",
        message=NewMessage("customer", "", kind="document", provider_message_id="DOC1"), media=MediaFile("image/svg+xml", b"<svg onload=alert(1)>"),
    )
    media = store.thread(chat.conversation_id)[1][0].media
    response = client.get(f"/api/conversations/{chat.conversation_id}/media/{media.id}", headers=_as("ana"))
    assert response.headers["content-type"] == "application/octet-stream" and response.headers["content-disposition"] == "attachment"


def test_receipts_only_move_forward_and_a_handoff_notifies_once_per_wait(platform):
    _engine, store, _lab, _client = platform
    chat = _whatsapp_chat(store)
    sent = store.append("restaurant", channel="whatsapp", contact_ref="573009998877", contact_name=None, message=NewMessage("assistant", "Hola", provider_message_id="WA-OUT-1"))
    assert store.mark_delivery("restaurant", ["WA-OUT-1"], "read") == 1
    assert store.mark_delivery("restaurant", ["WA-OUT-1"], "delivered") == 0
    assert store.mark_delivery("saas", ["WA-OUT-1"], "read") == 0  # los recibos de otro negocio no tocan este
    assert next(m for m in store.thread(chat.conversation_id)[1] if m.id == sent.entry_id).status == "read"
    store.request_handoff(chat.conversation_id, "complaint", "Me robaron")
    store.request_handoff(chat.conversation_id, "complaint", "¿Hola?")
    items, _unread = NotificationStore(_engine).recent(["restaurant"], ANA.user_id, limit=10)
    assert [item.title for item in items] == ["Ana tiene un reclamo"]


# ---------------------------------------------------------------------------
# Clientes, ventas y reportes
# ---------------------------------------------------------------------------

def _chat(store: ConversationStore, contact: str, name: str, *messages: NewMessage, channel: str = "whatsapp"):
    result = None
    for index, message in enumerate(messages):
        result = store.append("restaurant", channel=channel, contact_ref=contact, contact_name=name, message=message)
    return result


def test_each_customer_reaches_a_stage_that_only_moves_forward(platform):
    _engine, store, _lab, client = platform
    ana = _chat(store, "573001", "Ana", NewMessage("customer", "Hola"), NewMessage("assistant", "¡Hola! ¿Qué buscas?", "info"))
    _chat(store, "573002", "Beto", NewMessage("customer", "Quiero pedir"), NewMessage("assistant", "¡Listo! ¿Cómo pagas?", "buy"),
          NewMessage("customer", "¿y cuánto vale?"), NewMessage("assistant", "Vale $20.000", "info"))
    _chat(store, "s1", "Prueba", NewMessage("customer", "Hola"), channel="prueba")
    store.request_handoff(ana.conversation_id, "payment_review", "Ya pagué")
    found = {item["name"]: item for item in client.get("/api/businesses/restaurant/customers", headers=_as("ana")).json()}
    assert {name: item["stage"] for name, item in found.items()} == {"Ana": "payment", "Beto": "ready"}  # la prueba no es un cliente
    assert [c["name"] for c in client.get("/api/businesses/restaurant/customers", params={"stage": "ready"}, headers=_as("ana")).json()] == ["Beto"]
    assert [c["name"] for c in client.get("/api/businesses/restaurant/customers", params={"q": "an"}, headers=_as("ana")).json()] == ["Ana"]
    assert client.get("/api/businesses/restaurant/customers", headers=_as("beto")).status_code == 404


def test_recording_a_sale_makes_the_customer_a_client_and_cancelling_it_keeps_the_record(platform):
    _engine, store, _lab, client = platform
    ana = _chat(store, "573001", "Ana", NewMessage("customer", "Te pagué"), NewMessage("assistant", "Lo verifico", "buy"))
    store.request_handoff(ana.conversation_id, "payment_review", "Te pagué")
    body = {"customer_name": "Ana", "description": "2 hamburguesas", "amount": "40000", "currency": "cop", "conversation_id": ana.conversation_id}
    created = client.post("/api/businesses/restaurant/sales", json=body, headers=_as("ana"))
    assert created.status_code == 201 and (created.json()["amount"], created.json()["currency"], created.json()["created_by"]) == ("40000.00", "COP", "ana@example.com")
    (customer,) = client.get("/api/businesses/restaurant/customers", headers=_as("ana")).json()
    assert (customer["stage"], customer["purchases"], customer["spent"], customer["needs_human"]) == ("customer", 1, {"COP": "40000.00"}, False)
    cancelled = client.post(f"/api/businesses/restaurant/sales/{created.json()['id']}/cancel", headers=_as("ana")).json()
    assert cancelled["status"] == "cancelled"
    assert [s["status"] for s in client.get("/api/businesses/restaurant/sales", headers=_as("ana")).json()] == ["cancelled"]
    assert client.get("/api/businesses/restaurant/customers", headers=_as("ana")).json()[0]["spent"] == {}


@pytest.mark.parametrize(
    ("change", "field"),
    [({"customer_name": " "}, "customer_name"), ({"description": ""}, "description"), ({"amount": "-5"}, "amount"), ({"amount": "abc"}, "amount"), ({"currency": "pesos"}, "currency")],
)
def test_a_sale_with_bad_data_is_rejected_on_its_field(platform, change, field):
    _engine, _store, _lab, client = platform
    body = {"customer_name": "Ana", "description": "Pedido", "amount": "1000", "currency": "COP", **change}
    response = client.post("/api/businesses/restaurant/sales", json=body, headers=_as("ana"))
    assert response.status_code == 422 and response.json()["issues"][0]["path"].split(".")[-1] == field


def test_a_sale_cannot_point_to_another_business_conversation(platform):
    _engine, store, _lab, client = platform
    other = store.append("saas", channel="whatsapp", contact_ref="1", contact_name="X", message=NewMessage("customer", "Hola"))
    body = {"customer_name": "X", "description": "Plan", "amount": "1", "currency": "USD", "conversation_id": other.conversation_id}
    assert client.post("/api/businesses/restaurant/sales", json=body, headers=_as("ana")).status_code == 404


def test_the_report_counts_the_period_by_day_and_compares_it_with_the_previous_one(platform):
    _engine, store, _lab, client = platform
    _chat(store, "573001", "Ana", NewMessage("customer", "Hola"), NewMessage("assistant", "¡Hola!", "info"), NewMessage("agent", "Soy Juan"))
    store.request_handoff(_chat(store, "573002", "Beto", NewMessage("customer", "Quiero un asesor")).conversation_id, "human_request")
    client.post("/api/businesses/restaurant/sales", json={"customer_name": "Ana", "description": "Pedido", "amount": "25000", "currency": "COP"}, headers=_as("ana"))
    report = client.get("/api/businesses/restaurant/reports", params={"days": 7}, headers=_as("ana")).json()
    assert len(report["days"]) == 7 and report["days"][-1]["day"] == report["until"]
    assert report["totals"] | {"revenue": None} == {
        "conversations": 2, "customer_messages": 2, "assistant_messages": 1, "agent_messages": 1, "handoffs": 1, "sales": 1, "revenue": None,
    }
    assert report["totals"]["revenue"] == {"COP": "25000.00"} and report["previous"]["sales"] == 0
    assert report["funnel"] == {"new": 2, "interested": 1, "ready": 0, "payment": 0, "customer": 0}
    assert report["handoffs_by_reason"] == {"human_request": 1}
    assert sum(day["new_conversations"] for day in report["days"]) == 2
    assert client.get("/api/businesses/restaurant/reports", headers=_as("beto")).status_code == 404
