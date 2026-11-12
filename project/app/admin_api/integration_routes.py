"""Rutas de Integraciones: las claves de API del negocio y la API del asistente (su dirección y una prueba).

Reciben la petición, llaman a `IntegrationsService` y serializan la respuesta. Una clave completa sale una sola vez: en la respuesta
de crearla. Después solo se ve su comienzo.
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Request, status

from app.admin_api.errors import ApiError
from app.admin_api.routes import BusinessSlug, CurrentUser
from app.admin_api.schemas import api_key_payload
from app.business_config_application.integrations import IntegrationsService
from app.business_config_application.usage_limits import UsageGuard
from app.domain.business_config.api_keys import SCOPES

router = APIRouter(prefix="/api/businesses/{slug}")


def _integrations(request: Request) -> IntegrationsService:
    service = getattr(request.app.state, "integrations", None)
    if service is None:
        raise ApiError(status.HTTP_503_SERVICE_UNAVAILABLE, "Las integraciones no están disponibles en este servidor.", code="integrations_unavailable")
    return service


def _usage(request: Request) -> UsageGuard:
    return request.app.state.usage


Integrations = Annotated[IntegrationsService, Depends(_integrations)]
Usage = Annotated[UsageGuard, Depends(_usage)]


@router.get("/integrations")
def integrations_overview(slug: BusinessSlug, user: CurrentUser, service: Integrations) -> dict[str, Any]:
    overview = service.overview(user, slug)
    return {
        "assistant_api": {"url": overview.assistant_api_url, "chat_keys": overview.chat_keys},
        "api_keys": {"active": overview.active_keys},
        "scopes": [{"id": key, "label": label} for key, label in SCOPES.items()],
    }


@router.get("/api-keys")
def list_api_keys(slug: BusinessSlug, user: CurrentUser, service: Integrations) -> list[dict[str, Any]]:
    return [api_key_payload(key) for key in service.keys(user, slug)]


@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
def create_api_key(slug: BusinessSlug, user: CurrentUser, service: Integrations, usage: Usage, body: Annotated[dict[str, Any], Body()]) -> dict[str, Any]:
    usage.api_key_creation(user)
    created = service.create_key(user, slug, body)
    # La única vez que sale la clave completa.
    return {**api_key_payload(created.key), "secret": created.secret}


@router.post("/api-keys/{key_id}/revoke")
def revoke_api_key(slug: BusinessSlug, key_id: str, user: CurrentUser, service: Integrations) -> dict[str, Any]:
    return api_key_payload(service.revoke_key(user, slug, key_id))


@router.post("/integrations/assistant-api/try")
def try_assistant_api(slug: BusinessSlug, user: CurrentUser, service: Integrations, usage: Usage, body: Annotated[dict[str, Any], Body()]) -> dict[str, Any]:
    usage.playground_message(user, slug)
    return service.try_assistant_api(user, slug, str(body.get("message") or ""))
