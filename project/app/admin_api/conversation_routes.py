"""Rutas de la bandeja de conversaciones: los chats de los negocios del usuario, en vivo, sus avisos y la actividad de cada negocio.

Reciben la petición, llaman a `ConversationsService` y serializan la respuesta. Solo llegan a los negocios del usuario: una
conversación ajena responde igual que una inexistente.

En vivo: el panel pide `GET /conversations/{id}/live?since=<cursor>` cada pocos segundos y recibe solo lo nuevo o lo que cambió,
con el `cursor` para la próxima vez (la hora del servidor, no la del navegador). El equipo responde con `POST .../messages`: el
mensaje sale por el canal del cliente y la IA se pausa en ese chat; `POST .../assistant` la reanuda o la pausa.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any
from urllib.parse import unquote

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.concurrency import run_in_threadpool

from app.admin_api.errors import ApiError
from app.admin_api.routes import BusinessSlug, CurrentUser
from app.admin_api.schemas import (
    MarkNotificationsRead,
    SendReply,
    SetAssistant,
    activity_payload,
    chat_message_payload,
    conversation_payload,
    notification_payload,
)
from app.business_config_application.conversations import ConversationsService, NotificationsService, ReplyNotSentError
from app.business_config_application.usage_limits import UsageGuard
from app.domain.business_config.conversations import MAX_MEDIA_BYTES, validated_attachment
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


def _usage(request: Request) -> UsageGuard:
    return request.app.state.usage


Conversations = Annotated[ConversationsService, Depends(_conversations)]
Notifications = Annotated[NotificationsService, Depends(_notifications)]
Usage = Annotated[UsageGuard, Depends(_usage)]

_INLINE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf"}


def _since(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ApiError(status.HTTP_422_UNPROCESSABLE_ENTITY, "La marca de tiempo no es válida.", code="invalid") from None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


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


@router.get("/conversations/{conversation_id}/live")
def live(
    conversation_id: str, user: CurrentUser, conversations: Conversations, since: Annotated[str | None, Query(max_length=40)] = None
) -> dict[str, Any]:
    """La conversación y los mensajes nuevos o que cambiaron desde `since`, con el cursor para la próxima consulta."""
    cursor = datetime.now(timezone.utc)
    summary, messages = conversations.live(user, conversation_id, _since(since))
    return {
        "conversation": conversation_payload(summary),
        "messages": [chat_message_payload(message) for message in messages],
        "cursor": cursor.isoformat().replace("+00:00", "Z"),
    }


@router.post("/conversations/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
def reply(conversation_id: str, body: SendReply, user: CurrentUser, conversations: Conversations, usage: Usage) -> dict[str, Any]:
    """El equipo responde: el mensaje sale por el canal del cliente y la IA se pausa en ese chat."""
    usage.conversation_reply(user)
    try:
        return chat_message_payload(conversations.reply(user, conversation_id, body.text))
    except ReplyNotSentError as exc:
        raise ApiError(status.HTTP_502_BAD_GATEWAY, str(exc), code="reply_not_sent") from None


@router.post("/conversations/{conversation_id}/attachments", status_code=status.HTTP_201_CREATED)
async def send_attachment(conversation_id: str, request: Request, user: CurrentUser, conversations: Conversations, usage: Usage) -> dict[str, Any]:
    """El equipo envía un archivo: el cuerpo es el archivo tal cual (con su `Content-Type`); su nombre y el texto que lo acompaña
    van en los encabezados `X-File-Name` y `X-Caption` (codificados como en una URL). Sale por el canal del cliente y la IA se pausa."""
    usage.conversation_reply(user)
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > MAX_MEDIA_BYTES:
        raise ApiError(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "El archivo pesa más de 4 MB. Envía uno más liviano.", code="too_large")
    content = await request.body()
    attachment = validated_attachment(
        mime_type=request.headers.get("content-type"),
        content=content,
        file_name=unquote(request.headers.get("x-file-name", "")),
        caption=unquote(request.headers.get("x-caption", "")),
    )
    try:
        sent = await run_in_threadpool(conversations.send_attachment, user, conversation_id, attachment)
    except ReplyNotSentError as exc:
        raise ApiError(status.HTTP_502_BAD_GATEWAY, str(exc), code="reply_not_sent") from None
    return chat_message_payload(sent)


@router.post("/conversations/{conversation_id}/assistant")
def set_assistant(conversation_id: str, body: SetAssistant, user: CurrentUser, conversations: Conversations) -> dict[str, Any]:
    """Reanuda la IA en la conversación o la pausa para que la atienda el equipo."""
    return conversation_payload(conversations.set_assistant(user, conversation_id, active=body.active))


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: str, user: CurrentUser, conversations: Conversations) -> None:
    """Elimina el chat: sus mensajes, archivos y avisos, y lo que el asistente recuerda de ese cliente. Las ventas se conservan."""
    conversations.delete(user, conversation_id)


@router.delete("/businesses/{slug}/conversations/tests")
def delete_test_conversations(slug: BusinessSlug, user: CurrentUser, conversations: Conversations) -> dict[str, int]:
    """Borra de una vez los chats de «Probar asistente» del negocio."""
    return {"deleted": conversations.delete_test_chats(user, slug)}


@router.post("/conversations/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_read(conversation_id: str, user: CurrentUser, conversations: Conversations) -> None:
    conversations.mark_read(user, conversation_id)


@router.get("/conversations/{conversation_id}/media/{media_id}")
def media(conversation_id: str, media_id: str, user: CurrentUser, conversations: Conversations) -> Response:
    """Una foto, un audio o un documento de la conversación."""
    file = conversations.media(user, conversation_id, media_id)
    # Lo que manda un cliente nunca se ejecuta en el panel: solo se muestran en línea tipos seguros, sin scripts (ni SVG ni HTML).
    safe = file.mime_type in _INLINE_TYPES or file.mime_type.startswith(("audio/", "video/"))
    headers = {
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "default-src 'none'; sandbox",
        "Content-Disposition": "inline" if safe else "attachment",
    }
    return Response(content=file.content, media_type=file.mime_type if safe else "application/octet-stream", headers=headers)


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
