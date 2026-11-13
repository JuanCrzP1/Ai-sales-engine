"""Envía por el canal del cliente lo que el equipo responde desde el panel (implementa `OutboundMessenger`).

WhatsApp por código QR usa la instancia del negocio en el servidor de uazapi de la plataforma; Telegram, el bot del negocio. Los dos
tokens van cifrados en `business_channels`. Los clientes de cada canal los pone la raíz de composición. Si Telegram rechaza el código
del bot, el canal queda «desconectado» y Canales le pide al negocio el código nuevo.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.business_config_application.channels import ProviderFactory
from app.domain.business_config.channels import TELEGRAM, WHATSAPP, ChannelError
from app.domain.business_config.conversations import MediaFile
from app.infrastructure.business_config.channel_store import ChannelStore

NOT_CONNECTED = {
    WHATSAPP: "WhatsApp no está conectado en este negocio. Conéctalo en Canales para responder desde aquí.",
    TELEGRAM: "Telegram no está conectado en este negocio. Conéctalo en Canales para responder desde aquí.",
}


class ChannelMessenger:
    def __init__(self, channels: ChannelStore, providers: ProviderFactory, telegram: Callable[[str], Any] | None = None) -> None:
        self._channels = channels
        self._clients: dict[str, Callable[[str], Any]] = {WHATSAPP: providers}
        if telegram is not None:
            self._clients[TELEGRAM] = telegram

    def _send(self, business_slug: str, channel: str, send: Callable[[Any, str], str | None]) -> str | None:
        client = self._clients.get(channel)
        if client is None:
            raise ChannelError("Este canal todavía no permite responder desde el panel.")
        secrets = self._channels.channel_secrets(business_slug, channel)
        if secrets is None:
            raise ChannelError(NOT_CONNECTED[channel])
        try:
            return send(client(secrets.server_url), secrets.instance_token)
        except ChannelError as error:
            if error.gone and channel == TELEGRAM:
                self._channels.set_channel_status(business_slug, TELEGRAM, "disconnected")
            raise

    def send_text(self, business_slug: str, channel: str, contact_ref: str, text: str) -> str | None:
        return self._send(business_slug, channel, lambda client, token: client.send_text(token, contact_ref, text))

    def send_media(self, business_slug: str, channel: str, contact_ref: str, kind: str, media: MediaFile, caption: str) -> str | None:
        return self._send(business_slug, channel, lambda client, token: client.send_media(token, contact_ref, kind, media, caption))
