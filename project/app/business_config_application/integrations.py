"""Integraciones del panel: conectar el asistente y la plataforma con otras herramientas.

- Claves de API: crearlas (la clave se muestra una sola vez), verlas y revocarlas. Una clave es de un negocio (para conversar con
  su asistente, por ejemplo desde Leona) o de la cuenta de quien la crea, con permisos por área para los agentes de IA (MCP):
  entra a todos sus negocios o a algunos. Desde un negocio se ven las claves que llegan a él; uno ajeno responde como inexistente.
- La API del asistente: su dirección pública y una prueba desde el panel que responde como lo haría la API, con lo publicado.
- El servidor MCP: su dirección pública, para pegarla en el agente.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.business_config_application.access import BusinessAccess
from app.business_config_application.assistant_lab import AssistantLabService
from app.business_config_application.ports import ApiKeyStorage
from app.domain.business_config.access import Principal
from app.domain.business_config.api_keys import ApiKey, CreatedApiKey, validated_key_name
from app.domain.business_config.assistant_api import ApiReply, reply_payload
from app.domain.business_config.errors import AssistantUnavailableError
from app.domain.business_config.key_permissions import SCOPE_ASSISTANT_CHAT, expiry_from, validated_permissions, validated_reach
from app.domain.business_config.team import CONFIGURE

logger = logging.getLogger("integrations")

# El chat de prueba de «Probar la API» en la bandeja (canal `prueba`, como «Probar asistente»).
TRY_CONVERSATION = "prueba"


@dataclass(frozen=True)
class IntegrationsOverview:
    # La dirección pública de la API del asistente, o None si el motor no tiene una (en este equipo sin ngrok).
    assistant_api_url: str | None
    active_keys: int
    chat_keys: int
    # La dirección del servidor MCP para pegar en el agente, o None si no está disponible.
    mcp_url: str | None = None


def _owner(principal: Principal) -> dict[str, Any]:
    """De quién son las claves de la cuenta: el usuario; en este equipo, sin cuentas, el operador local."""
    return {"owner_user_id": None, "local": True} if principal.local_operator else {"owner_user_id": principal.user_id, "local": False}


class IntegrationsService:
    def __init__(
        self,
        keys: ApiKeyStorage,
        access: BusinessAccess,
        *,
        assistant_api_url: Callable[[], str | None] = lambda: None,
        mcp_url: Callable[[], str | None] = lambda: None,
        lab: AssistantLabService | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._keys = keys
        self._access = access
        self._api_url = assistant_api_url
        self._mcp_url = mcp_url
        self._lab = lab
        self._now = now

    def overview(self, principal: Principal, business: str) -> IntegrationsOverview:
        self._access.require(principal, business, CONFIGURE)
        now = self._now()
        usable = [key for key in self._keys.list_keys(business, **_owner(principal)) if key.usable(now)]
        return IntegrationsOverview(
            assistant_api_url=self._api_url(),
            active_keys=len(usable),
            chat_keys=sum(1 for key in usable if SCOPE_ASSISTANT_CHAT in key.scopes),
            mcp_url=self._mcp_url(),
        )

    def keys(self, principal: Principal, business: str) -> list[ApiKey]:
        self._access.require(principal, business, CONFIGURE)
        return self._keys.list_keys(business, **_owner(principal))

    def create_key(self, principal: Principal, business: str, payload: dict[str, Any]) -> CreatedApiKey:
        """Una clave nueva desde este negocio: de él solo, de todos los negocios de la cuenta o de algunos (todos de quien la crea)."""
        self._access.require(principal, business, CONFIGURE)
        name = validated_key_name(payload.get("name"))
        reach = validated_reach(payload.get("reach"), payload.get("businesses"), current=business)
        for slug in reach.businesses:
            self._access.require(principal, slug, CONFIGURE)
        permissions = payload.get("permissions")
        # Antes, una clave se pedía con `scopes`; conversar con el asistente sigue llegando así desde integraciones viejas.
        if permissions is None and payload.get("scopes") == [SCOPE_ASSISTANT_CHAT]:
            permissions = {"chat": "write"}
        scopes = validated_permissions(permissions, reach.kind)
        expires_at = expiry_from(payload.get("expires_in_days"), self._now())
        owner = _owner(principal)
        created = self._keys.create(
            name=name, scopes=scopes, reach=reach, created_by=principal.label, owner_user_id=owner["owner_user_id"], expires_at=expires_at,
        )
        logger.info("clave_de_api_creada", extra={"tenant": business, "scopes": list(scopes), "reach": reach.kind})
        return created

    def revoke_key(self, principal: Principal, business: str, key_id: str) -> ApiKey:
        self._access.require(principal, business, CONFIGURE)
        revoked = self._keys.revoke(business, key_id, **_owner(principal))
        logger.info("clave_de_api_revocada", extra={"tenant": business})
        return revoked

    def try_assistant_api(self, principal: Principal, business: str, message: str) -> dict[str, Any]:
        """Lo que respondería la API a ese mensaje, con lo publicado. Usa la clave de IA del negocio, como «Probar asistente», y
        queda en la bandeja como una prueba (no cuenta en Clientes ni Reportes)."""
        self._access.require(principal, business, CONFIGURE)
        if self._lab is None:
            raise AssistantUnavailableError("la inteligencia artificial no está disponible en este servidor")
        result = self._lab.talk(business, message=message, source="published")
        turn = result.turn
        parts = (turn.reply,) if turn.reply else ()
        return reply_payload(
            ApiReply(
                conversation_id=TRY_CONVERSATION, reply=turn.reply, parts=parts, handoff=turn.handoff, handoff_reason=turn.handoff_reason,
                attended_by="team" if turn.handoff else "assistant", intent=turn.intent, fallback=not turn.ai_answered,
            )
        )
