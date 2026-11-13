"""Envía por el canal del cliente lo que el equipo responde desde el panel (implementa `OutboundMessenger`).

Por ahora, WhatsApp por código QR: usa la instancia del negocio (su token cifrado en `business_channels`) en el servidor de uazapi
de la plataforma. El cliente de uazapi lo pone la raíz de composición.
"""
from __future__ import annotations

from app.business_config_application.channels import ProviderFactory
from app.domain.business_config.channels import WHATSAPP, ChannelError
from app.domain.business_config.conversations import MediaFile
from app.infrastructure.business_config.channel_store import ChannelStore


class ChannelMessenger:
    def __init__(self, channels: ChannelStore, providers: ProviderFactory) -> None:
        self._channels = channels
        self._providers = providers

    def _whatsapp(self, business_slug: str, channel: str):
        if channel != WHATSAPP:
            raise ChannelError("Este canal todavía no permite responder desde el panel.")
        secrets = self._channels.whatsapp_secrets(business_slug)
        if secrets is None:
            raise ChannelError("WhatsApp no está conectado en este negocio. Conéctalo en Canales para responder desde aquí.")
        return self._providers(secrets.server_url), secrets.instance_token

    def send_text(self, business_slug: str, channel: str, contact_ref: str, text: str) -> str | None:
        provider, token = self._whatsapp(business_slug, channel)
        return provider.send_text(token, contact_ref, text)

    def send_media(self, business_slug: str, channel: str, contact_ref: str, kind: str, media: MediaFile, caption: str) -> str | None:
        provider, token = self._whatsapp(business_slug, channel)
        return provider.send_media(token, contact_ref, kind, media, caption)
