"""Canales de cada negocio en la base (`business_channels`): WhatsApp por código QR, con sus tokens cifrados.

Los tokens se cifran con la misma clave Fernet que los datos de pago y la clave de IA, y solo se descifran para hablar con el servidor
de uazapi. Cada operación recibe el negocio y solo alcanza su fila; el motor llega por el identificador secreto del webhook.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from cryptography.fernet import InvalidToken
from sqlalchemy import delete, insert, select, update
from sqlalchemy.engine import Engine

from app.domain.business_config.channels import UAZAPI, WHATSAPP, ConnectionStatus, WhatsAppConnection, WhatsAppSecrets, token_hint
from app.domain.business_config.errors import SecretResolutionError
from app.infrastructure.business_config.payment_secret_store import check_secrets_key
from app.infrastructure.business_config.tables import business_channels, tenants
from app.infrastructure.business_config.tenancy import tenant_of


class ChannelStore:
    def __init__(self, engine: Engine, key: str | None = None) -> None:
        self._engine = engine
        self._key = key

    def _decrypt(self, ciphertext: str | None) -> str | None:
        if ciphertext is None:
            return None
        try:
            return check_secrets_key(self._key).decrypt(ciphertext.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise SecretResolutionError("el token del canal no se puede descifrar con la clave de cifrado actual") from exc

    def _encrypt(self, value: str) -> str:
        return check_secrets_key(self._key).encrypt(value.encode("utf-8")).decode("ascii")

    def _row(self, tenant_slug: str) -> Any:
        with self._engine.connect() as conn:
            tenant_id = tenant_of(conn, tenant_slug).id
            return conn.execute(
                select(business_channels).where(business_channels.c.tenant_id == tenant_id, business_channels.c.channel == WHATSAPP)
            ).first()

    # ------------------------------------------------------------------ panel

    def whatsapp(self, tenant_slug: str) -> WhatsAppConnection | None:
        row = self._row(tenant_slug)
        if row is None:
            return None
        return WhatsAppConnection(
            provider=row.provider, server_url=row.server_url, status=row.status, token_hint=row.token_hint,
            has_admin_token=row.admin_token_ciphertext is not None, phone=row.phone, profile_name=row.profile_name,
        )

    def whatsapp_secrets(self, tenant_slug: str) -> WhatsAppSecrets | None:
        row = self._row(tenant_slug)
        if row is None:
            return None
        return WhatsAppSecrets(tenant_slug, row.server_url, self._decrypt(row.token_ciphertext) or "", self._decrypt(row.admin_token_ciphertext), row.webhook_id)

    def save_whatsapp(self, tenant_slug: str, *, server_url: str, instance_token: str, admin_token: str | None) -> None:
        """Guarda (o reemplaza) la conexión del negocio, desconectada. Conserva el identificador del webhook si ya tenía uno."""
        values: dict[str, Any] = {
            "provider": UAZAPI,
            "server_url": server_url,
            "token_ciphertext": self._encrypt(instance_token),
            "admin_token_ciphertext": self._encrypt(admin_token) if admin_token else None,
            "token_hint": token_hint(instance_token),
            "status": "disconnected",
            "phone": None,
            "profile_name": None,
            "updated_at": datetime.now(timezone.utc),
        }
        with self._engine.begin() as conn:
            tenant_id = tenant_of(conn, tenant_slug).id
            key = (business_channels.c.tenant_id == tenant_id) & (business_channels.c.channel == WHATSAPP)
            if conn.execute(select(business_channels.c.webhook_id).where(key)).first() is None:
                conn.execute(insert(business_channels).values(tenant_id=tenant_id, channel=WHATSAPP, webhook_id=secrets.token_urlsafe(32), **values))
            else:
                conn.execute(update(business_channels).where(key).values(**values))

    def replace_instance_token(self, tenant_slug: str, instance_token: str) -> None:
        """La instancia se volvió a crear (el servidor la había borrado): guarda su token nuevo."""
        self._update(tenant_slug, token_ciphertext=self._encrypt(instance_token), token_hint=token_hint(instance_token))

    def set_status(self, tenant_slug: str, status: ConnectionStatus, *, phone: str | None = None, profile_name: str | None = None) -> None:
        self._update(tenant_slug, status=status, phone=phone if status == "connected" else None, profile_name=profile_name if status == "connected" else None)

    def _update(self, tenant_slug: str, **values: Any) -> None:
        with self._engine.begin() as conn:
            tenant_id = tenant_of(conn, tenant_slug).id
            conn.execute(
                update(business_channels)
                .where(business_channels.c.tenant_id == tenant_id, business_channels.c.channel == WHATSAPP)
                .values(updated_at=datetime.now(timezone.utc), **values)
            )

    def delete_whatsapp(self, tenant_slug: str) -> None:
        with self._engine.begin() as conn:
            tenant_id = tenant_of(conn, tenant_slug).id
            conn.execute(delete(business_channels).where(business_channels.c.tenant_id == tenant_id, business_channels.c.channel == WHATSAPP))

    # ------------------------------------------------------------------ motor

    def secrets_for_webhook(self, webhook_id: str) -> WhatsAppSecrets | None:
        """La conexión del webhook con ese identificador secreto, o None si no existe."""
        with self._engine.connect() as conn:
            row = conn.execute(
                select(business_channels, tenants.c.slug)
                .join(tenants, tenants.c.id == business_channels.c.tenant_id)
                .where(business_channels.c.webhook_id == webhook_id, business_channels.c.channel == WHATSAPP)
            ).first()
        if row is None:
            return None
        return WhatsAppSecrets(row.slug, row.server_url, self._decrypt(row.token_ciphertext) or "", self._decrypt(row.admin_token_ciphertext), row.webhook_id)
