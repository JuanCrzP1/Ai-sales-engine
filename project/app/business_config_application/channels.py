"""WhatsApp por código QR de cada negocio: guardar su servidor y su token, pedir el QR, seguir la conexión y desconectar.

El negocio pega la dirección de su servidor de uazapi y un token. Si es el de una instancia, se usa tal cual; si es el de administrador
del servidor, se crea una instancia solo para este negocio. Al pedir el QR se registra solo el webhook del negocio en el motor
(`webhook_base` + su identificador secreto); sin dirección pública del motor, la conexión funciona pero los mensajes no llegan, y el
panel lo avisa.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.business_config_application.ports import ChannelStorage, WhatsAppProvider
from app.domain.business_config.channels import ChannelError, ProviderStatus, WhatsAppConnection, WhatsAppSecrets, normalize_server_url

ProviderFactory = Callable[[str], WhatsAppProvider]


@dataclass(frozen=True)
class WhatsAppView:
    """Lo que el panel muestra del canal: la conexión guardada (o ninguna) y si los mensajes pueden llegar al motor."""

    connection: WhatsAppConnection | None
    webhook_ready: bool
    qrcode: str | None = None
    paircode: str | None = None


class WhatsAppChannelService:
    def __init__(self, storage: ChannelStorage, providers: ProviderFactory, *, webhook_base: str | None = None) -> None:
        self._storage = storage
        self._providers = providers
        self._webhook_base = (webhook_base or "").rstrip("/") or None

    def _view(self, tenant_slug: str, status: ProviderStatus | None = None) -> WhatsAppView:
        return WhatsAppView(
            self._storage.whatsapp(tenant_slug), self._webhook_base is not None, status.qrcode if status else None, status.paircode if status else None
        )

    def _secrets(self, tenant_slug: str) -> WhatsAppSecrets:
        secrets = self._storage.whatsapp_secrets(tenant_slug)
        if secrets is None:
            raise ChannelError("Primero guarda la dirección de tu servidor y tu token.")
        return secrets

    def get(self, tenant_slug: str) -> WhatsAppView:
        return self._view(tenant_slug)

    def configure(self, tenant_slug: str, *, server_url: str, token: str) -> WhatsAppView:
        """Comprueba el token con el servidor y lo guarda cifrado. Un token de administrador crea la instancia del negocio."""
        server = normalize_server_url(server_url)
        token = str(token or "").strip()
        if not token:
            raise ChannelError("Pega el token de tu servidor de uazapi.", field="token")
        provider = self._providers(server)
        try:
            provider.status(token)
            instance_token, admin_token = token, None
        except ChannelError as instance_error:
            if instance_error.field != "token":
                raise
            # No es el token de una instancia: quizá es el de administrador del servidor.
            try:
                instance_token, admin_token = provider.create_instance(token, _instance_name(tenant_slug)), token
            except ChannelError:
                raise instance_error from None
        self._storage.save_whatsapp(tenant_slug, server_url=server, instance_token=instance_token, admin_token=admin_token)
        return self._view(tenant_slug)

    def connect(self, tenant_slug: str) -> WhatsAppView:
        """Pide el código QR y registra el webhook del negocio. Si el servidor borró la instancia, la vuelve a crear."""
        secrets = self._secrets(tenant_slug)
        provider = self._providers(secrets.server_url)
        token = secrets.instance_token
        try:
            status = provider.connect(token)
        except ChannelError as error:
            if error.field != "token" or not secrets.admin_token:
                raise
            token = provider.create_instance(secrets.admin_token, _instance_name(tenant_slug))
            self._storage.replace_instance_token(tenant_slug, token)
            status = provider.connect(token)
        if self._webhook_base:
            provider.set_webhook(token, f"{self._webhook_base}/{secrets.webhook_id}")
        self._storage.set_status(tenant_slug, status.status, phone=status.phone, profile_name=status.profile_name)
        return self._view(tenant_slug, status)

    def refresh(self, tenant_slug: str) -> WhatsAppView:
        """El estado actual en el servidor: mientras conecta, trae el QR vigente (cambia cada pocos segundos)."""
        secrets = self._secrets(tenant_slug)
        try:
            status = self._providers(secrets.server_url).status(secrets.instance_token)
        except ChannelError as error:
            if error.field != "token":
                raise
            # La instancia ya no existe en el servidor (los de prueba la borran a la hora): queda desconectada.
            status = ProviderStatus("disconnected")
        self._storage.set_status(tenant_slug, status.status, phone=status.phone, profile_name=status.profile_name)
        return self._view(tenant_slug, status)

    def disconnect(self, tenant_slug: str) -> WhatsAppView:
        secrets = self._secrets(tenant_slug)
        try:
            self._providers(secrets.server_url).disconnect(secrets.instance_token)
        except ChannelError:
            pass  # Si el servidor ya no la tiene, para el negocio igual queda desconectada.
        self._storage.set_status(tenant_slug, "disconnected")
        return self._view(tenant_slug)

    def remove(self, tenant_slug: str) -> None:
        """Desconecta (si puede) y borra la conexión con sus tokens."""
        if self._storage.whatsapp_secrets(tenant_slug) is not None:
            self.disconnect(tenant_slug)
        self._storage.delete_whatsapp(tenant_slug)


def _instance_name(tenant_slug: str) -> str:
    return f"ai-sales-{tenant_slug}"[:60]
