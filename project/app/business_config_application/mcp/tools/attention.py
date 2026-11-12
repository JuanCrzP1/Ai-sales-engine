"""La atención humana del negocio (área «Atención humana»): el horario del equipo, lo que se le dice al cliente sobre cuánto tarda,
cuándo la IA retoma un chat que nadie atendió y a dónde llegan los avisos por correo.

Usa el MISMO servicio que el panel (`AttentionService`). Son ajustes de la operación: se aplican al instante, sin publicar. El
agente cambia solo lo que manda; lo demás queda como estaba.
"""
from __future__ import annotations

from typing import Any

from app.business_config_application.access import BusinessAccess
from app.business_config_application.attention import AttentionService, AttentionView
from app.business_config_application.mcp.access import McpAccess, McpBusinesses
from app.business_config_application.mcp.tool import McpTool, obj, text
from app.domain.business_config.attention import HOURS_MODES, REPLY_MINUTES, RESUME_MINUTES, TIMEZONES, WEEKDAYS, hours_payload
from app.domain.business_config.key_permissions import SCOPE_ATTENTION_READ, SCOPE_ATTENTION_WRITE

BUSINESS = {"business": text("Identificador del negocio (de list_businesses).")}
EDITABLE = ("hours_mode", "team_hours", "timezone", "reply_minutes", "resume_after_minutes", "email_enabled", "email_to")
HOURS_RANGE = {
    "type": "object",
    "properties": {
        "days": {"type": "array", "items": text("Día sin tildes.", enum=list(WEEKDAYS))},
        "opens": text("Hora de entrada, HH:MM (24 h)."),
        "closes": text("Hora de salida, HH:MM (24 h), después de la de entrada."),
    },
    "required": ["days", "opens", "closes"],
    "additionalProperties": False,
}


def _view(slug: str, view: AttentionView) -> dict[str, Any]:
    settings = view.settings
    return {
        "business": slug,
        "hours_mode": settings.hours_mode,
        "team_hours": hours_payload(settings.team_hours),
        "business_hours": hours_payload(view.business_hours),
        "timezone": settings.timezone,
        "reply_minutes": settings.reply_minutes,
        "resume_after_minutes": settings.resume_after_minutes,
        "email_enabled": settings.email_enabled,
        "email_to": settings.email_to,
        "account_emails": view.account_emails,
        "email_available": view.email_available,
        "team_available_now": view.team_available_now,
        "next_opening": view.next_opening.isoformat() if view.next_opening else None,
        "meaning": {
            "hours_mode": "business: el horario de «Mi negocio»; custom: team_hours; always: siempre hay alguien.",
            "reply_minutes": "Lo que se le dice al cliente sobre cuánto tarda el equipo (0: no se le dice).",
            "resume_after_minutes": "Cuánto espera el cliente sin respuesta antes de que la IA retome el chat (null: nunca).",
            "email_to": "A quién llegan los avisos por correo (null: a los correos de la cuenta, account_emails).",
        },
    }


def attention_tools(attention: AttentionService, access: BusinessAccess) -> list[McpTool]:
    businesses = McpBusinesses(access)

    def get_settings(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        slug = businesses.require(caller, args["business"])
        return _view(slug, attention.view(caller.principal, slug))

    def update(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        slug = businesses.require(caller, args["business"])
        current = attention.view(caller.principal, slug).settings
        payload: dict[str, Any] = {
            "hours_mode": current.hours_mode,
            "team_hours": hours_payload(current.team_hours),
            "timezone": current.timezone,
            "reply_minutes": current.reply_minutes,
            "resume_after_minutes": current.resume_after_minutes,
            "email_enabled": current.email_enabled,
            "email_to": current.email_to,
        }
        # Solo lo que el agente manda; `resume_after_minutes` y `email_to` aceptan null a propósito.
        payload.update({key: args[key] for key in EDITABLE if key in args})
        saved = attention.save(caller.principal, slug, payload)
        return {**_view(slug, saved), "message": "Guardado: se aplica desde ya, sin publicar."}

    return [
        McpTool(
            "get_attention_settings",
            "Ver la atención humana",
            "Cuándo hay alguien del equipo, lo que se le dice al cliente sobre cuánto tarda, cuándo la IA retoma un chat que nadie atendió y a dónde llegan los avisos por correo; y si ahora hay alguien.",
            SCOPE_ATTENTION_READ,
            obj(BUSINESS, ("business",)),
            get_settings,
            read_only=True,
        ),
        McpTool(
            "update_attention_settings",
            "Cambiar la atención humana",
            "Cambia solo los campos que mandes; se aplica al instante, sin publicar. Cambia a dónde llegan los avisos (email_to) solo si la persona te lo pide con ese correo.",
            SCOPE_ATTENTION_WRITE,
            obj({
                **BUSINESS,
                "hours_mode": text("De dónde sale el horario del equipo.", enum=list(HOURS_MODES)),
                "team_hours": {"type": "array", "items": HOURS_RANGE, "description": "El horario propio (con hours_mode=custom)."},
                "timezone": text("Zona horaria.", enum=list(TIMEZONES)),
                "reply_minutes": {"type": "integer", "enum": list(REPLY_MINUTES), "description": "Cuánto suele tardar el equipo (0: no se dice)."},
                "resume_after_minutes": {"type": "integer", "enum": list(RESUME_MINUTES), "description": "Minutos antes de que la IA retome; null: nunca."},
                "email_enabled": {"type": "boolean", "description": "Avisos por correo cuando un chat pasa a una persona."},
                "email_to": text("A quién llegan los avisos; null: a los correos de la cuenta."),
            }, ("business",)),
            update,
        ),
    ]
