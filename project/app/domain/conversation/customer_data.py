"""Los datos que el cliente ya dio en la conversación: su nombre, su teléfono, su negocio…

En un chat largo, un modelo pequeño pierde de vista lo que se dijo varios mensajes atrás y vuelve a pedir el nombre o el teléfono
(puerta de calidad, 15 nov 2026: 2 de 90 conversaciones, las dos en un chat largo). Por eso el motor no espera a que el asesor lo
encuentre en el historial: el asesor anota en su respuesta los datos que el cliente dio (`metadata.customer_data`,
`infrastructure/ai/prompting/output_contract.py`), el motor los guarda en la memoria del cliente (`turn_persistence.save_customer_data`) y se los
recuerda en cada mensaje (`prompting/sections/conversation.py`).

AI-first: qué dato dio el cliente lo entiende la IA; el código no lo busca por palabras. Aquí solo se ordena lo que anotó: el nombre
de cada dato en una forma (`phone` y `teléfono` son el mismo), los límites de largo y lo mínimo de datos personales:

- **De los datos de contacto** (teléfono, correo, documento, dirección) se guarda que los dio, no el valor. El asesor no lo necesita
  para atenderlo (está en el chat y el negocio lo ve en la bandeja) y, al verlo junto a los medios de pago, llegó a confundir el
  teléfono del cliente con el número de Nequi (producción, 13 nov 2026). Por lo mismo, un valor con un número largo (un celular, un
  documento) queda como dado, sin el número.
- **Los datos de pago del negocio nunca entran**: un valor que lleva uno no se guarda (`turn_persistence.save_customer_data`).
- **Se borran con la conversación** (`reset_conversation`, `forget_contact`): viven en la memoria del cliente, como el resumen.
"""
from __future__ import annotations

import re
import unicodedata

# Lo que se guarda en lugar del valor de un dato de contacto.
GIVEN = "dado"
# Cuántos datos se recuerdan de un cliente, y su largo máximo: lo justo para atenderlo sin llenar el prompt.
MAX_ITEMS = 12
MAX_NAME_CHARS = 30
MAX_VALUE_CHARS = 80

# El nombre de cada dato, en la forma que guarda la memoria y lee el asesor. Lo que no está aquí se guarda como lo escribió la IA.
_NAMES = {
    "nombre": "nombre", "name": "nombre", "nombre_completo": "nombre", "full_name": "nombre",
    "telefono": "teléfono", "phone": "teléfono", "celular": "teléfono", "whatsapp": "teléfono", "movil": "teléfono",
    "correo": "correo", "email": "correo", "correo_electronico": "correo", "mail": "correo",
    "documento": "documento", "document": "documento", "cedula": "documento", "dni": "documento",
    "direccion": "dirección", "address": "dirección",
    "ciudad": "ciudad", "city": "ciudad",
    "negocio": "negocio", "business": "negocio", "empresa": "negocio",
}
# Datos de contacto: se guarda que los dio, no el valor.
CONTACT = frozenset({"teléfono", "correo", "documento", "dirección"})
# Un número largo (7 cifras o más, con espacios o guiones): un celular, un documento o una cuenta. Un precio no («1.320.000»): lleva
# puntos o comas, como en `payment_data.py`.
_LONG_NUMBER = re.compile(r"\+?\d(?:[ -]?\d){6,}")


def _plain(text: str) -> str:
    """`Teléfono celular` → `telefono_celular`: la forma con la que se busca el nombre del dato."""
    letters = "".join(char for char in unicodedata.normalize("NFKD", text.strip().lower()) if not unicodedata.combining(char))
    return "_".join(letters.replace("_", " ").split())


def data_name(raw: object) -> str:
    """El nombre del dato en la forma que guarda la memoria: «teléfono» por `phone`, `Telefono` o `celular`; el resto, tal cual."""
    text = " ".join(str(raw or "").replace("_", " ").split())[:MAX_NAME_CHARS]
    return _NAMES.get(_plain(text), text.lower())


def _value(name: str, raw: object) -> str:
    value = " ".join(str(raw or "").split())
    if not value:
        return ""
    if name in CONTACT or _LONG_NUMBER.search(value):
        return GIVEN
    return value[:MAX_VALUE_CHARS].strip()


def tidy(raw: object) -> dict[str, str]:
    """Lo que anotó el asesor, ordenado: cada dato con su nombre en una forma y su valor (o «dado»), sin vacíos."""
    if not isinstance(raw, dict):
        return {}
    data: dict[str, str] = {}
    for raw_name, raw_value in raw.items():
        name = data_name(raw_name)
        value = _value(name, raw_value)
        if name and value:
            data[name] = value
    return data


def merge(known: dict[str, str], given: dict[str, str]) -> dict[str, str]:
    """Lo que ya se sabía con lo nuevo: si corrige un dato, manda lo último que dijo. Después del límite no entran datos nuevos (los
    que ya están se siguen corrigiendo)."""
    merged = {name: value for name, value in (known or {}).items() if name and value}
    for name, value in given.items():
        if name in merged or len(merged) < MAX_ITEMS:
            merged[name] = value
    return merged


def described(data: dict[str, str]) -> str:
    """Para el asesor: «su nombre (Camila), su teléfono y su negocio (tienda de ropa)». "" si no dio ninguno."""
    items = [f"su {name}" if value == GIVEN else f"su {name} ({value})" for name, value in (data or {}).items() if name and value]
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} y {items[-1]}"
