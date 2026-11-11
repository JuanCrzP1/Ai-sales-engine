"""Clientes, ventas y reportes de cada negocio.

- **Clientes**: cada persona que escribió por un canal real (no las pruebas del panel), con la etapa a la que llegó. La etapa solo
  avanza: nuevo → interesado (preguntó, contó un problema o dudó) → listo para comprar (quiso comprar) → pagó (reportó un pago que
  el equipo debe verificar) → cliente (el equipo registró su venta). La marca el asistente con lo que reconoce en cada mensaje.
- **Ventas**: las registra el equipo (qué compró, cuánto y en qué moneda), atadas a la conversación cuando la hay. Una venta anulada
  queda marcada y no suma.
- **Reportes**: lo que pasó en un periodo, por día y en total, comparado con el periodo anterior.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

STAGES = ("new", "interested", "ready", "payment", "customer")
_ORDER = {stage: index for index, stage in enumerate(STAGES)}
# Lo que reconoce el asistente en cada mensaje → la etapa a la que llega el cliente.
_INTENT_STAGE = {"pain": "interested", "info": "interested", "objection": "interested", "buy": "ready"}
SALE_STATUSES = ("confirmed", "cancelled")
MAX_REPORT_DAYS = 366
_CURRENCY = re.compile(r"[A-Z]{3}")


class SaleError(ValueError):
    """Un dato de la venta no sirve. `field` dice cuál; el mensaje es para el negocio."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field


def stage_for_intent(intent: str | None) -> str | None:
    return _INTENT_STAGE.get(str(intent or "").strip().lower())


def advanced(current: str | None, new: str | None) -> str | None:
    """La etapa nueva si avanza sobre la actual; si no, None (nunca retrocede)."""
    if new not in _ORDER:
        return None
    return new if _ORDER[new] > _ORDER.get(current or "new", 0) else None


def reached(stage: str, at_least: str) -> bool:
    return _ORDER.get(stage, 0) >= _ORDER[at_least]


@dataclass(frozen=True)
class Customer:
    """Un cliente: la conversación de un contacto en un canal, con su etapa y lo que ha comprado (por moneda)."""

    conversation_id: str
    name: str | None
    contact_ref: str
    channel: str
    stage: str
    first_contact_at: datetime
    last_message_at: datetime
    message_count: int
    needs_human: bool
    purchases: int = 0
    spent: dict[str, Decimal] = field(default_factory=dict)


@dataclass(frozen=True)
class NewSale:
    customer_name: str
    description: str
    amount: Decimal
    currency: str
    conversation_id: str | None = None

    @classmethod
    def checked(cls, *, customer_name: str, description: str, amount: object, currency: str, conversation_id: str | None = None) -> NewSale:
        name = " ".join(str(customer_name or "").split())
        what = " ".join(str(description or "").split())
        money = str(currency or "").strip().upper()
        if not name:
            raise SaleError("customer_name", "Escribe el nombre del cliente.")
        if len(name) > 120:
            raise SaleError("customer_name", "El nombre es muy largo.")
        if not what:
            raise SaleError("description", "Escribe qué compró.")
        if len(what) > 200:
            raise SaleError("description", "La descripción es muy larga (máximo 200 caracteres).")
        try:
            value = Decimal(str(amount)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError):
            raise SaleError("amount", "Escribe el valor de la venta.") from None
        if not value.is_finite() or value <= 0 or value >= Decimal("1000000000000"):
            raise SaleError("amount", "El valor debe ser mayor que cero.")
        if not _CURRENCY.fullmatch(money):
            raise SaleError("currency", "Elige la moneda.")
        return cls(name, what, value, money, conversation_id or None)


@dataclass(frozen=True)
class Sale:
    id: str
    customer_name: str
    description: str
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
    created_by: str | None = None
    conversation_id: str | None = None


@dataclass(frozen=True)
class ReportDay:
    day: date
    new_conversations: int = 0
    customer_messages: int = 0
    assistant_messages: int = 0
    agent_messages: int = 0
    sales: int = 0


@dataclass(frozen=True)
class ReportTotals:
    conversations: int = 0
    customer_messages: int = 0
    assistant_messages: int = 0
    agent_messages: int = 0
    handoffs: int = 0
    sales: int = 0
    revenue: dict[str, Decimal] = field(default_factory=dict)


@dataclass(frozen=True)
class Report:
    """Lo que pasó en el negocio entre `since` y `until` (días completos, en la hora de Colombia)."""

    since: date
    until: date
    days: list[ReportDay]
    totals: ReportTotals
    previous: ReportTotals
    # Cuántos clientes del periodo llegaron al menos a cada etapa (el embudo).
    funnel: dict[str, int]
    handoffs_by_reason: dict[str, int]
    ai_cost_usd: float | None = None
    ai_replies: int = 0
