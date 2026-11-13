"""A qué negocios llega cada usuario y qué puede hacer en cada uno.

En la nube, cada persona solo llega a los negocios donde es miembro, y su rol decide lo que puede hacer (ver
`domain/business_config/team.py`): un negocio ajeno se trata igual que uno inexistente, para no revelar que existe; en uno propio,
lo que su rol no permite responde «no puedes» con el motivo. En este equipo, sin cuentas, el operador local es el dueño de todos.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from app.business_config_application.ports import BusinessMembers
from app.business_config_application.service import BusinessConfigService
from app.domain.business_config.access import OWNER, Principal
from app.domain.business_config.errors import BusinessNotFoundError
from app.domain.business_config.records import BusinessSummary
from app.domain.business_config.team import ATTEND, DELETE_BUSINESS, can, refusal


class BusinessAccess:
    def __init__(self, configs: BusinessConfigService, members: BusinessMembers | None = None) -> None:
        # Sin `members` no hay cuentas: es la API local y solo el operador local llega hasta aquí.
        self._configs = configs
        self._members = members

    @property
    def has_accounts(self) -> bool:
        """Si hay cuentas (la nube): sin ellas no hay equipo."""
        return self._members is not None

    def _all_access(self, principal: Principal) -> bool:
        return self._members is None and principal.local_operator

    def role_of(self, principal: Principal, tenant_slug: str) -> str | None:
        """Su rol en el negocio, o None si no es miembro."""
        if self._all_access(principal):
            return OWNER
        if self._members is None:
            return None
        return self._members.role_of(tenant_slug, principal.user_id)

    def require(self, principal: Principal, tenant_slug: str, need: str = ATTEND) -> str:
        """Su rol, si es miembro y su rol permite `need`. Si no es miembro, falla como si el negocio no existiera."""
        role = self.role_of(principal, tenant_slug)
        if role is None:
            raise BusinessNotFoundError(f"{tenant_slug}: no existe o no pertenece a este usuario")
        if not can(role, need):
            raise refusal(need)
        return role

    def require_owner(self, principal: Principal, tenant_slug: str) -> None:
        """Como `require`, y además debe ser su dueño (por ejemplo, para eliminarlo)."""
        self.require(principal, tenant_slug, DELETE_BUSINESS)

    def list_for(self, principal: Principal) -> list[BusinessSummary]:
        """Sus negocios, cada uno con su rol."""
        businesses = self._configs.list_businesses()
        if self._all_access(principal):
            return [replace(business, role=OWNER) for business in businesses]
        roles = self._members.roles_of(principal.user_id) if self._members is not None else {}
        return [replace(business, role=roles[business.slug]) for business in businesses if business.slug in roles]

    def create_for(
        self, principal: Principal, tenant_slug: str, name: str, *, document: dict[str, Any] | None = None, created_by: str | None = None
    ) -> BusinessSummary:
        """Crea el negocio con este usuario como dueño, en la misma transacción. Con `document` (una plantilla), guarda su primer
        borrador a nombre de quien lo creó (por defecto, el usuario): nada se publica hasta que el negocio lo revise."""
        owner = None if self._all_access(principal) else principal.user_id
        created = self._configs.create_business(tenant_slug, name, document=document, owner_id=owner, created_by=created_by or principal.label)
        return replace(created, role=OWNER)
