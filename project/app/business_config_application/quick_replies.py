"""Respuestas rápidas del panel (Configuración → Respuestas rápidas y el chat de Conversaciones).

Todo el equipo las ve y las usa en el chat. Crearlas, editarlas y borrarlas es del dueño o de un administrador; los asesores solo
las usan, como en Intercom o Zendesk. El panel y los agentes de IA (MCP) usan este mismo servicio.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.business_config_application.access import BusinessAccess
from app.business_config_application.ports import QuickReplyStorage
from app.domain.business_config.access import Principal
from app.domain.business_config.conversations import Attachment, MediaFile, validated_attachment
from app.domain.business_config.quick_replies import QuickReply, QuickReplyFile, validated
from app.domain.business_config.team import CONFIGURE, can

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

    def view(self, principal: Principal, business: str) -> QuickRepliesView:
        role = self._access.require(principal, business)
        return QuickRepliesView(replies=self._storage.list(business), can_manage=can(role, CONFIGURE))

    def create(self, principal: Principal, business: str, payload: dict[str, Any]) -> QuickReply:
        self._access.require(principal, business, CONFIGURE)
        draft = validated(shortcut=payload.get("shortcut"), category=payload.get("category"), pieces=payload.get("pieces"))
        reply = self._storage.create(business, draft, created_by=principal.label)
        logger.info("respuesta_rapida_creada", extra={"tenant": business, "pieces": len(draft.pieces)})
        return reply

    def update(self, principal: Principal, business: str, reply_id: str, payload: dict[str, Any]) -> QuickReply:
        self._access.require(principal, business, CONFIGURE)
        draft = validated(shortcut=payload.get("shortcut"), category=payload.get("category"), pieces=payload.get("pieces"))
        reply = self._storage.update(business, reply_id, draft)
        logger.info("respuesta_rapida_editada", extra={"tenant": business, "pieces": len(draft.pieces)})
        return reply

    def delete(self, principal: Principal, business: str, reply_id: str) -> None:
        self._access.require(principal, business, CONFIGURE)
        self._storage.delete(business, reply_id)
        logger.info("respuesta_rapida_borrada", extra={"tenant": business})

    def upload_file(self, principal: Principal, business: str, attachment: Attachment) -> QuickReplyFile:
        """Guarda un archivo para usarlo en una respuesta (lo sube quien organiza el negocio). Queda suelto hasta que una respuesta
        lo nombre; si ninguna lo usa, se borra solo."""
        self._access.require(principal, business, CONFIGURE)
        saved = self._storage.save_file(business, attachment.media, created_by=principal.label)
        logger.info("archivo_de_respuesta_guardado", extra={"tenant": business, "kind": attachment.kind, "bytes": saved.size_bytes})
        return saved

    def file(self, principal: Principal, business: str, file_id: str) -> MediaFile:
        """Un archivo de las respuestas, para verlo en el panel (todo el equipo)."""
        self._access.require(principal, business)
        return self._storage.file(business, file_id)

    def attachment(self, principal: Principal, business: str, file_id: str, caption: object) -> Attachment:
        """Lo que sale al chat cuando se usa una respuesta con un archivo: el archivo guardado con su texto (ya con el nombre del
        cliente). Se revisa como cualquier archivo enviado desde el chat."""
        self._access.require(principal, business)
        media = self._storage.file(business, file_id)
        return validated_attachment(mime_type=media.mime_type, content=media.content, file_name=media.file_name, caption=caption)

    def mark_used(self, principal: Principal, business: str, reply_id: str) -> QuickReply:
        """Se usó en un chat: cuenta para que las más usadas salgan primero. Lo puede marcar cualquiera que llegue al negocio."""
        self._access.require(principal, business)
        return self._storage.mark_used(business, reply_id)
