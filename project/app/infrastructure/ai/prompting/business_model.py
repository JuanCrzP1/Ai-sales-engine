"""Qué tipo de oferta tiene el negocio, según lo que publicó: catálogo de productos, planes o servicio."""
from __future__ import annotations

from app.infrastructure.ai.prompting.text import as_dict


def resolve_business_model(business, pricing, inventory) -> str:
    """'catalog' si hay productos (en inventario o catálogo), 'saas' si hay planes y 'service' si no hay ninguno."""
    del business
    safe_pricing = as_dict(pricing)
    catalog_items = as_dict(safe_pricing.get("catalog")).get("items")
    plans = safe_pricing.get("plans")
    items = as_dict(inventory).get("items")
    if isinstance(items, list) and items:
        return "catalog"
    if isinstance(catalog_items, list) and catalog_items:
        return "catalog"
    if isinstance(plans, list) and plans:
        return "saas"
    return "service"


def detect_business_model(runtime_yaml: dict) -> str:
    payload = as_dict(runtime_yaml)
    return resolve_business_model(as_dict(payload.get("business")), as_dict(payload.get("pricing")), as_dict(payload.get("inventory")))
