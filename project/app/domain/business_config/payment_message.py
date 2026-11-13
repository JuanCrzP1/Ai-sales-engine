"""El mensaje con los datos de pago: lo escribe el sistema, nunca la IA, a partir de una plantilla que el negocio puede editar.

La IA nunca ve los números de pago (se equivocaría en un dígito o los daría a quien no debe): cuando el cliente elige cómo pagar, el
motor arma este mensaje con los datos reales. La plantilla usa marcadores:

- `{medio}`: el nombre del medio (Nequi, Yape, el banco, PayPal…) o «Pago en línea».
- `{datos}`: el número, la cuenta, la llave o el enlace, cada uno en su línea para copiarlo con un toque.
- `{titular}`: a nombre de quién está la cuenta (si el negocio lo escribió).
- `{instrucciones}`: lo que el negocio quiere que el cliente sepa al pagar por ese medio (si lo escribió).

Una línea cuyo marcador quedó vacío no se envía (sin titular, no sale «A nombre de:»). `{datos}` es obligatorio: sin él el
cliente no sabría a dónde pagar. El panel repite estas reglas para la vista previa (`apps/admin-web/src/domain/config/paymentMessage.ts`).
"""
from __future__ import annotations

import re

from app.domain.business_config.payment_catalog import DEFAULT_CASH_TEXT, method_kind

PLACEHOLDERS: tuple[str, ...] = ("medio", "datos", "titular", "instrucciones")
REQUIRED_PLACEHOLDER = "datos"
DEFAULT_PAYMENT_DETAILS = (
    "💳 *Datos para pagar*\n"
    "\n"
    "*{medio}*\n"
    "{datos}\n"
    "A nombre de: {titular}\n"
    "{instrucciones}\n"
    "\n"
    "Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅"
)
# El efectivo no tiene comprobante: con la plantilla de la plataforma, el cliente recibe cómo pagar y que se le confirma por aquí.
DEFAULT_CASH_DETAILS = (
    "💵 *Cómo pagar*\n"
    "\n"
    "*{medio}*\n"
    "{datos}\n"
    "\n"
    "Cualquier duda, escríbeme por aquí. ✅"
)
_PLACEHOLDER = re.compile(r"\{([^{}]*)\}")
LINK_NAME = "Pago en línea"
_ACCOUNT_TYPES = {"ahorros": "Cuenta de ahorros", "corriente": "Cuenta corriente"}


def template_problem(template: str) -> str | None:
    """Por qué la plantilla no sirve (para el negocio), o None si sirve."""
    names = _PLACEHOLDER.findall(template)
    unknown = sorted({name for name in names if name not in PLACEHOLDERS})
    if unknown:
        return f"La plantilla tiene un marcador que no existe: {{{unknown[0]}}}. Usa {{medio}}, {{datos}}, {{titular}} o {{instrucciones}}."
    if REQUIRED_PLACEHOLDER not in names:
        return "La plantilla debe tener {datos}: ahí van el número, la cuenta o el enlace para pagar."
    return None


def method_parts(method_type: str, details: dict) -> tuple[str, str]:
    """El medio y los datos de un método de pago ya resueltos (con los valores reales), o ("", "") si le falta algo. Lo arma el
    catálogo (`payment_catalog.py`): el nombre, y el dato como sale en el mensaje («Llave: …», «CLABE: …»)."""
    method = str(method_type or "").strip().lower()
    if method == "link":
        link = str(details.get("link") or "").strip()
        return (LINK_NAME, link) if link else ("", "")
    kind = method_kind(method)
    if kind is None:
        return "", ""
    if kind.data is None:  # efectivo: la instrucción del negocio es lo que el cliente necesita saber
        return kind.name, str(details.get("instructions") or "").strip() or DEFAULT_CASH_TEXT
    value = str(details.get(kind.data.slot) or "").strip()
    if not value:
        return "", ""
    if kind.needs_bank:
        bank = str(details.get("bank") or "").strip()
        account_type = str(details.get("account_type") or "").strip()
        if not (bank and account_type):
            return "", ""
        return bank, f"{_ACCOUNT_TYPES.get(account_type.lower(), f'Cuenta {account_type}')}\n{value}"
    if kind.custom:
        name, label = str(details.get("name") or "").strip(), str(details.get("data_label") or "").strip()
        return (name, f"{label}: {value}" if label else value) if name else ("", "")
    return kind.name, kind.data.shown_as.format(value=value)


def render_payment_details(template: str | None, *, medio: str, datos: str, titular: str = "", instrucciones: str = "") -> str:
    """El mensaje para el cliente. Sin plantilla propia (o con una que no sirve), el de la plataforma. Si la plantilla del negocio no
    tiene {instrucciones} y el medio tiene una, va al final: el cliente nunca se queda sin ella."""
    chosen = template if template and template.strip() and template_problem(template) is None else DEFAULT_PAYMENT_DETAILS
    values = {"medio": medio.strip(), "datos": datos.strip(), "titular": titular.strip(), "instrucciones": instrucciones.strip()}
    lines: list[str] = []
    for line in chosen.strip().split("\n"):
        names = _PLACEHOLDER.findall(line)
        if any(not values.get(name) for name in names):
            continue  # p. ej., «A nombre de: {titular}» sin titular
        lines.append(_PLACEHOLDER.sub(lambda match: values[match.group(1)], line).rstrip())
    message = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    if values["instrucciones"] and "{instrucciones}" not in chosen:
        message = f"{message}\n\n{values['instrucciones']}"
    return message
