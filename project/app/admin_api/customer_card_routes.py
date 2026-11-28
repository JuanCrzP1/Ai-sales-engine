"""Rutas de la ficha de un cliente: verla, cambiar su valor y su responsable, y sus notas. Solo llegan a los negocios del usuario."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

from app.admin_api.commerce_routes import _iso, customer_payload, sale_payload
from app.admin_api.errors import ApiError
from app.admin_api.routes import BusinessSlug, CurrentUser
from app.business_config_application.customer_card import CustomerCardService
from app.domain.business_config.customer_card import Assignee, CustomerCard, CustomerCardError, CustomerNote
from app.domain.business_config.errors import AssistantUnavailableError

router = APIRouter(prefix="/api/businesses/{slug}/customers/{conversation_id}")


def _cards(request: Request) -> CustomerCardService:
    service = getattr(request.app.state, "customer_cards", None)
    if service is None:
        raise AssistantUnavailableError("la ficha de los clientes no está disponible en este servidor")
    return service


Cards = Annotated[CustomerCardService, Depends(_cards)]


class UpdateCard(BaseModel):
    """Solo lo que cambia. `amount` vacío quita el valor; `owner_id` vacío deja al cliente sin responsable."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    amount: str | None = Field(default=None, max_length=20)
    currency: str | None = Field(default=None, max_length=3)
    owner_id: str | None = Field(default=None, max_length=120)


class NewNote(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    body: str = Field(max_length=4000)


def _assignee(member: Assignee) -> dict[str, Any]:
    return {"user_id": member.user_id, "email": member.email, "role": member.role}


def note_payload(note: CustomerNote) -> dict[str, Any]:
    return {"id": note.id, "body": note.body, "author": note.author, "created_at": _iso(note.created_at)}


def card_payload(card: CustomerCard) -> dict[str, Any]:
    return {
        "customer": customer_payload(card.customer),
        "stage_since": _iso(card.stage_since),
        "owner": _assignee(card.owner) if card.owner else None,
        "assignees": [_assignee(member) for member in card.assignees],
        "purchases": [sale_payload(sale) for sale in card.purchases],
        "notes": [note_payload(note) for note in card.notes],
        "events": [
            {
                "id": event.id, "kind": event.kind, "source": event.source, "from_stage": event.from_stage, "to_stage": event.to_stage,
                "detail": event.detail, "actor": event.actor, "created_at": _iso(event.created_at),
            }
            for event in card.events
        ],
    }


def _invalid(exc: CustomerCardError) -> ApiError:
    return ApiError(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc), code="invalid", issues=[{"path": exc.field, "message": str(exc)}])


@router.get("")
def card(slug: BusinessSlug, conversation_id: str, user: CurrentUser, cards: Cards) -> dict[str, Any]:
    """La ficha del cliente: su etapa, valor, responsable, compras, notas e historial."""
    return card_payload(cards.card(user, slug, conversation_id))


@router.patch("")
def update_card(slug: BusinessSlug, conversation_id: str, body: UpdateCard, user: CurrentUser, cards: Cards) -> dict[str, Any]:
    try:
        return card_payload(cards.update(user, slug, conversation_id, body.model_dump(exclude_unset=True)))
    except CustomerCardError as exc:
        raise _invalid(exc) from None


@router.post("/notes", status_code=status.HTTP_201_CREATED)
def add_note(slug: BusinessSlug, conversation_id: str, body: NewNote, user: CurrentUser, cards: Cards) -> dict[str, Any]:
    try:
        return note_payload(cards.add_note(user, slug, conversation_id, body.body))
    except CustomerCardError as exc:
        raise _invalid(exc) from None


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(slug: BusinessSlug, conversation_id: str, note_id: str, user: CurrentUser, cards: Cards) -> Response:
    cards.delete_note(user, slug, conversation_id, note_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
