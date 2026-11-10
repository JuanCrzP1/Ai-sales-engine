"""«LO QUE VENDE»: cada plan o producto con su precio, lo que incluye y lo que no, sus opciones y existencias, y las condiciones.

Una línea por oferta, con su precio en palabras («COP 110.000 al mes»). Si todo cabe en `OFFER_PROMPT_MAX_CHARS`, va todo; si no, lo
más relacionado con lo que busca el cliente (`relevance.py`) y cuántas opciones más hay. Los argumentos de valor (retorno de la
inversión, cómo defender el precio) solo aplican a negocios que venden planes a otros negocios.

Los interruptores del negocio (`config.features`) deciden si se dan precios (`pricing_enabled`), si van en todas sus monedas o solo en
la primera (`multi_currency`) y si se recomienda un solo plan (`multi_plan`).
"""
from __future__ import annotations

from app.domain.business_config.engine_policy import MAX_CATEGORIES, OFFER_PROMPT_MAX_CHARS
from app.infrastructure.ai.prompting import inventory, relevance
from app.infrastructure.ai.prompting.money import plan_price, product_price
from app.infrastructure.ai.prompting.sections.playbook import business_kind
from app.infrastructure.ai.prompting.text import as_dict, as_text, dicts, one_line, readable, section, sentence, texts
from app.infrastructure.ai.prompting.view import PromptView

HEADER = "LO QUE VENDE"
# Cómo defender el precio, según lo que eligió el negocio (`terms.price_framing`).
_FRAMING = {
    "comparativo": "Si duda por el precio, pregúntale cuánto le cuesta hoy no tenerlo.",
    "directo": "Si duda por el precio, dile con claridad cuánto cuesta y qué recibe, sin rodeos.",
}
MORE_OFFERS = "Hay {count} opciones más que no aparecen aquí: si el cliente busca algo distinto, pregúntale qué necesita y no inventes."
ONE_PLAN = "Recomienda un solo plan, el que mejor encaje con lo que necesita; no le muestres todos."
# Tipos de oferta del negocio (`sales.offer_mix`): texto libre, no ids. Solo se sugiere lo que de verdad está en «LO QUE VENDE».
_MIX = (
    ("core", "Lo principal que vende"),
    ("upsell", "Mejoras que puedes sugerir (solo si están en lo que vende)"),
    ("cross_sell", "Complementos que puedes sugerir con la compra (solo si están en lo que vende)"),
)


def _line(offer: dict, price: str, extra: list[str]) -> str:
    name = as_text(offer.get("name") or offer.get("id"))
    details = [sentence(one_line(offer.get("description")))] if one_line(offer.get("description")) else []
    if one_line(offer.get("target")):
        details.append(sentence(f"Para: {one_line(offer.get('target'))}"))
    if texts(offer.get("features")):
        details.append(sentence(f"Características: {', '.join(texts(offer.get('features')))}"))
    if texts(offer.get("includes")):
        details.append(sentence(f"Incluye: {', '.join(texts(offer.get('includes')))}"))
    if texts(offer.get("not_included")):
        details.append(sentence(f"No incluye: {', '.join(texts(offer.get('not_included')))}"))
    details += extra
    head = f"{name} — {price}" if price else name
    return f"{head}: {' '.join(details)}" if details else head


def _about(offer: dict) -> str:
    """Las palabras de una oferta para compararlas con lo que busca el cliente."""
    return " ".join([as_text(offer.get("name")), as_text(offer.get("description")), *texts(offer.get("features")), as_text(offer.get("category"))])


def _currencies(prices: dict, every: bool) -> dict:
    """Todas las monedas de un precio o, si el negocio no maneja varias, solo la primera."""
    return prices if every else dict(list(prices.items())[:1])


def _value_lines(pricing: dict) -> list[str]:
    framing = as_text(as_dict(pricing.get("price_framing")).get("type")).lower()
    roi = as_dict(pricing.get("roi"))
    hints = texts(pricing.get("roi_hints"))
    lines = []
    if framing in _FRAMING:
        lines.append(_FRAMING[framing])
    if roi.get("break_even_sales") is not None:
        lines.append(f"Argumento de valor: con {roi['break_even_sales']} ventas al mes el cliente recupera lo que paga.")
    elif roi.get("break_even_reservas") is not None:
        lines.append(f"Argumento de valor: con {roi['break_even_reservas']} reservas el cliente recupera lo que paga.")
    elif hints:
        lines.append(sentence(f"Argumento de valor: {hints[0]}"))
    return lines


def _entries(view: PromptView, show_prices: bool) -> list[tuple[str, str]]:
    pricing, features = view.pricing, view.features
    every_currency = features.get("multi_currency") is not False
    variants, track_stock = inventory.by_product(view.inventory), view.inventory.get("track_stock") is True
    entries = []
    for plan in dicts(pricing.get("plans")):
        if as_text(plan.get("name") or plan.get("id")):
            price = plan_price(_currencies(as_dict(plan.get("pricing")), every_currency)) if show_prices else ""
            entries.append((_line(plan, price, []), _about(plan)))
    for item in dicts(as_dict(pricing.get("catalog")).get("items")):
        if as_text(item.get("name") or item.get("id")):
            prices = _currencies(as_dict(item.get("price")), every_currency)
            extra = inventory.describe(variants.get(as_text(item.get("id")), []), track_stock=track_stock, currencies=set(prices) if show_prices else set())
            entries.append((_line(item, product_price(prices) if show_prices else "", extra), _about(item)))
    return entries


def render(view: PromptView) -> str:
    pricing = view.pricing
    show_prices = bool(view.features.get("pricing_enabled", True))
    entries = _entries(view, show_prices)
    shown = relevance.select(entries, size=lambda entry: len(entry[0]) + 3, text=lambda entry: entry[1], query=view.relevance_query, max_chars=OFFER_PROMPT_MAX_CHARS)
    lines = [f"- {line}" for line, _about_offer in shown]
    if len(shown) < len(entries):
        lines.append(f"- {MORE_OFFERS.format(count=len(entries) - len(shown))}")
    if view.features.get("multi_plan") is False and len(dicts(pricing.get("plans"))) > 1:
        lines.append(ONE_PLAN)
    categories = [name for category in dicts(as_dict(pricing.get("catalog")).get("categories")) if (name := as_text(category.get("name") or category.get("id")))]
    if categories:
        lines.append(sentence(f"Categorías: {', '.join(categories[:MAX_CATEGORIES])}"))
    mix = as_dict(pricing.get("business_offers"))
    lines += [sentence(f"{label}: {', '.join(readable(item) for item in texts(mix.get(key)))}") for key, label in _MIX if texts(mix.get(key))]
    conditions = texts(pricing.get("conditions"))
    if conditions:
        lines.append(sentence(f"Condiciones: {', '.join(conditions)}"))
    note = one_line(pricing.get("note"))
    if note:
        lines.append(sentence(f"Sobre el precio: {note}"))
    if not show_prices:
        lines.append("Los precios los confirma el equipo: no des valores.")
    if business_kind(view) == "plans":
        lines += _value_lines(pricing)
    return section(HEADER, lines)
