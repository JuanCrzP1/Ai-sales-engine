"""Los recordatorios del equipo en la base: listarlos, crearlos, marcarlos hechos y borrarlos.

`CommerceStore` lo expone (`reminders`, `create_reminder`, `set_reminder_done`, `delete_reminder`); aquí están sus consultas, y
también las que usan la ficha (`reminders_of_customer`) y el tablero (`next_reminders`). Solo alcanzan los clientes de canales
reales del negocio que reciben. `alert_due_reminders` crea el aviso de los que ya llegaron a su hora.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.engine import Connection, Engine

from app.domain.business_config.errors import ConversationNotFoundError
from app.domain.business_config.reminders import (
    ALERT_KIND,
    ALERT_TOO_LATE,
    FOR_ME,
    MAX_ALERTS_PER_RUN,
    MAX_LISTED_DONE,
    MAX_LISTED_OPEN,
    MAX_OPEN_PER_CUSTOMER,
    NewReminder,
    NextReminder,
    Reminder,
    ReminderError,
    alert_text,
)
from app.infrastructure.business_config.tables import business_members, conversations, customer_reminders, notifications
from app.infrastructure.business_config.tenancy import tenant_of

TEST_CHANNEL = "prueba"


class ReminderNotFoundError(ConversationNotFoundError):
    """El recordatorio no existe o es de otro negocio (la API responde como con un cliente que no existe)."""


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _key(value: str, error: type[Exception], what: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except ValueError as exc:
        raise error(f"{what} no existe") from exc


def _members(conn: Connection, tenant_id: Any) -> dict[str, str]:
    """El equipo del negocio: su `user_id` y cómo se llama (su correo)."""
    rows = conn.execute(select(business_members.c.user_id, business_members.c.email).where(business_members.c.tenant_id == tenant_id))
    return {row.user_id: row.email or "Alguien del equipo" for row in rows}


def _query():
    return select(customer_reminders, conversations.c.contact_name, conversations.c.contact_ref).join(
        conversations, conversations.c.id == customer_reminders.c.conversation_id
    )


def _reminder(row: Any, members: dict[str, str]) -> Reminder:
    return Reminder(
        id=str(row.id), conversation_id=str(row.conversation_id), customer_name=row.contact_name, customer_contact=row.contact_ref,
        title=row.title, due_at=_utc(row.due_at), assignee_id=row.assignee_id if row.assignee_id in members else None,
        assignee_label=members.get(row.assignee_id), created_by=row.created_by, created_at=_utc(row.created_at),
        done_at=_utc(row.done_at), done_by=row.done_by,
    )


def _real(tenant_id: Any) -> list[Any]:
    return [customer_reminders.c.tenant_id == tenant_id, conversations.c.tenant_id == tenant_id, conversations.c.channel != TEST_CHANNEL]


def list_reminders(engine: Engine, tenant_slug: str, *, done: bool, assignee_id: str | None = None) -> list[Reminder]:
    """Los pendientes por fecha (el más próximo primero) o los hechos (el último primero). Con `assignee_id`, solo los de esa persona."""
    with engine.connect() as conn:
        tenant = tenant_of(conn, tenant_slug)
        query = _query().where(*_real(tenant.id))
        if assignee_id is not None:
            query = query.where(customer_reminders.c.assignee_id == assignee_id)
        if done:
            query = query.where(customer_reminders.c.done_at.is_not(None)).order_by(customer_reminders.c.done_at.desc()).limit(MAX_LISTED_DONE)
        else:
            query = query.where(customer_reminders.c.done_at.is_(None)).order_by(customer_reminders.c.due_at).limit(MAX_LISTED_OPEN)
        members = _members(conn, tenant.id)
        return [_reminder(row, members) for row in conn.execute(query).all()]


def reminders_of_customer(conn: Connection, tenant_id: Any, conversation_id: Any) -> list[Reminder]:
    """Los de un cliente, para su ficha: los pendientes por fecha y después los últimos hechos."""
    members = _members(conn, tenant_id)
    mine = customer_reminders.c.conversation_id == conversation_id
    pending = conn.execute(_query().where(mine, customer_reminders.c.done_at.is_(None)).order_by(customer_reminders.c.due_at)).all()
    finished = conn.execute(
        _query().where(mine, customer_reminders.c.done_at.is_not(None)).order_by(customer_reminders.c.done_at.desc()).limit(10)
    ).all()
    return [_reminder(row, members) for row in (*pending, *finished)]


def next_reminders(conn: Connection, conversation_ids: list[Any]) -> dict[Any, NextReminder]:
    """El pendiente más próximo de cada uno de esos clientes, para su tarjeta."""
    if not conversation_ids:
        return {}
    rows = conn.execute(
        select(customer_reminders.c.conversation_id, customer_reminders.c.title, customer_reminders.c.due_at)
        .where(customer_reminders.c.conversation_id.in_(conversation_ids), customer_reminders.c.done_at.is_(None))
        .order_by(customer_reminders.c.due_at)
    ).all()
    found: dict[Any, NextReminder] = {}
    for row in rows:
        found.setdefault(row.conversation_id, NextReminder(row.title, _utc(row.due_at)))
    return found


def create_reminder(engine: Engine, tenant_slug: str, conversation_id: str, reminder: NewReminder, *, by_user: str | None, by: str | None) -> Reminder:
    """Crea el recordatorio. Sin responsable elegido, queda para quien lo crea (`by_user`) si es del equipo; si no, sin responsable."""
    key = _key(conversation_id, ConversationNotFoundError, "ese cliente")
    with engine.begin() as conn:
        tenant = tenant_of(conn, tenant_slug)
        found = conn.execute(
            select(conversations.c.id).where(conversations.c.id == key, conversations.c.tenant_id == tenant.id, conversations.c.channel != TEST_CHANNEL)
        ).first()
        if found is None:
            raise ConversationNotFoundError("ese cliente no existe o es de otro negocio")
        members = _members(conn, tenant.id)
        if reminder.assignee_id is FOR_ME:
            assignee = by_user if by_user in members else None
        else:
            assignee = reminder.assignee_id
            if assignee is not None and assignee not in members:
                raise ReminderError("assignee_id", "Esa persona no es del equipo de este negocio.")
        pending = conn.execute(
            select(func.count()).select_from(customer_reminders).where(customer_reminders.c.conversation_id == key, customer_reminders.c.done_at.is_(None))
        ).scalar_one()
        if pending >= MAX_OPEN_PER_CUSTOMER:
            raise ReminderError("title", f"Este cliente ya tiene {MAX_OPEN_PER_CUSTOMER} recordatorios pendientes: marca o borra alguno.")
        reminder_id = uuid.uuid4()
        conn.execute(
            insert(customer_reminders).values(
                id=reminder_id, tenant_id=tenant.id, conversation_id=key, title=reminder.title, due_at=reminder.due_at, assignee_id=assignee,
                created_by=by, created_at=datetime.now(timezone.utc),
            )
        )
        return _reminder(conn.execute(_query().where(customer_reminders.c.id == reminder_id)).one(), members)


def _mine(conn: Connection, tenant_id: Any, reminder_id: str) -> uuid.UUID:
    key = _key(reminder_id, ReminderNotFoundError, "ese recordatorio")
    if conn.execute(select(customer_reminders.c.id).where(customer_reminders.c.id == key, customer_reminders.c.tenant_id == tenant_id)).first() is None:
        raise ReminderNotFoundError("ese recordatorio no existe o es de otro negocio")
    return key


def set_reminder_done(engine: Engine, tenant_slug: str, reminder_id: str, done: bool, *, by: str | None) -> Reminder:
    """Lo marca hecho (a nombre de `by`) o lo vuelve a abrir. Marcarlo hecho dos veces no cambia quién ni cuándo."""
    with engine.begin() as conn:
        tenant = tenant_of(conn, tenant_slug)
        key = _mine(conn, tenant.id, reminder_id)
        if done:
            conn.execute(
                update(customer_reminders)
                .where(customer_reminders.c.id == key, customer_reminders.c.done_at.is_(None))
                .values(done_at=datetime.now(timezone.utc), done_by=by)
            )
        else:
            conn.execute(update(customer_reminders).where(customer_reminders.c.id == key).values(done_at=None, done_by=None))
        return _reminder(conn.execute(_query().where(customer_reminders.c.id == key)).one(), _members(conn, tenant.id))


def delete_reminder(engine: Engine, tenant_slug: str, reminder_id: str) -> None:
    with engine.begin() as conn:
        tenant = tenant_of(conn, tenant_slug)
        conn.execute(delete(customer_reminders).where(customer_reminders.c.id == _mine(conn, tenant.id, reminder_id)))


# ------------------------------------------------------------------ el aviso cuando llega la hora


def alert_due_reminders(engine: Engine, *, now: datetime, limit: int = MAX_ALERTS_PER_RUN) -> list[str]:
    """Crea el aviso de cada recordatorio pendiente al que ya le llegó la hora y devuelve sus ids (para la notificación al celular).

    Cada recordatorio avisa una sola vez: se reserva (`notified_at`) en la misma transacción que crea su aviso, y si otra revisión ya lo
    tomó, o alguien lo marcó hecho justo antes, no hace nada. El aviso es para su responsable; sin responsable, o si ya no es del
    equipo, para todo el equipo. Uno que venció hace más de `ALERT_TOO_LATE` ya no avisa.
    """
    due = (
        select(
            customer_reminders.c.id, customer_reminders.c.tenant_id, customer_reminders.c.conversation_id, customer_reminders.c.title,
            customer_reminders.c.assignee_id, conversations.c.contact_name, conversations.c.contact_ref,
        )
        .join(conversations, conversations.c.id == customer_reminders.c.conversation_id)
        .where(
            customer_reminders.c.done_at.is_(None),
            customer_reminders.c.notified_at.is_(None),
            customer_reminders.c.due_at <= now,
            customer_reminders.c.due_at >= now - ALERT_TOO_LATE,
            conversations.c.channel != TEST_CHANNEL,
        )
        .order_by(customer_reminders.c.due_at)
        .limit(max(1, limit))
    )
    with engine.connect() as conn:
        rows = conn.execute(due).all()
    teams: dict[Any, set[str]] = {}
    created: list[str] = []
    for row in rows:
        with engine.begin() as conn:
            claimed = conn.execute(
                update(customer_reminders)
                .where(customer_reminders.c.id == row.id, customer_reminders.c.notified_at.is_(None), customer_reminders.c.done_at.is_(None))
                .values(notified_at=now)
            ).rowcount
            if claimed != 1:
                continue
            if row.tenant_id not in teams:
                teams[row.tenant_id] = set(_members(conn, row.tenant_id))
            title, body = alert_text(row.title, row.contact_name, row.contact_ref)
            notification_id = uuid.uuid4()
            conn.execute(
                insert(notifications).values(
                    id=notification_id, tenant_id=row.tenant_id, conversation_id=row.conversation_id, kind=ALERT_KIND, title=title,
                    body=body, recipient_id=row.assignee_id if row.assignee_id in teams[row.tenant_id] else None, created_at=now,
                )
            )
        created.append(str(notification_id))
    return created
