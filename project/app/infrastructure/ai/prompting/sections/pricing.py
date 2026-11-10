"""Precios y pagos: qué se cobra, cuánto, condiciones, y las reglas para llevar al cliente a pagar.

Los datos de pago (links, números, cuentas) aparecen aquí solo para que el compositor los reemplace por su marcador antes de que el
prompt salga: la IA nunca los ve; el motor los entrega al cliente cuando elige el método (`ejecutar_pago`).

La lista de precios va entera si cabe en `PRICE_LIST_PROMPT_MAX_CHARS`; si no, la de lo más relacionado con lo que busca el cliente,
con el mismo criterio que el detalle de la oferta del perfil, y cuántos precios quedan por fuera.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.business_config.engine_policy import MAX_CATEGORIES, PRICE_LIST_PROMPT_MAX_CHARS
from app.infrastructure.ai.prompting import instructions, relevance
from app.infrastructure.ai.prompting.text import as_dict, as_list, as_text
from app.infrastructure.ai.prompting.view import PromptView

PRICE_FIELDS = ("implementation", "monthly", "first_payment", "price")


def _transfer_method_line(raw_method: object) -> str:
    method = as_dict(raw_method)
    kind = as_text(method.get("type", "")).lower()
    if kind in {"nequi", "daviplata"}:
        number = as_text(method.get("number", ""))
        return f"- {kind}: {number}" if number else ""
    if kind == "bank":
        details = [as_text(method.get(name, "")) for name in ("bank", "account_type", "account_number")]
        return f"- bank: {' / '.join(details)}" if all(details) else ""
    if kind == "breb":
        reference = as_text(method.get("reference", ""))
        return f"- breb: {reference}" if reference else ""
    return ""


def _transfer_lines(raw_payment: object) -> list[str]:
    transfer = as_dict(as_dict(raw_payment).get("transfer"))
    if not bool(transfer.get("enabled", False)):
        return []
    return [line for item in as_list(transfer.get("methods")) if (line := _transfer_method_line(item))]


@dataclass
class _Offer:
    """Lo que se lee de la oferta para hablar de precio y pago."""

    plan_names: list[str] = field(default_factory=list)
    # (línea de precio, de qué trata la oferta): lo segundo decide la relevancia cuando no caben todas.
    plan_prices: list[tuple[str, str]] = field(default_factory=list)
    product_names: list[str] = field(default_factory=list)
    product_prices: list[tuple[str, str]] = field(default_factory=list)
    category_names: list[str] = field(default_factory=list)
    includes: list[str] = field(default_factory=list)
    not_included: list[str] = field(default_factory=list)
    payment_links: list[str] = field(default_factory=list)
    transfer_lines: list[str] = field(default_factory=list)

    def add_transfers(self, payment: object) -> None:
        for line in _transfer_lines(payment):
            if line not in self.transfer_lines:
                self.transfer_lines.append(line)


def _about(offer: dict) -> str:
    """Las palabras de una oferta para compararlas con lo que busca el cliente: nombre, descripción, características y categoría."""
    return " ".join([as_text(offer.get("name")), as_text(offer.get("description")), *map(as_text, as_list(offer.get("features"))), as_text(offer.get("category"))])


def _add_unique(target: list[str], values: object) -> None:
    for value in as_list(values):
        text = as_text(value)
        if text and text not in target:
            target.append(text)


def _read_offer(pricing: dict) -> _Offer:
    offer = _Offer()
    for plan in as_list(pricing.get("plans", [])):
        if not isinstance(plan, dict):
            continue
        name = as_text(plan.get("name", "") or plan.get("id", ""))
        if name:
            offer.plan_names.append(name)
        payment = as_dict(plan.get("payment"))
        link = as_text(payment.get("link", ""))
        if link:
            offer.payment_links.append(f"{name or 'oferta'}: {link}")
        offer.add_transfers(payment)
        _add_unique(offer.includes, plan.get("includes", []))
        _add_unique(offer.not_included, plan.get("not_included", []))
        currencies = []
        for currency, values in as_dict(plan.get("pricing")).items():
            if not isinstance(values, dict):
                continue
            chunks = [f"{name_}={values.get(name_)}" for name_ in PRICE_FIELDS if values.get(name_) not in (None, "")]
            if chunks:
                currencies.append(f"{as_text(currency).upper()}: {', '.join(chunks)}")
        if currencies:
            offer.plan_prices.append((f"{name or 'oferta'} -> {' | '.join(currencies)}", _about(plan)))

    catalog = as_dict(pricing.get("catalog"))
    for item in as_list(catalog.get("items", [])):
        if not isinstance(item, dict):
            continue
        name = as_text(item.get("name", "") or item.get("id", ""))
        if name:
            offer.product_names.append(name)
        amounts = [f"{as_text(currency).upper()}: {amount}" for currency, amount in as_dict(item.get("price")).items() if amount not in (None, "")]
        if name and amounts:
            offer.product_prices.append((f"{name} -> {' | '.join(amounts)}", _about(item)))

    catalog_payment = as_dict(catalog.get("payment"))
    catalog_link = as_text(catalog_payment.get("link", ""))
    if catalog_link:
        offer.payment_links.append(f"catálogo: {catalog_link}")
    offer.add_transfers(catalog_payment)

    root_payment = as_dict(pricing.get("payment"))
    root_link = as_text(root_payment.get("link", ""))
    if root_link:
        offer.payment_links.append(root_link)
    offer.add_transfers(root_payment)

    for category in as_list(catalog.get("categories", [])):
        if isinstance(category, dict) and (name := as_text(category.get("name", "") or category.get("id", ""))):
            offer.category_names.append(name)
    return offer


def _payment_lines(offer: _Offer) -> list[str]:
    """Las reglas de pago: siempre presentes, porque controlan cuándo se entregan los datos."""
    lines = [f"LINK_AVAILABLE: {'true' if offer.payment_links else 'false'}", f"TRANSFER_AVAILABLE: {'true' if offer.transfer_lines else 'false'}"]
    lines.append(f"PAYMENT_LINKS: {' | '.join(offer.payment_links)}" if offer.payment_links else "sin links de pago definidos")
    lines += ["TRANSFER_METHODS:", "\n".join(offer.transfer_lines) if offer.transfer_lines else "- none", *instructions.PAYMENT_GUARDRAILS]
    if offer.payment_links and offer.transfer_lines:
        lines.append(instructions.ASK_LINK_OR_TRANSFER)
    elif offer.transfer_lines:
        kinds = [line.split(":")[0].strip("- ").strip() for line in offer.transfer_lines if ":" in line]
        lines.append(instructions.ASK_TRANSFER_METHOD.format(methods=", ".join(kind for kind in kinds if kind) or "transferencia"))
    return lines


def _value_lines(pricing: dict) -> list[str]:
    """Cómo defender el precio, si el negocio lo definió."""
    framing = str(as_dict(pricing.get("price_framing")).get("type") or "").strip().lower()
    break_even = as_dict(pricing.get("roi")).get("break_even_sales")
    hints = [hint for hint in (pricing.get("roi_hints") or []) if isinstance(hint, str) and hint.strip()]
    lines = []
    if framing == "comparativo":
        lines.append(instructions.PRICE_FRAMING_COMPARATIVE)
    elif framing:
        lines.append(instructions.PRICE_FRAMING.format(framing=framing))
    if break_even is not None:
        lines.append(instructions.ROI_BREAK_EVEN.format(sales=break_even))
    elif hints:
        lines.append(f"{hints[0]}.")
    return lines


def render(view: PromptView) -> str:
    pricing, features = view.pricing, view.features
    offer = _read_offer(pricing)
    if not bool(features.get("pricing_enabled", True)) and not offer.plan_prices and not offer.payment_links and not offer.transfer_lines:
        return ""

    payment_lines = _payment_lines(offer)
    is_catalog = bool(features.get("catalog_mode") or str(features.get("business_model", "")).lower() == "catalog")
    # Al empezar, un negocio que no vende por catálogo solo anuncia que tiene precios; el detalle llega cuando la conversación avanza.
    if view.state == "new" and not is_catalog:
        return "\n".join([instructions.PRICING_TEASER, *payment_lines])

    category_names = ", ".join(offer.category_names[:MAX_CATEGORIES])
    if offer.plan_names:
        offer_reference = ", ".join(offer.plan_names)
    elif category_names:
        offer_reference = category_names
    elif offer.product_names:
        offer_reference = "oferta de catálogo definida en pricing"
    else:
        offer_reference = "sin nombres específicos en pricing"
    conditions = ", ".join(as_text(item) for item in as_list(pricing.get("conditions", [])) if as_text(item)) or "sin condiciones explícitas"
    # Los precios de los planes o, en un catálogo, los de cada producto: sin ellos la IA no puede decir cuánto cuesta algo.
    entries = offer.plan_prices or offer.product_prices
    shown = relevance.select(entries, size=lambda entry: len(entry[0]) + 2, text=lambda entry: entry[1], query=view.relevance_query, max_chars=PRICE_LIST_PROMPT_MAX_CHARS)
    price_lines = [line for line, _about_offer in shown]
    if len(shown) < len(entries):
        price_lines.append(instructions.MORE_PRICES.format(count=len(entries) - len(shown)))
    prices = "; ".join(price_lines) or "valores definidos en pricing para este negocio"

    lines = [f"Qué se cobra: {offer_reference}.", f"Precios: {prices}.", f"Condiciones: {conditions}."]
    if offer.includes:
        lines.append(f"Incluye: {', '.join(offer.includes)}.")
    if offer.not_included:
        lines.append(f"No incluye: {', '.join(offer.not_included)}.")
    lines += [*_value_lines(pricing), instructions.PRICE_TALK]
    return "\n".join([*lines, *payment_lines])
