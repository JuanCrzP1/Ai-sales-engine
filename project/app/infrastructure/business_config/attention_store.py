"""La atención humana de cada negocio en la base (migración 0011).

- `business_attention_settings`: sus ajustes (sin fila, los de por defecto).
- `business_members.email`: el correo de cada dueño, tomado de su sesión.
- `notifications` y `notification_deliveries`: lo que hace falta para avisar al equipo y que cada aviso salga una sola vez por canal.

Cada operación recibe el negocio y solo alcanza sus filas.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import insert, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from app.domain.business_config.attention import AttentionSettings, hours_from, hours_payload, with_updated_at
from app.domain.business_config.errors import ConversationNotFoundError
from app.infrastructure.business_config.tables import (
    business_attention_settings,
    business_members,
    conversations,
    notification_deliveries,
    notifications,
    tenants,
)
from app.infrastructure.business_config.tenancy import tenant_of


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class AlertDetails:
    """Lo que dice un aviso para el equipo, con su negocio y su chat."""

    notification_id: str
    business_slug: str
    business_name: str
    kind: str
    title: str
    body: str | None
    conversation_id: str | None
    channel: str | None
    created_at: datetime


class AttentionStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # ------------------------------------------------------------------ ajustes

    def attention_settings(self, tenant_slug: str) -> AttentionSettings:
        with self._engine.connect() as conn:
            tenant = tenant_of(conn, tenant_slug)
            row = conn.execute(select(business_attention_settings).where(business_attention_settings.c.tenant_id == tenant.id)).first()
        if row is None:
            return AttentionSettings()
        return AttentionSettings(
            hours_mode=row.hours_mode,
            team_hours=hours_from(row.team_hours),
            timezone=row.timezone,
            reply_minutes=int(row.reply_minutes),
            resume_after_minutes=int(row.resume_after_minutes) if row.resume_after_minutes is not None else None,
            email_enabled=bool(row.email_enabled),
            email_to=row.email_to,
            updated_at=_utc(row.updated_at),
        )

    def save_attention_settings(self, tenant_slug: str, settings: AttentionSettings) -> AttentionSettings:
        now = _now()
        values: dict[str, Any] = {
            "hours_mode": settings.hours_mode,
            "team_hours": hours_payload(settings.team_hours),
            "timezone": settings.timezone,
            "reply_minutes": settings.reply_minutes,
            "resume_after_minutes": settings.resume_after_minutes,
            "email_enabled": settings.email_enabled,
            "email_to": settings.email_to,
            "updated_at": now,
        }
        for attempt in range(2):
            try:
                with self._engine.begin() as conn:
                    tenant = tenant_of(conn, tenant_slug)
                    key = business_attention_settings.c.tenant_id == tenant.id
                    if conn.execute(select(business_attention_settings.c.tenant_id).where(key)).first() is None:
                        conn.execute(insert(business_attention_settings).values(tenant_id=tenant.id, **values))
                    else:
                        conn.execute(update(business_attention_settings).where(key).values(**values))
                return with_updated_at(settings, now)
            except IntegrityError:
                # Dos guardados a la vez del primer ajuste: el segundo encuentra la fila y la actualiza.
                if attempt:
                    raise
        raise AssertionError("inalcanzable")

    # ------------------------------------------------------------------ el equipo

    def owner_emails(self, tenant_slug: str) -> list[str]:
        """Los correos de las cuentas dueñas del negocio que se conocen (se guardan al usar el panel)."""
        query = (
            select(business_members.c.email)
            .join(tenants, tenants.c.id == business_members.c.tenant_id)
            .where(tenants.c.slug == tenant_slug, business_members.c.email.is_not(None))
            .order_by(business_members.c.created_at)
        )
        with self._engine.connect() as conn:
            return [row.email for row in conn.execute(query) if str(row.email or "").strip()]

    def member_ids(self, tenant_slug: str) -> list[str]:
        query = select(business_members.c.user_id).join(tenants, tenants.c.id == business_members.c.tenant_id).where(tenants.c.slug == tenant_slug)
        with self._engine.connect() as conn:
            return [row.user_id for row in conn.execute(query)]

    def remember_email(self, user_id: str, email: str) -> None:
        """Anota el correo de la cuenta en los negocios de esa persona, solo si cambió (una escritura por cambio, no por visita)."""
        email = str(email or "").strip()
        if not email:
            return
        with self._engine.begin() as conn:
            conn.execute(
                update(business_members)
                .where(business_members.c.user_id == user_id, (business_members.c.email.is_(None)) | (business_members.c.email != email))
                .values(email=email)
            )

    # ------------------------------------------------------------------ avisos

    def alert(self, notification_id: str) -> AlertDetails:
        try:
            key = uuid.UUID(str(notification_id))
        except ValueError as exc:
            raise ConversationNotFoundError("aviso no válido") from exc
        query = (
            select(
                notifications.c.id, tenants.c.slug, tenants.c.name, notifications.c.kind, notifications.c.title, notifications.c.body,
                notifications.c.conversation_id, conversations.c.channel, notifications.c.created_at,
            )
            .select_from(
                notifications.join(tenants, tenants.c.id == notifications.c.tenant_id).outerjoin(
                    conversations, conversations.c.id == notifications.c.conversation_id
                )
            )
            .where(notifications.c.id == key)
        )
        with self._engine.connect() as conn:
            row = conn.execute(query).first()
        if row is None:
            raise ConversationNotFoundError("el aviso no existe")
        return AlertDetails(
            notification_id=str(row.id), business_slug=row.slug, business_name=row.name, kind=row.kind, title=row.title, body=row.body,
            conversation_id=str(row.conversation_id) if row.conversation_id else None, channel=row.channel, created_at=_utc(row.created_at),
        )

    def claim_delivery(self, notification_id: str, channel: str) -> bool:
        """Reserva el envío de un aviso por un canal. Solo el primero que lo intenta lo envía: los demás reciben False."""
        now = _now()
        try:
            with self._engine.begin() as conn:
                conn.execute(
                    insert(notification_deliveries).values(
                        notification_id=uuid.UUID(str(notification_id)), channel=channel, status="sending", created_at=now, updated_at=now
                    )
                )
        except IntegrityError:
            return False
        return True

    def finish_delivery(self, notification_id: str, channel: str, status: str, detail: str | None = None) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                update(notification_deliveries)
                .where(notification_deliveries.c.notification_id == uuid.UUID(str(notification_id)), notification_deliveries.c.channel == channel)
                .values(status=status, detail=(detail or None) and str(detail)[:300], updated_at=_now())
            )

    def delivery(self, notification_id: str, channel: str) -> tuple[str, str | None] | None:
        """El estado del envío de un aviso por un canal y su detalle, o None si no se intentó."""
        with self._engine.connect() as conn:
            row = conn.execute(
                select(notification_deliveries.c.status, notification_deliveries.c.detail).where(
                    notification_deliveries.c.notification_id == uuid.UUID(str(notification_id)), notification_deliveries.c.channel == channel
                )
            ).first()
        return (row.status, row.detail) if row is not None else None
