"""Cliente de la API de bots de Telegram: revisar el código del bot, registrar su webhook, enviar textos y archivos, mostrar
«escribiendo…», descargar lo que manda el cliente y leer cada aviso.

La API es oficial y siempre la misma (`https://api.telegram.org`), así que no hay servidor que validar. El token del bot va en la ruta
de cada llamada: por eso nunca se registra una ruta, una URL ni el texto de un error de httpx, solo el método y el código de respuesta.
Los errores llegan al negocio sin detalles técnicos.

Formato: el asistente escribe como en WhatsApp (`*negrita*`, `_cursiva_`, `~tachado~`). Aquí se pasa al HTML de Telegram; si Telegram
no lo acepta, el mensaje sale igual, como texto plano.
"""
from __future__ import annotations

import html
import mimetypes
import re
from typing import Any

import httpx

from app.domain.business_config.channels import (
    TELEGRAM_API,
    ChannelError,
    IncomingMessage,
    TelegramBot,
    telegram_chat_id,
    telegram_contact_ref,
)
from app.domain.business_config.conversations import MAX_CAPTION_CHARS, MAX_MEDIA_BYTES, MediaFile
from app.utils.logger import logger

TIMEOUT = httpx.Timeout(20.0, connect=8.0)
# Solo los mensajes nuevos: ni los editados, ni los de canales, ni los cambios de miembros.
ALLOWED_UPDATES = ["message"]
# Lo más largo que acepta Telegram en un mensaje; lo más largo se parte en varios.
MAX_TEXT_CHARS = 4096
_CHUNK_CHARS = 3800

REJECTED = "Telegram rechazó el código del bot: puede que lo hayas cambiado en @BotFather. Pega el código nuevo en Canales."
NO_ANSWER = "Telegram no respondió. Intenta de nuevo en un momento."
BUSY = "Telegram está recibiendo demasiados mensajes de este bot. Intenta de nuevo en un minuto."
BLOCKED = "El cliente bloqueó el bot o borró el chat en Telegram: no le llegan mensajes hasta que vuelva a escribirle."
NO_CHAT = "Telegram no encuentra este chat. El cliente debe escribirle primero al bot."
# El cliente tocó «Iniciar»: para el asistente es un saludo.
START_TEXT = "Hola"

# El tipo de mensaje de Telegram → el de la bandeja (y qué campo trae el archivo).
_MEDIA_FIELDS = (
    ("photo", "image"),
    ("voice", "audio"),
    ("audio", "audio"),
    ("video", "video"),
    ("video_note", "video"),
    ("animation", "video"),
    ("document", "document"),
    ("sticker", "sticker"),
)
# Cómo sale cada tipo desde el panel: el método de la API y el campo del archivo.
_SEND_METHODS = {"image": ("sendPhoto", "photo"), "video": ("sendVideo", "video"), "audio": ("sendAudio", "audio"), "document": ("sendDocument", "document")}
_EXTENSION_TYPES = {".oga": "audio/ogg", ".ogg": "audio/ogg", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".mp4": "video/mp4"}


class _NotFormatted(Exception):
    """Telegram no aceptó el formato del texto: se envía como texto plano."""


class TelegramClient:
    def __init__(self, server_url: str = TELEGRAM_API, *, transport: httpx.BaseTransport | None = None) -> None:
        # La dirección es siempre la oficial: el argumento existe para que el motor cree los clientes de todos los canales igual.
        self._transport = transport

    # ------------------------------------------------------------------ llamadas

    def _http(self) -> httpx.Client:
        return httpx.Client(base_url=TELEGRAM_API, timeout=TIMEOUT, transport=self._transport, follow_redirects=False)

    def _call(self, token: str, method: str, *, body: dict | None = None, data: dict | None = None, files: dict | None = None) -> Any:
        try:
            with self._http() as client:
                if files is not None:
                    response = client.post(f"/bot{token}/{method}", data=data, files=files)
                else:
                    response = client.post(f"/bot{token}/{method}", json=body or {})
        except httpx.HTTPError as exc:
            logger.warning("telegram_sin_respuesta", extra={"method": method, "error": type(exc).__name__})
            raise ChannelError(NO_ANSWER) from exc
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        payload = payload if isinstance(payload, dict) else {}
        if response.status_code == 200 and payload.get("ok") is True:
            return payload.get("result")
        description = str(payload.get("description") or "").lower()
        status = response.status_code
        if status in (401, 404):
            # El token no existe o lo cambiaron en @BotFather.
            raise ChannelError(REJECTED, gone=True)
        if status == 403:
            raise ChannelError(BLOCKED)
        if status == 429:
            raise ChannelError(BUSY)
        if status == 400 and "parse entities" in description:
            raise _NotFormatted()
        if status == 400 and "chat not found" in description:
            raise ChannelError(NO_CHAT)
        logger.warning("telegram_error", extra={"method": method, "status": status})
        raise ChannelError(NO_ANSWER)

    # ------------------------------------------------------------------ el bot

    def get_me(self, token: str) -> TelegramBot:
        """El bot de ese código. Si Telegram no lo reconoce, `ChannelError` con `gone`."""
        result = _record(self._call(token, "getMe"))
        bot_id, username = str(result.get("id") or "").strip(), _text(result.get("username"))
        if not bot_id or not username or result.get("is_bot") is False:
            logger.error("telegram_bot_incompleto")
            raise ChannelError(NO_ANSWER)
        return TelegramBot(id=bot_id, username=username, name=_text(result.get("first_name")) or username)

    def set_webhook(self, token: str, url: str, secret: str) -> None:
        """Los mensajes del bot llegan a `url` con la firma `secret`. Los que esperaban de antes no se responden (podrían ser de días)."""
        self._call(token, "setWebhook", body={"url": url, "secret_token": secret, "allowed_updates": ALLOWED_UPDATES, "drop_pending_updates": True})

    def webhook_url(self, token: str) -> str | None:
        """Adónde envía Telegram los mensajes del bot ahora mismo (None si a ningún lado)."""
        return _text(_record(self._call(token, "getWebhookInfo")).get("url")) or None

    def delete_webhook(self, token: str) -> None:
        """El bot deja de enviar mensajes aquí. Si Telegram ya no reconoce el código, no hay nada que quitar."""
        try:
            self._call(token, "deleteWebhook", body={"drop_pending_updates": False})
        except ChannelError as error:
            if not error.gone:
                raise

    # ------------------------------------------------------------------ mensajes

    def send_text(self, token: str, contact_ref: str, text: str) -> str | None:
        """Envía el texto (en varios mensajes si es muy largo) y devuelve el id del último."""
        chat_id = telegram_chat_id(contact_ref)
        sent: str | None = None
        for chunk in split_text(text):
            try:
                result = self._call(token, "sendMessage", body={"chat_id": chat_id, "text": to_telegram_html(chunk), "parse_mode": "HTML"})
            except _NotFormatted:
                result = self._call(token, "sendMessage", body={"chat_id": chat_id, "text": chunk})
            sent = _message_id(result) or sent
        return sent

    def send_media(self, token: str, contact_ref: str, kind: str, media: MediaFile, caption: str = "") -> str | None:
        """Envía un archivo (foto, video, audio o documento) con su texto y devuelve el id que le dio Telegram."""
        chat_id = telegram_chat_id(contact_ref)
        method, field = _SEND_METHODS.get(kind, _SEND_METHODS["document"])
        if kind == "audio" and media.mime_type in ("audio/ogg", "audio/opus"):
            method, field = "sendVoice", "voice"
        name = media.file_name or _default_name(field, media.mime_type)
        data: dict[str, str] = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption[:MAX_CAPTION_CHARS]
        # El texto va sin formato: así Telegram nunca lo rechaza por eso.
        return _message_id(self._call(token, method, data=data, files={field: (name, media.content, media.mime_type)}))

    def presence(self, token: str, contact_ref: str, presence: str = "composing", delay_ms: int = 30_000) -> None:
        """Muestra «escribiendo…» en el chat del cliente (Telegram lo quita a los 5 segundos o al enviar)."""
        action = "record_voice" if presence == "recording" else "typing"
        self._call(token, "sendChatAction", body={"chat_id": telegram_chat_id(contact_ref), "action": action})

    def download(self, token: str, file_id: str) -> MediaFile | None:
        """El archivo de un mensaje, o None si es más grande de lo que se guarda."""
        info = _record(self._call(token, "getFile", body={"file_id": file_id}))
        path = _text(info.get("file_path"))
        size = info.get("file_size")
        if not path or (isinstance(size, int) and size > MAX_MEDIA_BYTES):
            return None
        try:
            with self._http() as client:
                response = client.get(f"/file/bot{token}/{path}")
        except httpx.HTTPError as exc:
            logger.warning("telegram_archivo_sin_respuesta", extra={"error": type(exc).__name__})
            raise ChannelError(NO_ANSWER) from exc
        if response.status_code != 200 or not 0 < len(response.content) <= MAX_MEDIA_BYTES:
            return None
        return MediaFile(_mime_of(path, response.headers.get("content-type")), response.content)


# ---------------------------------------------------------------------------------------------------------- formato


def to_telegram_html(text: str) -> str:
    """El formato de WhatsApp en el HTML de Telegram: `*negrita*`, `_cursiva_` y `~tachado~`. Lo demás se escapa."""
    escaped = html.escape(text, quote=False)
    for mark, tag in (("*", "b"), ("_", "i"), ("~", "s")):
        m = re.escape(mark)
        pattern = re.compile(rf"(?<![\w{m}]){m}(?=\S)([^\n{m}]*?\S){m}(?![\w{m}])")
        escaped = pattern.sub(rf"<{tag}>\1</{tag}>", escaped)
    return escaped


def split_text(text: str) -> list[str]:
    """El texto en partes que Telegram acepta, cortando en un salto de línea o un espacio cuando se puede."""
    rest = text.strip()
    parts: list[str] = []
    while len(rest) > _CHUNK_CHARS:
        cut = rest.rfind("\n", 0, _CHUNK_CHARS)
        if cut <= _CHUNK_CHARS // 2:
            cut = rest.rfind(" ", 0, _CHUNK_CHARS)
        if cut <= _CHUNK_CHARS // 2:
            cut = _CHUNK_CHARS
        parts.append(rest[:cut].strip())
        rest = rest[cut:].strip()
    if rest:
        parts.append(rest)
    return parts


# ---------------------------------------------------------------------------------------------------------- avisos


def parse_update(payload: dict[str, Any]) -> IncomingMessage | None:
    """El mensaje de un cliente que trae el aviso (texto, foto, nota de voz, documento...), o None si no hay que atenderlo: otro tipo de
    aviso, un grupo o canal, otro bot, o un mensaje vacío."""
    message = _record(payload.get("message"))
    chat = _record(message.get("chat"))
    sender = _record(message.get("from"))
    if not message or chat.get("type") != "private" or sender.get("is_bot"):
        return None
    chat_id, message_id = chat.get("id"), message.get("message_id")
    if not isinstance(chat_id, int) or not isinstance(message_id, int):
        return None
    text = _text(message.get("text")) or _text(message.get("caption"))
    kind, media_ref, mime_type, file_name = "text", None, None, None
    for field, field_kind in _MEDIA_FIELDS:
        value = message.get(field)
        if not value:
            continue
        item = _record(value[-1] if isinstance(value, list) else value)  # las fotos vienen en varios tamaños: el último es el más grande
        kind, media_ref = field_kind, _text(item.get("file_id")) or None
        mime_type = _text(item.get("mime_type")).lower() or ("image/jpeg" if field == "photo" else None)
        file_name = _text(item.get("file_name")) or None
        break
    else:
        if message.get("location") or message.get("venue"):
            kind = "location"
        elif message.get("contact"):
            kind = "contact"
        elif not text:
            return None
    if kind == "text" and (text == "/start" or text.startswith("/start ")):
        text = START_TEXT
    return IncomingMessage(
        message_id=str(message_id), phone=telegram_contact_ref(chat_id), contact_name=_contact_name(sender, chat), text=text, kind=kind,
        mime_type=mime_type, file_name=file_name, media_ref=media_ref,
    )


def _contact_name(sender: dict[str, Any], chat: dict[str, Any]) -> str | None:
    full = " ".join(part for part in (_text(sender.get("first_name")) or _text(chat.get("first_name")), _text(sender.get("last_name"))) if part)
    username = _text(sender.get("username")) or _text(chat.get("username"))
    return full or (f"@{username}" if username else None)


def _record(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _message_id(result: Any) -> str | None:
    value = _record(result).get("message_id")
    return str(value) if isinstance(value, int) else None


def _mime_of(path: str, header: str | None) -> str:
    extension = ("." + path.rsplit(".", 1)[-1].lower()) if "." in path else ""
    if extension in _EXTENSION_TYPES:
        return _EXTENSION_TYPES[extension]
    guessed = mimetypes.guess_type(path)[0]
    sent = str(header or "").split(";")[0].strip().lower()
    return guessed or (sent if sent and sent != "application/octet-stream" else "application/octet-stream")


_DEFAULT_NAMES = {"photo": "foto", "video": "video", "audio": "audio", "voice": "nota-de-voz"}


def _default_name(field: str, mime_type: str) -> str:
    return _DEFAULT_NAMES.get(field, "documento") + (mimetypes.guess_extension(mime_type) or "")
