"""Cliente de uazapi (WhatsApp por código QR): instancias, conexión, webhook, envío de texto y lectura de los mensajes que llegan.

Usa la API de uazapiGO v2: el token de la instancia va en la cabecera `token` y el de administrador en `admintoken`. El servidor es el
de la plataforma (`UAZAPI_BASE_URL`); aun así, antes de cada llamada se resuelve y nunca se llama a una IP que no sea pública. Los
tokens nunca van a los registros, y los errores llegan al negocio sin detalles técnicos.
"""
from __future__ import annotations

import base64
import binascii
import re
import socket
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

import httpx

from app.domain.business_config.channels import (
    CONNECTION_STATUSES,
    ChannelError,
    DeliveryReceipt,
    IncomingMessage,
    ProviderStatus,
    WhatsAppUnavailableError,
    is_public_address,
    normalize_server_url,
    phone_digits,
)
from app.domain.business_config.conversations import MAX_MEDIA_BYTES, MediaFile
from app.infrastructure.channels.platform import is_simulator
from app.utils.logger import logger

TIMEOUT = httpx.Timeout(20.0, connect=8.0)
# Eventos que recibe el webhook: los mensajes, los recibos de entregado y leído, y los cambios de conexión. Se excluye lo que envió
# la propia API (evita responderse a sí mismo) y los grupos. Lo que el negocio escribe desde su celular sí llega: es una respuesta del
# equipo, y la IA no debe hablar encima de ella (`parse_own_message`).
WEBHOOK_EVENTS = ["messages", "messages_update", "connection"]
WEBHOOK_EXCLUDE = ["wasSentByApi", "isGroupYes"]
# Lo que no es el chat de un cliente: grupos, canales, difusiones y estados.
_NOT_A_CUSTOMER = re.compile(r"@(g\.us|newsletter|broadcast)$")
# El tipo de mensaje de WhatsApp (`messageType`, sin documentar en uazapi) → el de la bandeja.
_KINDS = (
    ("image", "image"),
    ("video", "video"),
    ("audio", "audio"),
    ("ptt", "audio"),
    ("document", "document"),
    ("sticker", "sticker"),
    ("location", "location"),
    ("contact", "contact"),
)
# Los recibos de WhatsApp → el estado de lo que salió.
_RECEIPTS = {"sent": "sent", "serverack": "sent", "delivered": "delivered", "deliveryack": "delivered", "read": "read", "played": "read"}
# El contenido en base64 de un archivo más grande que esto no se guarda (la bandeja dice que se vea en el teléfono).
_MAX_BASE64 = MAX_MEDIA_BYTES * 4 // 3 + 4
# El nombre con el que aparece la conexión en «Dispositivos vinculados» del teléfono del negocio.
DEVICE_NAME = "Asistente de ventas"

UNAVAILABLE = "La conexión de WhatsApp no está disponible en este momento. Intenta de nuevo más tarde."
NO_ANSWER = "WhatsApp no respondió. Intenta de nuevo en un momento."
BUSY = "WhatsApp está ocupado. Intenta de nuevo en un minuto."
GONE = "La conexión de este número ya no existe. Vuelve a conectarlo."

Resolver = Callable[[str], list[str]]


def _resolve(host: str) -> list[str]:
    return sorted({info[4][0] for info in socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)})


class UazapiClient:
    def __init__(self, server_url: str, *, transport: httpx.BaseTransport | None = None, resolver: Resolver | None = None) -> None:
        # El WhatsApp simulado de este equipo es el único servidor local permitido (`platform.is_simulator`); cualquier otro debe
        # ser público y con https.
        self._local = is_simulator(server_url)
        self._server = str(server_url).rstrip("/") if self._local else normalize_server_url(server_url)
        self._transport = transport
        self._resolver = resolver or _resolve

    # ------------------------------------------------------------------ llamadas

    def _check_public(self) -> None:
        if self._local:
            return
        host = urlsplit(self._server).hostname or ""
        try:
            addresses = self._resolver(host)
        except OSError as exc:
            logger.error("uazapi_servidor_no_resuelve", extra={"host": host})
            raise WhatsAppUnavailableError(UNAVAILABLE) from exc
        if not addresses or not all(is_public_address(address) for address in addresses):
            logger.error("uazapi_servidor_no_publico", extra={"host": host})
            raise WhatsAppUnavailableError(UNAVAILABLE)

    def _call(self, method: str, path: str, *, token: str | None = None, admin_token: str | None = None, body: dict | None = None) -> dict[str, Any]:
        self._check_public()
        headers = {"Accept": "application/json"}
        if token:
            headers["token"] = token
        if admin_token:
            headers["admintoken"] = admin_token
        try:
            with httpx.Client(base_url=self._server, timeout=TIMEOUT, transport=self._transport, follow_redirects=False) as client:
                response = client.request(method, path, headers=headers, json=body)
        except httpx.HTTPError as exc:
            logger.warning("uazapi_sin_respuesta", extra={"path": path, "error": type(exc).__name__})
            raise ChannelError(NO_ANSWER) from exc
        if response.status_code in (401, 404) and admin_token:
            # El token de administrador de la plataforma no sirve (o el servidor no es de uazapi): lo arregla quien opera la plataforma.
            logger.error("uazapi_administrador_rechazado", extra={"path": path, "status": response.status_code})
            raise WhatsAppUnavailableError(UNAVAILABLE)
        if response.status_code in (401, 404):
            raise ChannelError(GONE, gone=True)
        if response.status_code == 429:
            raise ChannelError(BUSY)
        if response.status_code >= 400:
            logger.warning("uazapi_error", extra={"path": path, "status": response.status_code})
            raise ChannelError(NO_ANSWER)
        try:
            payload = response.json()
        except ValueError as exc:
            logger.error("uazapi_respuesta_invalida", extra={"path": path})
            raise WhatsAppUnavailableError(UNAVAILABLE) from exc
        return payload if isinstance(payload, dict) else {"items": payload}

    # ------------------------------------------------------------------ instancia

    def status(self, token: str) -> ProviderStatus:
        return _provider_status(self._call("GET", "/instance/status", token=token))

    def create_instance(self, admin_token: str, name: str) -> str:
        """Crea una instancia con el token de administrador y devuelve su token."""
        payload = self._call("POST", "/instance/create", admin_token=admin_token, body={"name": name, "systemName": DEVICE_NAME})
        token = str((payload.get("instance") or {}).get("token") or payload.get("token") or "").strip()
        if not token:
            logger.error("uazapi_instancia_sin_token")
            raise ChannelError(NO_ANSWER)
        return token

    def connect(self, token: str) -> ProviderStatus:
        """Pide el código QR. Si la conexión ya está en curso, devuelve el QR que ya existe."""
        try:
            self._call("POST", "/instance/connect", token=token, body={})
        except ChannelError as error:
            if error.gone:
                raise
            # 409 (ya está conectando) y otros: el estado dice si hay un QR para mostrar.
        return self.status(token)

    def disconnect(self, token: str) -> None:
        self._call("POST", "/instance/disconnect", token=token)

    def delete_instance(self, token: str) -> None:
        """Cierra la sesión y borra la instancia del servidor. Si ya no existía, no pasa nada."""
        try:
            self._call("DELETE", "/instance", token=token)
        except ChannelError as error:
            if not error.gone:
                raise

    def set_webhook(self, token: str, url: str) -> None:
        self._call(
            "POST", "/webhook", token=token, body={"url": url, "enabled": True, "events": WEBHOOK_EVENTS, "excludeMessages": WEBHOOK_EXCLUDE}
        )

    def send_text(self, token: str, phone: str, text: str) -> str | None:
        """Envía un texto y devuelve el id que le dio WhatsApp (el que traen después los recibos de entregado y leído)."""
        payload = self._call("POST", "/send/text", token=token, body={"number": phone_digits(phone), "text": text})
        return str(payload.get("messageid") or payload.get("id") or "").strip() or None

    def send_media(self, token: str, phone: str, kind: str, media: MediaFile, caption: str = "") -> str | None:
        """Envía un archivo en base64 (foto, video, audio o documento, con su nombre) y devuelve el id que le dio WhatsApp."""
        body: dict[str, Any] = {
            "number": phone_digits(phone),
            "type": kind if kind in ("image", "video", "audio") else "document",
            "file": base64.b64encode(media.content).decode("ascii"),
        }
        if caption:
            body["text"] = caption
        if body["type"] == "document":
            body["docName"] = media.file_name or "documento"
        payload = self._call("POST", "/send/media", token=token, body=body)
        return str(payload.get("messageid") or payload.get("id") or "").strip() or None

    def presence(self, token: str, phone: str, presence: str = "composing", delay_ms: int = 30_000) -> None:
        """Muestra «escribiendo…» (o «grabando…») en el chat del cliente; se quita sola al enviar el mensaje."""
        self._call(
            "POST", "/message/presence", token=token,
            body={"number": phone_digits(phone), "presence": presence, "delay": max(1_000, min(int(delay_ms), 300_000))},
        )

    def download(self, token: str, message_id: str) -> MediaFile | None:
        """El archivo de un mensaje (foto, audio en MP3, documento...), o None si es más grande de lo que se guarda."""
        payload = self._call("POST", "/message/download", token=token, body={"id": message_id, "return_base64": True, "generate_mp3": True})
        data = str(payload.get("base64Data") or "")
        if not data or len(data) > _MAX_BASE64:
            return None
        if data.startswith("data:"):
            data = data.split(",", 1)[-1]
        try:
            content = base64.b64decode(data, validate=False)
        except (binascii.Error, ValueError):
            logger.warning("uazapi_archivo_invalido")
            return None
        mime_type = str(payload.get("mimetype") or "application/octet-stream").split(";")[0].strip().lower()
        return MediaFile(mime_type, content) if 0 < len(content) <= MAX_MEDIA_BYTES else None


def _provider_status(payload: dict[str, Any]) -> ProviderStatus:
    instance = payload.get("instance") if isinstance(payload.get("instance"), dict) else {}
    state = payload.get("status") if isinstance(payload.get("status"), dict) else {}
    raw = str(instance.get("status") or "").strip().lower()
    if state.get("connected") and state.get("loggedIn"):
        status = "connected"
    else:
        status = raw if raw in CONNECTION_STATUSES else "disconnected"
    jid = state.get("jid") if isinstance(state.get("jid"), dict) else {}
    qrcode = str(instance.get("qrcode") or "").strip() or None
    if qrcode and not qrcode.startswith("data:"):
        qrcode = f"data:image/png;base64,{qrcode}"
    return ProviderStatus(
        status=status,
        qrcode=qrcode if status == "connecting" else None,
        paircode=str(instance.get("paircode") or "").strip() or None,
        phone=phone_digits(jid.get("user")) or None,
        profile_name=str(instance.get("profileName") or "").strip() or None,
    )


def _record(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _kind(message_type: str) -> str:
    lowered = message_type.lower()
    for marker, kind in _KINDS:
        if marker in lowered:
            return kind
    if not lowered or any(marker in lowered for marker in ("conversation", "extendedtext", "text")):
        return "text"
    return "other"


def parse_incoming(payload: dict[str, Any]) -> IncomingMessage | None:
    """El mensaje de un cliente que trae el webhook (texto, foto, audio, documento...), o None si no hay que atenderlo: otro evento,
    un grupo o canal, un mensaje del propio negocio o de la API, o un aviso incompleto."""
    if _text(payload.get("EventType")).lower() != "messages":
        return None
    message = _record(payload.get("message"))
    if not message or message.get("fromMe") or message.get("wasSentByApi") or message.get("isGroup"):
        return None
    chat_id = _text(message.get("chatid")) or _text(message.get("sender"))
    if _NOT_A_CUSTOMER.search(chat_id) or chat_id.startswith("status@"):
        return None
    # El teléfono: del chat si es una cuenta normal; si es un id «@lid» de WhatsApp, del remitente.
    candidates = (chat_id, _text(message.get("sender_pn")), _text(message.get("sender")))
    return _message(message, candidates, contact_name=_text(message.get("senderName")) or None)


def parse_own_message(payload: dict[str, Any]) -> IncomingMessage | None:
    """Lo que el negocio escribió desde su celular (o WhatsApp Web) en el chat de un cliente: una respuesta del equipo. None si es
    otro evento, lo envió la API (eso ya está en la bandeja), es de un grupo o no se puede saber de qué cliente es."""
    if _text(payload.get("EventType")).lower() != "messages":
        return None
    message = _record(payload.get("message"))
    if not message or message.get("fromMe") is not True or message.get("wasSentByApi") or message.get("isGroup"):
        return None
    chat_id = _text(message.get("chatid"))
    if not chat_id or _NOT_A_CUSTOMER.search(chat_id) or chat_id.startswith("status@"):
        return None
    # El cliente es el chat (el remitente es el propio negocio); de un id «@lid», su número viene en `chatid_pn` si uazapi lo trae.
    return _message(message, (chat_id, _text(message.get("chatid_pn"))), contact_name=None)


def _message(message: dict[str, Any], candidates: tuple[str, ...], *, contact_name: str | None) -> IncomingMessage | None:
    phone = next((digits for jid in candidates if jid and not jid.endswith("@lid") for digits in [phone_digits(jid)] if 7 <= len(digits) <= 15), "")
    message_id = _text(message.get("messageid")) or _text(message.get("id"))
    if not phone or not message_id:
        return None
    content = _record(message.get("content"))
    kind = _kind(_text(message.get("messageType")))
    text = _text(message.get("text")) or _text(content.get("text")) or _text(content.get("caption"))
    if kind == "text" and not text:
        return None
    mime_type = (_text(message.get("mimetype")) or _text(content.get("mimetype"))).split(";")[0].strip().lower() or None
    file_name = _text(content.get("fileName")) or _text(message.get("fileName")) or None
    return IncomingMessage(
        message_id=message_id, phone=phone, contact_name=contact_name, text=text, kind=kind, mime_type=mime_type, file_name=file_name,
    )


def parse_receipt(payload: dict[str, Any]) -> DeliveryReceipt | None:
    """El recibo de entregado o leído de lo que salió (evento `messages_update`), o None si es otro evento o de un grupo."""
    if _text(payload.get("EventType")).lower() != "messages_update":
        return None
    event = _record(payload.get("event"))
    chat_id = _text(event.get("chatid")) or _text(event.get("Chat"))
    if event.get("IsGroup") or _NOT_A_CUSTOMER.search(chat_id):
        return None
    status = _RECEIPTS.get((_text(payload.get("state")) or _text(event.get("Type"))).lower())
    raw = event.get("MessageIDs")
    ids = tuple(item.strip() for item in (raw if isinstance(raw, list) else []) if isinstance(item, str) and 0 < len(item.strip()) <= 128)[:100]
    return DeliveryReceipt(ids, status) if status and ids else None


def connection_event(payload: dict[str, Any]) -> ProviderStatus | None:
    """El nuevo estado de la conexión que avisa el webhook (evento `connection`), o None si es otro evento."""
    if str(payload.get("EventType") or "").strip().lower() != "connection":
        return None
    return _provider_status(payload)
