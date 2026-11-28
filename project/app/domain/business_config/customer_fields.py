"""Los campos del cliente: los datos propios que cada negocio quiere guardar de sus clientes («Ciudad», «Cumpleaños», «Tipo de cliente»).

- **Un catálogo por negocio**: cada campo tiene nombre y tipo (texto, número, fecha, sí o no, o una lista de opciones). No puede haber
  dos que se lean igual (como las etiquetas: sin mayúsculas, acentos ni caracteres invisibles). El tipo no cambia después de creado;
  el nombre y las opciones, sí.
- **Cada cliente** tiene un valor por campo, o ninguno. Se ven y se cambian en su ficha, con quién lo cambió y cuándo.
- **Quién hace qué**: crear, renombrar, cambiar las opciones y borrar campos es de quien configura el negocio (el dueño o un
  administrador): afecta a todos sus clientes. Llenar los valores es de todo el que atiende. Al borrar un campo se borran sus valores;
  al quitar una opción de una lista, los clientes que la tenían quedan sin valor en ese campo.
- Los valores se guardan en una forma única, sin importar cómo se escribieron: el número sin separadores de miles («1200.5»), la fecha
  como «2026-11-29», el sí o no como «true» o «false» y la opción de una lista como está escrita en el campo.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.domain.business_config.customer_labels import clean_name, label_key

TEXT, NUMBER, DATE, YES_NO, CHOICE = "text", "number", "date", "yes_no", "choice"
FIELD_KINDS = (TEXT, NUMBER, DATE, YES_NO, CHOICE)

MAX_FIELDS = 30
MAX_FIELD_NAME = 40
MAX_OPTIONS = 30
MIN_OPTIONS = 2
MAX_OPTION = 40
MAX_TEXT_VALUE = 200
# Los dígitos de un número (sin contar los decimales): suficiente para cualquier precio o cantidad.
MAX_NUMBER_DIGITS = 15
MAX_DECIMALS = 4
OLDEST_YEAR, NEWEST_YEAR = 1900, 2100

_YES = {"si", "true", "1", "yes", "x"}
_NO = {"no", "false", "0"}


class FieldError(ValueError):
    """Un dato del campo o de su valor no sirve. `field` dice cuál; el mensaje es para el negocio."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field


def checked_field_name(name: object) -> str:
    text = clean_name(name)
    if not text:
        raise FieldError("name", "Escribe el nombre del campo.")
    if len(text) > MAX_FIELD_NAME:
        raise FieldError("name", f"El nombre es muy largo (máximo {MAX_FIELD_NAME} caracteres).")
    return text


def checked_kind(kind: object) -> str:
    value = str(kind or "").strip()
    if value not in FIELD_KINDS:
        raise FieldError("kind", "Elige qué tipo de dato es.")
    return value


def checked_options(options: object) -> tuple[str, ...]:
    """Las opciones de una lista: sin repetir (como se leen), sin vacías, entre `MIN_OPTIONS` y `MAX_OPTIONS`."""
    if not isinstance(options, (list, tuple)):
        raise FieldError("options", "Escribe las opciones de la lista.")
    chosen: dict[str, str] = {}
    for item in options:
        text = clean_name(item)
        if not text:
            continue
        if len(text) > MAX_OPTION:
            raise FieldError("options", f"«{text[:20]}…» es muy larga (máximo {MAX_OPTION} caracteres por opción).")
        if label_key(text) in chosen:
            raise FieldError("options", f"«{text}» está repetida.")
        chosen[label_key(text)] = text
    if len(chosen) < MIN_OPTIONS:
        raise FieldError("options", f"Una lista necesita al menos {MIN_OPTIONS} opciones.")
    if len(chosen) > MAX_OPTIONS:
        raise FieldError("options", f"Una lista puede tener hasta {MAX_OPTIONS} opciones.")
    return tuple(chosen.values())


@dataclass(frozen=True)
class NewField:
    name: str
    kind: str
    options: tuple[str, ...] = ()

    @classmethod
    def checked(cls, *, name: object, kind: object, options: object = None) -> NewField:
        kind_value = checked_kind(kind)
        return cls(checked_field_name(name), kind_value, checked_options(options) if kind_value == CHOICE else ())


@dataclass(frozen=True)
class FieldChange:
    """Lo que cambia en un campo, ya revisado: el nombre y/o las opciones de la lista (None, lo que no cambia)."""

    name: str | None = None
    options: tuple[str, ...] | None = None

    @classmethod
    def checked(cls, changes: dict[str, object]) -> FieldChange:
        change = cls(
            checked_field_name(changes["name"]) if "name" in changes else None,
            checked_options(changes["options"]) if "options" in changes else None,
        )
        if change.name is None and change.options is None:
            raise FieldError("name", "No hay nada que cambiar.")
        return change


@dataclass(frozen=True)
class CustomerField:
    """Un campo del catálogo, con cuántos clientes lo tienen lleno."""

    id: str
    name: str
    kind: str
    options: tuple[str, ...] = ()
    filled: int = 0
    created_at: datetime | None = None


@dataclass(frozen=True)
class FieldValue:
    """Un campo en la ficha de un cliente: su valor (None si está vacío) y quién lo puso y cuándo."""

    field: CustomerField
    value: str | None = None
    updated_by: str | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class FieldValues:
    """Los valores que el equipo cambia en la ficha: por id de campo, el valor escrito (None para dejarlo vacío)."""

    values: dict[str, object] = field(default_factory=dict)

    @classmethod
    def checked(cls, values: object) -> FieldValues:
        if not isinstance(values, dict) or not values:
            raise FieldError("values", "No hay nada que cambiar.")
        if len(values) > MAX_FIELDS:
            raise FieldError("values", "Son demasiados campos a la vez.")
        return cls({str(key): value for key, value in values.items()})


def _number(raw: object) -> str:
    if isinstance(raw, bool):
        raise ValueError
    if isinstance(raw, (int, float, Decimal)):
        amount = Decimal(str(raw))
    else:
        text = re.sub(r"[\s$]|COP|USD", "", str(raw), flags=re.I)
        if "," in text and "." in text:
            # El último separador es el decimal: «1.200,50» y «1,200.50».
            thousands = "." if text.rfind(",") > text.rfind(".") else ","
            text = text.replace(thousands, "").replace(",", ".")
        elif text.count(",") > 1 or text.count(".") > 1:
            text = text.replace(",", "").replace(".", "")  # «1.200.000»: solo miles
        elif (separator := "," if "," in text else "." if "." in text else ""):
            whole, _, decimals = text.partition(separator)
            # Un solo separador con tres cifras detrás son miles («1.200», «25,000»); si no, son decimales («1,5», «0.125»).
            thousands = len(decimals) == 3 and whole.lstrip("-") not in ("", "0")
            text = f"{whole}{decimals}" if thousands else f"{whole}.{decimals}"
        if not re.fullmatch(r"-?\d+(\.\d+)?", text):
            raise ValueError
        amount = Decimal(text)
    if not amount.is_finite():
        raise ValueError
    sign, digits, exponent = amount.normalize().as_tuple()
    whole = len(digits) + exponent if isinstance(exponent, int) else 0
    if whole > MAX_NUMBER_DIGITS or (isinstance(exponent, int) and -exponent > MAX_DECIMALS):
        raise ValueError
    text = format(amount.normalize(), "f")
    return "0" if text in ("-0", "") else text


def _date(raw: object) -> str:
    text = str(raw).strip()
    match = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    try:
        moment = date(int(match.group(3)), int(match.group(2)), int(match.group(1))) if match else date.fromisoformat(text[:10] if len(text) > 10 and text[10] == "T" else text)
    except (ValueError, TypeError):
        raise ValueError from None
    if not OLDEST_YEAR <= moment.year <= NEWEST_YEAR:
        raise ValueError
    return moment.isoformat()


def _yes_no(raw: object) -> str:
    if isinstance(raw, bool):
        return "true" if raw else "false"
    key = label_key(raw)
    if key in _YES:
        return "true"
    if key in _NO:
        return "false"
    raise ValueError


_PROBLEMS = {
    NUMBER: "Escribe un número.",
    DATE: "Elige una fecha.",
    YES_NO: "Elige sí o no.",
    CHOICE: "Elige una de las opciones.",
}


def checked_value(customer_field: CustomerField, raw: object) -> str | None:
    """El valor como se guarda, o None para dejar el campo vacío (también si llega en blanco). `FieldError` si no es de su tipo."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    path = f"values.{customer_field.id}"
    if customer_field.kind == TEXT:
        text = " ".join(clean_name(raw).split()) if not isinstance(raw, (dict, list)) else ""
        if not text:
            return None
        if len(text) > MAX_TEXT_VALUE:
            raise FieldError(path, f"Es muy largo (máximo {MAX_TEXT_VALUE} caracteres).")
        return text
    if customer_field.kind == CHOICE:
        found = next((option for option in customer_field.options if label_key(option) == label_key(raw)), None)
        if found is None:
            raise FieldError(path, _PROBLEMS[CHOICE])
        return found
    reader = {NUMBER: _number, DATE: _date, YES_NO: _yes_no}[customer_field.kind]
    try:
        return reader(raw)
    except (ValueError, InvalidOperation):
        raise FieldError(path, _PROBLEMS[customer_field.kind]) from None
