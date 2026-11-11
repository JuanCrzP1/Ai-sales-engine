"""Envía por el canal del cliente lo que el equipo responde desde el panel (implementa `OutboundMessenger`).

Por ahora, WhatsApp por código QR: usa la instancia del negocio (su token cifrado en `business_channels`) en el servidor de uazapi
de la plataforma. El cliente de uazapi lo pone la raíz de composición.
"""
from __future__ import annotations

from app.business_config_application.channels import ProviderFactory
from app.domain.business_config.channels import WHATSAPP, ChannelError
from app.infrastructure.business_config.channel_store import ChannelStore


class ChannelMessenger:
    def __init__(self, channels: ChannelStore, providers: ProviderFactory) -> None:
        self._channels = channels
        self._providers = providers

    def send_text(self, business_slug: str, channel: str, contact_ref: str, text: str) -> str | None:
        if channel != WHATSAPP:
            raise ChannelError("Este canal todavía no permite responder desde el panel.")
        secrets = self._channels.whatsapp_secrets(business_slug)
        if secrets is None:
            raise ChannelError("WhatsApp no está conectado en este negocio. Conéctalo en Canales para responder desde aquí.")
        return self._providers(secrets.server_url).send_text(secrets.instance_token, contact_ref, text)
