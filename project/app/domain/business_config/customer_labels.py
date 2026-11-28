"""Las etiquetas de los clientes: la forma del negocio de organizarlos a su manera («mayorista», «VIP», «llamar el lunes»).

- **Un catálogo por negocio**: cada etiqueta tiene nombre y color. No puede haber dos que se lean igual: «VIP», «vip» y « Vip » son la
  misma (tampoco cuentan los acentos ni los caracteres invisibles que llegan al copiar de WhatsApp).
- **Cada cliente** lleva las que quiera (hasta `MAX_LABELS_PER_CUSTOMER`). Se ven en su tarjeta y en su ficha, y el tablero y la lista
  se filtran por una.
- **Quién hace qué**: todo el que atiende las ve, se las pone a sus clientes, crea etiquetas y les cambia el color. Cambiarles el
  nombre y borrarlas es de quien configura el negocio (el dueño o un administrador): afecta a todos sus clientes. Al borrar una, sus
  clientes solo la pierden.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import datetime

MAX_LABELS = 50
MAX_LABELS_PER_CUSTOMER = 10
MAX_LABEL_NAME = 30
# Los colores que se pueden elegir (su tono lo pone el panel). El primero es el de una etiqueta nueva sin color.
LABEL_COLORS = ("slate", "blue", "violet", "pink", "red", "amber", "green", "teal")
DEFAULT_COLOR = LABEL_COLORS[0]


class LabelError(ValueError):
    """Un dato de la etiqueta no sirve. `field` dice cuál; el mensaje es para el negocio."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field


def clean_name(name: object) -> str:
    """El nombre como se guarda: sin caracteres invisibles ni de control, y con un solo espacio entre palabras."""
    visible = "".join(char for char in str(name or "") if unicodedata.category(char) not in ("Cf", "Cc", "Co", "Cs") or char in " \t")
    return " ".join(visible.split())


def label_key(name: object) -> str:
    """Cómo se lee el nombre: sin mayúsculas ni acentos. Dos etiquetas con la misma clave son la misma para el negocio."""
    plain = unicodedata.normalize("NFKD", clean_name(name))
    return "".join(char for char in plain if not unicodedata.combining(char)).casefold()


def checked_name(name: object) -> str:
    text = clean_name(name)
    if not text:
        raise LabelError("name", "Escribe el nombre de la etiqueta.")
    if len(text) > MAX_LABEL_NAME:
        raise LabelError("name", f"El nombre es muy largo (máximo {MAX_LABEL_NAME} caracteres).")
    return text


def checked_color(color: object) -> str:
    value = str(color or "").strip().lower() or DEFAULT_COLOR
    if value not in LABEL_COLORS:
        raise LabelError("color", "Elige uno de los colores.")
    return value


@dataclass(frozen=True)
class LabelRef:
    """Una etiqueta, como la lleva un cliente."""

    id: str
    name: str
    color: str


@dataclass(frozen=True)
class Label:
    """Una etiqueta del catálogo, con cuántos clientes la tienen."""

    id: str
    name: str
    color: str
    customers: int = 0
    created_at: datetime | None = None

    @property
    def ref(self) -> LabelRef:
        return LabelRef(self.id, self.name, self.color)


@dataclass(frozen=True)
class LabelChange:
    """Lo que cambia en una etiqueta, ya revisado: el nombre y/o el color (None, lo que no cambia)."""

    name: str | None = None
    color: str | None = None

    @classmethod
    def checked(cls, changes: dict[str, object]) -> LabelChange:
        change = cls(
            checked_name(changes["name"]) if "name" in changes else None,
            checked_color(changes["color"]) if "color" in changes else None,
        )
        if change.name is None and change.color is None:
            raise LabelError("name", "No hay nada que cambiar.")
        return change


def checked_selection(label_ids: object) -> list[str]:
    """Las etiquetas que el equipo le deja a un cliente: sin repetir y hasta el máximo."""
    if not isinstance(label_ids, (list, tuple)):
        raise LabelError("label_ids", "Elige las etiquetas.")
    chosen = list(dict.fromkeys(str(item).strip() for item in label_ids if str(item).strip()))
    if len(chosen) > MAX_LABELS_PER_CUSTOMER:
        raise LabelError("label_ids", f"Un cliente puede tener hasta {MAX_LABELS_PER_CUSTOMER} etiquetas.")
    return chosen
