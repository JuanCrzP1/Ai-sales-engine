"""Los avisos de cada negocio en `notifications`, con lo leído por cada persona en `notification_reads` (implementa
`NotificationStorage`)."""
from __future__ import annotations

from collections.abc import Collection
from datetime import datetime, timezone

from sqlalchemy import and_, func, insert, select
from sqlalchemy.engine import Engine

from app.domain.business_config.conversations import Notification
from app.infrastructure.business_config.tables import notification_reads, notifications, tenants


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class NotificationStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def _mine(self, tenant_slugs: Collection[str]):
        return tenants.c.slug.in_(list(tenant_slugs))

    def recent(self, tenant_slugs: Collection[str], user_id: str, *, limit: int) -> tuple[list[Notification], int]:
        """Los más recientes primero, con lo que esta persona ya leyó, y cuántos le faltan por leer."""
        read = and_(notification_reads.c.notification_id == notifications.c.id, notification_reads.c.user_id == user_id)
        base = notifications.join(tenants, tenants.c.id == notifications.c.tenant_id).outerjoin(notification_reads, read)
        query = (
            select(
                notifications.c.id, tenants.c.slug, tenants.c.name, notifications.c.conversation_id, notifications.c.kind,
                notifications.c.title, notifications.c.body, notifications.c.body_is_note, notifications.c.created_at,
                notification_reads.c.read_at,
            )
            .select_from(base)
            .where(self._mine(tenant_slugs))
            .order_by(notifications.c.created_at.desc())
            .limit(limit)
        )
        unread = select(func.count()).select_from(base).where(self._mine(tenant_slugs), notification_reads.c.read_at.is_(None))
        with self._engine.connect() as conn:
            rows = conn.execute(query).all()
            pending = conn.execute(unread).scalar_one()
        items = [
            Notification(
                id=str(row.id), business_slug=row.slug, business_name=row.name,
                conversation_id=str(row.conversation_id) if row.conversation_id else None, kind=row.kind, title=row.title,
                body=row.body, body_is_note=bool(row.body_is_note), created_at=_utc(row.created_at), read=row.read_at is not None,
            )
            for row in rows
        ]
        return items, pending

    def mark_read(self, tenant_slugs: Collection[str], user_id: str, ids: Collection[str] | None = None) -> int:
        """Marca como leídos, para esta persona, los avisos indicados de sus negocios (o todos). Devuelve cuántos marcó."""
        read = and_(notification_reads.c.notification_id == notifications.c.id, notification_reads.c.user_id == user_id)
        query = (
            select(notifications.c.id)
            .select_from(notifications.join(tenants, tenants.c.id == notifications.c.tenant_id).outerjoin(notification_reads, read))
            .where(self._mine(tenant_slugs), notification_reads.c.read_at.is_(None))
        )
        now = datetime.now(timezone.utc)
        with self._engine.begin() as conn:
            pending = [row.id for row in conn.execute(query)]
            if ids is not None:
                wanted = {str(value) for value in ids}
                pending = [value for value in pending if str(value) in wanted]
            if pending:
                conn.execute(insert(notification_reads), [{"notification_id": value, "user_id": user_id, "read_at": now} for value in pending])
        return len(pending)
