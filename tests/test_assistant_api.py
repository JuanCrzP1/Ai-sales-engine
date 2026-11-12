"""Integraciones: claves de API y la API del asistente (`POST /api/v1/assistant/messages`).

- Una clave es de un solo negocio, se muestra una sola vez y en la base solo queda su huella. Se puede revocar.
- La API responde con el mismo asistente de WhatsApp: lo publicado, la memoria del cliente, el paso a una persona según el
  horario del equipo y los avisos. El chat queda en la bandeja (canal `api`), con los datos de pago ocultos; la respuesta al
  sistema que llamó sale completa.
- Si el chat lo atiende una persona, la API no responde (`attended_by: team`). Un pedido repetido (`Idempotency-Key`) devuelve
  la misma respuesta sin gastar la IA.
- Errores claros (401, 403, 400, 422, 429) con `{code, message, issues}`.
- El panel crea, lista y revoca claves (solo de sus negocios), muestra la dirección de la API y la prueba con lo publicado.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.admin_api.main import create_app
from app.api.controllers import assistant_api as assistant_api_controller
from app.application.attention.resume_sweep import ResumeSweep
from app.business_config_application import usage_limits as usage_module
from app.business_config_application.access import BusinessAccess
from app.domain.business_config.access import Principal
from app.domain.business_config.ai_settings import AssistantTurn
from app.domain.business_config.api_keys import (
    KEY_PREFIX,
    MAX_ACTIVE_KEYS,
    SCOPE_ASSISTANT_CHAT,
    fingerprint,
    looks_like_key,
    validated_new_key,
)
from app.domain.business_config.assistant_api import parse_message
from app.domain.business_config.errors import InvalidFieldsError
from app.domain.business_config.usage_limits import UsageLimit
from app.infrastructure.business_config import runtime_access
from app.infrastructure.business_config.api_key_store import ApiKeyStore
from app.infrastructure.business_config.attention_store import AttentionStore
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import (
    _refresh_outdated_checks,
    build_business_config_service,
    create_business_config_engine,
    create_local_schema,
)
from app.infrastructure.business_config.example_businesses import import_example, load_example
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.notification_store import NotificationStore
from app.infrastructure.business_config.tables import api_keys, business_members, conversations, tenants
from app.infrastructure.business_config.usage_store import UsageCounterStore
from pipeline_harness import publish_document

URL = "/assistant/messages"
PAYMENT_NUMBER = "3001234567"


# ---------------------------------------------------------------------------
# El formato
# ---------------------------------------------------------------------------

def test_the_request_accepts_what_automation_platforms_send():
    nested = parse_message({"contact": {"id": "573001112233", "name": "Laura"}, "message": "Hola"})
    flat = parse_message({"contact_id": "573001112233", "contact_name": "Laura", "message": {"text": "Hola"}})
    phone = parse_message({"phone": 573001112233, "message": "Hola"})
    assert nested == flat and phone.contact_id == "573001112233" and phone.contact_name is None
    with pytest.raises(InvalidFieldsError) as error:
        parse_message({"contact": {"id": ""}, "message": "x" * 4001})
    assert {issue.path for issue in error.value.issues} == {"contact.id", "message"}
    with pytest.raises(InvalidFieldsError):
        parse_message(["no", "es", "un", "objeto"])


@pytest.mark.parametrize(
    "body, path, variable",
    [
        ({"contact": {"id": "{customer.phone}", "name": "Laura"}, "message": "Hola"}, "contact.id", "{customer.phone}"),
        ({"contact": {"id": "573001112233", "name": "{nombre}"}, "message": "Hola"}, "contact.name", "{nombre}"),
        ({"contact": {"id": "573001112233"}, "message": "{last_message}"}, "message", "{last_message}"),
        ({"contact_id": "{{ $json.phone }}", "message": "Hola"}, "contact.id", "{{ $json.phone }}"),
    ],
)
def test_a_variable_the_platform_did_not_replace_is_rejected_and_named(body, path, variable):
    # Si pasara, todos los clientes de esa plataforma caerían en un solo contacto «{nombre}» y el asistente mezclaría sus historias.
    with pytest.raises(InvalidFieldsError) as error:
        parse_message(body)
    [issue] = error.value.issues
    assert issue.path == path and f"«{variable}»" in issue.message and "no reemplazó" in issue.message


def test_a_customer_can_still_write_braces_in_the_message():
    assert parse_message({"contact": {"id": "1"}, "message": "Mi código es {A1} y quiero el plan"}).text == "Mi código es {A1} y quiero el plan"


def test_a_new_key_is_named_and_says_what_it_can_do():
    assert validated_new_key("  Leona   producción ", [SCOPE_ASSISTANT_CHAT, SCOPE_ASSISTANT_CHAT]) == ("Leona producción", (SCOPE_ASSISTANT_CHAT,))
    with pytest.raises(InvalidFieldsError) as error:
        validated_new_key("", ["config:write"])
    assert {issue.path for issue in error.value.issues} == {"name", "scopes"}


# ---------------------------------------------------------------------------
# Las claves en la base
# ---------------------------------------------------------------------------

@pytest.fixture
def store(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'claves.sqlite3').as_posix()}")
    create_local_schema(engine)
    service = build_business_config_service(engine, secrets_key="x" * 43 + "=")
    for slug in ("restaurant", "saas"):
        import_example(service, load_example(slug))
    yield engine
    engine.dispose()


def test_a_key_is_shown_once_and_only_its_fingerprint_is_stored(store):
    keys = ApiKeyStore(store)
    created = keys.create("restaurant", name="Leona", scopes=(SCOPE_ASSISTANT_CHAT,), created_by="ana@example.com")
    assert created.secret.startswith(KEY_PREFIX) and looks_like_key(created.secret) and created.key.prefix == created.secret[:15]
    with store.connect() as conn:
        row = conn.execute(select(api_keys)).one()
    assert row.key_hash == fingerprint(created.secret) and created.secret not in {str(value) for value in row}
    identity = keys.authenticate(created.secret)
    assert (identity.business_slug, identity.name, identity.scopes) == ("restaurant", "Leona", (SCOPE_ASSISTANT_CHAT,))
    assert keys.list_keys("restaurant")[0].last_used_at is not None
    assert keys.list_keys("saas") == []
    assert keys.authenticate(created.secret[:-1] + ("x" if created.secret[-1] != "x" else "y")) is None
    assert keys.authenticate("sk-or-v1-otra-cosa") is None


def test_a_revoked_key_stops_working_and_stays_listed_after_the_active_ones(store):
    keys = ApiKeyStore(store)
    old = keys.create("restaurant", name="Vieja", scopes=(SCOPE_ASSISTANT_CHAT,), created_by=None)
    new = keys.create("restaurant", name="Nueva", scopes=(SCOPE_ASSISTANT_CHAT,), created_by=None)
    revoked = keys.revoke("restaurant", old.key.id)
    assert not revoked.active and keys.authenticate(old.secret) is None and keys.authenticate(new.secret) is not None
    assert [key.name for key in keys.list_keys("restaurant")] == ["Nueva", "Vieja"]
    from app.domain.business_config.errors import BusinessNotFoundError

    with pytest.raises(BusinessNotFoundError):
        keys.revoke("saas", new.key.id)


def test_a_business_has_a_limit_of_active_keys(store):
    keys = ApiKeyStore(store)
    for index in range(MAX_ACTIVE_KEYS):
        keys.create("restaurant", name=f"Clave {index}", scopes=(SCOPE_ASSISTANT_CHAT,), created_by=None)
    with pytest.raises(InvalidFieldsError):
        keys.create("restaurant", name="Una más", scopes=(SCOPE_ASSISTANT_CHAT,), created_by=None)


def test_an_old_local_database_accepts_api_conversations(tmp_path):
    """Una base local de antes de la 0012: la tabla de conversaciones igual a la de hoy, pero con la restricción vieja."""
    from sqlalchemy.schema import CreateTable

    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'anterior.sqlite3').as_posix()}")
    create_local_schema(engine)
    old = str(CreateTable(conversations).compile(engine)).replace("'api', ", "")
    service = build_business_config_service(engine, secrets_key="x" * 43 + "=")
    import_example(service, load_example("restaurant"))
    from app.domain.business_config.conversations import NewMessage

    ConversationStore(engine).append("restaurant", channel="whatsapp", contact_ref="573", contact_name="Ana", message=NewMessage("customer", "Hola"))
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys=OFF")
        conn.exec_driver_sql("PRAGMA legacy_alter_table=ON")
        conn.exec_driver_sql("ALTER TABLE conversations RENAME TO vieja")
        for index in conversations.indexes:
            conn.exec_driver_sql(f"DROP INDEX IF EXISTS {index.name}")
        conn.exec_driver_sql(old)
        conn.exec_driver_sql("INSERT INTO conversations SELECT * FROM vieja")
        conn.exec_driver_sql("DROP TABLE vieja")
        conn.commit()
    _refresh_outdated_checks(engine)
    store = ConversationStore(engine)
    store.append("restaurant", channel="api", contact_ref="1", contact_name="Laura", message=NewMessage("customer", "Hola"))
    assert sorted(item.channel for item in store.recent(["restaurant"], channel=None, limit=5)) == ["api", "whatsapp"]
    with engine.connect() as conn:
        assert conn.exec_driver_sql("PRAGMA foreign_key_check").all() == []
    engine.dispose()


# ---------------------------------------------------------------------------
# La API del asistente
# ---------------------------------------------------------------------------

class FakeAI:
    """El asistente del negocio: responde lo que se le diga y anota lo que leyó."""

    reply = "Claro. El plan cuesta $50.000 y lo pagas por Nequi al 3001234567."
    metadata: dict = {"intent": "buy"}
    ai_used = True
    calls: list[dict] = []

    def generate_business_reply(self, **kwargs):
        FakeAI.calls.append(kwargs)
        return FakeAI.reply, FakeAI.ai_used, dict(FakeAI.metadata)


@pytest.fixture
def api(monkeypatch, tmp_path):
    url = publish_document(monkeypatch, tmp_path, "restaurant")
    engine = create_business_config_engine(url)
    key = ApiKeyStore(engine).create("restaurant", name="Leona", scopes=(SCOPE_ASSISTANT_CHAT,), created_by=None)
    FakeAI.reply, FakeAI.metadata, FakeAI.ai_used, FakeAI.calls = (
        "Claro. El plan cuesta $50.000 y lo pagas por Nequi al 3001234567.", {"intent": "buy"}, True, [],
    )
    alerts: list[str | None] = []
    monkeypatch.setattr(assistant_api_controller, "AIService", FakeAI)
    monkeypatch.setattr(assistant_api_controller, "deliver_alert", alerts.append)
    app = FastAPI()
    app.include_router(assistant_api_controller.router)
    yield TestClient(app), {"Authorization": f"Bearer {key.secret}"}, engine, alerts
    engine.dispose()
    runtime_access.dispose_shared_engines()


def _thread(engine):
    store = ConversationStore(engine)
    (summary,) = store.recent(["restaurant"], channel="api", limit=5)
    return summary, store.thread(summary.id)[1]


def test_the_assistant_answers_and_the_chat_lands_in_the_inbox(api):
    client, auth, engine, _alerts = api
    response = client.post(URL, headers=auth, json={"contact": {"id": "573001112233", "name": "Laura"}, "message": "¿Cuánto cuesta?"})
    body = response.json()
    assert response.status_code == 200
    # El sistema que llamó recibe la respuesta completa, para enviársela al cliente.
    assert body["reply"] == FakeAI.reply and body["parts"] == [FakeAI.reply]
    assert {key: body[key] for key in ("handoff", "attended_by", "intent", "fallback", "duplicate")} == {
        "handoff": False, "attended_by": "assistant", "intent": "buy", "fallback": False, "duplicate": False,
    }
    assert body["stage"] == "ready"
    assert FakeAI.calls[0]["user_id"] == "573001112233" and FakeAI.calls[0]["tenant"].slug == "restaurant"
    summary, messages = _thread(engine)
    assert summary.id == body["conversation_id"] and summary.contact_name == "Laura" and summary.channel == "api"
    # En la bandeja, los datos de pago quedan ocultos.
    assert [(m.author, PAYMENT_NUMBER in m.body) for m in messages] == [("customer", False), ("assistant", False)]


def test_when_the_chat_needs_a_person_the_api_says_so_and_then_stays_quiet(api):
    client, auth, engine, alerts = api
    FakeAI.reply, FakeAI.metadata = "Te paso con alguien del equipo.", {"intent": "info", "handoff": True, "handoff_reason": "human_request"}
    first = client.post(URL, headers=auth, json={"contact_id": "573009998877", "message": "Quiero hablar con una persona"}).json()
    # El restaurante no tiene horario: siempre hay alguien, así que la IA se pausa y el cliente sabe cuánto tarda el equipo.
    assert (first["handoff"], first["handoff_reason"], first["attended_by"]) == (True, "human_request", "team")
    assert first["parts"] == ["Te paso con alguien del equipo.", "Una persona de nuestro equipo te responderá en unos 10 minutos."]
    assert first["reply"] == "\n\n".join(first["parts"]) and len(alerts) == 1 and alerts[0]
    second = client.post(URL, headers=auth, json={"contact_id": "573009998877", "message": "¿Hola?"}).json()
    assert (second["reply"], second["attended_by"], second["handoff"]) == ("", "team", True)
    assert len(FakeAI.calls) == 1
    summary, _messages = _thread(engine)
    assert (summary.ai_paused, summary.needs_human) == (True, True)


def test_the_same_request_twice_gets_the_same_answer_without_spending_the_ai(api):
    client, auth, engine, _alerts = api
    request = {"contact": {"id": "573001112233"}, "message": "Hola"}
    first = client.post(URL, headers={**auth, "Idempotency-Key": "leona-msg-1"}, json=request).json()
    again = client.post(URL, headers={**auth, "Idempotency-Key": "leona-msg-1"}, json=request).json()
    # Exactamente la misma respuesta (con el dato de pago que recibió el cliente), sin gastar la IA ni repetir el mensaje.
    assert len(FakeAI.calls) == 1 and again["reply"] == first["reply"] == FakeAI.reply and again["duplicate"] is True
    assert again["conversation_id"] == first["conversation_id"] and len(_thread(engine)[1]) == 2
    # Guardada cifrada: el dato de pago no se lee en la base.
    from app.infrastructure.business_config.tables import api_idempotency

    with engine.connect() as conn:
        assert PAYMENT_NUMBER not in conn.execute(select(api_idempotency.c.response_ciphertext)).scalar_one()


def test_without_ai_it_answers_with_the_business_fallback_and_says_so(api):
    client, auth, _engine, _alerts = api
    FakeAI.reply, FakeAI.ai_used = "Gracias por escribirnos. En este momento no puedo responderte.", False
    body = client.post(URL, headers=auth, json={"contact": {"id": "1"}, "message": "Hola"}).json()
    assert body["fallback"] is True and body["reply"].startswith("Gracias por escribirnos")


def test_errors_are_clear_and_never_reach_the_assistant(api, monkeypatch):
    client, auth, engine, _alerts = api
    assert client.post(URL, json={"message": "Hola"}).json()["code"] == "invalid_api_key"
    wrong = client.post(URL, headers={"Authorization": "Bearer ase_live_" + "x" * 40}, json={"message": "Hola"})
    assert (wrong.status_code, wrong.headers["www-authenticate"]) == (401, "Bearer")
    bad_json = client.post(URL, headers={**auth, "Content-Type": "application/json"}, content=b"{no es json")
    assert (bad_json.status_code, bad_json.json()["code"]) == (400, "invalid_json")
    invalid = client.post(URL, headers=auth, json={"contact": {}, "message": ""})
    assert invalid.status_code == 422 and {issue["path"] for issue in invalid.json()["issues"]} == {"contact.id", "message"}
    unreplaced = client.post(URL, headers=auth, json={"contact": {"id": "{phone}", "name": "{customer.name}"}, "message": "Hola"})
    assert unreplaced.status_code == 422 and {issue["path"] for issue in unreplaced.json()["issues"]} == {"contact.id", "contact.name"}
    # Una clave sin el permiso de conversar.
    with engine.begin() as conn:
        conn.execute(update(api_keys).values(scopes=["config:read"]))
    forbidden = client.post(URL, headers=auth, json={"contact": {"id": "1"}, "message": "Hola"})
    assert (forbidden.status_code, forbidden.json()["code"]) == (403, "forbidden")
    assert FakeAI.calls == []


def test_a_key_has_a_rhythm_limit(api, monkeypatch):
    client, auth, _engine, _alerts = api
    monkeypatch.setattr(usage_module, "ASSISTANT_API_PER_KEY", UsageLimit("assistant_api_key", limit=1, window_seconds=60))
    assert client.post(URL, headers=auth, json={"contact": {"id": "1"}, "message": "Hola"}).status_code == 200
    limited = client.post(URL, headers=auth, json={"contact": {"id": "1"}, "message": "Hola otra vez"})
    assert (limited.status_code, limited.json()["code"]) == (429, "rate_limited") and int(limited.headers["retry-after"]) >= 1


def test_the_ai_takes_back_an_api_chat_silently_when_nobody_attended(api):
    _client, _auth, engine, _alerts = api
    store = ConversationStore(engine)
    from app.domain.business_config.conversations import NewMessage

    chat = store.append("restaurant", channel="api", contact_ref="1", contact_name="Laura", message=NewMessage("customer", "Una persona")).conversation_id
    store.request_handoff(chat, "human_request")
    with engine.begin() as conn:
        conn.execute(update(conversations).values(customer_waiting_since=datetime.now(timezone.utc) - timedelta(minutes=45)))
    continued, alerted = [], []
    sweep = ResumeSweep(
        waiting=store.waiting_chats, settings=AttentionStore(engine).attention_settings, resume=store.resume_waiting,
        pending=store.pending_customer_text, secrets=lambda _slug: None, continue_chat=lambda *args: continued.append(args), alerts=alerted.append,
    )
    assert sweep.run().resumed == 1 and continued == [] and len(alerted) == 1
    assert store.thread(chat)[0].ai_paused is False


# ---------------------------------------------------------------------------
# El panel: claves e integraciones
# ---------------------------------------------------------------------------

ANA = Principal(user_id="usuario-ana", email="ana@example.com")
BETO = Principal(user_id="usuario-beto", email="beto@example.com")


class Tokens:
    def verify(self, token: str) -> Principal | None:
        return {"token-de-ana": ANA, "token-de-beto": BETO}.get(token)


def _as(user: str) -> dict[str, str]:
    return {"Authorization": f"Bearer token-de-{user}"}


class FakeLab:
    """«Probar asistente», con su respuesta de prueba."""

    asked: list[tuple[str, str, str]] = []

    def talk(self, tenant_slug, *, message, source="draft", session_id=None):
        from app.business_config_application.assistant_lab import PlaygroundReply

        FakeLab.asked.append((tenant_slug, message, source))
        return PlaygroundReply("s" * 32, source, 1, AssistantTurn(reply="Hola, ¿en qué te ayudo?", intent="info"))


@pytest.fixture
def panel(store):
    service = build_business_config_service(store, secrets_key="x" * 43 + "=")
    with store.begin() as conn:
        ids = {row.slug: row.id for row in conn.execute(select(tenants.c.slug, tenants.c.id))}
        for slug, user in (("restaurant", ANA), ("saas", BETO)):
            conn.execute(business_members.insert().values(tenant_id=ids[slug], user_id=user.user_id, role="owner", created_at=datetime.now(timezone.utc)))
    FakeLab.asked = []
    app = create_app(
        service,
        FakeLab(),
        access=BusinessAccess(service, BusinessMembersStore(store)),
        verifier=Tokens(),
        conversations=ConversationStore(store),
        notifications=NotificationStore(store),
        usage=UsageCounterStore(store),
        api_keys=ApiKeyStore(store),
        assistant_api_url=lambda: "https://motor.example.com/api/v1/assistant/messages",
    )
    return TestClient(app)


def test_the_owner_creates_sees_and_revokes_keys_and_the_secret_is_shown_once(panel):
    base = "/api/businesses/restaurant"
    created = panel.post(f"{base}/api-keys", headers=_as("ana"), json={"name": "Leona", "scopes": [SCOPE_ASSISTANT_CHAT]})
    assert created.status_code == 201
    secret = created.json()["secret"]
    assert secret.startswith(KEY_PREFIX) and created.json()["created_by"] == "ana@example.com"
    listed = panel.get(f"{base}/api-keys", headers=_as("ana")).json()
    assert [(key["name"], key["active"]) for key in listed] == [("Leona", True)] and "secret" not in listed[0] and secret not in str(listed)
    overview = panel.get(f"{base}/integrations", headers=_as("ana")).json()
    assert overview["assistant_api"] == {"url": "https://motor.example.com/api/v1/assistant/messages", "chat_keys": 1}
    assert overview["api_keys"] == {"active": 1} and overview["scopes"] == [{"id": SCOPE_ASSISTANT_CHAT, "label": "Conversar con el asistente"}]
    revoked = panel.post(f"{base}/api-keys/{listed[0]['id']}/revoke", headers=_as("ana")).json()
    assert revoked["active"] is False and revoked["revoked_at"]
    invalid = panel.post(f"{base}/api-keys", headers=_as("ana"), json={"name": "", "scopes": []})
    assert invalid.status_code == 422 and {issue["path"] for issue in invalid.json()["issues"]} == {"name", "scopes"}


def test_nobody_reaches_the_keys_of_someone_elses_business(panel):
    mine = panel.post("/api/businesses/restaurant/api-keys", headers=_as("ana"), json={"name": "Leona", "scopes": [SCOPE_ASSISTANT_CHAT]}).json()
    assert panel.get("/api/businesses/restaurant/api-keys", headers=_as("beto")).status_code == 404
    assert panel.post(f"/api/businesses/saas/api-keys/{mine['id']}/revoke", headers=_as("beto")).status_code == 404
    assert panel.get("/api/businesses/restaurant/integrations").status_code == 401


def test_trying_the_api_from_the_panel_answers_like_the_api_with_what_was_published(panel):
    body = panel.post("/api/businesses/restaurant/integrations/assistant-api/try", headers=_as("ana"), json={"message": "Hola"}).json()
    assert FakeLab.asked == [("restaurant", "Hola", "published")]
    assert {key: body[key] for key in ("reply", "parts", "handoff", "attended_by", "intent", "fallback")} == {
        "reply": "Hola, ¿en qué te ayudo?", "parts": ["Hola, ¿en qué te ayudo?"], "handoff": False, "attended_by": "assistant",
        "intent": "info", "fallback": False,
    }


def test_the_same_request_while_the_first_is_still_being_answered_gets_a_clear_conflict(api):
    client, auth, engine, _alerts = api
    from app.domain.business_config.conversations import NewMessage

    # El primero ya quedó en la bandeja, pero su respuesta todavía no se guardó.
    ConversationStore(engine).append(
        "restaurant", channel="api", contact_ref="1", contact_name=None, message=NewMessage("customer", "Hola", provider_message_id="leona-msg-9"),
    )
    second = client.post(URL, headers={**auth, "Idempotency-Key": "leona-msg-9"}, json={"contact": {"id": "1"}, "message": "Hola"})
    assert (second.status_code, second.json()["code"]) == (409, "duplicate_in_progress") and FakeAI.calls == []
