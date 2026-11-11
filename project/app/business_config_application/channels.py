"""WhatsApp por código QR de cada negocio: conectar (mostrar el QR), seguir la conexión y desconectar.

El negocio no configura nada: toca «Conectar» y escanea. El servidor de uazapi y su token de administrador son de la plataforma
(`UazapiPlatform`). Al conectar, se crea la instancia del negocio (o se reutiliza la que ya tiene), se registra su webhook en el motor
(`webhook_base` + su identificador secreto) y se pide el QR. Desconectar borra la instancia del servidor, para no dejar instancias
olvidadas: volver a conectar crea otra.

Sin servidor de la plataforma o sin dirección pública del motor (los mensajes no llegarían), la conexión no está disponible.
"""
from __future__ import annotations

import secrets as random
from collections.abc import Callable
from dataclasses import dataclass

from app.business_config_application.ports import ChannelStorage, WhatsAppProvider
from app.domain.business_config.channels import (
    ChannelError,
    ProviderStatus,
    UazapiPlatform,
    WhatsAppConnection,
    WhatsAppUnavailableError,
)

ProviderFactory = Callable[[str], WhatsAppProvider]

UNAVAILABLE = "La conexión de WhatsApp por código QR todavía no está activa. Intenta más tarde."


@dataclass(frozen=True)
class WhatsAppView:
    """Lo que el panel muestra del canal: si se puede conectar, la conexión guardada (o ninguna) y, mientras conecta, el QR."""

    available: bool
    connection: WhatsAppConnection | None
    qrcode: str | None = None
    paircode: str | None = None


class WhatsAppChannelService:
    def __init__(
        self, storage: ChannelStorage, providers: ProviderFactory, *, platform: UazapiPlatform | None, webhook_base: str | None
    ) -> None:
        self._storage = storage
        self._providers = providers
        self._platform = platform
        self._webhook_base = (webhook_base or "").rstrip("/") or None

    @property
    def available(self) -> bool:
        return self._platform is not None and self._webhook_base is not None

    def _view(self, tenant_slug: str, status: ProviderStatus | None = None) -> WhatsAppView:
        return WhatsAppView(
            self.available, self._storage.whatsapp(tenant_slug), status.qrcode if status else None, status.paircode if status else None
        )

    def get(self, tenant_slug: str) -> WhatsAppView:
        return self._view(tenant_slug)

    def connect(self, tenant_slug: str) -> WhatsAppView:
        """Muestra el QR: reutiliza la instancia del negocio o crea una (si no tenía, o si el servidor la borró), y registra su webhook."""
        if self._platform is None or self._webhook_base is None:
            raise WhatsAppUnavailableError(UNAVAILABLE)
        platform = self._platform
        provider = self._providers(platform.server_url)
        current = self._storage.whatsapp_secrets(tenant_slug)
        token = current.instance_token if current and current.server_url == platform.server_url else None
        if token is not None:
            try:
                self._register_webhook(provider, tenant_slug, token)
                return self._connected(tenant_slug, provider.connect(token))
            except ChannelError as error:
                if not error.gone:
                    raise
                # El servidor ya no tiene la instancia (los de prueba la borran a la hora): se crea otra.
        token = provider.create_instance(platform.admin_token, _instance_name(tenant_slug))
        self._storage.save_whatsapp(tenant_slug, server_url=platform.server_url, instance_token=token)
        self._register_webhook(provider, tenant_slug, token)
        return self._connected(tenant_slug, provider.connect(token))

    def new_code(self, tenant_slug: str) -> WhatsAppView:
        """Un código QR nuevo: el servidor repite el mismo mientras la conexión sigue en curso, así que la reinicia."""
        current = self._storage.whatsapp_secrets(tenant_slug)
        if current is not None:
            try:
                self._providers(current.server_url).disconnect(current.instance_token)
            except ChannelError as error:
                if not error.gone:
                    raise
        return self.connect(tenant_slug)

    def refresh(self, tenant_slug: str) -> WhatsAppView:
        """El estado actual en el servidor: mientras conecta, trae el QR vigente (cambia cada pocos segundos)."""
        current = self._storage.whatsapp_secrets(tenant_slug)
        if current is None:
            return self._view(tenant_slug)
        try:
            status = self._providers(current.server_url).status(current.instance_token)
        except ChannelError as error:
            if not error.gone:
                raise
            status = ProviderStatus("disconnected")
        self._storage.set_status(tenant_slug, status.status, phone=status.phone, profile_name=status.profile_name)
        return self._view(tenant_slug, status)

    def disconnect(self, tenant_slug: str) -> WhatsAppView:
        """Cierra la sesión de WhatsApp y borra la instancia del servidor y la conexión guardada."""
        current = self._storage.whatsapp_secrets(tenant_slug)
        if current is not None:
            self._providers(current.server_url).delete_instance(current.instance_token)
            self._storage.delete_whatsapp(tenant_slug)
        return self._view(tenant_slug)

    def _register_webhook(self, provider: WhatsAppProvider, tenant_slug: str, token: str) -> None:
        current = self._storage.whatsapp_secrets(tenant_slug)
        if current is not None and self._webhook_base is not None:
            provider.set_webhook(token, f"{self._webhook_base}/{current.webhook_id}")

    def _connected(self, tenant_slug: str, status: ProviderStatus) -> WhatsAppView:
        self._storage.set_status(tenant_slug, status.status, phone=status.phone, profile_name=status.profile_name)
        return self._view(tenant_slug, status)


def _instance_name(tenant_slug: str) -> str:
    """Un nombre único por instancia: el negocio y un sufijo al azar (el servidor puede guardar instancias viejas con el mismo nombre)."""
    return f"ventas-{tenant_slug[:40]}-{random.token_hex(3)}"
