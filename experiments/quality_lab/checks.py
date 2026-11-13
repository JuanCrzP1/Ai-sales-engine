"""Revisiones exactas de cada respuesta: lo que se puede comprobar sin opinión."""
from __future__ import annotations

import re

from facts import known_amounts

PAYMENT_PLACEHOLDER = "[dato de pago]"
# Montos: «$18.000», «18000 COP», «18 mil», «110.000 pesos». Los números de 8 o más cifras seguidas son teléfonos o cuentas.
_MONEY = re.compile(
    r"(?:\$\s*(\d{1,3}(?:[.,]\d{3})+|\d+))|(\d{1,3}(?:[.,]\d{3})+|\d{4,7})\s*(?:cop|usd|pesos|d[oó]lares)?|(\d{1,3})\s*mil\b",
    re.IGNORECASE,
)


def _amounts(text: str) -> set[int]:
    found: set[int] = set()
    for match in _MONEY.finditer(text):
        dollars, number, thousands = match.groups()
        raw = dollars or number
        if raw:
            value = int(re.sub(r"[.,]", "", raw))
            if value >= 1000:
                found.add(value)
        elif thousands:
            found.add(int(thousands) * 1000)
    return found


# Un dato de pago real en la respuesta: un número largo (celular o cuenta), un enlace, una llave o la marca con la que el laboratorio
# oculta el dato que entregó el motor.
_PAYMENT_DATA = re.compile(r"\d{8,}|https?://|llave|\[dato entregado por el motor\]", re.IGNORECASE)
# Los turnos en los que el cliente necesita los datos de pago: los eligió o los pidió otra vez.
PAYMENT_DATA_TURNS = ("metodo", "reenvio_pago")
# Los turnos en los que no debe llegarle ningún dato de pago: solo pregunta si puede pagar con un medio, o no entendió algo.
NO_PAYMENT_DATA_TURNS = ("pregunta_medio", "aclaracion_pago")
ENGINE_DATA = "[dato entregado por el motor]"
# Así empieza el mensaje con los datos de pago (la plantilla de la plataforma).
_DETAILS_START = ("💳", "💵")


def check_turn(reply: str, *, facts: dict, previous_reply: str, ai_used: bool, format_error: str, kind: str = "") -> dict:
    known = known_amounts(facts)
    # Válido: un precio publicado, la suma de dos (implementación más el primer mes) o un precio por una cantidad de hasta 10.
    allowed = known | {a + b for a in known for b in known} | {a * quantity for a in known for quantity in range(2, 11)}
    invented = sorted(amount for amount in _amounts(reply) if amount not in allowed)
    max_words = int(facts.get("max_palabras") or 80)
    return {
        "precios_inventados": invented,
        "marcador_de_pago_visible": PAYMENT_PLACEHOLDER in reply,
        "sin_ia": not ai_used,
        "formato_imperfecto": bool(format_error),
        "demasiado_larga": len(reply.split()) > max_words + 5,
        "varias_preguntas": reply.count("?") > 2,
        "repite_respuesta_anterior": bool(previous_reply) and reply.strip() == previous_reply.strip(),
        # Pidió los datos para pagar y no le llegaron (como «Cuando lo hagas, avísame» sin el número).
        "datos_de_pago_faltantes": kind in PAYMENT_DATA_TURNS and not _PAYMENT_DATA.search(reply),
        # Preguntó si puede pagar con un medio, o no entendió algo, y le llegó una cuenta («¿puedo transferir?» → la cuenta).
        "datos_de_pago_sin_pedir": kind in NO_PAYMENT_DATA_TURNS and ENGINE_DATA in reply,
        # Le llegaron los datos de pago sin una palabra del asesor: el mensaje es solo la plantilla.
        "asesor_callado": ENGINE_DATA in reply and reply.lstrip().startswith(_DETAILS_START),
    }


def violations(check: dict) -> int:
    return sum(1 for key, value in check.items() if (bool(value) if not isinstance(value, list) else bool(value)))
