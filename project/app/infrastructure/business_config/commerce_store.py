"""Clientes, ventas y reportes de cada negocio en la base (implementa `CommerceStorage`).

Los clientes salen de las conversaciones de canales reales (las pruebas del panel no cuentan), con la etapa que guarda cada
conversación. Las ventas viven en `sales`. Los reportes cuentan por día en la hora de Colombia (`REPORT_TIMEZONE`). Cada consulta
recibe el negocio y solo alcanza sus filas.
"""
from __future__ import annotations

import uuid
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import and_, func, insert, or_, select, update
from sqlalchemy.engine import Connection, Engine

from app.domain.business_config.commerce import STAGES, Customer, NewSale, ReportDay, ReportTotals, Sale, SaleError, reached
from app.domain.business_config.errors import ConversationNotFoundError
from app.infrastructure.business_config.tables import conversation_entries, conversations, sales
from app.infrastructure.business_config.tenancy import tenant_of

REPORT_TIMEZONE = ZoneInfo("America/Bogota")
TEST_CHANNEL = "prueba"
MAX_CUSTOMERS = 300


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _day(value: datetime) -> date:
    return _utc(value).astimezone(REPORT_TIMEZONE).date()


def _bounds(since: date, until: date) -> tuple[datetime, datetime]:
    """El periodo en UTC: desde el comienzo de `since` hasta el final de `until`, en la hora de Colombia."""
    start = datetime.combine(since, time.min, REPORT_TIMEZONE).astimezone(timezone.utc)
    end = datetime.combine(until + timedelta(days=1), time.min, REPORT_TIMEZONE).astimezone(timezone.utc)
    return start, end


def _sale(row: Any) -> Sale:
    return Sale(
        id=str(row.id), customer_name=row.customer_name, description=row.description, amount=Decimal(row.amount), currency=row.currency,
        status=row.status, created_at=_utc(row.created_at), created_by=row.created_by,
        conversation_id=str(row.conversation_id) if row.conversation_id else None,
    )


class CommerceStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # ------------------------------------------------------------------ clientes

    def customers(self, tenant_slug: str, *, stage: str | None = None, query: str | None = None, limit: int = MAX_CUSTOMERS) -> list[Customer]:
        with self._engine.connect() as conn:
            tenant = tenant_of(conn, tenant_slug)
            where = [conversations.c.tenant_id == tenant.id, conversations.c.channel != TEST_CHANNEL]
            if stage in STAGES:
                where.append(conversations.c.stage == stage)
            text = " ".join(str(query or "").split()).lower()
            if text:
                pattern = f"%{text}%"
                where.append(or_(func.lower(conversations.c.contact_name).like(pattern), conversations.c.contact_ref.like(pattern)))
            rows = conn.execute(
                select(conversations).where(*where).order_by(conversations.c.last_message_at.desc()).limit(max(1, min(limit, MAX_CUSTOMERS)))
            ).all()
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
                first_contact_at=_utc(row.started_at), last_message_at=_utc(row.last_message_at), message_count=row.message_count,
                needs_human=bool(row.needs_human), purchases=counts[row.id], spent=dict(bought[row.id]),
            )
            for row in rows
        ]

    # ------------------------------------------------------------------ ventas

    def record_sale(self, tenant_slug: str, sale: NewSale, *, created_by: str | None) -> Sale:
        """Registra la venta. Si es de una conversación, su cliente pasa a «cliente» y deja de esperar la verificación del pago."""
        now = datetime.now(timezone.utc)
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            conversation_id = self._conversation_of(conn, tenant.id, sale.conversation_id) if sale.conversation_id else None
            sale_id = uuid.uuid4()
            conn.execute(
                insert(sales).values(
                    id=sale_id, tenant_id=tenant.id, conversation_id=conversation_id, customer_name=sale.customer_name,
                    description=sale.description, amount=sale.amount, currency=sale.currency, status="confirmed", created_by=created_by,
                    created_at=now,
                )
            )
            if conversation_id is not None:
                conn.execute(update(conversations).where(conversations.c.id == conversation_id).values(stage="customer", updated_at=now))
                conn.execute(
                    update(conversations)
                    .where(conversations.c.id == conversation_id, conversations.c.handoff_reason == "payment_review")
                    .values(needs_human=False)
                )
            row = conn.execute(select(sales).where(sales.c.id == sale_id)).one()
        return _sale(row)

    @staticmethod
    def _conversation_of(conn: Connection, tenant_id: Any, conversation_id: str) -> Any:
        try:
            key = uuid.UUID(str(conversation_id))
        except ValueError as exc:
            raise ConversationNotFoundError("la conversación no existe") from exc
        found = conn.execute(select(conversations.c.id).where(conversations.c.id == key, conversations.c.tenant_id == tenant_id)).scalar_one_or_none()
        if found is None:
            raise ConversationNotFoundError("la conversación no existe o es de otro negocio")
        return found

    def cancel_sale(self, tenant_slug: str, sale_id: str) -> Sale:
        try:
            key = uuid.UUID(str(sale_id))
        except ValueError as exc:
            raise SaleError("sale", "Esa venta no existe.") from exc
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            mine = and_(sales.c.id == key, sales.c.tenant_id == tenant.id)
            if conn.execute(select(sales.c.id).where(mine)).first() is None:
                raise SaleError("sale", "Esa venta no existe.")
            conn.execute(update(sales).where(mine, sales.c.status == "confirmed").values(status="cancelled", cancelled_at=datetime.now(timezone.utc)))
            return _sale(conn.execute(select(sales).where(mine)).one())

    def sales(self, tenant_slug: str, *, since: date, limit: int = 500) -> list[Sale]:
        start, _end = _bounds(since, since)
        with self._engine.connect() as conn:
            tenant = tenant_of(conn, tenant_slug)
            rows = conn.execute(
                select(sales).where(sales.c.tenant_id == tenant.id, sales.c.created_at >= start).order_by(sales.c.created_at.desc()).limit(limit)
            ).all()
        return [_sale(row) for row in rows]

    # ------------------------------------------------------------------ reportes

    def report_data(self, tenant_slug: str, *, since: date, until: date) -> tuple[list[ReportDay], ReportTotals, dict[str, int], dict[str, int]]:
        """Por día y en total: conversaciones nuevas, mensajes por autor y ventas; el embudo y los pasos a una persona."""
        start, end = _bounds(since, until)
        with self._engine.connect() as conn:
            tenant = tenant_of(conn, tenant_slug)
            real = and_(conversations.c.tenant_id == tenant.id, conversations.c.channel != TEST_CHANNEL)
            started = conn.execute(select(conversations.c.started_at).where(real, conversations.c.started_at >= start, conversations.c.started_at < end)).scalars().all()
            entries = conn.execute(
                select(conversation_entries.c.created_at, conversation_entries.c.author)
                .join(conversations, conversations.c.id == conversation_entries.c.conversation_id)
                .where(real, conversation_entries.c.created_at >= start, conversation_entries.c.created_at < end)
            ).all()
            sold = conn.execute(
                select(sales.c.created_at, sales.c.amount, sales.c.currency)
                .where(sales.c.tenant_id == tenant.id, sales.c.status == "confirmed", sales.c.created_at >= start, sales.c.created_at < end)
            ).all()
            active = conn.execute(select(conversations.c.stage).where(real, conversations.c.last_message_at >= start, conversations.c.last_message_at < end)).scalars().all()
            handoffs = conn.execute(
                select(conversations.c.handoff_reason).where(real, conversations.c.handoff_requested_at >= start, conversations.c.handoff_requested_at < end)
            ).scalars().all()

        per_day: dict[date, dict[str, int]] = defaultdict(Counter)
        for moment in started:
            per_day[_day(moment)]["new_conversations"] += 1
        for moment, author in entries:
            per_day[_day(moment)][f"{author}_messages"] += 1
        revenue: dict[str, Decimal] = defaultdict(Decimal)
        for moment, amount, currency in sold:
            per_day[_day(moment)]["sales"] += 1
            revenue[currency] += Decimal(amount)
        days = []
        current = since
        while current <= until:
            counts = per_day.get(current, {})
            days.append(
                ReportDay(
                    current, counts.get("new_conversations", 0), counts.get("customer_messages", 0), counts.get("assistant_messages", 0),
                    counts.get("agent_messages", 0), counts.get("sales", 0),
                )
            )
            current += timedelta(days=1)
        totals = ReportTotals(
            conversations=len(started),
            customer_messages=sum(day.customer_messages for day in days),
            assistant_messages=sum(day.assistant_messages for day in days),
            agent_messages=sum(day.agent_messages for day in days),
            handoffs=len(handoffs),
            sales=len(sold),
            revenue=dict(revenue),
        )
        funnel = {stage: sum(1 for value in active if reached(value or "new", stage)) for stage in STAGES}
        reasons = dict(Counter(reason or "human_request" for reason in handoffs))
        return days, totals, funnel, reasons
