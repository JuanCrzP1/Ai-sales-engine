"""Integraciones del panel: conectar el asistente con otras herramientas.

- Claves de API de cada negocio: crearlas (la clave se muestra una sola vez), verlas y revocarlas. Solo las del negocio de quien
  pregunta; uno ajeno responde como inexistente.
- La API del asistente: su dirección pública y una prueba desde el panel que responde como lo haría la API, con lo publicado.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.business_config_application.access import BusinessAccess
from app.business_config_application.assistant_lab import AssistantLabService
from app.business_config_application.ports import ApiKeyStorage
from app.domain.business_config.access import Principal
from app.domain.business_config.api_keys import SCOPE_ASSISTANT_CHAT, ApiKey, CreatedApiKey, validated_new_key
from app.domain.business_config.assistant_api import ApiReply, reply_payload
from app.domain.business_config.errors import AssistantUnavailableError

logger = logging.getLogger("integrations")

# El chat de prueba de «Probar la API» en la bandeja (canal `prueba`, como «Probar asistente»).
TRY_CONVERSATION = "prueba"


@dataclass(frozen=True)
class IntegrationsOverview:
    # La dirección pública de la API del asistente, o None si el motor no tiene una (en este equipo sin ngrok).
    assistant_api_url: str | None
    active_keys: int
    chat_keys: int


class IntegrationsService:
    def __init__(
        self,
        keys: ApiKeyStorage,
        access: BusinessAccess,
        *,
        assistant_api_url: Callable[[], str | None] = lambda: None,
        lab: AssistantLabService | None = None,
    ) -> None:
        self._keys = keys
        self._access = access
        self._api_url = assistant_api_url
        self._lab = lab

    def overview(self, principal: Principal, business: str) -> IntegrationsOverview:
        self._access.require(principal, business)
        active = [key for key in self._keys.list_keys(business) if key.active]
        return IntegrationsOverview(
            assistant_api_url=self._api_url(),
            active_keys=len(active),
            chat_keys=sum(1 for key in active if SCOPE_ASSISTANT_CHAT in key.scopes),
        )

    def keys(self, principal: Principal, business: str) -> list[ApiKey]:
        self._access.require(principal, business)
        return self._keys.list_keys(business)

    def create_key(self, principal: Principal, business: str, payload: dict[str, Any]) -> CreatedApiKey:
        self._access.require(principal, business)
        name, scopes = validated_new_key(payload.get("name"), payload.get("scopes"))
        created = self._keys.create(business, name=name, scopes=scopes, created_by=principal.label)
        logger.info("clave_de_api_creada", extra={"tenant": business, "scopes": list(scopes)})
        return created

    def revoke_key(self, principal: Principal, business: str, key_id: str) -> ApiKey:
        self._access.require(principal, business)
        revoked = self._keys.revoke(business, key_id)
        logger.info("clave_de_api_revocada", extra={"tenant": business})
        return revoked

    def try_assistant_api(self, principal: Principal, business: str, message: str) -> dict[str, Any]:
        """Lo que respondería la API a ese mensaje, con lo publicado. Usa la clave de IA del negocio, como «Probar asistente», y
        queda en la bandeja como una prueba (no cuenta en Clientes ni Reportes)."""
        self._access.require(principal, business)
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
