"""Variantes y existencias de un producto del catálogo, en palabras: «talla S, color blanco; talla M, color blanco (agotada)».

Si el negocio controla existencias (`inventory.track_stock`), una variante sin unidades va «agotada» y un producto sin ninguna, agotado.
Nunca se dice cuántas unidades quedan, y el código interno de la variante (`sku`) es solo para el equipo: no va a la IA.
"""
from __future__ import annotations

from app.infrastructure.ai.prompting.money import product_price
from app.infrastructure.ai.prompting.text import as_dict, as_text, dicts, sentence
from app.infrastructure.ai.prompting.vocabulary import ATTRIBUTES, said

SOLD_OUT = "Agotado por ahora: no lo ofrezcas como disponible."


def by_product(inventory: dict) -> dict[str, list[dict]]:
    """Las variantes de cada producto, por su id."""
    return {product: dicts(item.get("variants")) for item in dicts(inventory.get("items")) if (product := as_text(item.get("product_id")))}


def _attributes(variant: dict) -> str:
    return ", ".join(f"{said(key, ATTRIBUTES)} {as_text(value)}" for key, value in as_dict(variant.get("attributes")).items() if as_text(value))


def _price(variant: dict, currencies: set[str] | None) -> str:
    """El precio propio de la variante, solo si el negocio lo escribió (si no, vale lo mismo que el producto)."""
    prices = {currency: price.get("amount") for price in dicts(variant.get("prices")) if (currency := as_text(price.get("currency")))}
    return product_price({currency: value for currency, value in prices.items() if currencies is None or currency in currencies})


def describe(variants: list[dict], *, track_stock: bool, currencies: set[str] | None = None) -> list[str]:
    """Las frases que van en la línea del producto: sus opciones y, si se acabaron todas, que está agotado."""
    options: list[str] = []
    sold_out = 0
    for variant in variants:
        name = _attributes(variant)
        if not name:
            continue
        price = _price(variant, currencies)
        empty = track_stock and isinstance(variant.get("stock"), int) and variant["stock"] <= 0
        sold_out += empty
        options.append(name + (f" ({price})" if price else "") + (" (agotada)" if empty else ""))
    if not options:
        return []
    lines = [sentence(f"Opciones: {'; '.join(options)}")]
    if sold_out == len(options):
        lines.append(SOLD_OUT)
    return lines
