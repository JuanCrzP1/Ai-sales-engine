"""«LO QUE VENDE»: cada plan o producto con su precio, lo que incluye y lo que no, y las condiciones.

Una línea por oferta, con su precio en palabras («COP 110.000 al mes»). Si todo cabe en `OFFER_PROMPT_MAX_CHARS`, va todo; si no, lo
más relacionado con lo que busca el cliente (`relevance.py`) y cuántas opciones más hay. Los argumentos de valor (retorno de la
inversión, cómo defender el precio) solo aplican a negocios que venden planes a otros negocios.
"""
from __future__ import annotations

from app.domain.business_config.engine_policy import MAX_CATEGORIES, OFFER_PROMPT_MAX_CHARS
from app.infrastructure.ai.prompting import relevance
from app.infrastructure.ai.prompting.money import plan_price, product_price
from app.infrastructure.ai.prompting.sections.playbook import business_kind
from app.infrastructure.ai.prompting.text import as_dict, as_list, as_text, dicts, one_line, section, sentence, texts
from app.infrastructure.ai.prompting.view import PromptView

HEADER = "LO QUE VENDE"
# Cómo defender el precio, según lo que eligió el negocio (`terms.price_framing`).
_FRAMING = {
    "comparativo": "Si duda por el precio, pregúntale cuánto le cuesta hoy no tenerlo.",
    "directo": "Si duda por el precio, dile con claridad cuánto cuesta y qué recibe, sin rodeos.",
}
MORE_OFFERS = "Hay {count} opciones más que no aparecen aquí: si el cliente busca algo distinto, pregúntale qué necesita y no inventes."


def _line(offer: dict, price: str) -> str:
    name = as_text(offer.get("name") or offer.get("id"))
    details = [sentence(one_line(offer.get("description")))] if one_line(offer.get("description")) else []
    if texts(offer.get("features")):
        details.append(sentence(f"Características: {', '.join(texts(offer.get('features')))}"))
    if texts(offer.get("includes")):
        details.append(sentence(f"Incluye: {', '.join(texts(offer.get('includes')))}"))
    if texts(offer.get("not_included")):
        details.append(sentence(f"No incluye: {', '.join(texts(offer.get('not_included')))}"))
    head = f"{name} — {price}" if price else name
    return f"{head}: {' '.join(details)}" if details else head


def _about(offer: dict) -> str:
    """Las palabras de una oferta para compararlas con lo que busca el cliente."""
    return " ".join([as_text(offer.get("name")), as_text(offer.get("description")), *texts(offer.get("features")), as_text(offer.get("category"))])


def _value_lines(pricing: dict) -> list[str]:
    framing = as_text(as_dict(pricing.get("price_framing")).get("type")).lower()
    break_even = as_dict(pricing.get("roi")).get("break_even_sales")
    hints = texts(pricing.get("roi_hints"))
    lines = []
    if framing in _FRAMING:
        lines.append(_FRAMING[framing])
    if break_even is not None:
        lines.append(f"Argumento de valor: con {break_even} ventas al mes el cliente recupera lo que paga.")
    elif hints:
        lines.append(sentence(f"Argumento de valor: {hints[0]}"))
    return lines


def render(view: PromptView) -> str:
    pricing = view.pricing
    show_prices = bool(view.features.get("pricing_enabled", True))
    plans, items = dicts(pricing.get("plans")), dicts(as_dict(pricing.get("catalog")).get("items"))
    entries = [(_line(plan, plan_price(plan.get("pricing")) if show_prices else ""), _about(plan)) for plan in plans if as_text(plan.get("name") or plan.get("id"))]
    entries += [(_line(item, product_price(item.get("price")) if show_prices else ""), _about(item)) for item in items if as_text(item.get("name") or item.get("id"))]
    shown = relevance.select(entries, size=lambda entry: len(entry[0]) + 3, text=lambda entry: entry[1], query=view.relevance_query, max_chars=OFFER_PROMPT_MAX_CHARS)
    lines = [f"- {line}" for line, _about_offer in shown]
    if len(shown) < len(entries):
        lines.append(f"- {MORE_OFFERS.format(count=len(entries) - len(shown))}")
    categories = [name for category in dicts(as_dict(pricing.get("catalog")).get("categories")) if (name := as_text(category.get("name") or category.get("id")))]
    if categories:
        lines.append(sentence(f"Categorías: {', '.join(categories[:MAX_CATEGORIES])}"))
    conditions = texts(pricing.get("conditions"))
    if conditions:
        lines.append(sentence(f"Condiciones: {', '.join(conditions)}"))
    if not show_prices:
        lines.append("Los precios los confirma el equipo: no des valores.")
    if business_kind(view) == "plans":
        lines += _value_lines(pricing)
    return section(HEADER, lines)
