"""WhatsApp por código QR (uazapi): conectar desde el panel y responder desde el motor.

- La dirección del servidor solo puede ser https pública: el panel nunca llama a la red interna.
- Un token de instancia se usa tal cual; uno de administrador crea la instancia del negocio. Los tokens se guardan cifrados y nunca
  vuelven al panel.
- Al pedir el QR se registra el webhook del negocio, con su identificador secreto.
- El motor responde solo mensajes de texto de clientes, una vez cada uno, envía la respuesta por el servidor del negocio y la guarda
  en la bandeja con los datos de pago ocultos. Un aviso con otro token se rechaza.

Sin llamadas reales: uazapi es un servidor simulado (httpx) y la IA, una respuesta fija.
"""
from __future__ import annotations

import json

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin_api.main import create_app
from app.api.controllers import whatsapp_qr_webhook
from app.business_config_application.channels import WhatsAppChannelService
from app.domain.business_config.channels import ChannelError, ProviderStatus, normalize_server_url
from app.infrastructure.business_config import runtime_access
from app.infrastructure.business_config.channel_store import ChannelStore
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine
from app.infrastructure.business_config.tables import business_channels
from app.infrastructure.channels.uazapi import UazapiClient, parse_incoming
from pipeline_harness import publish_document
from test_admin_api import BASE_URL, LOCAL_CLIENT, Local

PUBLIC = lambda _host: ["104.21.0.10"]  # noqa: E731 - el servidor simulado resuelve a una IP pública
INSTANCE_TOKEN = "token-de-instancia-de-prueba-1234"
ADMIN_TOKEN = "token-de-administrador-de-prueba-9876"
WEBHOOK_BASE = "https://motor.example/api/v1/channels/whatsapp"


# ---------------------------------------------------------------------------
# Dirección del servidor
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw", ["https://free.uazapi.com", "free.uazapi.com", "https://free.uazapi.com/", "HTTPS://Free.Uazapi.com"])
def test_a_public_https_server_is_accepted_and_normalized(raw):
    assert normalize_server_url(raw) == "https://free.uazapi.com"


@pytest.mark.parametrize(
    "raw",
    ["http://free.uazapi.com", "https://localhost", "https://127.0.0.1", "https://10.0.0.5", "https://192.168.1.4:8080", "https://servidor.local",
     "https://usuario:clave@free.uazapi.com", "https://free.uazapi.com/instance", "https://free.uazapi.com?x=1", "https://intranet", ""],
)
def test_a_server_that_is_not_public_https_is_rejected(raw):
    with pytest.raises(ChannelError):
        normalize_server_url(raw)


def test_a_name_that_resolves_to_a_private_address_is_never_called():
    calls = []
    client = UazapiClient("https://trampa.example", transport=httpx.MockTransport(lambda request: calls.append(request)), resolver=lambda _h: ["10.0.0.7"])
    with pytest.raises(ChannelError, match="servidor público"):
        client.status(INSTANCE_TOKEN)
    assert calls == []


# ---------------------------------------------------------------------------
# Cliente de uazapi
# ---------------------------------------------------------------------------

class FakeUazapi:
    """Un servidor de uazapi en memoria: instancias por token, conexión con QR y mensajes enviados."""

    def __init__(self) -> None:
        self.instances: dict[str, dict] = {INSTANCE_TOKEN: {"status": "disconnected"}}
        self.webhooks: dict[str, dict] = {}
        self.sent: list[tuple[str, dict]] = []
        self.requests: list[httpx.Request] = []
        self.created = 0

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path, token, admin = request.url.path, request.headers.get("token"), request.headers.get("admintoken")
        body = json.loads(request.content or b"{}")
        if path in ("/instance/create", "/instance/init"):
            if admin != ADMIN_TOKEN:
                return httpx.Response(401, json={"error": "Invalid AdminToken Header"})
            self.created += 1
            new = f"instancia-creada-{self.created}-abcdef"
            self.instances[new] = {"status": "disconnected"}
            return httpx.Response(200, json={"instance": {"token": new, "status": "disconnected"}})
        instance = self.instances.get(token or "")
        if instance is None:
            return httpx.Response(401, json={"code": 401, "message": "Invalid token.", "data": {}})
        if path == "/instance/status":
            connected = instance["status"] == "connected"
            return httpx.Response(200, json={
                "instance": {"status": instance["status"], "qrcode": "iVBORw0KGgo=" if instance["status"] == "connecting" else "", "profileName": "Sabor Casero" if connected else ""},
                "status": {"connected": connected, "loggedIn": connected, "jid": {"user": "573001112233"} if connected else None},
            })
        if path == "/instance/connect":
            instance["status"] = "connecting"
            return httpx.Response(200, json={"response": "Connecting"})
        if path == "/instance/disconnect":
            instance["status"] = "disconnected"
            return httpx.Response(200, json={"response": "Disconnected"})
        if path == "/webhook":
            self.webhooks[token] = body
            return httpx.Response(200, json=[body])
        if path == "/send/text":
            self.sent.append((token, body))
            return httpx.Response(200, json={"response": {"status": "success"}})
        return httpx.Response(404, json={"error": "not found"})

    def client(self, server_url: str) -> UazapiClient:
        return UazapiClient(server_url, transport=httpx.MockTransport(self.handler), resolver=PUBLIC)


def test_the_client_reads_the_qr_and_the_connected_number():
    server = FakeUazapi()
    client = server.client("https://free.uazapi.com")
    connecting = client.connect(INSTANCE_TOKEN)
    assert connecting.status == "connecting" and connecting.qrcode == "data:image/png;base64,iVBORw0KGgo="
    server.instances[INSTANCE_TOKEN]["status"] = "connected"
    assert client.status(INSTANCE_TOKEN) == ProviderStatus("connected", None, None, "573001112233", "Sabor Casero")
    assert all(request.headers["token"] == INSTANCE_TOKEN for request in server.requests)


def test_the_client_sends_text_and_registers_a_webhook_that_ignores_its_own_messages():
    server = FakeUazapi()
    client = server.client("https://free.uazapi.com")
    client.send_text(INSTANCE_TOKEN, "+57 300 111 2233", "Hola")
    client.set_webhook(INSTANCE_TOKEN, f"{WEBHOOK_BASE}/abc")
    assert server.sent == [(INSTANCE_TOKEN, {"number": "573001112233", "text": "Hola"})]
    assert server.webhooks[INSTANCE_TOKEN] == {
        "url": f"{WEBHOOK_BASE}/abc", "enabled": True, "events": ["messages", "connection"], "excludeMessages": ["wasSentByApi", "fromMeYes", "isGroupYes"],
    }


def test_a_rejected_token_is_reported_on_its_field():
    with pytest.raises(ChannelError) as error:
        FakeUazapi().client("https://free.uazapi.com").status("otro-token")
    assert error.value.field == "token"


INCOMING = {
    "EventType": "messages",
    "token": INSTANCE_TOKEN,
    "message": {"messageid": "MSG1", "chatid": "573009998877@s.whatsapp.net", "sender": "573009998877@s.whatsapp.net", "senderName": "Ana",
                "fromMe": False, "isGroup": False, "messageType": "Conversation", "text": "Hola, ¿qué venden?"},
}


def test_only_text_messages_from_a_customer_are_answered():
    message = parse_incoming(INCOMING)
    assert (message.message_id, message.phone, message.contact_name, message.text) == ("MSG1", "573009998877", "Ana", "Hola, ¿qué venden?")
    for change in ({"fromMe": True}, {"wasSentByApi": True}, {"isGroup": True}, {"chatid": "120363@g.us"}, {"text": "  "}):
        assert parse_incoming({**INCOMING, "message": {**INCOMING["message"], **change}}) is None
    assert parse_incoming({**INCOMING, "EventType": "messages_update"}) is None


# ---------------------------------------------------------------------------
# Panel: guardar, pedir el QR, seguir la conexión y desconectar
# ---------------------------------------------------------------------------

@pytest.fixture
def panel(tmp_path):
    local = Local(tmp_path / "panel.sqlite3")
    server = FakeUazapi()
    whatsapp = WhatsAppChannelService(ChannelStore(local.engine, local.key), server.client, webhook_base=WEBHOOK_BASE)
    local.app = create_app(build_business_config_service(local.engine, secrets_key=local.key), whatsapp=whatsapp)
    local.client = TestClient(local.app, base_url=BASE_URL, client=LOCAL_CLIENT, raise_server_exceptions=False)
    assert local.client.post("/api/businesses", json={"slug": "sabor_casero", "name": "Sabor Casero"}).status_code == 201
    yield local, server
    local.engine.dispose()


URL = "/api/businesses/sabor_casero/channels/whatsapp"


def test_an_instance_token_is_saved_encrypted_and_never_returned(panel):
    local, _server = panel
    assert local.client.get(URL).json()["configured"] is False
    response = local.client.put(URL, json={"server_url": "free.uazapi.com", "token": INSTANCE_TOKEN})
    assert response.status_code == 200
    body = response.json()
    assert body | {"token_hint": "…1234"} == {
        "configured": True, "provider": "uazapi", "server_url": "https://free.uazapi.com", "status": "disconnected", "token_hint": "…1234",
        "has_admin_token": False, "phone": None, "profile_name": None, "webhook_ready": True, "qrcode": None, "paircode": None,
    }
    assert INSTANCE_TOKEN not in response.text
    with local.engine.connect() as conn:
        stored = conn.execute(select(business_channels)).first()
    assert INSTANCE_TOKEN not in json.dumps({key: str(value) for key, value in stored._mapping.items()})


def test_an_admin_token_creates_the_business_instance(panel):
    local, server = panel
    body = local.client.put(URL, json={"server_url": "https://free.uazapi.com", "token": ADMIN_TOKEN}).json()
    assert body["has_admin_token"] is True and len(server.instances) == 2
    assert ChannelStore(local.engine, local.key).whatsapp_secrets("sabor_casero").instance_token.startswith("instancia-creada-")


def test_a_token_the_server_rejects_is_reported_and_nothing_is_saved(panel):
    local, _server = panel
    response = local.client.put(URL, json={"server_url": "https://free.uazapi.com", "token": "no-sirve"})
    assert response.status_code == 422 and response.json()["issues"][0]["path"] == "token"
    assert local.client.get(URL).json()["configured"] is False
    assert local.client.put(URL, json={"server_url": "http://free.uazapi.com", "token": INSTANCE_TOKEN}).json()["issues"][0]["path"] == "server_url"


def test_connecting_shows_the_qr_registers_the_webhook_and_follows_the_connection(panel):
    local, server = panel
    local.client.put(URL, json={"server_url": "https://free.uazapi.com", "token": INSTANCE_TOKEN})
    connecting = local.client.post(f"{URL}/connect").json()
    assert connecting["status"] == "connecting" and connecting["qrcode"].startswith("data:image/png;base64,")
    webhook_id = ChannelStore(local.engine, local.key).whatsapp_secrets("sabor_casero").webhook_id
    assert len(webhook_id) >= 32 and server.webhooks[INSTANCE_TOKEN]["url"] == f"{WEBHOOK_BASE}/{webhook_id}"

    server.instances[INSTANCE_TOKEN]["status"] = "connected"
    connected = local.client.get(f"{URL}/status").json()
    assert (connected["status"], connected["phone"], connected["profile_name"], connected["qrcode"]) == ("connected", "573001112233", "Sabor Casero", None)
    assert local.client.get(URL).json()["status"] == "connected"

    assert local.client.post(f"{URL}/disconnect").json()["status"] == "disconnected"
    assert local.client.delete(URL).status_code == 204
    assert local.client.get(URL).json()["configured"] is False


def test_if_the_server_deleted_the_instance_the_admin_token_creates_it_again(panel):
    local, server = panel
    local.client.put(URL, json={"server_url": "https://free.uazapi.com", "token": ADMIN_TOKEN})
    first = ChannelStore(local.engine, local.key).whatsapp_secrets("sabor_casero").instance_token
    server.instances.pop(first)  # los servidores de prueba borran la instancia a la hora
    assert local.client.post(f"{URL}/connect").json()["status"] == "connecting"
    assert ChannelStore(local.engine, local.key).whatsapp_secrets("sabor_casero").instance_token not in (first, ADMIN_TOKEN)


def test_without_a_public_engine_address_the_panel_warns_that_messages_will_not_arrive(tmp_path):
    local = Local(tmp_path / "panel.sqlite3")
    server = FakeUazapi()
    local.app = create_app(build_business_config_service(local.engine, secrets_key=local.key), whatsapp=WhatsAppChannelService(ChannelStore(local.engine, local.key), server.client))
    client = TestClient(local.app, base_url=BASE_URL, client=LOCAL_CLIENT)
    client.post("/api/businesses", json={"slug": "sabor_casero", "name": "Sabor Casero"})
    client.put(URL, json={"server_url": "https://free.uazapi.com", "token": INSTANCE_TOKEN})
    assert client.post(f"{URL}/connect").json()["webhook_ready"] is False
    assert server.webhooks == {}
    local.engine.dispose()


# ---------------------------------------------------------------------------
# Motor: el webhook responde con el asistente del negocio
# ---------------------------------------------------------------------------

class FakeAI:
    def generate_business_reply(self, **kwargs):
        FakeAI.received = kwargs
        return "¡Hola Ana! Tenemos hamburguesas artesanales.", True, {"intent": "info", "handoff": False}


@pytest.fixture
def engine_webhook(monkeypatch, tmp_path):
    url = publish_document(monkeypatch, tmp_path, "restaurant")
    store = create_business_config_engine(url)
    import os

    channels = ChannelStore(store, os.environ["BUSINESS_CONFIG_SECRETS_KEY"])
    channels.save_whatsapp("restaurant", server_url="https://free.uazapi.com", instance_token=INSTANCE_TOKEN, admin_token=None)
    webhook_id = channels.whatsapp_secrets("restaurant").webhook_id
    server = FakeUazapi()
    monkeypatch.setattr(whatsapp_qr_webhook, "AIService", FakeAI)
    monkeypatch.setattr(whatsapp_qr_webhook, "UazapiClient", server.client)
    monkeypatch.setattr(whatsapp_qr_webhook, "_seen", whatsapp_qr_webhook._SeenMessages())
    app = FastAPI()
    app.include_router(whatsapp_qr_webhook.router)
    yield TestClient(app), f"/channels/whatsapp/{webhook_id}", server, store
    store.dispose()
    runtime_access.dispose_shared_engines()


def test_a_customer_message_is_answered_through_the_business_server_and_saved_in_the_inbox(engine_webhook):
    client, path, server, store = engine_webhook
    assert client.post(path, json=INCOMING).json() == {"status": "accepted"}
    assert server.sent == [(INSTANCE_TOKEN, {"number": "573009998877", "text": "¡Hola Ana! Tenemos hamburguesas artesanales."})]
    assert FakeAI.received["user_id"] == "573009998877" and FakeAI.received["tenant"].slug == "restaurant"
    thread = ConversationStore(store).recent(["restaurant"], channel="whatsapp", limit=5)
    assert [(item.contact_name, item.channel) for item in thread] == [("Ana", "whatsapp")]


def test_the_same_message_is_answered_once(engine_webhook):
    client, path, server, _store = engine_webhook
    client.post(path, json=INCOMING)
    assert client.post(path, json=INCOMING).json() == {"status": "duplicate"}
    assert len(server.sent) == 1


def test_a_notice_with_another_token_or_an_unknown_route_is_rejected(engine_webhook):
    client, path, server, _store = engine_webhook
    assert client.post(path, json={**INCOMING, "token": "otro"}).status_code == 403
    assert client.post("/channels/whatsapp/" + "x" * 40, json=INCOMING).status_code == 404
    assert client.post("/channels/whatsapp/corto", json=INCOMING).status_code == 404
    assert server.sent == []


def test_group_and_own_messages_are_ignored_and_connection_notices_update_the_status(engine_webhook):
    client, path, server, store = engine_webhook
    group = {**INCOMING, "message": {**INCOMING["message"], "isGroup": True, "chatid": "120363@g.us"}}
    assert client.post(path, json=group).json() == {"status": "ignored"}
    notice = {"EventType": "connection", "token": INSTANCE_TOKEN, "instance": {"status": "connected", "profileName": "Mesa Activa"},
              "status": {"connected": True, "loggedIn": True, "jid": {"user": "573001112233"}}}
    assert client.post(path, json=notice).json() == {"status": "ok"}
    import os

    connection = ChannelStore(store, os.environ["BUSINESS_CONFIG_SECRETS_KEY"]).whatsapp("restaurant")
    assert (connection.status, connection.phone, connection.profile_name) == ("connected", "573001112233", "Mesa Activa")
    assert server.sent == []
