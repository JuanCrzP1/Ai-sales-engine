"""Las respuestas rápidas de cada negocio en la base (migración 0015, tabla `quick_replies`).

Cada operación recibe el negocio y solo alcanza sus filas: una respuesta de otro negocio responde igual que una que no existe.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.engine import Engine, Row
from sqlalchemy.exc import IntegrityError

from app.domain.business_config.errors import FieldIssue, InvalidFieldsError, QuickReplyNotFoundError
from app.domain.business_config.quick_replies import MAX_QUICK_REPLIES, QuickReply, QuickReplyDraft
from app.infrastructure.business_config.tables import quick_replies
from app.infrastructure.business_config.tenancy import tenant_of

_TAKEN = "Ya tienes una respuesta rápida con ese atajo. Usa otro."


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _key(reply_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(reply_id))
    except ValueError as exc:
        raise QuickReplyNotFoundError("respuesta rápida no válida") from exc


def _reply(row: Row) -> QuickReply:
    pieces = tuple(str(piece) for piece in (row.pieces or []) if isinstance(piece, str))
    return QuickReply(
        id=str(row.id), shortcut=row.shortcut, category=row.category, pieces=pieces, use_count=int(row.use_count or 0),
        last_used_at=_utc(row.last_used_at), created_at=_utc(row.created_at), updated_at=_utc(row.updated_at),
    )


class QuickReplyStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list(self, tenant_slug: str) -> list[QuickReply]:
        """Todas las del negocio: las más usadas primero y, entre iguales, por atajo."""
        with self._engine.connect() as conn:
            tenant = tenant_of(conn, tenant_slug)
            rows = conn.execute(
                select(quick_replies)
                .where(quick_replies.c.tenant_id == tenant.id)
                .order_by(quick_replies.c.use_count.desc(), quick_replies.c.shortcut)
            ).all()
        return [_reply(row) for row in rows]

    def create(self, tenant_slug: str, draft: QuickReplyDraft, *, created_by: str | None) -> QuickReply:
        now = _now()
        try:
            with self._engine.begin() as conn:
                tenant = tenant_of(conn, tenant_slug)
                count = conn.execute(select(func.count()).select_from(quick_replies).where(quick_replies.c.tenant_id == tenant.id)).scalar_one()
                if count >= MAX_QUICK_REPLIES:
                    full = f"Llegaste al máximo de {MAX_QUICK_REPLIES} respuestas rápidas. Borra las que ya no uses."
                    raise InvalidFieldsError(full, [FieldIssue("quick_replies", full)])
                reply_id = uuid.uuid4()
                conn.execute(
                    insert(quick_replies).values(
                        id=reply_id, tenant_id=tenant.id, shortcut=draft.shortcut, category=draft.category, pieces=list(draft.pieces),
                        use_count=0, created_by=created_by, created_at=now, updated_at=now,
                    )
                )
                row = conn.execute(select(quick_replies).where(quick_replies.c.id == reply_id)).one()
        except IntegrityError:
            raise InvalidFieldsError(_TAKEN, [FieldIssue("shortcut", _TAKEN)]) from None
        return _reply(row)

    def update(self, tenant_slug: str, reply_id: str, draft: QuickReplyDraft) -> QuickReply:
        key = _key(reply_id)
        try:
            with self._engine.begin() as conn:
                tenant = tenant_of(conn, tenant_slug)
                mine = (quick_replies.c.id == key) & (quick_replies.c.tenant_id == tenant.id)
                result = conn.execute(
                    update(quick_replies).where(mine).values(
                        shortcut=draft.shortcut, category=draft.category, pieces=list(draft.pieces), updated_at=_now()
                    )
                )
                if result.rowcount == 0:
                    raise QuickReplyNotFoundError("la respuesta rápida no existe")
                row = conn.execute(select(quick_replies).where(mine)).one()
        except IntegrityError:
            raise InvalidFieldsError(_TAKEN, [FieldIssue("shortcut", _TAKEN)]) from None
        return _reply(row)

    def delete(self, tenant_slug: str, reply_id: str) -> None:
        key = _key(reply_id)
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            result = conn.execute(delete(quick_replies).where(quick_replies.c.id == key, quick_replies.c.tenant_id == tenant.id))
        if result.rowcount == 0:
            raise QuickReplyNotFoundError("la respuesta rápida no existe")

    def mark_used(self, tenant_slug: str, reply_id: str) -> QuickReply:
        """Suma un uso (en la base, sin leer antes: dos usos a la vez cuentan los dos)."""
        key = _key(reply_id)
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            mine = (quick_replies.c.id == key) & (quick_replies.c.tenant_id == tenant.id)
            result = conn.execute(update(quick_replies).where(mine).values(use_count=quick_replies.c.use_count + 1, last_used_at=_now()))
            if result.rowcount == 0:
                raise QuickReplyNotFoundError("la respuesta rápida no existe")
            row = conn.execute(select(quick_replies).where(mine)).one()
        return _reply(row)
