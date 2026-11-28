"""Lo que comparten las consultas de clientes, ventas y el tablero: el periodo en la hora de Colombia, cuáles conversaciones son
clientes de un negocio y cómo se arma cada cliente con lo que ha comprado.

Lo usan `commerce_store.py` (clientes, ventas y reportes) y `pipeline_store.py` (el tablero).
"""
from __future__ import annotations

import uuid
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import false, func, or_, select
from sqlalchemy.engine import Connection

from app.domain.business_config.commerce import LOST, Customer, Sale
from app.domain.business_config.customer_labels import LabelRef
from app.infrastructure.business_config.tables import business_members, conversation_labels, conversations, customer_labels, sales

REPORT_TIMEZONE = ZoneInfo("America/Bogota")
TEST_CHANNEL = "prueba"
MAX_CUSTOMERS = 300


def utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def day_of(value: datetime) -> date:
    return utc(value).astimezone(REPORT_TIMEZONE).date()


def bounds(since: date, until: date) -> tuple[datetime, datetime]:
    """El periodo en UTC: desde el comienzo de `since` hasta el final de `until`, en la hora de Colombia."""
    start = datetime.combine(since, time.min, REPORT_TIMEZONE).astimezone(timezone.utc)
    end = datetime.combine(until + timedelta(days=1), time.min, REPORT_TIMEZONE).astimezone(timezone.utc)
    return start, end


def real_customers(tenant_id: Any, query: str | None = None, label: str | None = None) -> list[Any]:
    """Las condiciones de «los clientes de este negocio»: sus conversaciones de canales reales y, con `query`, las que coinciden por
    nombre o número; con `label` (el id de una etiqueta), solo quienes la llevan."""
    where = [conversations.c.tenant_id == tenant_id, conversations.c.channel != TEST_CHANNEL]
    text = " ".join(str(query or "").split()).lower()
    if text:
        pattern = f"%{text}%"
        where.append(or_(func.lower(conversations.c.contact_name).like(pattern), conversations.c.contact_ref.like(pattern)))
    if label:
        try:
            label_id = uuid.UUID(str(label))
        except ValueError:
            return [*where, false()]  # una etiqueta que no existe no la lleva nadie
        where.append(
            conversations.c.id.in_(
                select(conversation_labels.c.conversation_id).where(conversation_labels.c.label_id == label_id, conversation_labels.c.tenant_id == tenant_id)
            )
        )
    return where


def customers_of(conn: Connection, rows: list[Any]) -> list[Customer]:
    """Los clientes de esas conversaciones, con lo que ha comprado cada uno (por moneda)."""
    ids = [row.id for row in rows]
    bought: dict[Any, dict[str, Decimal]] = defaultdict(dict)
    counts: Counter = Counter()
    if ids:
        for sale in conn.execute(
            select(sales.c.conversation_id, sales.c.currency, func.sum(sales.c.amount).label("total"), func.count().label("n"))
            .where(sales.c.conversation_id.in_(ids), sales.c.status == "confirmed")
            .group_by(sales.c.conversation_id, sales.c.currency)
        ):
            bought[sale.conversation_id][sale.currency] = Decimal(sale.total)
            counts[sale.conversation_id] += int(sale.n)
    owners = owner_labels(conn, rows)
    tagged = labels_by_customer(conn, ids)
    return [
        Customer(
            conversation_id=str(row.id), name=row.contact_name, contact_ref=row.contact_ref, channel=row.channel, stage=row.stage or "new",
            first_contact_at=utc(row.started_at), last_message_at=utc(row.last_message_at), message_count=row.message_count,
            needs_human=bool(row.needs_human), purchases=counts[row.id], spent=dict(bought[row.id]),
            lost_reason=row.lost_reason if row.stage == LOST else None,
            deal_amount=Decimal(row.deal_amount) if row.deal_amount is not None and row.deal_currency else None,
            deal_currency=row.deal_currency if row.deal_amount is not None else None,
            # Si esa persona ya no es del equipo, el cliente queda sin responsable.
            owner_id=row.owner_id if row.owner_id in owners else None, owner_label=owners.get(row.owner_id),
            labels=tuple(tagged.get(row.id, ())),
        )
        for row in rows
    ]


def labels_by_customer(conn: Connection, conversation_ids: list[Any]) -> dict[Any, list[LabelRef]]:
    """Las etiquetas de cada una de esas conversaciones, por nombre."""
    if not conversation_ids:
        return {}
    found = conn.execute(
        select(conversation_labels.c.conversation_id, customer_labels.c.id, customer_labels.c.name, customer_labels.c.color)
        .join(customer_labels, customer_labels.c.id == conversation_labels.c.label_id)
        .where(conversation_labels.c.conversation_id.in_(conversation_ids))
        .order_by(customer_labels.c.name_key)
    ).all()
    by_customer: dict[Any, list[LabelRef]] = defaultdict(list)
    for row in found:
        by_customer[row.conversation_id].append(LabelRef(str(row.id), row.name, row.color))
    return by_customer


def owner_labels(conn: Connection, rows: list[Any]) -> dict[str, str]:
    """Cómo se llama el responsable de cada una de esas conversaciones: solo quienes siguen en el equipo de ese negocio."""
    wanted = {(row.tenant_id, row.owner_id) for row in rows if row.owner_id}
    if not wanted:
        return {}
    found = conn.execute(
        select(business_members.c.tenant_id, business_members.c.user_id, business_members.c.email)
        .where(business_members.c.tenant_id.in_({tenant for tenant, _ in wanted}), business_members.c.user_id.in_({user for _, user in wanted}))
    ).all()
    return {member.user_id: member.email or "Alguien del equipo" for member in found if (member.tenant_id, member.user_id) in wanted}


def sale_of(row: Any) -> Sale:
    return Sale(
        id=str(row.id), customer_name=row.customer_name, description=row.description, amount=Decimal(row.amount), currency=row.currency,
        status=row.status, created_at=utc(row.created_at), created_by=row.created_by,
        conversation_id=str(row.conversation_id) if row.conversation_id else None,
    )
