"""Qué puede hacer el asistente en este negocio: tipo de oferta, canales, métodos de cierre, datos a pedir y acciones."""
from __future__ import annotations

from app.infrastructure.ai.prompting import instructions
from app.infrastructure.ai.prompting.business_model import detect_business_model
from app.infrastructure.ai.prompting.text import as_dict, as_text, dedupe
from app.infrastructure.ai.prompting.view import PromptView
from app.utils.logger import logger

HEADER = "CAPACIDADES DEL NEGOCIO:"
CLOSING_METHOD_NAMES = ("link_payment", "human_handoff", "data_collection")


def _steering_log(view: PromptView, kind: str, **extra) -> None:
    logger.info({"event": "backend_prompt_steering", "type": kind, "tenant": view.tenant, "user_id": view.user_id, **extra})


def business_model_line(view: PromptView) -> str:
    business_model = detect_business_model(view.runtime)
    _steering_log(view, "business_model_inference", business_model=business_model)
    return f"modelo: {business_model}"


def catalog_steering(view: PromptView) -> str:
    """En un catálogo, la guía para nombrar productos reales; si no es catálogo, nada."""
    pricing = view.pricing
    is_catalog = bool(pricing.get("model") == "catalog" or isinstance(pricing.get("catalog"), dict)) or detect_business_model(view.runtime) == "catalog"
    if not is_catalog:
        return ""
    _steering_log(view, "catalog_steering")
    return instructions.CATALOG_STEERING


def _channels(raw_value: object) -> list[str]:
    if isinstance(raw_value, dict):
        raw_value = raw_value.get("allowed", [])
    if isinstance(raw_value, str):
        items = [raw_value]
    elif isinstance(raw_value, list):
        items = raw_value
    else:
        items = []
    return dedupe(as_text(item) for item in items)


def _actions(capabilities: dict) -> str:
    raw_actions = capabilities.get("actions", [])
    if isinstance(raw_actions, dict):
        raw_actions = dedupe(
            as_text(item) for key in ("primary", "support") for item in (raw_actions.get(key) if isinstance(raw_actions.get(key), list) else [])
        )
    return ", ".join(as_text(item) for item in raw_actions if as_text(item)) or "sin acciones definidas"


def _closing_methods(capabilities: dict) -> list[str]:
    methods = as_dict(capabilities.get("closing_methods"))
    enabled = []
    for name in CLOSING_METHOD_NAMES:
        raw = methods.get(name)
        if (isinstance(raw, dict) and bool(raw.get("enabled", False))) or raw is True:
            enabled.append(name)
    return enabled


def _data_collection(capabilities: dict) -> tuple[bool, list[str]]:
    raw = capabilities.get("data_collection")
    if isinstance(raw, dict):
        enabled, fields = bool(raw.get("enabled", False)), raw.get("fields", [])
    else:
        enabled, fields = (raw if isinstance(raw, bool) else False), []
    if isinstance(fields, str):
        fields = [fields]
    elif not isinstance(fields, list):
        fields = []
    return enabled, dedupe(as_text(item) for item in fields)


def render(view: PromptView) -> str:
    capabilities = view.capabilities
    legacy_channels = _channels(capabilities.get("channels", []))
    business_channels = _channels(capabilities.get("business_channels", []))
    system_channels = _channels(capabilities.get("system_channels", []))
    # Una configuración que solo trae `channels` los usa como canales de atención.
    if not business_channels and not system_channels and legacy_channels:
        business_channels = list(legacy_channels)

    actions = _actions(capabilities)
    closing_methods = _closing_methods(capabilities)
    closing_methods_text = ", ".join(closing_methods) or "sin métodos de cierre activos"
    data_enabled, data_fields = _data_collection(capabilities)
    data_fields_text = ", ".join(data_fields) or "sin campos definidos"

    # En una conversación en curso basta lo que se puede hacer; la presentación de canales va al empezar.
    if view.state in ("active", "warm"):
        lines = []
        if closing_methods:
            lines.append(f"Métodos de cierre: {closing_methods_text}")
        if data_enabled and data_fields:
            lines.append(f"Datos a recopilar: {data_fields_text}")
        lines.append(f"Acciones: {actions}")
        return "\n".join(lines)

    return "\n".join(
        [
            "TIPOS DE CANALES:",
            f"CANALES DE ATENCION (business_channels): {', '.join(business_channels) or 'sin canales de atencion definidos'}",
            f"CANALES DEL SISTEMA (system_channels): {', '.join(system_channels) or 'sin canales de sistema definidos'}",
            instructions.CHANNEL_TYPES_RULE,
            instructions.CLOSING_METHODS.format(closing_methods=closing_methods_text),
            instructions.DATA_COLLECTION.format(data_collection_fields=data_fields_text),
            f"Acciones disponibles: {actions}",
        ]
    )
