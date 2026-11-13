"""Rutas de las respuestas rápidas de un negocio (Configuración → Respuestas rápidas y el chat).

Reciben la petición, llaman a `QuickRepliesService` y serializan la respuesta. Verlas y marcarlas como usadas: quien llega al negocio.
Crearlas, editarlas y borrarlas: su dueño.
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Path, Request, Response, status
from fastapi.concurrency import run_in_threadpool

from app.admin_api.files import file_response, read_upload
from app.admin_api.routes import BusinessSlug, CurrentUser
from app.admin_api.schemas import quick_replies_payload, quick_reply_file_payload, quick_reply_payload
from app.business_config_application.quick_replies import QuickRepliesService
from app.domain.business_config.errors import AssistantUnavailableError

router = APIRouter(prefix="/api")


def _quick_replies(request: Request) -> QuickRepliesService:
    service = getattr(request.app.state, "quick_replies", None)
    if service is None:
        raise AssistantUnavailableError("las respuestas rápidas no están disponibles en este servidor")
    return service


QuickReplies = Annotated[QuickRepliesService, Depends(_quick_replies)]
ReplyId = Annotated[str, Path(max_length=64)]


@router.get("/businesses/{slug}/quick-replies")
def list_quick_replies(slug: BusinessSlug, user: CurrentUser, service: QuickReplies) -> dict[str, Any]:
    return quick_replies_payload(service.view(user, slug))


@router.post("/businesses/{slug}/quick-replies", status_code=status.HTTP_201_CREATED)
def create_quick_reply(slug: BusinessSlug, user: CurrentUser, service: QuickReplies, body: Annotated[dict[str, Any], Body()]) -> dict[str, Any]:
    return quick_reply_payload(service.create(user, slug, body))


@router.put("/businesses/{slug}/quick-replies/{reply_id}")
def update_quick_reply(
    slug: BusinessSlug, reply_id: ReplyId, user: CurrentUser, service: QuickReplies, body: Annotated[dict[str, Any], Body()]
) -> dict[str, Any]:
    return quick_reply_payload(service.update(user, slug, reply_id, body))


@router.delete("/businesses/{slug}/quick-replies/{reply_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quick_reply(slug: BusinessSlug, reply_id: ReplyId, user: CurrentUser, service: QuickReplies) -> Response:
    service.delete(user, slug, reply_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/businesses/{slug}/quick-replies/files", status_code=status.HTTP_201_CREATED)
async def upload_quick_reply_file(slug: BusinessSlug, request: Request, user: CurrentUser, service: QuickReplies) -> dict[str, Any]:
    """Sube un archivo para una respuesta (el cuerpo es el archivo tal cual, como al enviarlo desde el chat)."""
    attachment = await read_upload(request)
    return quick_reply_file_payload(await run_in_threadpool(service.upload_file, user, slug, attachment))


@router.get("/businesses/{slug}/quick-replies/files/{file_id}")
def quick_reply_file(slug: BusinessSlug, file_id: ReplyId, user: CurrentUser, service: QuickReplies) -> Response:
    return file_response(service.file(user, slug, file_id))


@router.post("/businesses/{slug}/quick-replies/{reply_id}/use")
def use_quick_reply(slug: BusinessSlug, reply_id: ReplyId, user: CurrentUser, service: QuickReplies) -> dict[str, Any]:
    """Se usó en un chat: las más usadas salen primero."""
    return quick_reply_payload(service.mark_used(user, slug, reply_id))
