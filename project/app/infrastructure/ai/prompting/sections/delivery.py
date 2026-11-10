"""«CÓMO COMPRA Y RECIBE EL CLIENTE»: los pasos y requisitos para comprar o recibir el servicio, y la entrega (domicilio, envío,
recogida) con su costo y su tiempo, o si hay que agendar.

Si el negocio entrega de alguna forma, también se dice lo que no hace («No hace envíos.»): así la IA no promete un envío que no existe.
Un negocio que no entrega nada físico (una escuela, una agencia) no recibe esas negaciones.
"""
from __future__ import annotations

from app.infrastructure.ai.prompting.money import amount
from app.infrastructure.ai.prompting.text import as_dict, as_text, dicts, one_line, section, sentence, texts
from app.infrastructure.ai.prompting.view import PromptView
from app.infrastructure.ai.prompting.vocabulary import SCOPES

HEADER = "CÓMO COMPRA Y RECIBE EL CLIENTE"
_DELIVERY_TYPES = {"propio": "Domicilio propio", "tercero": "Domicilio con mensajería externa"}


def main_currency(view: PromptView) -> str:
    """La moneda en que el negocio da sus precios (la primera de su oferta): los costos de entrega no la traen."""
    pricing = view.pricing
    for plan in dicts(pricing.get("plans")):
        for currency in as_dict(plan.get("pricing")):
            return currency
    for item in dicts(as_dict(pricing.get("catalog")).get("items")):
        for currency in as_dict(item.get("price")):
            return currency
    return ""


def _cost(cost: dict, currency: str) -> str:
    kind, value = as_text(cost.get("type")).lower(), cost.get("value")
    if kind == "gratis":
        return "gratis"
    if kind == "fijo" and value not in (None, ""):
        return f"cuesta {amount(currency, value)}"
    if kind == "variable":
        return f"el costo depende del destino (desde {amount(currency, value)})" if isinstance(value, (int, float)) and value > 0 else "el costo depende del destino"
    return ""


def _time(time: dict) -> str:
    low, high = as_text(time.get("min")), as_text(time.get("max"))
    if low and high and low != high:
        return f"tarda de {low} a {high}"
    return f"tarda {low or high}" if low or high else ""


def _mode(label: str, mode: dict, currency: str) -> str:
    details = [part for part in (_cost(as_dict(mode.get("cost")), currency), _time(as_dict(mode.get("time")))) if part]
    return sentence(f"{label}: {'; '.join(details)}" if details else label)


def _fulfillment(view: PromptView) -> list[str]:
    logistics = as_dict(view.business.get("logistics"))
    delivery, shipping, pickup = (as_dict(logistics.get(key)) for key in ("delivery", "shipping", "pickup"))
    currency = main_currency(view)
    delivers = any(mode.get("available") is True for mode in (delivery, shipping, pickup))
    lines = []
    if delivery.get("available") is True:
        zones = texts(delivery.get("zones"))
        label = _DELIVERY_TYPES.get(as_text(delivery.get("type")), "Domicilio") + (f" en {', '.join(zones)}" if zones else "")
        lines.append(_mode(label, delivery, currency))
    elif delivers and delivery:
        lines.append("No hace domicilios.")
    if shipping.get("available") is True:
        providers = texts(shipping.get("providers"))
        scope = SCOPES.get(as_text(shipping.get("scope")), "")
        label = "Envíos" + (f" {scope}" if scope else "") + (f" con {', '.join(providers)}" if providers else "")
        lines.append(_mode(label, shipping, currency))
    elif delivers and shipping:
        lines.append("No hace envíos.")
    if pickup.get("available") is True:
        lines.append(sentence(f"Recogida: {one_line(pickup.get('instructions'))}" if one_line(pickup.get("instructions")) else "El cliente puede recoger su pedido"))
    elif delivers and pickup:
        lines.append("No hay recogida en el local.")
    if as_dict(logistics.get("scheduling")).get("required") is True:
        lines.append("Este servicio requiere agendar una cita o reserva.")
    return lines


def render(view: PromptView) -> str:
    solution = as_dict(view.sales.get("solution"))
    steps, requirements = texts(solution.get("process_steps")), texts(solution.get("requirements"))
    lines = [
        sentence("Pasos para comprar o recibir el servicio: " + "; ".join(f"{index}) {step}" for index, step in enumerate(steps, 1))) if steps else "",
        sentence(f"Requisitos del cliente: {'; '.join(requirements)}") if requirements else "",
        *_fulfillment(view),
    ]
    return section(HEADER, lines)
