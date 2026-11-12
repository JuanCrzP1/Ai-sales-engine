"""Respuestas rápidas del panel (Configuración → Respuestas rápidas y el chat de Conversaciones).

Quien llega al negocio las ve y las usa en el chat. Crearlas, editarlas y borrarlas es de quien organiza el negocio: hoy su dueño
(es el único rol que existe). Cuando haya asesores, ellos solo las usarán, como en Intercom o Zendesk. El panel y los agentes de IA
(MCP) usan este mismo servicio.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.business_config_application.access import BusinessAccess
from app.business_config_application.ports import QuickReplyStorage
from app.domain.business_config.access import Principal
from app.domain.business_config.errors import NotOwnerError
from app.domain.business_config.quick_replies import QuickReply, validated

logger = logging.getLogger("quick_replies")


@dataclass(frozen=True)
class QuickRepliesView:
    replies: list[QuickReply]
    # Quien mira puede crearlas, editarlas y borrarlas.
    can_manage: bool


class QuickRepliesService:
    def __init__(self, storage: QuickReplyStorage, access: BusinessAccess) -> None:
        self._storage = storage
        self._access = access

    def _can_manage(self, principal: Principal, business: str) -> bool:
        try:
            self._access.require_owner(principal, business)
        except NotOwnerError:
            return False
        return True

    def view(self, principal: Principal, business: str) -> QuickRepliesView:
        self._access.require(principal, business)
        return QuickRepliesView(replies=self._storage.list(business), can_manage=self._can_manage(principal, business))

    def create(self, principal: Principal, business: str, payload: dict[str, Any]) -> QuickReply:
        self._access.require_owner(principal, business)
        draft = validated(shortcut=payload.get("shortcut"), category=payload.get("category"), pieces=payload.get("pieces"))
        reply = self._storage.create(business, draft, created_by=principal.label)
        logger.info("respuesta_rapida_creada", extra={"tenant": business, "pieces": len(draft.pieces)})
        return reply

    def update(self, principal: Principal, business: str, reply_id: str, payload: dict[str, Any]) -> QuickReply:
        self._access.require_owner(principal, business)
        draft = validated(shortcut=payload.get("shortcut"), category=payload.get("category"), pieces=payload.get("pieces"))
        reply = self._storage.update(business, reply_id, draft)
        logger.info("respuesta_rapida_editada", extra={"tenant": business, "pieces": len(draft.pieces)})
        return reply

    def delete(self, principal: Principal, business: str, reply_id: str) -> None:
        self._access.require_owner(principal, business)
        self._storage.delete(business, reply_id)
        logger.info("respuesta_rapida_borrada", extra={"tenant": business})

    def mark_used(self, principal: Principal, business: str, reply_id: str) -> QuickReply:
        """Se usó en un chat: cuenta para que las más usadas salgan primero. Lo puede marcar cualquiera que llegue al negocio."""
        self._access.require(principal, business)
        return self._storage.mark_used(business, reply_id)
