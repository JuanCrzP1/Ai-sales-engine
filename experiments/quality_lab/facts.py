"""La ficha de hechos de un negocio: lo que es verdad según lo que publicó. La usan los escenarios (para preguntar por productos
reales) y el juez (para saber qué se inventó). Nunca lleva datos de pago: solo los tipos de pago disponibles.

Lleva todo lo que el negocio configura y llega al asistente (entrega, inventario, financiación, políticas, horario, cliente ideal y su
estrategia de venta): si el asistente dice algo cierto que la ficha no trae, el juez lo castigaría como inventado."""
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


def _inventory(runtime: dict, pricing: dict) -> dict:
    """Las opciones de cada producto por su nombre, con su precio propio y si están agotadas (sin el código interno)."""
    inventory = _dict(runtime.get("inventory"))
    names = {item.get("id"): item.get("name") for item in _list(_dict(pricing.get("catalog")).get("items")) if isinstance(item, dict)}
    track = inventory.get("track_stock") is True
    out = {}
    for entry in _list(inventory.get("items")):
        name = names.get(_dict(entry).get("product_id"))
        options = [
            {"opcion": _dict(variant.get("attributes")), **({"precio": variant["prices"]} if variant.get("prices") else {}),
             **({"agotada": variant.get("stock", 1) <= 0} if track else {})}
            for variant in _list(_dict(entry).get("variants")) if isinstance(variant, dict)
        ]
        if name and options:
            out[name] = options
    return out


def _strategy(runtime: dict) -> dict:
    """La estrategia de venta que escribió el negocio, tal como la recibe el motor."""
    business, sales = _dict(runtime.get("business")), _dict(runtime.get("sales"))
    strategy = {
        "problemas_en_sus_palabras": _list(business.get("pain_points")),
        "problemas": _dict(_dict(sales.get("pain")).get("clusters")),
        "casos_tipicos": _list(business.get("use_cases")),
        "motivos": _dict(business.get("value_drivers")),
        "angulos": _dict(sales.get("angles")),
        "objeciones": _dict(sales.get("objection")),
        "orden_de_la_conversacion": _dict(sales.get("conversation_flow")),
        "reglas_de_avance": _dict(sales.get("progression_rules")),
        "atencion": _dict(sales.get("support")),
        "averiguar": _list(_dict(sales.get("discovery")).get("objectives")),
        "cierre": {key: value for key, value in _dict(sales.get("closing")).items() if key not in ("behavior", "next_step")},
    }
    return {key: value for key, value in strategy.items() if value}


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
        "posicionamiento": business.get("positioning") or "",
        "pruebas_de_confianza": _list(business.get("credibility")),
        "cliente_ideal": _dict(business.get("customer_profile")),
        "horario": _list(profile.get("opening_hours")),
        "entrega": _dict(business.get("logistics")),
        "pasos_y_requisitos": {key: value for key, value in _dict(_dict(runtime.get("sales")).get("solution")).items() if key in ("process_steps", "requirements")},
        "inventario": _inventory(runtime, pricing),
        "aclaracion_del_precio": pricing.get("note") or "",
        "mezcla_de_oferta": {key: value for key, value in _dict(pricing.get("business_offers")).items() if key != "financing"},
        "financiacion": _dict(_dict(pricing.get("business_offers")).get("financing")),
        "politicas": _dict(profile.get("policies")),
        "lo_que_no_hace": _dict(capabilities.get("constraints")),
        "estrategia_de_venta": _strategy(runtime),
        # Las reglas del negocio para pasar el chat a una persona («Cuándo pasar a una persona»); {} si usa las de siempre.
        "paso_a_persona": _dict(config.get("escalation")),
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
    # Costos de entrega y precios propios de una variante: también son valores publicados.
    for mode in _dict(facts.get("entrega")).values():
        collect(_dict(_dict(mode).get("cost")).get("value"))
    for options in _dict(facts.get("inventario")).values():
        for option in options:
            for price in _list(option.get("precio")):
                collect(_dict(price).get("amount"))
    return amounts
