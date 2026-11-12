"""El servidor MCP en la operación del día a día (fase 2): un agente de IA lee las conversaciones y les responde a los clientes, ve
los clientes, las ventas y los reportes, registra y anula ventas, ajusta la atención humana y el modelo de IA.

Con la base real (SQLite) y el panel «en la nube» (cada usuario solo llega a lo suyo). Lo que importa:
- cada área solo aparece y funciona con su permiso;
- una conversación de un negocio al que la clave no entra (aunque sea del mismo dueño) responde como inexistente;
- los datos de pago del negocio nunca salen en los mensajes que lee el agente;
- responder sale por el canal del cliente a nombre del negocio y pausa la IA; si el canal falla, el agente lo sabe;
- lo que registra el agente queda a su nombre; la clave de IA del negocio nunca sale.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin_api.main import create_app
from app.business_config_application.access import BusinessAccess
from app.domain.business_config.access import Principal
from app.domain.business_config.ai_models import AIModel
from app.domain.business_config.channels import ChannelError
from app.domain.business_config.conversations import NewMessage
from app.domain.business_config.payment_data import REDACTED_PAYMENT_VALUE, payment_values, redact_values
from app.infrastructure.business_config.ai_usage_store import AIUsageStore
from app.infrastructure.business_config.api_key_store import ApiKeyStore
from app.infrastructure.business_config.attention_store import AttentionStore
from app.infrastructure.business_config.commerce_store import CommerceStore
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import (
    build_assistant_lab_service,
    build_business_config_service,
    create_business_config_engine,
    create_local_schema,
)
from app.infrastructure.business_config.example_businesses import import_example, load_example
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.notification_store import NotificationStore
from app.infrastructure.business_config.tables import business_members, tenants
from app.infrastructure.business_config.usage_store import UsageCounterStore

ANA = Principal(user_id="usuario-ana", email="ana@example.com")
BETO = Principal(user_id="usuario-beto", email="beto@example.com")
AI_KEY = "sk-or-v1-clave-ficticia-de-ana-000000001"
MODELS = [
    AIModel("openai/gpt-4o-mini", "GPT-4o mini", "OpenAI", 0.15, 0.6, 128000),
    AIModel("google/gemini-2.5-flash", "Gemini 2.5 Flash", "Google", 0.3, 2.5, 1000000),
    AIModel("meta-llama/llama-3.3-70b-instruct:free", "Llama 3.3 70B (gratis)", "Meta", 0, 0, 128000),
]
EVERYTHING = {"conversations": "write", "sales": "write", "attention": "write", "assistant": "write"}


class Tokens:
    def verify(self, token: str) -> Principal | None:
        return {"token-de-ana": ANA, "token-de-beto": BETO}.get(token)


class Catalog:
    def models(self) -> list[AIModel]:
        return list(MODELS)


class Messenger:
    """El canal del cliente: lo que se le responde sale por aquí."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str, str]] = []
        self.fail = False

    def send_text(self, business_slug, channel, contact_ref, text):
        if self.fail:
            raise ChannelError("WhatsApp no está conectado en este negocio")
        self.sent.append((business_slug, channel, contact_ref, text))
        return f"WA-{len(self.sent)}"


@pytest.fixture
def platform(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'operacion.sqlite3').as_posix()}")
    create_local_schema(engine)
    secrets_key = Fernet.generate_key().decode()
    service = build_business_config_service(engine, secrets_key=secrets_key)
    for slug in ("restaurant", "clinic", "saas"):
        import_example(service, load_example(slug))
    with engine.begin() as conn:
        ids = {row.slug: row.id for row in conn.execute(select(tenants.c.slug, tenants.c.id))}
        for slug, user in (("restaurant", ANA), ("clinic", ANA), ("saas", BETO)):
            conn.execute(business_members.insert().values(tenant_id=ids[slug], user_id=user.user_id, role="owner", created_at=datetime.now(timezone.utc)))
    lab = build_assistant_lab_service(engine, service, secrets_key=secrets_key, catalog=Catalog(), default_model="openai/gpt-4o-mini")
    lab.save_ai_settings("restaurant", model=None, api_key=AI_KEY)
    store = ConversationStore(engine)
    messenger = Messenger()
    app = create_app(
        service,
        lab,
        access=BusinessAccess(service, BusinessMembersStore(engine)),
        verifier=Tokens(),
        conversations=store,
        notifications=NotificationStore(engine),
        usage=UsageCounterStore(engine),
        messenger=messenger,
        commerce=CommerceStore(engine),
        ai_usage=AIUsageStore(engine),
        attention=AttentionStore(engine),
        api_keys=ApiKeyStore(engine),
        mcp_url=lambda: "https://panel.example.com/api/mcp",
    )
    yield TestClient(app), service, store, messenger
    engine.dispose()


def _key(client: TestClient, permissions: dict, *, user: str = "ana", business: str = "restaurant", **body) -> str:
    payload = {"name": "Agente de operación", "reach": "all", "permissions": permissions, **body}
    response = client.post(f"/api/businesses/{business}/api-keys", headers={"Authorization": f"Bearer token-de-{user}"}, json=payload)
    assert response.status_code == 201, response.text
    return response.json()["secret"]


def _call(client: TestClient, secret: str, tool: str, **arguments) -> dict:
    response = client.post(
        "/api/mcp", headers={"Authorization": f"Bearer {secret}"},
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": arguments}},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _ok(client: TestClient, secret: str, tool: str, **arguments) -> dict:
    result = _call(client, secret, tool, **arguments)["result"]
    assert not result.get("isError"), result
    return result["structuredContent"]


def _error(client: TestClient, secret: str, tool: str, **arguments) -> dict:
    result = _call(client, secret, tool, **arguments)["result"]
    assert result["isError"] is True, result
    return result["structuredContent"]


def _tools(client: TestClient, secret: str) -> dict[str, dict]:
    response = client.post("/api/mcp", headers={"Authorization": f"Bearer {secret}"}, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    return {tool["name"]: tool for tool in response.json()["result"]["tools"]}


def _chat(store: ConversationStore, slug: str = "restaurant", contact: str = "+573001112233", name: str = "Laura", *messages: NewMessage) -> str:
    return store.record(slug, channel="whatsapp", contact_ref=contact, contact_name=name, messages=list(messages) or [NewMessage("customer", "Hola, ¿tienen mesa?")])


# ---------------------------------------------------------------------------
# Permisos por área
# ---------------------------------------------------------------------------

def test_each_area_brings_its_tools_and_only_with_its_permission(platform):
    client, *_ = platform
    readers = _tools(client, _key(client, {"conversations": "read", "sales": "read", "attention": "read"}))
    assert {"list_conversations", "get_conversation", "get_activity", "list_customers", "list_sales", "get_report", "get_attention_settings"} <= set(readers)
    assert not {"reply_to_customer", "record_sale", "cancel_sale", "update_attention_settings", "set_ai_model", "get_business_config"} & set(readers)
    writers = _tools(client, _key(client, EVERYTHING))
    for name in ("reply_to_customer", "cancel_sale", "set_ai_model"):
        assert writers[name]["annotations"]["destructiveHint"] is True, name
    for name in ("list_conversations", "get_report", "get_ai_settings"):
        assert writers[name]["annotations"]["readOnlyHint"] is True, name
    denied = _call(client, _key(client, {"conversations": "read"}), "reply_to_customer", conversation_id="a" * 32, text="Hola")
    assert denied["error"]["code"] == -32602


def test_the_panel_offers_the_new_areas_to_choose(platform):
    client, *_ = platform
    overview = client.get("/api/businesses/restaurant/integrations", headers={"Authorization": "Bearer token-de-ana"}).json()
    areas = {area["id"]: area for area in overview["areas"]}
    assert {"conversations", "sales", "attention"} <= set(areas)
    assert areas["conversations"]["read"] and areas["conversations"]["write"]


# ---------------------------------------------------------------------------
# Conversaciones
# ---------------------------------------------------------------------------

def test_the_agent_reads_the_chats_it_can_reach_and_nothing_else(platform):
    client, _service, store, _messenger = platform
    mine = _chat(store, "restaurant", "+571", "Laura")
    clinic = _chat(store, "clinic", "+572", "Pedro")
    theirs = _chat(store, "saas", "+573", "Cliente de Beto")
    only_restaurant = _key(client, {"conversations": "read"}, reach="some", businesses=["restaurant"])
    listed = _ok(client, only_restaurant, "list_conversations")
    assert [item["conversation_id"] for item in listed["conversations"]] == [mine] and listed["businesses"] == ["restaurant"]
    assert _ok(client, only_restaurant, "get_conversation", conversation_id=mine)["messages"][0]["text"] == "Hola, ¿tienen mesa?"
    # Del mismo dueño pero fuera del alcance de la clave, o de otra cuenta: como si no existiera.
    for other in (clinic, theirs, "f" * 32, "no-es-un-id"):
        assert _error(client, only_restaurant, "get_conversation", conversation_id=other)["error"].startswith("Esa conversación no existe")
    everywhere = _key(client, {"conversations": "read"})
    assert {item["conversation_id"] for item in _ok(client, everywhere, "list_conversations")["conversations"]} == {mine, clinic}
    assert _error(client, everywhere, "list_conversations", business="saas")["error"].startswith("Ese negocio no existe")


def test_payment_data_never_reaches_the_agent_in_the_messages(platform):
    client, service, store, _messenger = platform
    values = payment_values(service.compile_sections("restaurant"))
    assert values, "el ejemplo del restaurante debe tener datos de pago"
    chat = _chat(
        store, "restaurant", "+571", "Laura",
        NewMessage("customer", "¿A dónde te pago?"),
        NewMessage("assistant", f"Puedes pagar a {values[0]}", "buy"),
        NewMessage("customer", f"Listo, ya pagué a {values[0]}"),
    )
    secret = _key(client, {"conversations": "read"})
    read = json.dumps(_ok(client, secret, "get_conversation", conversation_id=chat), ensure_ascii=False)
    listed = json.dumps(_ok(client, secret, "list_conversations", business="restaurant"), ensure_ascii=False)
    for value in values:
        assert value not in read and value not in listed
    assert REDACTED_PAYMENT_VALUE in read and REDACTED_PAYMENT_VALUE in listed


def test_hiding_payment_values_covers_the_longest_first():
    assert redact_values("Nequi 3001234567 o cuenta 30012345678", ["3001234567", "30012345678", "ab"]) == "Nequi [dato de pago] o cuenta [dato de pago]"


def test_replying_goes_to_the_customer_as_the_business_and_pauses_the_ai(platform):
    client, _service, store, messenger = platform
    chat = _chat(store)
    secret = _key(client, {"conversations": "write"})
    sent = _ok(client, secret, "reply_to_customer", conversation_id=chat, text="Hola Laura, sí tenemos mesa a las 8.")
    assert messenger.sent == [("restaurant", "whatsapp", "+573001112233", "Hola Laura, sí tenemos mesa a las 8.")]
    assert sent["message"]["author"] == "agent" and sent["message"]["status"] == "sent" and sent["ai_paused"] is True
    resumed = _ok(client, secret, "set_conversation_assistant", conversation_id=chat, active=True)["conversation"]
    assert resumed["ai_paused"] is False
    messenger.fail = True
    failed = _error(client, secret, "reply_to_customer", conversation_id=chat, text="¿Sigues ahí?")
    assert "no entregó" in failed["error"] and "no enviado" in failed["error"]
    assert _ok(client, secret, "get_conversation", conversation_id=chat)["messages"][-1]["status"] == "failed"


def test_marking_attended_stops_the_wait(platform):
    client, _service, store, _messenger = platform
    chat = store.record("restaurant", channel="whatsapp", contact_ref="+579", contact_name="Sofía", messages=[NewMessage("customer", "Quiero hablar con una persona")], handoff=True, handoff_reason="human_request")
    secret = _key(client, {"conversations": "write"})
    waiting = _ok(client, secret, "list_conversations", waiting_human=True)["conversations"]
    assert [item["conversation_id"] for item in waiting] == [chat] and waiting[0]["handoff_reason"] == "human_request"
    assert _ok(client, secret, "get_activity", business="restaurant")["waiting_human"] == 1
    assert _ok(client, secret, "mark_conversation_attended", conversation_id=chat)["conversation"]["waiting_human"] is False
    assert _ok(client, secret, "list_conversations", waiting_human=True)["conversations"] == []


# ---------------------------------------------------------------------------
# Clientes y ventas
# ---------------------------------------------------------------------------

def test_the_agent_records_a_confirmed_sale_in_its_name_and_can_cancel_it(platform):
    client, _service, store, _messenger = platform
    chat = _chat(store)
    secret = _key(client, {"sales": "write"})
    sale = _ok(client, secret, "record_sale", business="restaurant", customer_name="Laura", description="Cena para 4", amount=180000, currency="cop", conversation_id=chat)["sale"]
    assert sale["amount"] == "180000.00" and sale["currency"] == "COP" and sale["created_by"] == "Agente «Agente de operación» (ana@example.com)"
    customers = _ok(client, secret, "list_customers", business="restaurant")["customers"]
    assert [(item["name"], item["stage"], item["purchases"]) for item in customers] == [("Laura", "customer", 1)]
    report = _ok(client, secret, "get_report", business="restaurant", days=7)
    assert report["totals"]["sales"] == 1 and report["totals"]["revenue"] == {"COP": "180000.00"}
    assert _ok(client, secret, "cancel_sale", business="restaurant", sale_id=sale["sale_id"])["sale"]["status"] == "cancelled"
    assert _ok(client, secret, "get_report", business="restaurant", days=7)["totals"]["sales"] == 0
    wrong = _error(client, secret, "record_sale", business="restaurant", customer_name="Laura", description="Cena", amount="-5", currency="COP")
    assert wrong["issues"] == [{"path": "amount", "message": "El valor debe ser mayor que cero."}]
    assert _error(client, secret, "cancel_sale", business="restaurant", sale_id="no-existe")["issues"][0]["path"] == "sale_id"


def test_a_sale_cannot_link_a_conversation_of_another_business(platform):
    client, _service, store, _messenger = platform
    clinic_chat = _chat(store, "clinic", "+572", "Pedro")
    secret = _key(client, {"sales": "write"})
    result = _call(client, secret, "record_sale", business="restaurant", customer_name="Pedro", description="Cena", amount="1000", currency="COP", conversation_id=clinic_chat)["result"]
    assert result["isError"] is True and result["structuredContent"]["error"].startswith("Esa conversación no existe")
    assert _ok(client, secret, "list_sales", business="restaurant")["sales"] == []


# ---------------------------------------------------------------------------
# Atención humana y modelo de IA
# ---------------------------------------------------------------------------

def test_the_agent_changes_only_the_attention_settings_it_sends(platform):
    client, *_ = platform
    secret = _key(client, {"attention": "write"})
    before = _ok(client, secret, "get_attention_settings", business="restaurant")
    after = _ok(client, secret, "update_attention_settings", business="restaurant", reply_minutes=30, resume_after_minutes=None)
    assert after["reply_minutes"] == 30 and after["resume_after_minutes"] is None
    assert (after["timezone"], after["hours_mode"], after["email_enabled"]) == (before["timezone"], before["hours_mode"], before["email_enabled"])
    custom = _ok(client, secret, "update_attention_settings", business="restaurant", hours_mode="custom", team_hours=[{"days": ["lunes", "martes"], "opens": "09:00", "closes": "18:00"}])
    assert custom["team_hours"] == [{"days": ["lunes", "martes"], "opens": "09:00", "closes": "18:00"}]
    wrong = _error(client, secret, "update_attention_settings", business="restaurant", team_hours=[{"days": ["lunes"], "opens": "18:00", "closes": "09:00"}])
    assert wrong["issues"][0]["path"] == "team_hours[0].closes"
    assert _ok(client, secret, "get_attention_settings", business="restaurant")["team_hours"] == custom["team_hours"]


def test_the_agent_sees_and_changes_the_model_but_never_the_ai_key(platform):
    client, *_ = platform
    secret = _key(client, {"assistant": "write"})
    settings = _ok(client, secret, "get_ai_settings", business="restaurant")
    assert settings["ai_key_configured"] is True and settings["uses_default_model"] is True
    free = _ok(client, secret, "list_ai_models", business="restaurant", free_only=True)["models"]
    assert [model["id"] for model in free] == ["meta-llama/llama-3.3-70b-instruct:free"]
    assert [model["id"] for model in _ok(client, secret, "list_ai_models", business="restaurant", query="gemini flash")["models"]] == ["google/gemini-2.5-flash"]
    changed = _ok(client, secret, "set_ai_model", business="restaurant", model="google/gemini-2.5-flash")
    assert changed["model"] == "google/gemini-2.5-flash"
    assert _error(client, secret, "set_ai_model", business="restaurant", model="inventado/modelo")["issues"][0]["path"] == "model"
    assert _ok(client, secret, "set_ai_model", business="restaurant")["uses_default_model"] is True
    everything = json.dumps([settings, changed], ensure_ascii=False)
    assert AI_KEY not in everything and AI_KEY[-4:] not in everything
    assert "api_key" not in _tools(client, secret)["set_ai_model"]["inputSchema"]["properties"]
