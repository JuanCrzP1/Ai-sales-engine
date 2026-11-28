"""La ficha de un cliente en la base: leerla completa, cambiar su valor y su responsable, y sus notas.

`CommerceStore` lo expone (`customer_card`, `update_customer_deal`, `add_customer_note`, `delete_customer_note`); aquí están sus
consultas. Como el resto de clientes, solo alcanza las conversaciones de canales reales del negocio que recibe.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.engine import Connection, Engine

from app.domain.business_config.customer_card import (
    EVENT_OWNER,
    EVENT_VALUE,
    MAX_EVENTS,
    MAX_NOTES,
    SOURCE_TEAM,
    UNSET,
    Assignee,
    CustomerCard,
    CustomerCardError,
    CustomerEvent,
    CustomerNote,
    DealChange,
    money_text,
)
from app.domain.business_config.errors import ConversationNotFoundError
from app.infrastructure.business_config.commerce_queries import customers_of, real_customers, sale_of, utc
from app.infrastructure.business_config.customer_events import record_event
from app.infrastructure.business_config.reminder_store import reminders_of_customer
from app.infrastructure.business_config.tables import business_members, conversations, customer_events, customer_notes, sales
from app.infrastructure.business_config.tenancy import tenant_of

_ROLE_ORDER = {"owner": 0, "admin": 1, "agent": 2}


def _key(value: str, what: str = "ese cliente") -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except ValueError as exc:
        raise ConversationNotFoundError(f"{what} no existe") from exc


def _row(conn: Connection, tenant_id: Any, key: uuid.UUID) -> Any:
    row = conn.execute(select(conversations).where(conversations.c.id == key, *real_customers(tenant_id))).first()
    if row is None:
        raise ConversationNotFoundError("ese cliente no existe o es de otro negocio")
    return row


def _assignees(conn: Connection, tenant_id: Any) -> list[Assignee]:
    """El equipo del negocio: quienes pueden ser responsables de un cliente. Primero el dueño, después los demás por correo."""
    rows = conn.execute(select(business_members.c.user_id, business_members.c.email, business_members.c.role).where(business_members.c.tenant_id == tenant_id)).all()
    return sorted((Assignee(row.user_id, row.email, row.role) for row in rows), key=lambda member: (_ROLE_ORDER.get(member.role, 9), member.label.lower()))


def _note(row: Any) -> CustomerNote:
    return CustomerNote(id=str(row.id), body=row.body, author=row.author, created_at=utc(row.created_at))


def _card(conn: Connection, tenant_id: Any, key: uuid.UUID) -> CustomerCard:
    row = _row(conn, tenant_id, key)
    assignees = _assignees(conn, tenant_id)
    purchases = conn.execute(select(sales).where(sales.c.conversation_id == key, sales.c.tenant_id == tenant_id).order_by(sales.c.created_at.desc())).all()
    notes = conn.execute(
        select(customer_notes).where(customer_notes.c.conversation_id == key).order_by(customer_notes.c.created_at.desc()).limit(MAX_NOTES)
    ).all()
    events = conn.execute(
        select(customer_events).where(customer_events.c.conversation_id == key).order_by(customer_events.c.created_at.desc()).limit(MAX_EVENTS)
    ).all()
    return CustomerCard(
        customer=customers_of(conn, [row])[0],
        stage_since=utc(row.stage_changed_at),
        owner=next((member for member in assignees if member.user_id == row.owner_id), None),
        assignees=assignees,
        purchases=[sale_of(sale) for sale in purchases],
        notes=[_note(note) for note in notes],
        events=[
            CustomerEvent(
                id=str(event.id), kind=event.kind, source=event.source, created_at=utc(event.created_at), from_stage=event.from_stage,
                to_stage=event.to_stage, detail=event.detail, actor=event.actor,
            )
            for event in events
        ],
        reminders=reminders_of_customer(conn, tenant_id, key),
    )


def read_card(engine: Engine, tenant_slug: str, conversation_id: str) -> CustomerCard:
    key = _key(conversation_id)
    with engine.connect() as conn:
        return _card(conn, tenant_of(conn, tenant_slug).id, key)


def update_deal(engine: Engine, tenant_slug: str, conversation_id: str, change: DealChange, *, by: str | None = None) -> CustomerCard:
    """Cambia el valor y/o el responsable. Cada cambio de verdad queda en el historial, a nombre de `by`."""
    key, now = _key(conversation_id), datetime.now(timezone.utc)
    with engine.begin() as conn:
        tenant = tenant_of(conn, tenant_slug)
        row = _row(conn, tenant.id, key)
        values: dict[str, Any] = {}
        if change.value is not UNSET:
            amount, currency = change.value if change.value is not None else (None, None)
            if (row.deal_amount, row.deal_currency) != (amount, currency):
                values.update(deal_amount=amount, deal_currency=currency)
                record_event(
                    conn, tenant_id=tenant.id, conversation_id=key, kind=EVENT_VALUE, source=SOURCE_TEAM,
                    detail=money_text(amount, currency) if amount is not None else None, actor=by, at=now,
                )
        if change.owner_id is not UNSET and change.owner_id != row.owner_id:
            owner = next((member for member in _assignees(conn, tenant.id) if member.user_id == change.owner_id), None)
            if change.owner_id is not None and owner is None:
                raise CustomerCardError("owner_id", "Esa persona no es del equipo de este negocio.")
            values["owner_id"] = change.owner_id
            record_event(
                conn, tenant_id=tenant.id, conversation_id=key, kind=EVENT_OWNER, source=SOURCE_TEAM, detail=owner.label if owner else None,
                actor=by, at=now,
            )
        if values:
            conn.execute(update(conversations).where(conversations.c.id == key).values(**values))
        return _card(conn, tenant.id, key)


def add_note(engine: Engine, tenant_slug: str, conversation_id: str, body: str, *, author: str | None = None) -> CustomerNote:
    key = _key(conversation_id)
    with engine.begin() as conn:
        tenant = tenant_of(conn, tenant_slug)
        _row(conn, tenant.id, key)
        count = conn.execute(select(func.count()).select_from(customer_notes).where(customer_notes.c.conversation_id == key)).scalar_one()
        if count >= MAX_NOTES:
            raise CustomerCardError("body", "Este cliente ya tiene muchas notas: borra alguna antes de agregar otra.")
        note_id = uuid.uuid4()
        conn.execute(
            insert(customer_notes).values(
                id=note_id, tenant_id=tenant.id, conversation_id=key, body=body, author=author, created_at=datetime.now(timezone.utc)
            )
        )
        return _note(conn.execute(select(customer_notes).where(customer_notes.c.id == note_id)).one())


def delete_note(engine: Engine, tenant_slug: str, conversation_id: str, note_id: str) -> None:
    key, note = _key(conversation_id), _key(note_id, "esa nota")
    with engine.begin() as conn:
        tenant = tenant_of(conn, tenant_slug)
        _row(conn, tenant.id, key)
        gone = conn.execute(delete(customer_notes).where(customer_notes.c.id == note, customer_notes.c.conversation_id == key, customer_notes.c.tenant_id == tenant.id))
        if gone.rowcount == 0:
            raise ConversationNotFoundError("esa nota no existe")
