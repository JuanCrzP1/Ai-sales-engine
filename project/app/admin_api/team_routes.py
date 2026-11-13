"""Rutas del equipo de un negocio (Configuración → Equipo) y de las invitaciones por enlace.

Las del equipo son del dueño o de un administrador (`TeamService` revisa el rol y las reglas). Ver una invitación no pide sesión:
quien recibe el enlace todavía no ha entrado; aceptarla sí, con la cuenta del correo invitado.
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Path, Request, Response, status

from app.admin_api.routes import BusinessSlug, CurrentUser
from app.admin_api.schemas import invitation_payload, team_member_payload, team_payload
from app.business_config_application.team import TeamService
from app.domain.business_config.errors import AssistantUnavailableError

router = APIRouter(prefix="/api")


def _team(request: Request) -> TeamService:
    service = getattr(request.app.state, "team", None)
    if service is None:
        raise AssistantUnavailableError("el equipo solo existe con cuentas, en el panel de la nube")
    return service


Team = Annotated[TeamService, Depends(_team)]
ItemId = Annotated[str, Path(max_length=200)]
Token = Annotated[str, Path(max_length=200)]


@router.get("/businesses/{slug}/team")
def get_team(slug: BusinessSlug, user: CurrentUser, team: Team) -> dict[str, Any]:
    return team_payload(team.view(user, slug))


@router.post("/businesses/{slug}/team/invitations", status_code=status.HTTP_201_CREATED)
def invite(slug: BusinessSlug, user: CurrentUser, team: Team, body: Annotated[dict[str, Any], Body()]) -> dict[str, Any]:
    issued = team.invite(user, slug, body)
    return {**invitation_payload(issued.invitation), "token": issued.token}


@router.post("/businesses/{slug}/team/invitations/{invitation_id}/renew")
def renew_invitation(slug: BusinessSlug, invitation_id: ItemId, user: CurrentUser, team: Team) -> dict[str, Any]:
    issued = team.renew(user, slug, invitation_id)
    return {**invitation_payload(issued.invitation), "token": issued.token}


@router.delete("/businesses/{slug}/team/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invitation(slug: BusinessSlug, invitation_id: ItemId, user: CurrentUser, team: Team) -> Response:
    team.revoke(user, slug, invitation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/businesses/{slug}/team/members/{user_id}")
def change_role(slug: BusinessSlug, user_id: ItemId, user: CurrentUser, team: Team, body: Annotated[dict[str, Any], Body()]) -> dict[str, Any]:
    return team_member_payload(team.change_role(user, slug, user_id, body), user.user_id)


@router.delete("/businesses/{slug}/team/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(slug: BusinessSlug, user_id: ItemId, user: CurrentUser, team: Team) -> Response:
    team.remove(user, slug, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/invitations/{token}")
def preview_invitation(token: Token, team: Team) -> dict[str, Any]:
    """Sin sesión: de qué negocio es, para quién y con qué rol. Un enlace que no sirve responde con el motivo."""
    return invitation_payload(team.preview(token))


@router.post("/invitations/{token}/accept")
def accept_invitation(token: Token, user: CurrentUser, team: Team) -> dict[str, Any]:
    return {"business": team.accept(user, token)}
