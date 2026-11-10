"""Precios en palabras para la IA: «COP 110.000 al mes», como los diría un vendedor en Colombia."""
from __future__ import annotations

from app.infrastructure.ai.prompting.text import as_dict, as_text

# Campos de precio de un plan, en el orden en que se dicen.
PLAN_FIELDS = (("implementation", "{amount} de implementación"), ("first_payment", "primer pago de {amount}"), ("monthly", "{amount} al mes"),
               ("annual", "{amount} al año"), ("price", "{amount}"))


def amount(currency: str, value: object) -> str:
    """`COP 18.000`, `USD 45`, `USD 9,99`."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return f"{as_text(currency).upper()} {as_text(value)}".strip()
    whole = f"{int(number):,}".replace(",", ".")
    cents = round((number - int(number)) * 100)
    return f"{as_text(currency).upper()} {whole}" + (f",{cents:02d}" if cents else "")


def plan_price(pricing: object) -> str:
    """Todas las monedas de un plan: «COP 100.000 de implementación + COP 110.000 al mes · USD 40 + USD 45 al mes»."""
    by_currency = []
    for currency, values in as_dict(pricing).items():
        values = as_dict(values)
        parts = [template.format(amount=amount(currency, values[field])) for field, template in PLAN_FIELDS if values.get(field) not in (None, "")]
        if parts:
            by_currency.append(" + ".join(parts))
    return " · ".join(by_currency)


def product_price(price: object) -> str:
    """«COP 18.000» o, en varias monedas, «COP 18.000 · USD 5»."""
    return " · ".join(amount(currency, value) for currency, value in as_dict(price).items() if value not in (None, ""))
