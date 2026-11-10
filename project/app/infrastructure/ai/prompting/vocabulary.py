"""Los identificadores que guarda el panel (`detect_pain`, `license_type`, `price`), dichos en español para la IA.

Lo que no está en estas tablas se dice tal cual, con espacios en lugar de `_` (`text.readable`): un negocio puede escribir sus propios
pasos, datos u objeciones y el motor los usa igual.
"""
from __future__ import annotations

import unicodedata
from collections.abc import Iterable

from app.infrastructure.ai.prompting.text import as_text, dedupe, readable

# Pasos de la conversación (`sales.conversation_flow.steps` y `required_flow`).
STEPS = {
    "detect_pain": "entender qué necesita",
    "amplify_impact": "mostrarle lo que le cuesta no resolverlo",
    "present_solution": "presentarle la opción que lo resuelve",
    "validate_requirements": "revisar que cumpla los requisitos",
    "guide_next_step": "guiarlo al siguiente paso",
}
# Lo que el negocio no quiere que haga el asistente (`sales.conversation_flow.forbid`).
FORBIDDEN = {
    "responder_sin_direccion": "responder sin llevar la conversación a un siguiente paso",
    "responder_sin_solucion": "responder sin ofrecer una solución",
}
# Temas de objeción (`sales.objections[].topic`).
OBJECTIONS = {
    "price": "el precio", "precio": "el precio", "time": "el tiempo", "tiempo": "el tiempo", "trust": "la confianza",
    "confianza": "la confianza", "competition": "la competencia", "competencia": "la competencia",
}
# Datos que se piden al cliente (`capabilities.data_collection.fields` y `sales.closing.required_data`).
DATA = {
    "name": "nombre", "nombre": "nombre", "phone": "teléfono", "telefono": "teléfono", "address": "dirección", "direccion": "dirección",
    "email": "correo", "correo": "correo", "city": "ciudad", "ciudad": "ciudad", "day": "día", "dia": "día", "hour": "hora",
    "hora": "hora", "date": "fecha", "fecha": "fecha", "dates": "fechas", "fechas": "fechas", "destination": "destino",
    "destino": "destino", "details": "detalles", "detalles": "detalles", "license_type": "tipo de licencia", "document": "documento",
    "documento": "documento",
}
# Características de una variante (`inventory.items[].variants[].attributes`).
ATTRIBUTES = {"size": "talla", "talla": "talla", "color": "color", "colour": "color"}
# Alcance de un envío (`fulfillment.shipping.scope`).
SCOPES = {"local": "locales", "nacional": "nacionales", "internacional": "internacionales"}


def _key(value: str) -> str:
    """`Teléfono` → `telefono`: la clave con la que se busca en las tablas."""
    plain = "".join(char for char in unicodedata.normalize("NFKD", value.strip().lower()) if not unicodedata.combining(char))
    return plain.replace(" ", "_")


def said(identifier: object, names: dict[str, str]) -> str:
    """El identificador en español: el de la tabla o, si no está, legible tal cual."""
    text = as_text(identifier)
    return names.get(_key(text)) or readable(text)


def said_all(identifiers: Iterable[object], names: dict[str, str]) -> list[str]:
    """Cada identificador en español, sin repetidos (`telefono` y `phone` son el mismo dato)."""
    return dedupe(said(identifier, names) for identifier in identifiers)


def quoted(phrases: Iterable[str]) -> str:
    """«quiero pedir», «lo quiero»: frases del cliente o del negocio, tal como se escribieron."""
    return ", ".join(f"«{phrase}»" for phrase in phrases if phrase)


def joined(items: list[str], *, last: str = "y") -> str:
    """«a», «a y b», «a, b y c»."""
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} {last} {items[-1]}"
