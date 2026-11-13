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

import base64
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
from app.infrastructure.channels.uazapi import parse_own_message, UazapiClient, parse_incoming, parse_receipt
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
        self.presences: list[dict] = []
        self.requests: list[httpx.Request] = []
        self.created = 0
        # Lo que devuelve /message/download por id de mensaje: (tipo, contenido).
        self.files: dict[str, tuple[str, bytes]] = {}
        self.fail_send = False

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
            if self.fail_send:
                return httpx.Response(500, json={"error": "Failed to send message"})
            self.sent.append((token, body))
            return httpx.Response(200, json={"id": "r1a2b3c4", "messageid": f"WA-OUT-{len(self.sent)}", "response": {"status": "success"}})
        if path == "/send/media":
            self.sent.append((token, body))
            return httpx.Response(200, json={"messageid": f"WA-MEDIA-{len(self.sent)}"})
        if path == "/message/presence":
            self.presences.append(body)
            return httpx.Response(200, json={"response": "Chat presence sent successfully"})
        if path == "/message/download":
            if body["id"] not in self.files:
                return httpx.Response(404, json={"error": "Message not found"})
            mime, content = self.files[body["id"]]
            return httpx.Response(200, json={"fileURL": "https://cdn.example/x", "mimetype": mime, "base64Data": base64.b64encode(content).decode()})
        return httpx.Response(404, json={"error": "not found"})

    def client(self, server_url: str) -> UazapiClient:
        return UazapiClient(server_url, transport=httpx.MockTransport(self.handler), resolver=PUBLIC)


def test_the_client_sends_a_file_in_base64_with_its_name_and_text():
    from app.domain.business_config.conversations import MediaFile

    server = FakeUazapi()
    client = server.client("https://free.uazapi.com")
    pdf = MediaFile("application/pdf", b"%PDF-1.7", "Catálogo.pdf")
    assert client.send_media(INSTANCE_TOKEN, "+57 300 111 2233", "document", pdf, "El catálogo") == "WA-MEDIA-1"
    photo = MediaFile("image/jpeg", b"\xff\xd8\xff", "foto.jpg")
    client.send_media(INSTANCE_TOKEN, "573001112233", "image", photo)
    assert [body for _token, body in server.sent] == [
        {"number": "573001112233", "type": "document", "file": base64.b64encode(b"%PDF-1.7").decode(), "text": "El catálogo", "docName": "Catálogo.pdf"},
        # Una foto no lleva nombre, y sin texto no se manda leyenda.
        {"number": "573001112233", "type": "image", "file": base64.b64encode(b"\xff\xd8\xff").decode()},
    ]


def test_the_client_reads_the_qr_and_the_connected_number():
    server = FakeUazapi()
    client = server.client("https://free.uazapi.com")
    connecting = client.connect(INSTANCE_TOKEN)
    assert connecting.status == "connecting" and connecting.qrcode == "data:image/png;base64,iVBORw0KGgo="
    server.instances[INSTANCE_TOKEN]["status"] = "connected"
    assert client.status(INSTANCE_TOKEN) == ProviderStatus("connected", None, None, "573001112233", "Sabor Casero")
    assert all(request.headers["token"] == INSTANCE_TOKEN for request in server.requests)


def test_the_client_sends_text_and_registers_a_webhook_that_ignores_what_the_api_sent():
    server = FakeUazapi()
    client = server.client("https://free.uazapi.com")
    assert client.send_text(INSTANCE_TOKEN, "+57 300 111 2233", "Hola") == "WA-OUT-1"
    client.set_webhook(INSTANCE_TOKEN, f"{WEBHOOK_BASE}/abc")
    assert server.sent == [(INSTANCE_TOKEN, {"number": "573001112233", "text": "Hola"})]
    assert server.webhooks[INSTANCE_TOKEN] == {
        "url": f"{WEBHOOK_BASE}/abc", "enabled": True, "events": ["messages", "messages_update", "connection"],
        # Lo que escribe el negocio desde su celular sí llega: es una respuesta del equipo.
        "excludeMessages": ["wasSentByApi", "isGroupYes"],
    }


def test_the_client_shows_typing_and_downloads_files_up_to_the_size_limit():
    server = FakeUazapi()
    client = server.client("https://free.uazapi.com")
    client.presence(INSTANCE_TOKEN, "573009998877@s.whatsapp.net", "composing", 30_000)
    assert server.presences == [{"number": "573009998877", "presence": "composing", "delay": 30000}]
    server.files["FOTO1"] = ("image/jpeg", b"jpeg-bytes")
    assert client.download(INSTANCE_TOKEN, "FOTO1").content == b"jpeg-bytes"
    assert json.loads(server.requests[-1].content) == {"id": "FOTO1", "return_base64": True, "generate_mp3": True}
    server.files["GRANDE"] = ("video/mp4", b"x" * (4 * 1024 * 1024 + 1))
    assert client.download(INSTANCE_TOKEN, "GRANDE") is None


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


def _incoming(**changes) -> dict:
    return {**INCOMING, "message": {**INCOMING["message"], **changes}}


def test_messages_from_customers_are_read_with_their_kind_and_the_rest_ignored():
    message = parse_incoming(INCOMING)
    assert (message.message_id, message.phone, message.contact_name, message.text, message.kind) == ("MSG1", "573009998877", "Ana", "Hola, ¿qué venden?", "text")
    for change in ({"fromMe": True}, {"wasSentByApi": True}, {"isGroup": True}, {"chatid": "120363@g.us"}, {"text": "  "}, {"chatid": "status@broadcast"}):
        assert parse_incoming(_incoming(**change)) is None
    assert parse_incoming({**INCOMING, "EventType": "messages_update"}) is None
    photo = parse_incoming(_incoming(messageType="ImageMessage", text="", content={"caption": "el comprobante", "mimetype": "image/jpeg"}))
    assert (photo.kind, photo.text, photo.mime_type) == ("image", "el comprobante", "image/jpeg")
    voice = parse_incoming(_incoming(messageType="AudioMessage", text="", content={"mimetype": "audio/ogg; codecs=opus", "PTT": True}))
    assert (voice.kind, voice.text, voice.mime_type) == ("audio", "", "audio/ogg")
    document = parse_incoming(_incoming(messageType="DocumentMessage", text="", content={"fileName": "factura.pdf"}))
    assert (document.kind, document.file_name) == ("document", "factura.pdf")


def test_a_contact_with_a_whatsapp_lid_is_answered_on_their_phone():
    message = parse_incoming(_incoming(chatid="2459912345678@lid", sender="2459912345678@lid", sender_pn="573009998877@s.whatsapp.net"))
    assert message.phone == "573009998877"
    assert parse_incoming(_incoming(chatid="2459912345678@lid", sender="2459912345678@lid")) is None


def test_delivery_receipts_are_read():
    receipt = {"EventType": "messages_update", "token": INSTANCE_TOKEN, "type": "ReadReceipt", "state": "Read",
               "event": {"Chat": "573009998877@s.whatsapp.net", "MessageIDs": ["WA-OUT-1"], "Type": "Read", "IsFromMe": True, "IsGroup": False}}
    assert parse_receipt(receipt).message_ids == ("WA-OUT-1",) and parse_receipt(receipt).status == "read"
    assert parse_receipt({**receipt, "state": "Delivered"}).status == "delivered"
    assert parse_receipt({**receipt, "event": {**receipt["event"], "IsGroup": True}}) is None
    assert parse_receipt({**receipt, "state": "Played"}).status == "read"
    assert parse_receipt(INCOMING) is None


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
    """El asistente del negocio: responde lo que se le diga y anota lo que leyó."""

    reply = "¡Hola Ana! Tenemos hamburguesas artesanales."
    metadata: dict = {"intent": "info"}
    received: list[str] = []
    while_thinking = None

    def generate_business_reply(self, **kwargs):
        FakeAI.received.append(kwargs["user_message"])
        FakeAI.last = kwargs
        if FakeAI.while_thinking:
            FakeAI.while_thinking()
        return FakeAI.reply, True, dict(FakeAI.metadata)


class FakeMedia:
    """La IA que ve fotos y escucha audios, con la clave del negocio."""

    keys: list[str] = []

    def describe_image(self, api_key, media, *, on_usage=None):
        from app.infrastructure.ai.media_interpreter import ImageUnderstanding

        FakeMedia.keys.append(api_key)
        return ImageUnderstanding("Captura de una transferencia de Nequi", True, "Nequi, $210.000, 10 de noviembre")

    def transcribe_audio(self, api_key, media, *, on_usage=None):
        FakeMedia.keys.append(api_key)
        return "Hola, quiero saber el precio del plan básico"


@pytest.fixture
def engine_webhook(monkeypatch, tmp_path):
    import os

    url = publish_document(monkeypatch, tmp_path, "restaurant")
    store = create_business_config_engine(url)
    channels = ChannelStore(store, os.environ["BUSINESS_CONFIG_SECRETS_KEY"])
    channels.save_whatsapp("restaurant", server_url="https://free.uazapi.com", instance_token=INSTANCE_TOKEN)
    webhook_id = channels.whatsapp_secrets("restaurant").webhook_id
    server = FakeUazapi()
    FakeAI.reply, FakeAI.metadata, FakeAI.received, FakeAI.while_thinking = "¡Hola Ana! Tenemos hamburguesas artesanales.", {"intent": "info"}, [], None
    FakeMedia.keys = []
    monkeypatch.setattr(whatsapp_qr_webhook, "AIService", FakeAI)
    monkeypatch.setattr(whatsapp_qr_webhook, "UazapiClient", server.client)
    monkeypatch.setattr(whatsapp_qr_webhook, "OpenRouterMediaInterpreter", FakeMedia)
    monkeypatch.setattr(whatsapp_qr_webhook, "_business_key", lambda _slug: "clave-del-negocio")
    app = FastAPI()
    app.include_router(whatsapp_qr_webhook.router)
    yield TestClient(app), f"/channels/whatsapp/{webhook_id}", server, ConversationStore(store)
    store.dispose()
    runtime_access.dispose_shared_engines()


OWN = {
    "EventType": "messages",
    "token": INSTANCE_TOKEN,
    "message": {"messageid": "PHONE1", "chatid": "573009998877@s.whatsapp.net", "sender": "573001112233@s.whatsapp.net",
                "fromMe": True, "wasSentByApi": False, "isGroup": False, "messageType": "Conversation", "text": "Hola Ana, soy Laura del restaurante"},
}


def test_what_the_business_writes_from_its_phone_is_read_as_a_reply_to_that_customer():
    own = parse_own_message(OWN)
    assert (own.message_id, own.phone, own.text, own.kind, own.contact_name) == ("PHONE1", "573009998877", "Hola Ana, soy Laura del restaurante", "text", None)
    # Lo que envió la API, un mensaje del cliente, un grupo o un chat sin número no son respuestas del equipo.
    for change in ({"wasSentByApi": True}, {"fromMe": False}, {"isGroup": True}, {"chatid": "120363@g.us"}, {"chatid": "1234@lid"}):
        assert parse_own_message({**OWN, "message": {**OWN["message"], **change}}) is None
    assert parse_incoming(OWN) is None


def test_a_reply_from_the_business_phone_takes_the_chat_and_the_assistant_stops_answering(engine_webhook):
    client, path, server, conversations = engine_webhook
    client.post(path, json=INCOMING)
    assert client.post(path, json=OWN).json() == {"status": "team_reply"}
    assert client.post(path, json=OWN).json() == {"status": "duplicate"}
    summary, messages = _thread(conversations)
    assert [(m.author, m.body) for m in messages][-1] == ("agent", "Hola Ana, soy Laura del restaurante")
    assert (summary.ai_paused, summary.needs_human, summary.customer_waiting_since) == (True, False, None)
    # El cliente responde: la IA no habla encima de Laura, y el cliente empieza a esperarla.
    assert client.post(path, json=_incoming(messageid="MSG2", text="¡Gracias Laura!")).json() == {"status": "stored"}
    assert len(server.sent) == 1
    assert _thread(conversations)[0].customer_waiting_since is not None


def _thread(conversations: ConversationStore):
    (summary,) = conversations.recent(["restaurant"], channel="whatsapp", limit=5)
    return conversations.thread(summary.id)


def test_the_customer_message_is_saved_at_once_answered_with_typing_and_its_reply_keeps_the_whatsapp_id(engine_webhook):
    client, path, server, conversations = engine_webhook
    assert client.post(path, json=INCOMING).json() == {"status": "accepted"}
    assert server.presences == [{"number": "573009998877", "presence": "composing", "delay": 30000}]
    assert server.sent == [(INSTANCE_TOKEN, {"number": "573009998877", "text": "¡Hola Ana! Tenemos hamburguesas artesanales."})]
    assert FakeAI.last["user_id"] == "573009998877" and FakeAI.last["tenant"].slug == "restaurant"
    summary, messages = _thread(conversations)
    assert [(m.author, m.kind, m.status) for m in messages] == [("customer", "text", "received"), ("assistant", "text", "sent")]
    assert summary.contact_name == "Ana" and summary.unread_count == 1 and summary.assistant_typing is False and not summary.ai_paused


def test_the_same_whatsapp_message_is_saved_and_answered_once(engine_webhook):
    client, path, server, conversations = engine_webhook
    client.post(path, json=INCOMING)
    assert client.post(path, json=INCOMING).json() == {"status": "duplicate"}
    assert len(server.sent) == 1 and len(_thread(conversations)[1]) == 2


def test_delivery_and_read_receipts_mark_what_went_out_and_never_go_back(engine_webhook):
    client, path, _server, conversations = engine_webhook
    client.post(path, json=INCOMING)
    receipt = {"EventType": "messages_update", "token": INSTANCE_TOKEN, "type": "ReadReceipt", "state": "Read",
               "event": {"Chat": "573009998877@s.whatsapp.net", "MessageIDs": ["WA-OUT-1"], "Type": "Read", "IsGroup": False}}
    assert client.post(path, json=receipt).json() == {"status": "ok"}
    assert client.post(path, json={**receipt, "state": "Delivered"}).json() == {"status": "ok"}
    assert _thread(conversations)[1][-1].status == "read"


def test_a_payment_receipt_photo_is_saved_seen_and_passed_to_the_team(engine_webhook):
    client, path, server, conversations = engine_webhook
    server.files["FOTO1"] = ("image/jpeg", b"jpeg-del-comprobante")
    FakeAI.reply, FakeAI.metadata = "Perfecto, ya lo reviso y te confirmo en un momento.", {"intent": "buy", "handoff": True, "handoff_reason": "payment_review"}
    photo = _incoming(messageid="FOTO1", messageType="ImageMessage", text="", content={"mimetype": "image/jpeg"})
    assert client.post(path, json=photo).json() == {"status": "accepted"}
    assert FakeAI.received == ["Ya pagué, te envío el comprobante (Nequi, $210.000, 10 de noviembre)."]
    assert FakeMedia.keys == ["clave-del-negocio"]
    summary, messages = _thread(conversations)
    customer = messages[0]
    assert (customer.kind, customer.media.mime_type, customer.media_note) == ("image", "image/jpeg", "Captura de una transferencia de Nequi")
    assert conversations.media(summary.id, customer.media.id).content == b"jpeg-del-comprobante"
    # Después de la respuesta, el cliente sabe cuánto suele tardar el equipo (el restaurante no tiene horario: siempre hay alguien).
    assert [m.body for m in messages if m.author == "assistant"] == [
        "Perfecto, ya lo reviso y te confirmo en un momento.", "Una persona de nuestro equipo te responderá en unos 10 minutos.",
    ]
    assert (summary.needs_human, summary.ai_paused, summary.handoff_reason) == (True, True, "payment_review")
    assert summary.customer_waiting_since is not None


def test_a_voice_note_is_transcribed_and_answered_like_text(engine_webhook):
    client, path, server, conversations = engine_webhook
    server.files["AUDIO1"] = ("audio/mpeg", b"mp3")
    voice = _incoming(messageid="AUDIO1", messageType="AudioMessage", text="", content={"mimetype": "audio/ogg; codecs=opus"})
    client.post(path, json=voice)
    assert FakeAI.received == ["Hola, quiero saber el precio del plan básico"]
    customer = _thread(conversations)[1][0]
    assert (customer.kind, customer.media_note, customer.media.mime_type) == ("audio", "Hola, quiero saber el precio del plan básico", "audio/mpeg")


def test_after_the_handoff_the_assistant_stays_quiet_and_the_team_sees_each_new_message(engine_webhook):
    client, path, server, conversations = engine_webhook
    FakeAI.reply, FakeAI.metadata = "Te paso con alguien del equipo por este mismo chat.", {"intent": "info", "handoff": True, "handoff_reason": "human_request"}
    client.post(path, json=_incoming(text="Quiero hablar con un asesor humano"))
    assert client.post(path, json=_incoming(messageid="MSG2", text="¿Hola?")).json() == {"status": "stored"}
    assert [sent["text"] for _token, sent in server.sent] == [
        "Te paso con alguien del equipo por este mismo chat.", "Una persona de nuestro equipo te responderá en unos 10 minutos.",
    ]
    assert FakeAI.received == ["Quiero hablar con un asesor humano"]
    summary, messages = _thread(conversations)
    assert [m.body for m in messages][-1] == "¿Hola?" and summary.unread_count == 2 and summary.handoff_reason == "human_request"


def test_if_the_team_takes_the_chat_while_the_assistant_thinks_nothing_is_sent(engine_webhook):
    client, path, server, conversations = engine_webhook

    def team_takes_over():
        (summary,) = conversations.recent(["restaurant"], channel="whatsapp", limit=5)
        conversations.set_ai_paused(summary.id, True)

    FakeAI.while_thinking = team_takes_over
    client.post(path, json=INCOMING)
    assert server.sent == [] and [m.author for m in _thread(conversations)[1]] == ["customer"]


def test_a_reply_that_whatsapp_rejects_stays_marked_as_not_sent(engine_webhook):
    client, path, server, conversations = engine_webhook
    server.fail_send = True
    client.post(path, json=INCOMING)
    assert [(m.author, m.status) for m in _thread(conversations)[1]] == [("customer", "received"), ("assistant", "failed")]


def test_stickers_are_kept_but_not_answered(engine_webhook):
    client, path, server, conversations = engine_webhook
    server.files["ST1"] = ("image/webp", b"webp")
    client.post(path, json=_incoming(messageid="ST1", messageType="StickerMessage", text=""))
    assert server.sent == [] and FakeAI.received == [] and _thread(conversations)[1][0].kind == "sticker"


def test_a_notice_with_another_token_or_an_unknown_route_is_rejected(engine_webhook):
    client, path, server, _conversations = engine_webhook
    assert client.post(path, json={**INCOMING, "token": "otro"}).status_code == 403
    assert client.post(path, json={key: value for key, value in INCOMING.items() if key != "token"}).status_code == 403
    assert client.post("/channels/whatsapp/" + "x" * 40, json=INCOMING).status_code == 404
    assert client.post("/channels/whatsapp/corto", json=INCOMING).status_code == 404
    assert server.sent == []


def test_group_and_own_messages_are_ignored_and_connection_notices_update_the_status(engine_webhook):
    import os

    client, path, server, conversations = engine_webhook
    group = {**INCOMING, "message": {**INCOMING["message"], "isGroup": True, "chatid": "120363@g.us"}}
    assert client.post(path, json=group).json() == {"status": "ignored"}
    notice = {"EventType": "connection", "token": INSTANCE_TOKEN, "instance": {"status": "connected", "profileName": "Mesa Activa"},
              "status": {"connected": True, "loggedIn": True, "jid": {"user": "573001112233"}}}
    assert client.post(path, json=notice).json() == {"status": "ok"}
    connection = ChannelStore(conversations._engine, os.environ["BUSINESS_CONFIG_SECRETS_KEY"]).whatsapp("restaurant")
    assert (connection.status, connection.phone, connection.profile_name) == ("connected", "573001112233", "Mesa Activa")
    assert server.sent == []
