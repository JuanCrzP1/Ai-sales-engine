"""Lo que comparten las consultas de clientes, ventas y el tablero: el periodo en la hora de Colombia, cuáles conversaciones son
clientes de un negocio y cómo se arma cada cliente con lo que ha comprado.

Lo usan `commerce_store.py` (clientes, ventas y reportes) y `pipeline_store.py` (el tablero).
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select
from sqlalchemy.engine import Connection

from app.domain.business_config.commerce import LOST, Customer
from app.infrastructure.business_config.tables import conversations, sales

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


def real_customers(tenant_id: Any, query: str | None = None) -> list[Any]:
    """Las condiciones de «los clientes de este negocio»: sus conversaciones de canales reales y, con `query`, las que coinciden por
    nombre o número."""
    where = [conversations.c.tenant_id == tenant_id, conversations.c.channel != TEST_CHANNEL]
    text = " ".join(str(query or "").split()).lower()
    if text:
        pattern = f"%{text}%"
        where.append(or_(func.lower(conversations.c.contact_name).like(pattern), conversations.c.contact_ref.like(pattern)))
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
    return [
        Customer(
            conversation_id=str(row.id), name=row.contact_name, contact_ref=row.contact_ref, channel=row.channel, stage=row.stage or "new",
            first_contact_at=utc(row.started_at), last_message_at=utc(row.last_message_at), message_count=row.message_count,
            needs_human=bool(row.needs_human), purchases=counts[row.id], spent=dict(bought[row.id]),
            lost_reason=row.lost_reason if row.stage == LOST else None,
        )
        for row in rows
    ]
