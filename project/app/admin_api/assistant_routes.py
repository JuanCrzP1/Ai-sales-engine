"""Rutas de la inteligencia artificial y del área de pruebas de cada negocio.

Reciben la petición, llaman a `AssistantLabService` y serializan la respuesta. La clave de IA entra por aquí y nunca sale:
las respuestas solo dicen si está configurada y sus últimos caracteres. Sus errores se convierten en respuestas en `errors.py`.
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, status

from app.admin_api.routes import BusinessSlug, CurrentUser
from app.admin_api.schemas import (
    PlaygroundMessage,
    SaveAISettings,
    ai_models_payload,
    ai_settings_payload,
    ai_usage_payload,
    key_check_payload,
    playground_payload,
)
from app.business_config_application.assistant_lab import AssistantLabService
from app.business_config_application.usage_limits import UsageGuard
from app.domain.business_config.errors import AssistantUnavailableError

router = APIRouter(prefix="/api/businesses/{slug}")


def _lab(request: Request) -> AssistantLabService:
    lab = getattr(request.app.state, "assistant_lab", None)
    if lab is None:
        raise AssistantUnavailableError("la inteligencia artificial no está disponible en este servidor")
    return lab


def _usage(request: Request) -> UsageGuard:
    return request.app.state.usage


Lab = Annotated[AssistantLabService, Depends(_lab)]
# Lo que gasta la clave de IA del negocio pasa por los límites de uso: más allá, 429 con `Retry-After`.
Usage = Annotated[UsageGuard, Depends(_usage)]


@router.get("/ai")
def get_ai_settings(slug: BusinessSlug, lab: Lab) -> dict[str, Any]:
    return ai_settings_payload(lab.ai_settings(slug))


@router.put("/ai")
def save_ai_settings(slug: BusinessSlug, body: SaveAISettings, lab: Lab) -> dict[str, Any]:
    return ai_settings_payload(lab.save_ai_settings(slug, model=body.model, api_key=body.api_key, clear_key=body.clear_key))


@router.get("/ai/models")
def get_ai_models(slug: BusinessSlug, lab: Lab) -> dict[str, Any]:
    return ai_models_payload(lab.ai_models(slug))


@router.get("/ai/usage")
def get_ai_usage(slug: BusinessSlug, lab: Lab) -> dict[str, Any]:
    return ai_usage_payload(lab.ai_usage(slug))


@router.post("/ai/verify")
def verify_ai_key(slug: BusinessSlug, lab: Lab, user: CurrentUser, usage: Usage) -> dict[str, Any]:
    usage.ai_key_check(user)
    return key_check_payload(lab.verify_ai_key(slug))


@router.post("/playground")
def talk(slug: BusinessSlug, body: PlaygroundMessage, lab: Lab, user: CurrentUser, usage: Usage) -> dict[str, Any]:
    usage.playground_message(user, slug)
    return playground_payload(lab.talk(slug, message=body.message, source=body.source, session_id=body.session_id))


@router.delete("/playground/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def reset_conversation(slug: BusinessSlug, session_id: str, lab: Lab) -> None:
    lab.reset(slug, session_id)
