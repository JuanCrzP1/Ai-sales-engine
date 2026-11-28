"""La ficha de un cliente: todo lo que el negocio sabe y decide de esa persona, en un solo lugar.

- **Valor**: cuánto vale lo que el cliente podría comprar (un monto y su moneda). Lo pone el equipo; suma en «Por cerrar» mientras el
  cliente siga en el embudo sin comprar.
- **Responsable**: la persona del equipo que lo atiende. Solo puede ser alguien del negocio.
- **Notas**: lo que el equipo anota de ese cliente («prefiere que lo llamen en la tarde»). El cliente nunca las ve.
- **Historial**: cada cambio de etapa, de valor y de responsable, con quién lo hizo y cuándo. La etapa la cambian el asistente (con
  lo que reconoce en el chat), el equipo (a mano, o al confirmar un pago) o una venta registrada.
- **Compras**: sus ventas, también las anuladas.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.domain.business_config.commerce import Customer, Sale

MAX_NOTE = 2000
MAX_NOTES = 200
MAX_EVENTS = 100
_CURRENCY = re.compile(r"[A-Z]{3}")

# Qué cambió.
EVENT_STAGE, EVENT_VALUE, EVENT_OWNER = "stage", "value", "owner"
EVENT_KINDS = (EVENT_STAGE, EVENT_VALUE, EVENT_OWNER)
# Quién lo cambió: el asistente con lo que reconoció en el chat, alguien del equipo o una venta registrada.
SOURCE_ASSISTANT, SOURCE_TEAM, SOURCE_SALE = "assistant", "team", "sale"
EVENT_SOURCES = (SOURCE_ASSISTANT, SOURCE_TEAM, SOURCE_SALE)


class CustomerCardError(ValueError):
    """Un dato de la ficha no sirve. `field` dice cuál; el mensaje es para el negocio."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field


class _Unset:
    """Un dato que la petición no trae: se deja como está (distinto de None, que lo borra)."""

    def __repr__(self) -> str:
        return "UNSET"


UNSET = _Unset()


@dataclass(frozen=True)
class DealChange:
    """Lo que el equipo cambia en la ficha, ya revisado. Lo que no viene queda `UNSET`."""

    # (monto, moneda), None para quitar el valor, o UNSET.
    value: tuple[Decimal, str] | None | _Unset = UNSET
    # El responsable (su `user_id`), None para dejarlo sin responsable, o UNSET.
    owner_id: str | None | _Unset = UNSET

    @property
    def empty(self) -> bool:
        return self.value is UNSET and self.owner_id is UNSET

    @classmethod
    def checked(cls, changes: dict[str, object]) -> DealChange:
        """`changes` trae solo lo que cambia: `amount` y `currency` (juntos; `amount` vacío quita el valor) y/o `owner_id`."""
        value: tuple[Decimal, str] | None | _Unset = UNSET
        if "amount" in changes:
            raw = changes.get("amount")
            if raw is None or str(raw).strip() == "":
                value = None
            else:
                try:
                    amount = Decimal(str(raw)).quantize(Decimal("0.01"))
                except (InvalidOperation, ValueError):
                    raise CustomerCardError("amount", "Escribe el valor en números.") from None
                if not amount.is_finite() or amount <= 0 or amount >= Decimal("1000000000000"):
                    raise CustomerCardError("amount", "El valor debe ser mayor que cero.")
                currency = str(changes.get("currency") or "").strip().upper()
                if not _CURRENCY.fullmatch(currency):
                    raise CustomerCardError("currency", "Elige la moneda.")
                value = (amount, currency)
        owner: str | None | _Unset = UNSET
        if "owner_id" in changes:
            owner = str(changes.get("owner_id") or "").strip() or None
        change = cls(value, owner)
        if change.empty:
            raise CustomerCardError("amount", "No hay nada que cambiar.")
        return change


def checked_note(body: object) -> str:
    text = "\n".join(line.rstrip() for line in str(body or "").strip().splitlines())
    if not text:
        raise CustomerCardError("body", "Escribe la nota.")
    if len(text) > MAX_NOTE:
        raise CustomerCardError("body", f"La nota es muy larga (máximo {MAX_NOTE} caracteres).")
    return text


@dataclass(frozen=True)
class Assignee:
    """Alguien del equipo que puede ser responsable de un cliente."""

    user_id: str
    email: str | None
    role: str

    @property
    def label(self) -> str:
        return self.email or "Alguien del equipo"


@dataclass(frozen=True)
class CustomerNote:
    id: str
    body: str
    author: str | None
    created_at: datetime


@dataclass(frozen=True)
class CustomerEvent:
    """Un cambio en la ficha. `from_stage` y `to_stage`, en un cambio de etapa; `detail`, el motivo de «no compró», el valor nuevo o
    el nombre del responsable; `actor`, quién lo hizo cuando fue una persona."""

    id: str
    kind: str
    source: str
    created_at: datetime
    from_stage: str | None = None
    to_stage: str | None = None
    detail: str | None = None
    actor: str | None = None


@dataclass(frozen=True)
class CustomerCard:
    customer: Customer
    # Desde cuándo está en su etapa (None si nunca cambió desde que existe el historial).
    stage_since: datetime | None = None
    owner: Assignee | None = None
    assignees: list[Assignee] = field(default_factory=list)
    purchases: list[Sale] = field(default_factory=list)
    notes: list[CustomerNote] = field(default_factory=list)
    events: list[CustomerEvent] = field(default_factory=list)


def money_text(amount: Decimal, currency: str) -> str:
    """El valor como queda en el historial: «COP 210.000» o «USD 45,50» (el panel lo vuelve a escribir a su manera)."""
    whole, cents = f"{amount:.2f}".split(".")
    grouped = f"{int(whole):,}".replace(",", ".")
    return f"{currency} {grouped}" if cents == "00" else f"{currency} {grouped},{cents}"
