"""El equipo de un negocio (Configuración → Equipo) y las invitaciones por enlace.

Del lado de quien administra (dueño o administrador): ver el equipo, invitar con un correo y un rol, renovar o retirar una invitación,
cambiar roles y quitar personas, con las reglas de `domain/business_config/team.py`. Del lado de quien recibe el enlace: ver de qué
negocio es (sin sesión) y aceptarlo (con su cuenta, la del correo invitado). El enlace solo se muestra al crear o renovar.

Solo existe con cuentas (la nube): en este equipo el operador local es el dueño de todo y no hay a quién invitar.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.business_config_application.access import BusinessAccess
from app.business_config_application.ports import TeamStorage
from app.domain.business_config.access import Principal
from app.domain.business_config.errors import AssistantUnavailableError
from app.domain.business_config.team import (
    TEAM,
    Invitation,
    Member,
    check_acceptance,
    check_removal,
    check_role_change,
    invitation_expiry,
    new_invitation_token,
    token_fingerprint,
    validated_invitation,
)

logger = logging.getLogger("team")


@dataclass(frozen=True)
class TeamView:
    members: list[Member]
    invitations: list[Invitation]
    # Quién mira: para marcar «Tú» y saber a quién puede tocar.
    me: str
    my_role: str


@dataclass(frozen=True)
class IssuedInvitation:
    invitation: Invitation
    # El enlace secreto: solo ahora. Después solo queda su huella.
    token: str


class TeamService:
    def __init__(self, storage: TeamStorage, access: BusinessAccess, clock: Callable[[], datetime] | None = None) -> None:
        self._storage = storage
        self._access = access
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def _manager(self, principal: Principal, business: str) -> str:
        if not self._access.has_accounts:
            raise AssistantUnavailableError("el equipo solo existe con cuentas, en el panel de la nube")
        return self._access.require(principal, business, TEAM)

    def view(self, principal: Principal, business: str) -> TeamView:
        role = self._manager(principal, business)
        return TeamView(self._storage.members(business), self._storage.invitations(business), principal.user_id, role)

    def invite(self, principal: Principal, business: str, payload: dict[str, Any]) -> IssuedInvitation:
        role = self._manager(principal, business)
        email, invited_role = validated_invitation(email=payload.get("email"), role=payload.get("role"), actor_role=role)
        token = new_invitation_token()
        now = self._clock()
        invitation = self._storage.invite(
            business, email=email, role=invited_role, token_hash=token_fingerprint(token), invited_by=principal.label, now=now, expires_at=invitation_expiry(now)
        )
        logger.info("invitacion_creada", extra={"tenant": business, "role": invited_role})
        return IssuedInvitation(invitation, token)

    def renew(self, principal: Principal, business: str, invitation_id: str) -> IssuedInvitation:
        """Un enlace nuevo por 7 días más; el anterior deja de servir."""
        self._manager(principal, business)
        token = new_invitation_token()
        now = self._clock()
        invitation = self._storage.renew(business, invitation_id, token_hash=token_fingerprint(token), now=now, expires_at=invitation_expiry(now))
        return IssuedInvitation(invitation, token)

    def revoke(self, principal: Principal, business: str, invitation_id: str) -> None:
        self._manager(principal, business)
        self._storage.revoke(business, invitation_id, now=self._clock())

    def change_role(self, principal: Principal, business: str, user_id: str, payload: dict[str, Any]) -> Member:
        actor_role = self._manager(principal, business)
        new_role = payload.get("role")
        member = self._storage.change_role(
            business,
            user_id,
            lambda target_role, owners: check_role_change(
                actor_id=principal.user_id, actor_role=actor_role, target_id=user_id, target_role=target_role, new_role=new_role, owners=owners
            ),
        )
        logger.info("rol_cambiado", extra={"tenant": business, "role": member.role})
        return member

    def remove(self, principal: Principal, business: str, user_id: str) -> None:
        actor_role = self._manager(principal, business)
        self._storage.remove(
            business,
            user_id,
            lambda target_role, owners: check_removal(actor_id=principal.user_id, actor_role=actor_role, target_id=user_id, target_role=target_role, owners=owners),
        )
        logger.info("miembro_quitado", extra={"tenant": business})

    # --------------------------------------------------------------------------------------------- quien recibe el enlace

    def preview(self, token: str) -> Invitation:
        """De qué negocio es y con qué rol, para mostrarlo antes de entrar. Sin sesión: no revela nada si el enlace no sirve."""
        return check_acceptance(self._storage.invitation_by_token(token_fingerprint(token)), email=None, now=self._clock())

    def accept(self, principal: Principal, token: str) -> str:
        """Lo pone en el equipo (con su cuenta, la del correo invitado) y devuelve el negocio."""
        if not self._access.has_accounts or principal.local_operator:
            raise AssistantUnavailableError("el equipo solo existe con cuentas, en el panel de la nube")
        now = self._clock()
        business = self._storage.accept(
            token_fingerprint(token),
            user_id=principal.user_id,
            email=principal.email,
            now=now,
            check=lambda invitation: check_acceptance(invitation, email=principal.email or "", now=now),
        )
        logger.info("invitacion_aceptada", extra={"tenant": business})
        return business
