"""A qué negocios llega cada usuario.

En la nube, cada persona solo ve, crea y modifica sus negocios: un negocio ajeno se trata igual que uno inexistente, para no
revelar que existe. En este equipo, sin cuentas, el operador local administra todos los negocios.
"""
from __future__ import annotations

from typing import Any

from app.business_config_application.ports import BusinessMembers
from app.business_config_application.service import BusinessConfigService
from app.domain.business_config.access import Principal
from app.domain.business_config.errors import BusinessNotFoundError, NotOwnerError
from app.domain.business_config.records import BusinessSummary


class BusinessAccess:
    def __init__(self, configs: BusinessConfigService, members: BusinessMembers | None = None) -> None:
        # Sin `members` no hay cuentas: es la API local y solo el operador local llega hasta aquí.
        self._configs = configs
        self._members = members

    def _all_access(self, principal: Principal) -> bool:
        return self._members is None and principal.local_operator

    def require(self, principal: Principal, tenant_slug: str) -> None:
        """Falla como si el negocio no existiera cuando no es de este usuario."""
        if self._all_access(principal):
            return
        if self._members is None or not self._members.is_member(tenant_slug, principal.user_id):
            raise BusinessNotFoundError(f"{tenant_slug}: no existe o no pertenece a este usuario")

    def require_owner(self, principal: Principal, tenant_slug: str) -> None:
        """Como `require`, y además debe ser su dueño (por ejemplo, para eliminarlo)."""
        self.require(principal, tenant_slug)
        if self._all_access(principal) or self._members is None:
            return
        if not self._members.is_owner(tenant_slug, principal.user_id):
            raise NotOwnerError("Solo el dueño del negocio puede hacer esto.")

    def list_for(self, principal: Principal) -> list[BusinessSummary]:
        businesses = self._configs.list_businesses()
        if self._all_access(principal):
            return businesses
        mine = self._members.slugs_of(principal.user_id) if self._members is not None else set()
        return [business for business in businesses if business.slug in mine]

    def create_for(
        self, principal: Principal, tenant_slug: str, name: str, *, document: dict[str, Any] | None = None, created_by: str | None = None
    ) -> BusinessSummary:
        """Crea el negocio con este usuario como dueño, en la misma transacción. Con `document` (una plantilla), guarda su primer
        borrador a nombre de quien lo creó (por defecto, el usuario): nada se publica hasta que el negocio lo revise."""
        owner = None if self._all_access(principal) else principal.user_id
        return self._configs.create_business(tenant_slug, name, document=document, owner_id=owner, created_by=created_by or principal.label)
