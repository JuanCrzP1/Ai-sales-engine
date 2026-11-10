"""Rutas de la bandeja de conversaciones: los chats de los negocios del usuario, sus avisos y la actividad de cada negocio.

Reciben la petición, llaman a `ConversationsService` y serializan la respuesta. Solo llegan a los negocios del usuario: una
conversación ajena responde igual que una inexistente.
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request

from app.admin_api.routes import BusinessSlug, CurrentUser
from app.admin_api.schemas import MarkNotificationsRead, activity_payload, chat_message_payload, conversation_payload, notification_payload
from app.business_config_application.conversations import ConversationsService, NotificationsService
from app.domain.business_config.errors import AssistantUnavailableError

router = APIRouter(prefix="/api")


def _conversations(request: Request) -> ConversationsService:
    service = getattr(request.app.state, "conversations", None)
    if service is None:
        raise AssistantUnavailableError("la bandeja de conversaciones no está disponible en este servidor")
    return service


def _notifications(request: Request) -> NotificationsService:
    service = getattr(request.app.state, "notifications", None)
    if service is None:
        raise AssistantUnavailableError("los avisos no están disponibles en este servidor")
    return service


Conversations = Annotated[ConversationsService, Depends(_conversations)]
Notifications = Annotated[NotificationsService, Depends(_notifications)]


@router.get("/conversations")
def inbox(
    user: CurrentUser,
    conversations: Conversations,
    business: Annotated[str | None, Query(max_length=64)] = None,
    channel: Annotated[str | None, Query(max_length=20)] = None,
    waiting_human: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[dict[str, Any]]:
    """Lo más reciente primero. Sin `business`, de todos los negocios del usuario; con `waiting_human`, las que esperan a una persona."""
    items = conversations.inbox(user, business=business, channel=channel, waiting_human=waiting_human, limit=limit)
    return [conversation_payload(item) for item in items]


@router.get("/conversations/{conversation_id}")
def thread(conversation_id: str, user: CurrentUser, conversations: Conversations) -> dict[str, Any]:
    summary, messages = conversations.thread(user, conversation_id)
    return {"conversation": conversation_payload(summary), "messages": [chat_message_payload(message) for message in messages]}


@router.get("/businesses/{slug}/activity")
def activity(slug: BusinessSlug, user: CurrentUser, conversations: Conversations) -> dict[str, Any]:
    """Lo que pasó hoy en el negocio, para su inicio."""
    return activity_payload(conversations.activity(user, slug))


@router.post("/conversations/{conversation_id}/handoff/resolve")
def resolve_handoff(conversation_id: str, user: CurrentUser, conversations: Conversations) -> dict[str, Any]:
    """Alguien del equipo ya atendió a quien pidió una persona."""
    return conversation_payload(conversations.resolve_handoff(user, conversation_id))


@router.get("/notifications")
def notifications(user: CurrentUser, service: Notifications, limit: Annotated[int, Query(ge=1, le=100)] = 20) -> dict[str, Any]:
    items, unread = service.recent(user, limit=limit)
    return {"items": [notification_payload(item) for item in items], "unread": unread}


@router.post("/notifications/read")
def mark_notifications_read(body: MarkNotificationsRead, user: CurrentUser, service: Notifications) -> dict[str, int]:
    return {"marked": service.mark_read(user, body.ids)}
