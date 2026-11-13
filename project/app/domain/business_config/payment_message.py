"""El mensaje con los datos de pago: lo escribe el sistema, nunca la IA, a partir de una plantilla que el negocio puede editar.

La IA nunca ve los números de pago (se equivocaría en un dígito o los daría a quien no debe): cuando el cliente elige cómo pagar, el
motor arma este mensaje con los datos reales. La plantilla usa marcadores:

- `{medio}`: Nequi, Daviplata, el banco, Bre-B o «Pago en línea».
- `{datos}`: el número, la cuenta, la llave o el enlace, cada uno en su línea para copiarlo con un toque.
- `{titular}`: a nombre de quién está la cuenta (si el negocio lo escribió).

Una línea cuyo marcador quedó vacío no se envía (sin titular, no sale «A nombre de:»). `{datos}` es obligatorio: sin él el
cliente no sabría a dónde pagar. El panel repite estas reglas para la vista previa (`apps/admin-web/src/domain/config/paymentMessage.ts`).
"""
from __future__ import annotations

import re

PLACEHOLDERS: tuple[str, ...] = ("medio", "datos", "titular")
REQUIRED_PLACEHOLDER = "datos"
DEFAULT_PAYMENT_DETAILS = (
    "💳 *Datos para pagar*\n"
    "\n"
    "*{medio}*\n"
    "{datos}\n"
    "A nombre de: {titular}\n"
    "\n"
    "Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅"
)
_PLACEHOLDER = re.compile(r"\{([^{}]*)\}")
_METHOD_NAMES = {"nequi": "Nequi", "daviplata": "Daviplata", "breb": "Bre-B", "link": "Pago en línea"}
_ACCOUNT_TYPES = {"ahorros": "Cuenta de ahorros", "corriente": "Cuenta corriente"}


def template_problem(template: str) -> str | None:
    """Por qué la plantilla no sirve (para el negocio), o None si sirve."""
    names = _PLACEHOLDER.findall(template)
    unknown = sorted({name for name in names if name not in PLACEHOLDERS})
    if unknown:
        return f"La plantilla tiene un marcador que no existe: {{{unknown[0]}}}. Usa {{medio}}, {{datos}} o {{titular}}."
    if REQUIRED_PLACEHOLDER not in names:
        return "La plantilla debe tener {datos}: ahí van el número, la cuenta o el enlace para pagar."
    return None


def method_parts(method_type: str, details: dict) -> tuple[str, str]:
    """El medio y los datos de un método de pago ya resueltos (con los valores reales), o ("", "") si le falta algo."""
    kind = str(method_type or "").strip().lower()
    if kind == "link":
        link = str(details.get("link") or "").strip()
        return (_METHOD_NAMES["link"], link) if link else ("", "")
    if kind in ("nequi", "daviplata"):
        number = str(details.get("number") or "").strip()
        return (_METHOD_NAMES[kind], number) if number else ("", "")
    if kind == "bank":
        bank = str(details.get("bank") or "").strip()
        account_type = str(details.get("account_type") or "").strip()
        account_number = str(details.get("account_number") or "").strip()
        if not (bank and account_type and account_number):
            return "", ""
        return bank, f"{_ACCOUNT_TYPES.get(account_type.lower(), f'Cuenta {account_type}')}\n{account_number}"
    if kind == "breb":
        reference = str(details.get("reference") or "").strip()
        return (_METHOD_NAMES["breb"], f"Llave: {reference}") if reference else ("", "")
    return "", ""


def render_payment_details(template: str | None, *, medio: str, datos: str, titular: str = "") -> str:
    """El mensaje para el cliente. Sin plantilla propia (o con una que no sirve), el de la plataforma."""
    chosen = template if template and template.strip() and template_problem(template) is None else DEFAULT_PAYMENT_DETAILS
    values = {"medio": medio.strip(), "datos": datos.strip(), "titular": titular.strip()}
    lines: list[str] = []
    for line in chosen.strip().split("\n"):
        names = _PLACEHOLDER.findall(line)
        if any(not values.get(name) for name in names):
            continue  # p. ej., «A nombre de: {titular}» sin titular
        lines.append(_PLACEHOLDER.sub(lambda match: values[match.group(1)], line).rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
