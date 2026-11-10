"""Cliente de uazapi (WhatsApp por código QR): estado, conexión, webhook, envío de texto y lectura de los mensajes que llegan.

Usa la API de uazapiGO v2: el token de la instancia va en la cabecera `token` y el de administrador en `admintoken`. Antes de cada
llamada resuelve el servidor y se niega a llamar a una IP que no sea pública: el panel nunca sirve de puente hacia la red interna.
Los tokens nunca van a los registros.
"""
from __future__ import annotations

import socket
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

import httpx

from app.domain.business_config.channels import (
    CONNECTION_STATUSES,
    ChannelError,
    IncomingMessage,
    ProviderStatus,
    is_public_address,
    normalize_server_url,
    phone_digits,
)
from app.utils.logger import logger

TIMEOUT = httpx.Timeout(20.0, connect=8.0)
# Eventos que recibe el webhook: los mensajes y los cambios de conexión. Se excluye lo que envió la propia API (evita responderse a
# sí mismo), lo que escribe el negocio desde su teléfono y los grupos.
WEBHOOK_EVENTS = ["messages", "connection"]
WEBHOOK_EXCLUDE = ["wasSentByApi", "fromMeYes", "isGroupYes"]
PERSONAL_CHAT = "@s.whatsapp.net"

Resolver = Callable[[str], list[str]]


def _resolve(host: str) -> list[str]:
    return sorted({info[4][0] for info in socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)})


class UazapiClient:
    def __init__(self, server_url: str, *, transport: httpx.BaseTransport | None = None, resolver: Resolver | None = None) -> None:
        self._server = normalize_server_url(server_url)
        self._transport = transport
        self._resolver = resolver or _resolve

    # ------------------------------------------------------------------ llamadas

    def _check_public(self) -> None:
        host = urlsplit(self._server).hostname or ""
        try:
            addresses = self._resolver(host)
        except OSError as exc:
            raise ChannelError("No encontramos ese servidor. Revisa la dirección.", field="server_url") from exc
        if not addresses or not all(is_public_address(address) for address in addresses):
            raise ChannelError("La dirección debe ser la de un servidor público.", field="server_url")

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
            raise ChannelError("El servidor de uazapi no respondió. Intenta de nuevo en un momento.") from exc
        if response.status_code == 401:
            raise ChannelError("El servidor rechazó el token. Revisa que lo hayas copiado completo.", field="token")
        if response.status_code == 404:
            raise ChannelError("Ese servidor no tiene esa función de uazapi.", field="server_url")
        if response.status_code == 429:
            raise ChannelError("El servidor de uazapi está ocupado. Intenta de nuevo en un minuto.")
        if response.status_code >= 400:
            logger.warning("uazapi_error", extra={"path": path, "status": response.status_code})
            raise ChannelError("El servidor de uazapi no pudo hacerlo. Intenta de nuevo.")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ChannelError("El servidor no respondió como uno de uazapi. Revisa la dirección.", field="server_url") from exc
        return payload if isinstance(payload, dict) else {"items": payload}

    # ------------------------------------------------------------------ instancia

    def status(self, token: str) -> ProviderStatus:
        return _provider_status(self._call("GET", "/instance/status", token=token))

    def create_instance(self, admin_token: str, name: str) -> str:
        """Crea una instancia con el token de administrador y devuelve su token."""
        payload = self._call("POST", "/instance/create", admin_token=admin_token, body={"name": name})
        token = str((payload.get("instance") or {}).get("token") or payload.get("token") or "").strip()
        if not token:
            raise ChannelError("El servidor no entregó el token de la instancia.")
        return token

    def connect(self, token: str) -> ProviderStatus:
        """Pide el código QR. Si la conexión ya está en curso, devuelve el QR que ya existe."""
        try:
            self._call("POST", "/instance/connect", token=token, body={})
        except ChannelError:
            # 409 (ya está conectando) y otros: el estado dice si hay un QR para mostrar.
            pass
        return self.status(token)

    def disconnect(self, token: str) -> None:
        self._call("POST", "/instance/disconnect", token=token)

    def set_webhook(self, token: str, url: str) -> None:
        self._call(
            "POST", "/webhook", token=token, body={"url": url, "enabled": True, "events": WEBHOOK_EVENTS, "excludeMessages": WEBHOOK_EXCLUDE}
        )

    def send_text(self, token: str, phone: str, text: str) -> None:
        self._call("POST", "/send/text", token=token, body={"number": phone_digits(phone), "text": text})


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


def parse_incoming(payload: dict[str, Any]) -> IncomingMessage | None:
    """El mensaje de texto de un cliente que trae el webhook, o None si no hay que responderlo (otro evento, un grupo, un mensaje
    del propio negocio o de la API, o sin texto)."""
    if str(payload.get("EventType") or "").strip().lower() != "messages":
        return None
    message = payload.get("message") if isinstance(payload.get("message"), dict) else {}
    chat_id = str(message.get("chatid") or message.get("sender") or "")
    if message.get("fromMe") or message.get("wasSentByApi") or message.get("isGroup") or not chat_id.endswith(PERSONAL_CHAT):
        return None
    text = str(message.get("text") or "").strip()
    phone = phone_digits(chat_id)
    message_id = str(message.get("messageid") or message.get("id") or "").strip()
    if not text or not phone or not message_id:
        return None
    name = str(message.get("senderName") or "").strip() or None
    return IncomingMessage(message_id=message_id, phone=phone, contact_name=name, text=text)


def connection_event(payload: dict[str, Any]) -> ProviderStatus | None:
    """El nuevo estado de la conexión que avisa el webhook (evento `connection`), o None si es otro evento."""
    if str(payload.get("EventType") or "").strip().lower() != "connection":
        return None
    return _provider_status(payload)
