"""Cómo se vende en este negocio: el manual según su tipo (productos, planes, servicios o servicios con cita)."""
from __future__ import annotations

from app.infrastructure.ai.prompting import instructions
from app.infrastructure.ai.prompting.business_model import detect_business_model
from app.infrastructure.ai.prompting.text import as_dict, as_list
from app.infrastructure.ai.prompting.view import PromptView

# El tipo de oferta que declara el negocio (`features.business_model`), en los manuales que existen.
_DECLARED = {"catalog": "catalog", "checkout": "catalog", "saas": "plans", "service_booking": "booking"}


def business_kind(view: PromptView) -> str:
    """catalog, plans, services o booking. Primero lo que el negocio eligió; si no, lo que muestra su oferta."""
    if str(as_dict(view.sales.get("closing")).get("strategy") or "").strip().lower() == "booking":
        return "booking"
    features = view.features
    declared = _DECLARED.get(str(features.get("business_model") or "").strip().lower())
    if declared:
        return declared
    catalog = bool(features["catalog_mode"]) if "catalog_mode" in features else detect_business_model(view.runtime) == "catalog"
    if catalog:
        return "catalog"
    return "plans" if as_list(view.pricing.get("plans")) else "services"


def render(view: PromptView) -> str:
    return instructions.PLAYBOOKS[business_kind(view)].strip()
