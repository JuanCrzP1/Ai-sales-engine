"""Rutas de las etiquetas de los clientes: el catálogo de cada negocio y las que lleva cada cliente."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

from app.admin_api.commerce_routes import customer_payload
from app.admin_api.errors import ApiError
from app.admin_api.routes import BusinessSlug, CurrentUser
from app.business_config_application.customer_labels import CustomerLabelService
from app.domain.business_config.customer_labels import LABEL_COLORS, Label, LabelError
from app.domain.business_config.errors import AssistantUnavailableError

router = APIRouter(prefix="/api/businesses/{slug}")


def _labels(request: Request) -> CustomerLabelService:
    service = getattr(request.app.state, "customer_labels", None)
    if service is None:
        raise AssistantUnavailableError("las etiquetas de los clientes no están disponibles en este servidor")
    return service


Labels = Annotated[CustomerLabelService, Depends(_labels)]


class NewLabel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    name: str = Field(max_length=120)
    color: str | None = Field(default=None, max_length=20)


class UpdateLabel(BaseModel):
    """Solo lo que cambia: el nombre y/o el color."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    name: str | None = Field(default=None, max_length=120)
    color: str | None = Field(default=None, max_length=20)


class CustomerLabels(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    label_ids: list[str] = Field(max_length=50)


def label_payload(label: Label) -> dict[str, Any]:
    return {"id": label.id, "name": label.name, "color": label.color, "customers": label.customers}


def _invalid(exc: LabelError) -> ApiError:
    return ApiError(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc), code="invalid", issues=[{"path": exc.field, "message": str(exc)}])


@router.get("/labels")
def labels(slug: BusinessSlug, user: CurrentUser, service: Labels) -> dict[str, Any]:
    """El catálogo de etiquetas del negocio, con cuántos clientes lleva cada una, y los colores que se pueden elegir."""
    return {"labels": [label_payload(item) for item in service.labels(user, slug)], "colors": list(LABEL_COLORS)}


@router.post("/labels", status_code=status.HTTP_201_CREATED)
def create_label(slug: BusinessSlug, body: NewLabel, user: CurrentUser, service: Labels) -> dict[str, Any]:
    try:
        return label_payload(service.create(user, slug, name=body.name, color=body.color))
    except LabelError as exc:
        raise _invalid(exc) from None


@router.patch("/labels/{label_id}")
def update_label(slug: BusinessSlug, label_id: str, body: UpdateLabel, user: CurrentUser, service: Labels) -> dict[str, Any]:
    try:
        return label_payload(service.update(user, slug, label_id, body.model_dump(exclude_unset=True)))
    except LabelError as exc:
        raise _invalid(exc) from None


@router.delete("/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_label(slug: BusinessSlug, label_id: str, user: CurrentUser, service: Labels) -> Response:
    service.delete(user, slug, label_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/customers/{conversation_id}/labels")
def set_customer_labels(slug: BusinessSlug, conversation_id: str, body: CustomerLabels, user: CurrentUser, service: Labels) -> dict[str, Any]:
    """Deja al cliente con esas etiquetas (y solo esas)."""
    try:
        return customer_payload(service.assign(user, slug, conversation_id, body.label_ids))
    except LabelError as exc:
        raise _invalid(exc) from None
