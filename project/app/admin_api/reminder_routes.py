"""Rutas de los recordatorios del equipo: los del negocio (o los míos) y los de cada cliente."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

from app.admin_api.commerce_routes import _iso
from app.admin_api.errors import ApiError
from app.admin_api.routes import BusinessSlug, CurrentUser
from app.business_config_application.reminders import ReminderService
from app.domain.business_config.errors import AssistantUnavailableError
from app.domain.business_config.reminders import FOR_ME, Reminder, ReminderError

router = APIRouter(prefix="/api/businesses/{slug}")


def _reminders(request: Request) -> ReminderService:
    service = getattr(request.app.state, "reminders", None)
    if service is None:
        raise AssistantUnavailableError("los recordatorios no están disponibles en este servidor")
    return service


Reminders = Annotated[ReminderService, Depends(_reminders)]


class NewReminderBody(BaseModel):
    """Sin `assignee_id`, queda para quien lo crea; con `assignee_id` vacío, sin responsable."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    title: str = Field(max_length=400)
    due_at: str = Field(max_length=40)
    assignee_id: str | None = Field(default=None, max_length=120)


class MarkReminder(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    done: bool


def reminder_payload(item: Reminder) -> dict[str, Any]:
    return {
        "id": item.id, "conversation_id": item.conversation_id, "customer_name": item.customer_name, "customer_contact": item.customer_contact,
        "title": item.title, "due_at": _iso(item.due_at),
        "assignee": {"user_id": item.assignee_id, "label": item.assignee_label} if item.assignee_id else None,
        "created_by": item.created_by, "created_at": _iso(item.created_at), "done_at": _iso(item.done_at), "done_by": item.done_by,
    }


def _invalid(exc: ReminderError) -> ApiError:
    return ApiError(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc), code="invalid", issues=[{"path": exc.field, "message": str(exc)}])


@router.get("/reminders")
def reminders(
    slug: BusinessSlug, user: CurrentUser, service: Reminders, done: Annotated[bool, Query()] = False, mine: Annotated[bool, Query()] = False,
) -> list[dict[str, Any]]:
    """Los pendientes por fecha (o los hechos, el último primero); con `mine`, solo los de quien pide."""
    return [reminder_payload(item) for item in service.reminders(user, slug, done=done, mine=mine)]


@router.post("/customers/{conversation_id}/reminders", status_code=status.HTTP_201_CREATED)
def create_reminder(slug: BusinessSlug, conversation_id: str, body: NewReminderBody, user: CurrentUser, service: Reminders) -> dict[str, Any]:
    assignee = body.assignee_id if "assignee_id" in body.model_fields_set else FOR_ME
    try:
        return reminder_payload(service.create(user, slug, conversation_id, title=body.title, due_at=body.due_at, assignee_id=assignee))
    except ReminderError as exc:
        raise _invalid(exc) from None


@router.patch("/reminders/{reminder_id}")
def mark_reminder(slug: BusinessSlug, reminder_id: str, body: MarkReminder, user: CurrentUser, service: Reminders) -> dict[str, Any]:
    return reminder_payload(service.mark(user, slug, reminder_id, done=body.done))


@router.delete("/reminders/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(slug: BusinessSlug, reminder_id: str, user: CurrentUser, service: Reminders) -> Response:
    service.delete(user, slug, reminder_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
