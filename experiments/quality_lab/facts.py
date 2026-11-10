"""La ficha de hechos de un negocio: lo que es verdad según lo que publicó. La usan los escenarios (para preguntar por productos
reales) y el juez (para saber qué se inventó). Nunca lleva datos de pago: solo los tipos de pago disponibles."""
from __future__ import annotations

from typing import Any


def _dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _offers(pricing: dict) -> list[dict]:
    offers = []
    for plan in _list(pricing.get("plans")):
        if isinstance(plan, dict) and plan.get("name"):
            prices = {
                currency: {field: amount for field, amount in _dict(values).items() if amount not in (None, "")}
                for currency, values in _dict(plan.get("pricing")).items()
            }
            offers.append({"name": plan["name"], "kind": "plan", "prices": prices, "description": plan.get("description") or "",
                           "includes": _list(plan.get("includes")), "not_included": _list(plan.get("not_included"))})
    for item in _list(_dict(pricing.get("catalog")).get("items")):
        if isinstance(item, dict) and item.get("name"):
            offers.append({"name": item["name"], "kind": "producto", "prices": _dict(item.get("price")), "description": item.get("description") or "",
                           "features": _list(item.get("features")), "category": item.get("category") or ""})
    return offers


def _payment_kinds(pricing: dict) -> dict[str, bool]:
    blocks = [_dict(plan.get("payment")) for plan in _list(pricing.get("plans")) if isinstance(plan, dict)]
    blocks += [_dict(_dict(pricing.get("catalog")).get("payment")), _dict(pricing.get("payment"))]
    link = any(str(block.get("link") or "").strip() for block in blocks)
    transfers = sorted({
        str(_dict(method).get("type") or "")
        for block in blocks
        if _dict(block.get("transfer")).get("enabled")
        for method in _list(_dict(block.get("transfer")).get("methods"))
        if _dict(method).get("type")
    })
    return {"link": link, **{kind: True for kind in transfers}}


def business_facts(runtime: dict, business_model: str) -> dict:
    business, config = _dict(runtime.get("business")), _dict(runtime.get("config"))
    profile, pricing = _dict(config.get("profile")), _dict(runtime.get("pricing"))
    capabilities = _dict(runtime.get("capabilities")) or _dict(config.get("capabilities"))
    return {
        "nombre": profile.get("name") or business.get("name"),
        "modelo": business_model,
        "sector": business.get("industry") or "",
        "descripcion": profile.get("description") or business.get("description") or "",
        "promesa": business.get("promise") or "",
        "diferenciadores": _list(profile.get("differentiators")),
        "ubicacion": _dict(profile.get("location")),
        "modalidades": _list(profile.get("service_modes")),
        "oferta": _offers(pricing),
        "condiciones": _list(pricing.get("conditions")),
        "pagos_disponibles": _payment_kinds(pricing),
        "canales_de_atencion": _list(_dict(capabilities.get("business_channels")).get("allowed")),
        "datos_que_pide": _list(_dict(capabilities.get("data_collection")).get("fields")),
        "tono": profile.get("tone") or "",
        "max_palabras": _dict(config.get("response")).get("max_words"),
        "preguntas_frecuentes": _list(_dict(config.get("knowledge")).get("faqs")),
        "beneficios": _list(profile.get("benefits")),
        "argumentos_de_venta": _list(profile.get("arguments")),
        "argumentos_de_valor": {
            "ventas_al_mes_para_recuperar_la_inversion": _dict(pricing.get("roi")).get("break_even_sales"),
            "otros": _list(pricing.get("roi_hints")),
            "encuadre_del_precio": _dict(pricing.get("price_framing")).get("type"),
        },
        "motivos_de_compra": _dict(_dict(runtime.get("sales")).get("buying_motivation")),
        "promociones": _list(profile.get("promotions")),
        "instrucciones": _list(profile.get("instructions")),
        "mensaje_pago_reportado": _dict(_dict(config.get("post_payment")).get("on_user_report")).get("message") or "",
    }


def known_amounts(facts: dict) -> set[int]:
    """Todos los valores de precio publicados, en cualquier moneda y campo."""
    amounts: set[int] = set()

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            for item in value.values():
                collect(item)
        elif isinstance(value, (int, float)) and value > 0:
            amounts.add(int(value))

    for offer in facts["oferta"]:
        collect(offer["prices"])
    return amounts
