"""Quién llama al servidor MCP: la clave con la que se presenta, su dueño, lo que puede y a qué negocios entra.

El agente actúa COMO el dueño de la clave: cada negocio pasa por la misma comprobación que el panel (`BusinessAccess`) y, además,
por el alcance de la clave. Un negocio al que no llega responde igual que uno que no existe.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.business_config_application.access import BusinessAccess
from app.domain.business_config.access import Principal
from app.domain.business_config.errors import BusinessNotFoundError
from app.domain.business_config.key_permissions import KeyReach
from app.domain.business_config.validation import is_valid_slug


@dataclass(frozen=True)
class McpAccess:
    principal: Principal
    key_id: str
    key_name: str
    scopes: frozenset[str]
    reach: KeyReach

    def has(self, scope: str) -> bool:
        return scope in self.scopes

    @property
    def author(self) -> str:
        """Cómo queda en el historial de versiones lo que guarda el agente."""
        return f"Agente «{self.key_name}» ({self.principal.label})"


class McpBusinesses:
    """A qué negocios llega una llamada: los del dueño de la clave que su alcance permite."""

    def __init__(self, access: BusinessAccess) -> None:
        self._access = access

    def require(self, caller: McpAccess, business: str) -> str:
        slug = str(business or "").strip()
        if not is_valid_slug(slug) or not caller.reach.allows(slug):
            raise BusinessNotFoundError(f"{slug}: esta clave no entra a ese negocio o no existe")
        self._access.require(caller.principal, slug)
        return slug

    def visible(self, caller: McpAccess):
        return [business for business in self._access.list_for(caller.principal) if caller.reach.allows(business.slug)]
