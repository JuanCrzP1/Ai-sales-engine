"""Rutas del Centro de ayuda del panel: los temas con sus artículos, buscar y leer uno. Las ve cualquiera con sesión: la ayuda es
igual para todos los negocios."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query, Request

from app.admin_api.routes import CurrentUser
from app.business_config_application.help import HelpService
from app.domain.business_config.help import MAX_QUERY

router = APIRouter(prefix="/api/help")


def _help(request: Request) -> HelpService:
    return request.app.state.help


Help = Annotated[HelpService, Depends(_help)]


@router.get("")
def help_index(user: CurrentUser, service: Help) -> dict[str, Any]:
    return service.index()


@router.get("/search")
def help_search(user: CurrentUser, service: Help, q: Annotated[str, Query(max_length=MAX_QUERY)] = "") -> dict[str, Any]:
    return service.search(q)


@router.get("/articles/{slug}")
def help_article(slug: Annotated[str, Path(max_length=80)], user: CurrentUser, service: Help) -> dict[str, Any]:
    return service.read(slug)
