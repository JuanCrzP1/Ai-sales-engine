"""Telegram: el negocio conecta su propio bot pegando el código de @BotFather, y el asistente atiende sus chats como los de WhatsApp.

- El código se revisa con Telegram, se guarda cifrado y nunca vuelve al panel. El webhook se registra solo, con una firma secreta que
  sale del token: un aviso sin esa firma se rechaza.
- Un bot nunca queda en dos negocios, y conectar el bot de otro negocio no le toca su webhook.
- Si el código deja de servir (lo cambiaron en @BotFather) o el bot se conectó en otra plataforma, Canales lo dice y pide reconectar.
- Cada cliente es `tg-<chat>`: su memoria nunca se cruza con un número de WhatsApp. Solo se atienden chats privados de personas.
- El equipo responde desde el panel por Telegram; al eliminar el negocio, el bot deja de enviar mensajes aquí.

Sin llamadas reales: Telegram es un servidor simulado (httpx) y la IA, una respuesta fija.
"""
from __future__ import annotations

import json
import os

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin_api.main import create_app
from app.api.controllers import telegram_webhook, whatsapp_qr_webhook
from app.application.attention.resume_sweep import ResumeSweep
from app.business_config_application.channels import TelegramChannelService
from app.domain.business_config.channels import (
    TELEGRAM,
    ChannelError,
    ChannelSecrets,
    TelegramBot,
    telegram_chat_id,
    telegram_webhook_secret,
    validated_bot_token,
)
from app.domain.business_config.conversations import MAX_MEDIA_BYTES, MediaFile, WaitingChat
from app.domain.business_config.errors import InvalidFieldsError
from app.infrastructure.business_config import runtime_access
from app.infrastructure.business_config.channel_messenger import ChannelMessenger
from app.infrastructure.business_config.channel_store import ChannelStore
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine
from app.infrastructure.business_config.tables import business_channels
from app.infrastructure.channels.telegram import TelegramClient, parse_update, split_text, to_telegram_html
from pipeline_harness import publish_document
from test_admin_api import BASE_URL, LOCAL_CLIENT, Local
from test_whatsapp_qr_channel import FakeAI, FakeMedia

TOKEN = "7123456789:AAH" + "a" * 32
OTHER_TOKEN = "7999999999:AAH" + "b" * 32
WEBHOOK_BASE = "https://motor.example/api/v1/channels/telegram"


# ---------------------------------------------------------------------------
# Telegram simulado
# ---------------------------------------------------------------------------

class FakeTelegram:
    """La API de bots en memoria: bots por token, webhooks, mensajes enviados y archivos para descargar."""

    def __init__(self) -> None:
        self.bots: dict[str, dict] = {
            TOKEN: {"id": 7123456789, "is_bot": True, "first_name": "Café Aroma", "username": "CafeAromaBot"},
            OTHER_TOKEN: {"id": 7999999999, "is_bot": True, "first_name": "Otro", "username": "OtroBot"},
        }
        self.webhooks: dict[str, dict] = {}
        self.calls: list[tuple[str, str, dict]] = []
        self.uploads: list[tuple[str, str, bytes]] = []
        self.files: dict[str, tuple[str, bytes, int]] = {"FOTO-GRANDE": ("photos/file_7.jpg", b"\xff\xd8foto", 6)}
        self.reject_html = False
        self.blocked: set[str] = set()
        self.next_id = 500

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.handler)

    def client(self, *_args, **_kwargs) -> TelegramClient:
        return TelegramClient(transport=self.transport)

    def sent(self, method: str = "sendMessage") -> list[dict]:
        return [body for _token, name, body in self.calls if name == method]

    def handler(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.startswith("/file/bot"):
            token, file_path = path[len("/file/bot"):].split("/", 1)
            match = next((content for stored, content, _size in self.files.values() if stored == file_path), None)
            return httpx.Response(200, content=match) if token in self.bots and match else httpx.Response(404)
        token, method = path[len("/bot"):].split("/", 1)
        if token not in self.bots:
            return httpx.Response(401, json={"ok": False, "error_code": 401, "description": "Unauthorized"})
        if request.headers.get("content-type", "").startswith("multipart/"):
            body = {"multipart": True}
            self.uploads.append((token, method, request.content))
        else:
            body = json.loads(request.content or b"{}")
        self.calls.append((token, method, body))
        bot = self.bots[token]
        if method == "getMe":
            return self._ok(bot)
        if method == "setWebhook":
            self.webhooks[token] = {"url": body["url"], "secret": body["secret_token"], "allowed": body["allowed_updates"]}
            return self._ok(True)
        if method == "deleteWebhook":
            self.webhooks.pop(token, None)
            return self._ok(True)
        if method == "getWebhookInfo":
            return self._ok({"url": self.webhooks.get(token, {}).get("url", "")})
        if method in ("sendMessage", "sendPhoto", "sendVoice", "sendDocument", "sendVideo", "sendAudio"):
            chat = str(body.get("chat_id", ""))
            if chat in self.blocked:
                return httpx.Response(403, json={"ok": False, "error_code": 403, "description": "Forbidden: bot was blocked by the user"})
            if self.reject_html and body.get("parse_mode") == "HTML":
                return httpx.Response(400, json={"ok": False, "error_code": 400, "description": "Bad Request: can't parse entities"})
            self.next_id += 1
            return self._ok({"message_id": self.next_id})
        if method == "sendChatAction":
            return self._ok(True)
        if method == "getFile":
            stored = self.files.get(body["file_id"])
            if stored is None:
                return httpx.Response(400, json={"ok": False, "error_code": 400, "description": "Bad Request: invalid file_id"})
            return self._ok({"file_id": body["file_id"], "file_path": stored[0], "file_size": stored[2]})
        return httpx.Response(404, json={"ok": False, "error_code": 404, "description": "Not Found"})

    @staticmethod
    def _ok(result) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": result})


# ---------------------------------------------------------------------------
# El código del bot y el formato
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw", [TOKEN, f"  {TOKEN}\n", TOKEN[:20] + " " + TOKEN[20:]])
def test_the_bot_code_is_accepted_without_spaces(raw):
    assert validated_bot_token(raw) == TOKEN


@pytest.mark.parametrize("raw", ["", "hola", "7123456789", "abc:AAH" + "a" * 32, "7123456789:corto", "https://t.me/CafeAromaBot"])
def test_something_that_is_not_a_bot_code_is_explained_on_its_field(raw):
    with pytest.raises(InvalidFieldsError) as refused:
        validated_bot_token(raw)
    assert refused.value.issues[0].path == "token" and "@BotFather" in refused.value.issues[0].message


def test_a_telegram_contact_is_never_a_whatsapp_number_and_the_signature_depends_on_the_token():
    assert telegram_chat_id("tg-55") == "55"
    with pytest.raises(ChannelError):
        telegram_chat_id("573001112233")
    assert telegram_webhook_secret(TOKEN, "w" * 32) != telegram_webhook_secret(OTHER_TOKEN, "w" * 32)
    assert TOKEN not in telegram_webhook_secret(TOKEN, "w" * 32) and len(telegram_webhook_secret(TOKEN, "w" * 32)) == 64


def test_whatsapp_formatting_becomes_telegram_html_and_the_rest_is_escaped():
    assert to_telegram_html("*Plan básico* a $50.000 _al mes_ ~antes $60.000~") == "<b>Plan básico</b> a $50.000 <i>al mes</i> <s>antes $60.000</s>"
    assert to_telegram_html("2 < 3 & <script>") == "2 &lt; 3 &amp; &lt;script&gt;"
    assert to_telegram_html("archivo_de_precios.pdf y 3*4*5") == "archivo_de_precios.pdf y 3*4*5"


def test_a_long_reply_is_split_where_telegram_accepts_it():
    lines = ("Una línea de la respuesta.\n" * 300).strip()
    parts = split_text(lines)
    assert len(parts) > 1 and all(len(part) <= 4096 for part in parts) and all(part.endswith("respuesta.") for part in parts)
    assert " ".join(parts).split() == lines.split()
    words = split_text("palabra " * 1500)
    assert len(words) > 1 and " ".join(words).split() == ("palabra " * 1500).split()


# ---------------------------------------------------------------------------
# Los avisos de Telegram
# ---------------------------------------------------------------------------

def update(**message) -> dict:
    base = {"message_id": 10, "date": 1, "chat": {"id": 5551234, "type": "private", "first_name": "Ana"},
            "from": {"id": 5551234, "is_bot": False, "first_name": "Ana", "last_name": "Pérez", "username": "anap"}, "text": "Hola, ¿qué venden?"}
    return {"update_id": 900, "message": {**base, **message}}


def test_messages_from_people_are_read_with_their_kind_and_the_rest_ignored():
    text = parse_update(update())
    assert (text.message_id, text.phone, text.contact_name, text.text, text.kind) == ("10", "tg-5551234", "Ana Pérez", "Hola, ¿qué venden?", "text")
    assert parse_update(update(text="/start")).text == "Hola" and parse_update(update(text="/start promo")).text == "Hola"
    photo = parse_update(update(text=None, caption="¿Este?", photo=[{"file_id": "FOTO-CHICA"}, {"file_id": "FOTO-GRANDE"}]))
    assert (photo.kind, photo.text, photo.media_ref, photo.mime_type) == ("image", "¿Este?", "FOTO-GRANDE", "image/jpeg")
    voice = parse_update(update(text=None, voice={"file_id": "VOZ", "mime_type": "audio/ogg"}))
    assert (voice.kind, voice.media_ref, voice.mime_type) == ("audio", "VOZ", "audio/ogg")
    document = parse_update(update(text=None, document={"file_id": "DOC", "file_name": "pedido.pdf", "mime_type": "application/pdf"}))
    assert (document.kind, document.file_name) == ("document", "pedido.pdf")
    assert parse_update(update(text=None, location={"latitude": 4.6, "longitude": -74.1})).kind == "location"
    # Sin nombre, su usuario.
    assert parse_update(update(**{"from": {"id": 5551234, "is_bot": False, "username": "anap"}, "chat": {"id": 5551234, "type": "private"}})).contact_name == "@anap"
    # Grupos, canales, otros bots, mensajes editados y avisos vacíos: nada que atender.
    assert parse_update(update(chat={"id": -100, "type": "group"})) is None
    assert parse_update(update(**{"from": {"id": 1, "is_bot": True}})) is None
    assert parse_update({"update_id": 1, "edited_message": update()["message"]}) is None
    assert parse_update(update(text=None)) is None


# ---------------------------------------------------------------------------
# Cliente de Telegram
# ---------------------------------------------------------------------------

def test_the_client_sends_formatted_text_and_plain_text_if_telegram_refuses_the_format():
    fake = FakeTelegram()
    client = fake.client()
    assert client.send_text(TOKEN, "tg-5551234", "*Hola* Ana") == "501"
    assert fake.sent()[-1] == {"chat_id": "5551234", "text": "<b>Hola</b> Ana", "parse_mode": "HTML"}
    fake.reject_html = True
    assert client.send_text(TOKEN, "tg-5551234", "*Hola _Ana*_") == "502"
    assert fake.sent()[-1] == {"chat_id": "5551234", "text": "*Hola _Ana*_"}


def test_the_client_sends_files_shows_typing_and_downloads_up_to_the_limit():
    fake = FakeTelegram()
    client = fake.client()
    assert client.send_media(TOKEN, "tg-5551234", "image", MediaFile("image/png", b"\x89PNG", "menu.png"), "El menú") == "501"
    token, method, content = fake.uploads[-1]
    assert (token, method) == (TOKEN, "sendPhoto") and b'name="photo"; filename="menu.png"' in content and b"El men" in content
    client.send_media(TOKEN, "tg-5551234", "audio", MediaFile("audio/ogg", b"OggS"), "")
    assert fake.uploads[-1][1] == "sendVoice"
    client.send_media(TOKEN, "tg-5551234", "document", MediaFile("application/pdf", b"%PDF", "lista.pdf"), "")
    assert fake.uploads[-1][1] == "sendDocument"
    client.presence(TOKEN, "tg-5551234")
    assert fake.sent("sendChatAction") == [{"chat_id": "5551234", "action": "typing"}]
    assert client.download(TOKEN, "FOTO-GRANDE") == MediaFile("image/jpeg", b"\xff\xd8foto")
    fake.files["ENORME"] = ("documents/file_9.pdf", b"x", MAX_MEDIA_BYTES + 1)
    assert client.download(TOKEN, "ENORME") is None


def test_a_rejected_code_is_gone_and_a_blocked_bot_is_explained():
    fake = FakeTelegram()
    with pytest.raises(ChannelError) as rejected:
        fake.client().get_me("7000000000:AAH" + "z" * 32)
    assert rejected.value.gone and "@BotFather" in str(rejected.value)
    fake.blocked.add("5551234")
    with pytest.raises(ChannelError) as blocked:
        fake.client().send_text(TOKEN, "tg-5551234", "Hola")
    assert not blocked.value.gone and "bloqueó el bot" in str(blocked.value)


# ---------------------------------------------------------------------------
# Panel: conectar, revisar y desconectar el bot
# ---------------------------------------------------------------------------

URL = "/api/businesses/sabor_casero/channels/telegram"
NOTHING = {"available": True, "status": "disconnected", "bot_username": None, "bot_name": None, "link": None, "problem": None}


@pytest.fixture
def panel(tmp_path):
    local = Local(tmp_path / "panel.sqlite3")
    fake = FakeTelegram()
    store = ChannelStore(local.engine, local.key)
    local.app = create_app(
        build_business_config_service(local.engine, secrets_key=local.key),
        telegram=TelegramChannelService(store, fake.client(), webhook_base=WEBHOOK_BASE),
    )
    local.client = TestClient(local.app, base_url=BASE_URL, client=LOCAL_CLIENT, raise_server_exceptions=False)
    for slug, name in (("sabor_casero", "Sabor Casero"), ("otro_negocio", "Otro Negocio")):
        assert local.client.post("/api/businesses", json={"slug": slug, "name": name}).status_code == 201
    yield local, fake, store
    local.engine.dispose()


def test_connecting_checks_the_code_registers_the_signed_webhook_and_never_shows_the_code(panel):
    local, fake, store = panel
    assert local.client.get(URL).json() == NOTHING
    response = local.client.post(f"{URL}/connect", json={"token": f" {TOKEN} "})
    assert response.status_code == 200
    assert response.json() == {"available": True, "status": "connected", "bot_username": "CafeAromaBot", "bot_name": "Café Aroma",
                               "link": "https://t.me/CafeAromaBot", "problem": None}
    secrets = store.channel_secrets("sabor_casero", TELEGRAM)
    assert fake.webhooks[TOKEN] == {"url": f"{WEBHOOK_BASE}/{secrets.webhook_id}", "secret": telegram_webhook_secret(TOKEN, secrets.webhook_id), "allowed": ["message"]}
    assert TOKEN not in response.text and TOKEN not in local.client.get(URL).text
    with local.engine.connect() as conn:
        stored = conn.execute(select(business_channels)).first()
    assert TOKEN not in json.dumps({key: str(value) for key, value in stored._mapping.items()}) and TOKEN not in repr(secrets)
    # Conectarlo otra vez (o cambiarle el nombre en @BotFather) conserva la misma ruta del webhook.
    fake.bots[TOKEN]["first_name"] = "Café Aroma Oficial"
    assert local.client.post(f"{URL}/connect", json={"token": TOKEN}).json()["bot_name"] == "Café Aroma Oficial"
    assert store.channel_secrets("sabor_casero", TELEGRAM).webhook_id == secrets.webhook_id


def test_a_code_that_is_wrong_or_unknown_to_telegram_is_explained_on_its_field(panel):
    local, fake, _store = panel
    malformed = local.client.post(f"{URL}/connect", json={"token": "hola"})
    assert malformed.status_code == 422 and malformed.json()["issues"][0]["path"] == "token"
    unknown = local.client.post(f"{URL}/connect", json={"token": "7000000000:AAH" + "z" * 32})
    assert unknown.status_code == 422 and "no reconoce" in unknown.json()["message"] and unknown.json()["issues"][0]["path"] == "token"
    assert fake.webhooks == {} and local.client.get(URL).json() == NOTHING


def test_a_bot_never_ends_up_in_two_businesses_and_its_webhook_is_not_touched(panel):
    local, fake, store = panel
    local.client.post(f"{URL}/connect", json={"token": TOKEN})
    before = dict(fake.webhooks[TOKEN])
    taken = local.client.post("/api/businesses/otro_negocio/channels/telegram/connect", json={"token": TOKEN})
    assert taken.status_code == 409 and "otro negocio" in taken.json()["message"]
    assert fake.webhooks[TOKEN] == before and store.channel_secrets("otro_negocio", TELEGRAM) is None


def test_changing_the_bot_unhooks_the_previous_one(panel):
    local, fake, _store = panel
    local.client.post(f"{URL}/connect", json={"token": TOKEN})
    assert local.client.post(f"{URL}/connect", json={"token": OTHER_TOKEN}).json()["bot_username"] == "OtroBot"
    assert TOKEN not in fake.webhooks and OTHER_TOKEN in fake.webhooks


def test_checking_finds_a_changed_code_or_a_bot_connected_elsewhere_and_reconnecting_brings_it_back(panel):
    local, fake, store = panel
    local.client.post(f"{URL}/connect", json={"token": TOKEN})
    assert local.client.get(f"{URL}/status").json()["status"] == "connected"
    # Lo conectaron en otra plataforma: Telegram envía sus mensajes allá.
    fake.webhooks[TOKEN]["url"] = "https://otra-plataforma.example/hook"
    elsewhere = local.client.get(f"{URL}/status").json()
    assert elsewhere["status"] == "disconnected" and "otra plataforma" in elsewhere["problem"]
    back = local.client.post(f"{URL}/reconnect").json()
    assert back["status"] == "connected" and back["problem"] is None
    assert fake.webhooks[TOKEN]["url"].endswith(store.channel_secrets("sabor_casero", TELEGRAM).webhook_id)
    # Cambiaron el código en @BotFather: el guardado ya no sirve.
    fake.bots["7123456789:AAH" + "c" * 32] = fake.bots.pop(TOKEN)
    revoked = local.client.get(f"{URL}/status").json()
    assert revoked["status"] == "disconnected" and "Volver a conectar" in revoked["problem"]
    assert local.client.get(URL).json()["problem"] == revoked["problem"]
    assert local.client.post(f"{URL}/reconnect").status_code == 502


def test_disconnecting_unhooks_the_bot_and_keeps_the_chats(panel):
    local, fake, store = panel
    local.client.post(f"{URL}/connect", json={"token": TOKEN})
    assert local.client.post(f"{URL}/disconnect").json() == NOTHING
    assert TOKEN not in fake.webhooks and store.channel_secrets("sabor_casero", TELEGRAM) is None
    # Si Telegram ya no reconoce el código, desconectar igual funciona.
    local.client.post(f"{URL}/connect", json={"token": TOKEN})
    fake.bots.pop(TOKEN)
    assert local.client.post(f"{URL}/disconnect").json() == NOTHING


def test_without_a_public_engine_address_telegram_is_not_available(tmp_path):
    local = Local(tmp_path / "panel.sqlite3")
    fake = FakeTelegram()
    local.app = create_app(
        build_business_config_service(local.engine, secrets_key=local.key),
        telegram=TelegramChannelService(ChannelStore(local.engine, local.key), fake.client(), webhook_base=None),
    )
    client = TestClient(local.app, base_url=BASE_URL, client=LOCAL_CLIENT, raise_server_exceptions=False)
    client.post("/api/businesses", json={"slug": "sabor_casero", "name": "Sabor Casero"})
    assert client.get(URL).json()["available"] is False
    refused = client.post(f"{URL}/connect", json={"token": TOKEN})
    assert refused.status_code == 503 and fake.webhooks == {}
    local.engine.dispose()


def test_deleting_the_business_unhooks_its_bot(panel):
    local, fake, _store = panel
    local.client.post(f"{URL}/connect", json={"token": TOKEN})
    deleted = local.client.delete("/api/businesses/sabor_casero", params={"confirm": "Sabor Casero"})
    assert deleted.status_code == 204 and TOKEN not in fake.webhooks


def test_the_team_replies_from_the_panel_by_telegram_and_a_changed_code_marks_the_channel(panel):
    local, fake, store = panel
    local.client.post(f"{URL}/connect", json={"token": TOKEN})
    messenger = ChannelMessenger(store, lambda _url: None, telegram=fake.client)
    assert messenger.send_text("sabor_casero", TELEGRAM, "tg-5551234", "Hola Ana, soy Laura") == "501"
    assert messenger.send_media("sabor_casero", TELEGRAM, "tg-5551234", "document", MediaFile("application/pdf", b"%PDF", "lista.pdf"), "La lista") == "502"
    with pytest.raises(ChannelError) as missing:
        messenger.send_text("otro_negocio", TELEGRAM, "tg-5551234", "Hola")
    assert "Telegram no está conectado" in str(missing.value)
    fake.bots.pop(TOKEN)
    with pytest.raises(ChannelError):
        messenger.send_text("sabor_casero", TELEGRAM, "tg-5551234", "Hola")
    assert store.telegram("sabor_casero").status == "disconnected"


# ---------------------------------------------------------------------------
# Motor: el webhook responde con el asistente del negocio
# ---------------------------------------------------------------------------

@pytest.fixture
def engine_webhook(monkeypatch, tmp_path):
    url = publish_document(monkeypatch, tmp_path, "restaurant")
    store = create_business_config_engine(url)
    channels = ChannelStore(store, os.environ["BUSINESS_CONFIG_SECRETS_KEY"])
    channels.save_telegram("restaurant", token=TOKEN, bot=TelegramBot("7123456789", "CafeAromaBot", "Café Aroma"), webhook_id="w" * 32)
    fake = FakeTelegram()
    FakeAI.reply, FakeAI.metadata, FakeAI.received, FakeAI.while_thinking = "¡Hola Ana! Tenemos *hamburguesas* artesanales.", {"intent": "info"}, [], None
    FakeMedia.keys = []
    monkeypatch.setattr(whatsapp_qr_webhook, "AIService", FakeAI)
    monkeypatch.setattr(whatsapp_qr_webhook, "TelegramClient", fake.client)
    monkeypatch.setattr(whatsapp_qr_webhook, "OpenRouterMediaInterpreter", FakeMedia)
    monkeypatch.setattr(whatsapp_qr_webhook, "_business_key", lambda _slug: "clave-del-negocio")
    app = FastAPI()
    app.include_router(telegram_webhook.router)
    headers = {telegram_webhook.SECRET_HEADER: telegram_webhook_secret(TOKEN, "w" * 32)}
    yield TestClient(app), f"/channels/telegram/{'w' * 32}", headers, fake, ConversationStore(store), channels
    store.dispose()
    runtime_access.dispose_shared_engines()


def _thread(conversations: ConversationStore):
    (summary,) = conversations.recent(["restaurant"], channel="telegram", limit=5)
    return conversations.thread(summary.id)


def test_a_customer_message_is_saved_answered_with_typing_and_remembered_as_a_telegram_contact(engine_webhook):
    client, path, headers, fake, conversations, _channels = engine_webhook
    assert client.post(path, json=update(), headers=headers).json() == {"status": "accepted"}
    assert fake.sent("sendChatAction") == [{"chat_id": "5551234", "action": "typing"}]
    assert fake.sent() == [{"chat_id": "5551234", "text": "¡Hola Ana! Tenemos <b>hamburguesas</b> artesanales.", "parse_mode": "HTML"}]
    assert FakeAI.last["user_id"] == "tg-5551234" and FakeAI.received == ["Hola, ¿qué venden?"]
    summary, messages = _thread(conversations)
    assert summary.contact_name == "Ana Pérez" and summary.channel == "telegram"
    assert [(m.author, m.status) for m in messages] == [("customer", "received"), ("assistant", "sent")]
    # Telegram repite el aviso: no se guarda ni se responde dos veces.
    assert client.post(path, json=update(), headers=headers).json() == {"status": "duplicate"}
    assert len(fake.sent()) == 1


def test_a_photo_is_downloaded_seen_and_answered(engine_webhook):
    client, path, headers, fake, conversations, _channels = engine_webhook
    photo = update(text=None, caption="Ya pagué", photo=[{"file_id": "FOTO-GRANDE"}])
    assert client.post(path, json=photo, headers=headers).json() == {"status": "accepted"}
    assert FakeMedia.keys == ["clave-del-negocio"] and "comprobante" in FakeAI.received[0]
    _summary, messages = _thread(conversations)
    assert messages[0].kind == "image" and messages[0].media_note


def test_a_notice_without_the_signature_or_to_an_unknown_route_is_rejected(engine_webhook):
    client, path, headers, fake, _conversations, _channels = engine_webhook
    assert client.post(path, json=update()).status_code == 403
    assert client.post(path, json=update(), headers={telegram_webhook.SECRET_HEADER: telegram_webhook_secret(OTHER_TOKEN, "w" * 32)}).status_code == 403
    assert client.post(f"/channels/telegram/{'x' * 32}", json=update(), headers=headers).status_code == 404
    assert client.post("/channels/telegram/corto", json=update(), headers=headers).status_code == 404
    assert fake.calls == []


def test_groups_and_bots_are_ignored(engine_webhook):
    client, path, headers, fake, _conversations, _channels = engine_webhook
    assert client.post(path, json=update(chat={"id": -100, "type": "group"}), headers=headers).json() == {"status": "ignored"}
    assert client.post(path, json={"update_id": 2, "my_chat_member": {}}, headers=headers).json() == {"status": "ignored"}
    assert fake.calls == []


def test_if_telegram_rejects_the_code_the_reply_stays_not_sent_and_canales_asks_for_the_new_one(engine_webhook):
    client, path, headers, fake, conversations, channels = engine_webhook
    fake.bots.pop(TOKEN)
    client.post(path, json=update(), headers=headers)
    _summary, messages = _thread(conversations)
    assert [(m.author, m.status) for m in messages] == [("customer", "received"), ("assistant", "failed")]
    assert channels.telegram("restaurant").status == "disconnected"


def test_a_telegram_chat_nobody_attended_is_resumed_by_telegram():
    resumed: list[tuple[str, str]] = []
    secrets_asked: list[tuple[str, str]] = []
    secrets = ChannelSecrets("restaurant", "https://api.telegram.org", TOKEN, "w" * 32, TELEGRAM)
    from datetime import datetime, timedelta, timezone

    from app.domain.business_config.attention import AttentionSettings

    now = datetime(2026, 11, 13, 15, tzinfo=timezone.utc)
    chat = WaitingChat(id="c1", business_slug="restaurant", channel=TELEGRAM, contact_ref="tg-5551234", waiting_since=now - timedelta(hours=2))
    sweep = ResumeSweep(
        waiting=lambda **_kw: [chat], settings=lambda _slug: AttentionSettings(resume_after_minutes=30), resume=lambda *_a, **_kw: "aviso-1",
        pending=lambda *_a, **_kw: "¿Siguen ahí?", secrets=lambda slug, channel: secrets_asked.append((slug, channel)) or secrets,
        continue_chat=lambda s, conversation, contact, text: resumed.append((s.channel, contact)), alerts=lambda _n: None, clock=lambda: now,
    )
    assert sweep.run().resumed == 1
    assert secrets_asked == [("restaurant", TELEGRAM)] and resumed == [(TELEGRAM, "tg-5551234")]


def test_a_local_database_from_before_telegram_upgrades_without_losing_whatsapp(tmp_path):
    from sqlalchemy import create_engine, inspect

    from app.infrastructure.business_config.database import create_local_schema

    engine = create_engine(f"sqlite:///{(tmp_path / 'antes.sqlite3').as_posix()}")
    create_local_schema(engine)
    with engine.begin() as conn:
        conn.exec_driver_sql("DROP INDEX business_channels_account_key")
        conn.exec_driver_sql("ALTER TABLE business_channels DROP COLUMN account_id")
        conn.exec_driver_sql("ALTER TABLE business_channels DROP COLUMN account_username")
        conn.exec_driver_sql(
            "INSERT INTO business_channels (tenant_id, channel, provider, server_url, token_ciphertext, webhook_id, status, updated_at) "
            "VALUES ('00000000000000000000000000000001', 'whatsapp', 'uazapi', 'https://free.uazapi.com', 'cifrado', 'w-antiguo', 'connected', '2026-11-01')"
        )
    create_local_schema(engine)
    columns = {column["name"] for column in inspect(engine).get_columns("business_channels")}
    assert {"account_id", "account_username"} <= columns
    assert "business_channels_account_key" in {index["name"] for index in inspect(engine).get_indexes("business_channels")}
    with engine.connect() as conn:
        assert conn.exec_driver_sql("SELECT webhook_id, status FROM business_channels").all() == [("w-antiguo", "connected")]
    engine.dispose()
