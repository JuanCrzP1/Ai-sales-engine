"""WhatsApp por código QR (uazapi): conectar desde el panel y responder desde el motor.

- El servidor de uazapi y su token de administrador son de la plataforma (variables de entorno): el negocio solo toca «Conectar» y
  escanea. Nunca envía ni recibe servidores ni tokens.
- Al conectar se crea la instancia del negocio (o se reutiliza), se registra su webhook con su identificador secreto y se muestra
  el QR. Si el servidor borró la instancia, se crea otra. Desconectar la borra del servidor.
- Sin servidor de la plataforma o sin dirección pública del motor, la conexión no está disponible.
- El motor responde solo mensajes de texto de clientes, una vez cada uno, envía la respuesta por la instancia del negocio y la
  guarda en la bandeja con los datos de pago ocultos. Un aviso sin el token de la instancia se rechaza.

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
from app.domain.business_config.channels import ChannelError, ProviderStatus, UazapiPlatform, WhatsAppUnavailableError, normalize_server_url
from app.infrastructure.business_config import runtime_access
from app.infrastructure.business_config.channel_store import ChannelStore
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine
from app.infrastructure.business_config.tables import business_channels
from app.infrastructure.channels.platform import uazapi_platform
from app.infrastructure.channels.uazapi import UazapiClient, parse_incoming
from pipeline_harness import publish_document
from test_admin_api import BASE_URL, LOCAL_CLIENT, Local

PUBLIC = lambda _host: ["104.21.0.10"]  # noqa: E731 - el servidor simulado resuelve a una IP pública
INSTANCE_TOKEN = "token-de-instancia-de-prueba-1234"
ADMIN_TOKEN = "token-de-administrador-de-prueba-9876"
WEBHOOK_BASE = "https://motor.example/api/v1/channels/whatsapp"
PLATFORM = UazapiPlatform("https://free.uazapi.com", ADMIN_TOKEN)


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
    with pytest.raises(ValueError):
        normalize_server_url(raw)


def test_a_name_that_resolves_to_a_private_address_is_never_called():
    calls = []
    client = UazapiClient("https://trampa.example", transport=httpx.MockTransport(lambda request: calls.append(request)), resolver=lambda _h: ["10.0.0.7"])
    with pytest.raises(WhatsAppUnavailableError):
        client.status(INSTANCE_TOKEN)
    assert calls == []


def test_the_platform_server_comes_from_the_environment_and_never_shows_its_token(monkeypatch):
    monkeypatch.delenv("UAZAPI_BASE_URL", raising=False)
    monkeypatch.delenv("UAZAPI_ADMIN_TOKEN", raising=False)
    assert uazapi_platform() is None
    monkeypatch.setenv("UAZAPI_BASE_URL", "free.uazapi.com/")
    monkeypatch.setenv("UAZAPI_ADMIN_TOKEN", ADMIN_TOKEN)
    platform = uazapi_platform()
    assert platform == PLATFORM and ADMIN_TOKEN not in repr(platform)
    monkeypatch.setenv("UAZAPI_BASE_URL", "http://10.0.0.5")
    assert uazapi_platform() is None


# ---------------------------------------------------------------------------
# Cliente de uazapi
# ---------------------------------------------------------------------------

class FakeUazapi:
    """Un servidor de uazapi en memoria: instancias por token, conexión con QR y mensajes enviados."""

    def __init__(self) -> None:
        self.instances: dict[str, dict] = {INSTANCE_TOKEN: {"status": "disconnected"}}
        self.created_names: list[tuple[str, str]] = []
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
            self.created_names.append((body["name"], body["systemName"]))
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
        if path == "/instance" and request.method == "DELETE":
            self.instances.pop(token)
            return httpx.Response(200, json={"response": "Instance Deleted"})
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


def test_an_instance_the_server_no_longer_has_is_reported_as_gone_and_a_rejected_admin_token_as_unavailable():
    client = FakeUazapi().client("https://free.uazapi.com")
    with pytest.raises(ChannelError) as error:
        client.status("otro-token")
    assert error.value.gone is True and "token" not in str(error.value)
    with pytest.raises(WhatsAppUnavailableError) as unavailable:
        client.create_instance("otro-administrador", "ventas-x")
    assert "token" not in str(unavailable.value) and "uazapi" not in str(unavailable.value)
    client.delete_instance("ya-no-existe")  # borrar lo que ya no existe no falla


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

def _panel(tmp_path, *, platform=PLATFORM, webhook_base=WEBHOOK_BASE):
    local = Local(tmp_path / "panel.sqlite3")
    server = FakeUazapi()
    whatsapp = WhatsAppChannelService(ChannelStore(local.engine, local.key), server.client, platform=platform, webhook_base=webhook_base)
    local.app = create_app(build_business_config_service(local.engine, secrets_key=local.key), whatsapp=whatsapp)
    local.client = TestClient(local.app, base_url=BASE_URL, client=LOCAL_CLIENT, raise_server_exceptions=False)
    assert local.client.post("/api/businesses", json={"slug": "sabor_casero", "name": "Sabor Casero"}).status_code == 201
    return local, server


@pytest.fixture
def panel(tmp_path):
    local, server = _panel(tmp_path)
    yield local, server
    local.engine.dispose()


URL = "/api/businesses/sabor_casero/channels/whatsapp"
NOTHING = {"available": True, "status": "disconnected", "phone": None, "profile_name": None, "qrcode": None, "paircode": None}


def test_the_business_only_sees_the_connection_never_the_server_or_the_tokens(panel):
    local, server = panel
    assert local.client.get(URL).json() == NOTHING
    assert local.client.put(URL, json={"server_url": "https://otro.example", "token": "x"}).status_code == 405
    response = local.client.post(f"{URL}/connect")
    assert response.status_code == 200
    assert set(response.json()) == set(NOTHING)
    created = ChannelStore(local.engine, local.key).whatsapp_secrets("sabor_casero").instance_token
    for secret in (ADMIN_TOKEN, created, "free.uazapi.com"):
        assert secret not in response.text and secret not in local.client.get(URL).text
    with local.engine.connect() as conn:
        stored = conn.execute(select(business_channels)).first()
    assert created not in json.dumps({key: str(value) for key, value in stored._mapping.items()})
    assert ADMIN_TOKEN not in json.dumps({key: str(value) for key, value in stored._mapping.items()})


def test_connecting_creates_the_business_instance_registers_its_webhook_and_shows_the_qr(panel):
    local, server = panel
    connecting = local.client.post(f"{URL}/connect").json()
    assert connecting["status"] == "connecting" and connecting["qrcode"].startswith("data:image/png;base64,")
    secrets = ChannelStore(local.engine, local.key).whatsapp_secrets("sabor_casero")
    assert secrets.instance_token.startswith("instancia-creada-") and secrets.server_url == "https://free.uazapi.com"
    assert len(secrets.webhook_id) >= 32 and server.webhooks[secrets.instance_token]["url"] == f"{WEBHOOK_BASE}/{secrets.webhook_id}"
    (name, device), = server.created_names
    assert name.startswith("ventas-sabor_casero-") and device == "Asistente de ventas"

    # Conectar otra vez reutiliza la instancia; un código nuevo reinicia la conexión.
    assert local.client.post(f"{URL}/connect").json()["status"] == "connecting"
    assert local.client.post(f"{URL}/new-code").json()["qrcode"].startswith("data:image/png;base64,")
    assert server.created == 1

    server.instances[secrets.instance_token]["status"] = "connected"
    connected = local.client.get(f"{URL}/status").json()
    assert (connected["status"], connected["phone"], connected["profile_name"], connected["qrcode"]) == ("connected", "573001112233", "Sabor Casero", None)
    assert local.client.get(URL).json()["status"] == "connected"


def test_disconnecting_deletes_the_instance_from_the_server(panel):
    local, server = panel
    local.client.post(f"{URL}/connect")
    token = ChannelStore(local.engine, local.key).whatsapp_secrets("sabor_casero").instance_token
    assert local.client.post(f"{URL}/disconnect").json() == NOTHING
    assert token not in server.instances and ChannelStore(local.engine, local.key).whatsapp_secrets("sabor_casero") is None
    assert local.client.get(f"{URL}/status").json() == NOTHING
    assert local.client.post(f"{URL}/connect").json()["status"] == "connecting" and server.created == 2


def test_if_the_server_deleted_the_instance_connecting_creates_another(panel):
    local, server = panel
    local.client.post(f"{URL}/connect")
    first = ChannelStore(local.engine, local.key).whatsapp_secrets("sabor_casero").instance_token
    server.instances.pop(first)  # los servidores de prueba borran la instancia a la hora
    assert local.client.get(f"{URL}/status").json()["status"] == "disconnected"
    assert local.client.post(f"{URL}/connect").json()["status"] == "connecting"
    assert ChannelStore(local.engine, local.key).whatsapp_secrets("sabor_casero").instance_token not in (first, ADMIN_TOKEN)


@pytest.mark.parametrize("missing", ["platform", "webhook_base"])
def test_without_the_platform_server_or_a_public_engine_address_the_connection_is_not_available(tmp_path, missing):
    local, server = _panel(tmp_path, **{missing: None})
    assert local.client.get(URL).json()["available"] is False
    response = local.client.post(f"{URL}/connect")
    assert response.status_code == 503 and "no está activa" in response.json()["message"]
    assert server.requests == []
    local.engine.dispose()


def test_a_rejected_platform_token_is_not_explained_to_the_business(tmp_path):
    local, _server = _panel(tmp_path, platform=UazapiPlatform("https://free.uazapi.com", "administrador-vencido"))
    response = local.client.post(f"{URL}/connect")
    assert response.status_code == 503
    assert "token" not in response.text and "uazapi" not in response.text
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
    channels.save_whatsapp("restaurant", server_url="https://free.uazapi.com", instance_token=INSTANCE_TOKEN)
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
    assert client.post(path, json={key: value for key, value in INCOMING.items() if key != "token"}).status_code == 403
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
