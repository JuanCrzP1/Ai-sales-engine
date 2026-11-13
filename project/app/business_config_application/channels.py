"""Los canales de cada negocio: WhatsApp por código QR (conectar mostrando el QR, seguir la conexión y desconectar) y Telegram con el
bot del propio negocio (`TelegramChannelService`, al final).

El negocio no configura nada: toca «Conectar» y escanea. El servidor de uazapi y su token de administrador son de la plataforma
(`UazapiPlatform`). Al conectar, se crea la instancia del negocio (o se reutiliza la que ya tiene), se registra su webhook en el motor
(`webhook_base` + su identificador secreto) y se pide el QR. Desconectar borra la instancia del servidor, para no dejar instancias
olvidadas: volver a conectar crea otra.

Sin servidor de la plataforma o sin dirección pública del motor (los mensajes no llegarían), la conexión no está disponible.
"""
from __future__ import annotations

import logging
import secrets as random
from collections.abc import Callable
from dataclasses import dataclass

from app.business_config_application.ports import ChannelStorage, TelegramApi, TelegramStorage, WhatsAppProvider
from app.domain.business_config.channels import (
    BOT_IN_USE,
    TELEGRAM,
    BotInUseError,
    ChannelError,
    ChannelUnavailableError,
    ProviderStatus,
    TelegramConnection,
    UazapiPlatform,
    WhatsAppConnection,
    WhatsAppUnavailableError,
    bot_id_of,
    telegram_webhook_secret,
    validated_bot_token,
)
from app.domain.business_config.errors import FieldIssue, InvalidFieldsError

ProviderFactory = Callable[[str], WhatsAppProvider]
logger = logging.getLogger(__name__)

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


# ---------------------------------------------------------------------------------------------------------- Telegram

TELEGRAM_UNAVAILABLE = "Telegram todavía no está activo en esta plataforma. Intenta más tarde."
UNKNOWN_TOKEN = "Telegram no reconoce ese código. Cópialo completo desde @BotFather (si lo cambiaste, pídele el nuevo con /token)."
# Hay un bot guardado pero no recibe los mensajes aquí: Telegram rechazó su código o alguien lo conectó en otra plataforma.
NOT_RECEIVING = "Tu bot dejó de recibir los mensajes aquí. Toca «Volver a conectar» o pega el código nuevo de @BotFather."
ELSEWHERE = "Tu bot está enviando los mensajes a otra plataforma (quizá lo conectaste en otro sistema). Toca «Volver a conectar» para traerlos aquí."


@dataclass(frozen=True)
class TelegramView:
    """Lo que el panel muestra del bot: si se puede conectar, el bot guardado (o ninguno) y, si no recibe mensajes, por qué."""

    available: bool
    connection: TelegramConnection | None
    problem: str | None = None


class TelegramChannelService:
    """El bot de Telegram del negocio: el negocio lo crea con @BotFather y pega el código. Aquí se revisa con Telegram, se registra su
    webhook (con su firma secreta) y se guarda cifrado. Un bot nunca queda en dos negocios."""

    def __init__(self, storage: TelegramStorage, api: TelegramApi, *, webhook_base: str | None) -> None:
        self._storage = storage
        self._api = api
        self._webhook_base = (webhook_base or "").rstrip("/") or None

    @property
    def available(self) -> bool:
        return self._webhook_base is not None

    def get(self, tenant_slug: str, problem: str | None = None) -> TelegramView:
        connection = self._storage.telegram(tenant_slug)
        if problem is None and connection is not None and connection.status != "connected":
            problem = NOT_RECEIVING
        return TelegramView(self.available, connection, problem if connection is not None else None)

    def connect(self, tenant_slug: str, token: object) -> TelegramView:
        """Conecta el bot de ese código (o lo cambia por otro). Si el código no sirve, `InvalidFieldsError` en el campo `token`."""
        clean = validated_bot_token(token)
        try:
            return self._connect(tenant_slug, clean)
        except ChannelError as error:
            if error.gone:
                raise InvalidFieldsError(UNKNOWN_TOKEN, [FieldIssue("token", UNKNOWN_TOKEN)]) from None
            raise

    def reconnect(self, tenant_slug: str) -> TelegramView:
        """Vuelve a registrar el webhook del bot guardado (por ejemplo, si alguien lo conectó en otra plataforma)."""
        current = self._storage.channel_secrets(tenant_slug, TELEGRAM)
        if current is None:
            return self.get(tenant_slug)
        try:
            return self._connect(tenant_slug, current.instance_token)
        except ChannelError as error:
            if error.gone:
                self._storage.set_channel_status(tenant_slug, TELEGRAM, "disconnected")
            raise

    def _connect(self, tenant_slug: str, token: str) -> TelegramView:
        if self._webhook_base is None:
            raise ChannelUnavailableError(TELEGRAM_UNAVAILABLE)
        bot = self._api.get_me(token)
        owner = self._storage.channel_owner(TELEGRAM, bot.id)
        if owner is not None and owner != tenant_slug:
            # Antes de tocar su webhook: nunca se le quita el bot a otro negocio.
            raise BotInUseError(BOT_IN_USE)
        previous = self._storage.channel_secrets(tenant_slug, TELEGRAM)
        webhook_id = previous.webhook_id if previous else random.token_urlsafe(32)
        self._api.set_webhook(token, f"{self._webhook_base}/{webhook_id}", telegram_webhook_secret(token, webhook_id))
        try:
            self._storage.save_telegram(tenant_slug, token=token, bot=bot, webhook_id=webhook_id)
        except ChannelError:
            self._quietly_unhook(token)  # otro negocio lo conectó en el mismo instante: el bot no se queda apuntando aquí
            raise
        if previous is not None and bot_id_of(previous.instance_token) != bot.id:
            self._quietly_unhook(previous.instance_token)  # el bot anterior deja de enviar mensajes aquí
        logger.info("telegram_conectado", extra={"tenant": tenant_slug})
        return self.get(tenant_slug)

    def refresh(self, tenant_slug: str) -> TelegramView:
        """Pregunta a Telegram si el bot sigue recibiendo los mensajes aquí, y lo anota."""
        current = self._storage.channel_secrets(tenant_slug, TELEGRAM)
        if current is None or self._webhook_base is None:
            return self.get(tenant_slug)
        try:
            bot = self._api.get_me(current.instance_token)
            url = self._api.webhook_url(current.instance_token)
        except ChannelError as error:
            if not error.gone:
                raise
            self._storage.set_channel_status(tenant_slug, TELEGRAM, "disconnected")
            return self.get(tenant_slug, problem=NOT_RECEIVING)
        if url != f"{self._webhook_base}/{current.webhook_id}":
            self._storage.set_channel_status(tenant_slug, TELEGRAM, "disconnected")
            return self.get(tenant_slug, problem=ELSEWHERE)
        # Si el negocio le cambió el nombre o el usuario en @BotFather, se ve el nuevo.
        self._storage.save_telegram(tenant_slug, token=current.instance_token, bot=bot, webhook_id=current.webhook_id)
        return self.get(tenant_slug)

    def disconnect(self, tenant_slug: str) -> TelegramView:
        """El bot deja de enviar mensajes aquí y se borra su conexión. Los chats y su historial se quedan."""
        current = self._storage.channel_secrets(tenant_slug, TELEGRAM)
        if current is not None:
            self._quietly_unhook(current.instance_token)
            self._storage.delete_channel(tenant_slug, TELEGRAM)
            logger.info("telegram_desconectado", extra={"tenant": tenant_slug})
        return self.get(tenant_slug)

    def _quietly_unhook(self, token: str) -> None:
        """Quita el webhook del bot. Si Telegram no responde, no detiene nada: los avisos que lleguen después no encuentran negocio."""
        try:
            self._api.delete_webhook(token)
        except ChannelError as error:
            logger.warning("telegram_webhook_no_quitado", extra={"error": type(error).__name__})
