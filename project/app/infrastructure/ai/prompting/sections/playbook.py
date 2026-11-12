"""Cómo se vende en este negocio: el manual según su tipo (productos, planes, servicios o servicios con cita) y cómo se cierra según la
estrategia de cierre que eligió (confirmar la compra, enviar el pago, capturar datos o agendar)."""
from __future__ import annotations

from app.infrastructure.ai.prompting import instructions
from app.infrastructure.ai.prompting.business_model import detect_business_model
from app.infrastructure.ai.prompting.text import as_dict, as_list
from app.infrastructure.ai.prompting.view import PromptView

# Lo que el negocio dice que vende («Qué vendes», `features.business_model`), en los manuales que existen. «checkout» y «process»
# son opciones retiradas: el contrato ya las traduce, y aquí se conservan por si llega una configuración compilada antes.
_DECLARED = {
    "catalog": "catalog", "saas": "plans", "services": "services", "service_booking": "booking",
    "checkout": "catalog", "process": "services",
}


def closing_strategy(view: PromptView) -> str:
    """La estrategia de cierre que eligió el negocio (`sales.closing.strategy`), o "" si no eligió ninguna."""
    return str(as_dict(view.sales.get("closing")).get("strategy") or "").strip().lower()


def business_kind(view: PromptView) -> str:
    """catalog, plans, services o booking. Primero lo que el negocio eligió; si no, lo que muestra su oferta."""
    if closing_strategy(view) == "booking":
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
    """El manual del tipo de negocio y, al final, cómo se cierra: según la estrategia elegida o, si no hay, según el tipo."""
    kind = business_kind(view)
    closing = instructions.CLOSING_STRATEGIES.get(closing_strategy(view)) or instructions.PLAYBOOK_CLOSINGS[kind]
    return f"{instructions.PLAYBOOKS[kind].strip()}\n{closing.strip()}"
