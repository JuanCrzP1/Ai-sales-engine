"""Canales de cada negocio en la base (`business_channels`): WhatsApp por código QR y Telegram, con sus tokens cifrados.

Los tokens se cifran con la misma clave Fernet que los datos de pago y la clave de IA, y solo se descifran para hablar con el canal
(uazapi o la API de Telegram). Cada operación recibe el negocio y solo alcanza su fila; el motor llega por el identificador secreto del
webhook. Un bot de Telegram nunca queda en dos negocios: lo garantiza un índice único (`business_channels_account_key`).
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from cryptography.fernet import InvalidToken
from sqlalchemy import delete, insert, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from app.domain.business_config.channels import (
    BOT_IN_USE,
    TELEGRAM,
    TELEGRAM_API,
    UAZAPI,
    WHATSAPP,
    BotInUseError,
    ChannelSecrets,
    ConnectionStatus,
    TelegramBot,
    TelegramConnection,
    WhatsAppConnection,
)
from app.domain.business_config.errors import SecretResolutionError
from app.infrastructure.business_config.payment_secret_store import check_secrets_key
from app.infrastructure.business_config.tables import business_channels, tenants
from app.infrastructure.business_config.tenancy import tenant_of



class ChannelStore:
    def __init__(self, engine: Engine, key: str | None = None) -> None:
        self._engine = engine
        self._key = key

    def _decrypt(self, ciphertext: str) -> str:
        try:
            return check_secrets_key(self._key).decrypt(ciphertext.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise SecretResolutionError("el token del canal no se puede descifrar con la clave de cifrado actual") from exc

    def _encrypt(self, value: str) -> str:
        return check_secrets_key(self._key).encrypt(value.encode("utf-8")).decode("ascii")

    def _row(self, tenant_slug: str, channel: str) -> Any:
        with self._engine.connect() as conn:
            tenant_id = tenant_of(conn, tenant_slug).id
            return conn.execute(
                select(business_channels).where(business_channels.c.tenant_id == tenant_id, business_channels.c.channel == channel)
            ).first()

    def _secrets(self, tenant_slug: str, row: Any) -> ChannelSecrets:
        return ChannelSecrets(tenant_slug, row.server_url, self._decrypt(row.token_ciphertext), row.webhook_id, row.channel)

    # ------------------------------------------------------------------ panel

    def whatsapp(self, tenant_slug: str) -> WhatsAppConnection | None:
        row = self._row(tenant_slug, WHATSAPP)
        if row is None:
            return None
        return WhatsAppConnection(status=row.status, phone=row.phone, profile_name=row.profile_name)

    def telegram(self, tenant_slug: str) -> TelegramConnection | None:
        row = self._row(tenant_slug, TELEGRAM)
        if row is None:
            return None
        return TelegramConnection(status=row.status, bot_username=row.account_username, bot_name=row.profile_name)

    def channel_secrets(self, tenant_slug: str, channel: str) -> ChannelSecrets | None:
        """Lo necesario para hablar con ese canal del negocio, o None si no lo tiene."""
        row = self._row(tenant_slug, channel)
        return None if row is None else self._secrets(tenant_slug, row)

    def whatsapp_secrets(self, tenant_slug: str) -> ChannelSecrets | None:
        return self.channel_secrets(tenant_slug, WHATSAPP)

    def save_whatsapp(self, tenant_slug: str, *, server_url: str, instance_token: str) -> None:
        """Guarda (o reemplaza) la instancia del negocio, desconectada. Conserva el identificador del webhook si ya tenía uno."""
        self._save(tenant_slug, WHATSAPP, {
            "provider": UAZAPI,
            "server_url": server_url,
            "token_ciphertext": self._encrypt(instance_token),
            "status": "disconnected",
            "phone": None,
            "profile_name": None,
        })

    def save_telegram(self, tenant_slug: str, *, token: str, bot: TelegramBot, webhook_id: str) -> None:
        """Guarda (o reemplaza) el bot del negocio, ya conectado: su webhook quedó registrado en Telegram con `webhook_id` (el que ya
        tenía el negocio, si tenía). Si el bot ya está en otro negocio, `BotInUseError`."""
        try:
            self._save(tenant_slug, TELEGRAM, {
                "provider": TELEGRAM,
                "server_url": TELEGRAM_API,
                "token_ciphertext": self._encrypt(token),
                "status": "connected",
                "phone": None,
                "profile_name": bot.name,
                "account_id": bot.id,
                "account_username": bot.username,
            }, webhook_id=webhook_id)
        except IntegrityError as exc:
            raise BotInUseError(BOT_IN_USE) from exc

    def channel_owner(self, channel: str, account_id: str) -> str | None:
        """El negocio que tiene conectada esa cuenta del canal (en Telegram, el bot), o None."""
        with self._engine.connect() as conn:
            row = conn.execute(
                select(tenants.c.slug)
                .join(business_channels, business_channels.c.tenant_id == tenants.c.id)
                .where(business_channels.c.channel == channel, business_channels.c.account_id == account_id)
            ).first()
        return row.slug if row else None

    def _save(self, tenant_slug: str, channel: str, values: dict[str, Any], *, webhook_id: str | None = None) -> None:
        values = {**values, "updated_at": datetime.now(timezone.utc)}
        with self._engine.begin() as conn:
            tenant_id = tenant_of(conn, tenant_slug).id
            key = (business_channels.c.tenant_id == tenant_id) & (business_channels.c.channel == channel)
            if conn.execute(select(business_channels.c.webhook_id).where(key)).first() is None:
                new_id = webhook_id or secrets.token_urlsafe(32)
                conn.execute(insert(business_channels).values(tenant_id=tenant_id, channel=channel, webhook_id=new_id, **values))
            else:
                conn.execute(update(business_channels).where(key).values(**values))

    def set_status(self, tenant_slug: str, status: ConnectionStatus, *, phone: str | None = None, profile_name: str | None = None) -> None:
        """El estado de WhatsApp: el número y el nombre solo se guardan mientras está conectado."""
        self._update(tenant_slug, WHATSAPP, status=status, phone=phone if status == "connected" else None, profile_name=profile_name if status == "connected" else None)

    def set_channel_status(self, tenant_slug: str, channel: str, status: ConnectionStatus) -> None:
        """Solo el estado (en Telegram, el bot sigue guardado: «desconectado» quiere decir que Telegram rechazó el código)."""
        self._update(tenant_slug, channel, status=status)

    def _update(self, tenant_slug: str, channel: str, **values: Any) -> None:
        with self._engine.begin() as conn:
            tenant_id = tenant_of(conn, tenant_slug).id
            conn.execute(
                update(business_channels)
                .where(business_channels.c.tenant_id == tenant_id, business_channels.c.channel == channel)
                .values(updated_at=datetime.now(timezone.utc), **values)
            )

    def delete_channel(self, tenant_slug: str, channel: str) -> None:
        with self._engine.begin() as conn:
            tenant_id = tenant_of(conn, tenant_slug).id
            conn.execute(delete(business_channels).where(business_channels.c.tenant_id == tenant_id, business_channels.c.channel == channel))

    def delete_whatsapp(self, tenant_slug: str) -> None:
        self.delete_channel(tenant_slug, WHATSAPP)

    # ------------------------------------------------------------------ motor

    def secrets_for_webhook(self, webhook_id: str, channel: str = WHATSAPP) -> ChannelSecrets | None:
        """La conexión de ese canal con ese identificador secreto de webhook, o None si no existe."""
        with self._engine.connect() as conn:
            row = conn.execute(
                select(business_channels, tenants.c.slug)
                .join(tenants, tenants.c.id == business_channels.c.tenant_id)
                .where(business_channels.c.webhook_id == webhook_id, business_channels.c.channel == channel)
            ).first()
        return None if row is None else self._secrets(row.slug, row)
