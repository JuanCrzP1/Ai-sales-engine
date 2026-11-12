"""El modelo de IA del asistente (área «Asistente IA»): ver el modelo y lo que ha gastado, buscar modelos y cambiarlo.

Usa el MISMO servicio que el panel (`AssistantLabService`). La clave de IA del negocio es un secreto de la persona: el agente solo
sabe si está puesta, nunca la ve ni la cambia. Cambiar el modelo se aplica al instante en las respuestas a los clientes reales.
"""
from __future__ import annotations

from typing import Any

from app.business_config_application.access import BusinessAccess
from app.business_config_application.assistant_lab import AssistantLabService
from app.business_config_application.mcp.access import McpAccess, McpBusinesses
from app.business_config_application.mcp.tool import McpTool, obj, text
from app.domain.business_config.key_permissions import SCOPE_CONFIG_READ, SCOPE_CONFIG_WRITE

BUSINESS = {"business": text("Identificador del negocio (de list_businesses).")}
DEFAULT_MODELS = 25
MAX_MODELS = 100


def ai_tools(lab: AssistantLabService, access: BusinessAccess) -> list[McpTool]:
    businesses = McpBusinesses(access)

    def settings_of(slug: str) -> dict[str, Any]:
        settings = lab.ai_settings(slug)
        usage = lab.ai_usage(slug)
        return {
            "business": slug,
            "provider": settings.provider,
            "model": settings.model,
            "uses_default_model": settings.model is None,
            # Solo si está puesta: la clave es de la persona.
            "ai_key_configured": settings.key_configured,
            "last_30_days": {
                "since": usage.since.isoformat(),
                "replies": usage.replies,
                "tokens": usage.prompt_tokens + usage.completion_tokens,
                "cost_usd": usage.cost_usd,
            },
            "note": None if settings.key_configured else "Sin clave de IA el asistente no responde: la persona debe ponerla en el panel (Configuración → Inteligencia artificial).",
        }

    def get_settings(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        return settings_of(businesses.require(caller, args["business"]))

    def models(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        slug = businesses.require(caller, args["business"])
        catalog = lab.ai_models(slug)
        words = str(args.get("query") or "").lower().split()
        found = [model for model in catalog.models if all(word in f"{model.id} {model.name} {model.provider}".lower() for word in words)]
        if args.get("free_only"):
            found = [model for model in found if model.free]
        limit = max(1, min(int(args.get("limit") or DEFAULT_MODELS), MAX_MODELS))
        return {
            "business": slug,
            "default_model": catalog.default_model,
            "models": [
                {
                    "id": model.id,
                    "name": model.name,
                    "provider": model.provider,
                    "recommended": model.recommended,
                    "free": model.free,
                    "usd_per_million_tokens": {"prompt": model.prompt_usd_per_million, "completion": model.completion_usd_per_million},
                    "context_length": model.context_length,
                }
                for model in found[:limit]
            ],
            "total": len(found),
            "note": "Los recomendados van primero. Busca con query para ver otros.",
        }

    def set_model(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        slug = businesses.require(caller, args["business"])
        lab.save_ai_settings(slug, model=args.get("model") or None)
        return {**settings_of(slug), "message": "Modelo cambiado: el asistente ya responde con él a los clientes."}

    return [
        McpTool(
            "get_ai_settings",
            "Ver el modelo de IA",
            "El modelo con el que responde el asistente, si hay clave de IA puesta (nunca la clave) y las respuestas, tokens y costo de los últimos 30 días.",
            SCOPE_CONFIG_READ,
            obj(BUSINESS, ("business",)),
            get_settings,
            read_only=True,
        ),
        McpTool(
            "list_ai_models",
            "Ver los modelos de IA",
            "Los modelos que se pueden elegir para el asistente, los recomendados primero, con su precio por millón de tokens.",
            SCOPE_CONFIG_READ,
            obj({
                **BUSINESS,
                "query": text("Buscar por nombre o proveedor (opcional), por ejemplo «claude» o «gemini flash»."),
                "free_only": {"type": "boolean", "description": "Solo los gratuitos."},
                "limit": {"type": "integer", "description": f"Cuántos (1 a {MAX_MODELS}; por defecto {DEFAULT_MODELS})."},
            }, ("business",)),
            models,
            read_only=True,
        ),
        McpTool(
            "set_ai_model",
            "Cambiar el modelo de IA",
            "Cambia el modelo con el que responde el asistente (un id de list_ai_models; vacío vuelve al de la plataforma). Se aplica AL INSTANTE a los clientes reales y cambia el costo: muéstrale a la persona el modelo y su precio y pide su confirmación.",
            SCOPE_CONFIG_WRITE,
            obj({**BUSINESS, "model": text("El id del modelo (de list_ai_models); vacío: el de la plataforma.")}, ("business",)),
            set_model,
            destructive=True,
        ),
    ]
