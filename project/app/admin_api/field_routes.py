"""Rutas de los campos del cliente: el catálogo de cada negocio y los valores de cada cliente."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

from app.admin_api.commerce_routes import _iso
from app.admin_api.errors import ApiError
from app.admin_api.routes import BusinessSlug, CurrentUser
from app.business_config_application.customer_fields import CustomerFieldService
from app.domain.business_config.customer_fields import (
    FIELD_KINDS,
    MAX_FIELD_NAME,
    MAX_FIELDS,
    MAX_OPTION,
    MAX_OPTIONS,
    MAX_TEXT_VALUE,
    YES_NO,
    CustomerField,
    FieldError,
    FieldValue,
)
from app.domain.business_config.errors import AssistantUnavailableError

router = APIRouter(prefix="/api/businesses/{slug}")


def _fields(request: Request) -> CustomerFieldService:
    service = getattr(request.app.state, "customer_fields", None)
    if service is None:
        raise AssistantUnavailableError("los campos del cliente no están disponibles en este servidor")
    return service


Fields = Annotated[CustomerFieldService, Depends(_fields)]


class NewCustomerField(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    name: str = Field(max_length=200)
    kind: str = Field(max_length=20)
    options: list[str] | None = Field(default=None, max_length=100)


class UpdateCustomerField(BaseModel):
    """Solo lo que cambia: el nombre y/o las opciones de una lista."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    name: str | None = Field(default=None, max_length=200)
    options: list[str] | None = Field(default=None, max_length=100)


class CustomerFieldValues(BaseModel):
    """Por id de campo, el valor nuevo; vacío o null lo deja vacío. Solo cambian los que llegan."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    values: dict[str, str | float | int | bool | None] = Field(max_length=60)


def field_payload(item: CustomerField) -> dict[str, Any]:
    return {"id": item.id, "name": item.name, "kind": item.kind, "options": list(item.options), "filled": item.filled}


def _value(item: FieldValue) -> str | bool | None:
    if item.value is None:
        return None
    return item.value == "true" if item.field.kind == YES_NO else item.value


def field_value_payload(item: FieldValue) -> dict[str, Any]:
    return {
        "field": field_payload(item.field), "value": _value(item), "updated_by": item.updated_by, "updated_at": _iso(item.updated_at),
    }


def _invalid(exc: FieldError) -> ApiError:
    return ApiError(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc), code="invalid", issues=[{"path": exc.field, "message": str(exc)}])


LIMITS = {"fields": MAX_FIELDS, "name": MAX_FIELD_NAME, "options": MAX_OPTIONS, "option": MAX_OPTION, "text": MAX_TEXT_VALUE}


@router.get("/customer-fields")
def customer_fields(slug: BusinessSlug, user: CurrentUser, service: Fields) -> dict[str, Any]:
    """Los campos del negocio, con cuántos clientes tienen lleno cada uno, los tipos que se pueden elegir y los límites."""
    return {"fields": [field_payload(item) for item in service.fields(user, slug)], "kinds": list(FIELD_KINDS), "limits": LIMITS}


@router.post("/customer-fields", status_code=status.HTTP_201_CREATED)
def create_customer_field(slug: BusinessSlug, body: NewCustomerField, user: CurrentUser, service: Fields) -> dict[str, Any]:
    try:
        return field_payload(service.create(user, slug, name=body.name, kind=body.kind, options=body.options))
    except FieldError as exc:
        raise _invalid(exc) from None


@router.patch("/customer-fields/{field_id}")
def update_customer_field(slug: BusinessSlug, field_id: str, body: UpdateCustomerField, user: CurrentUser, service: Fields) -> dict[str, Any]:
    try:
        return field_payload(service.update(user, slug, field_id, body.model_dump(exclude_unset=True)))
    except FieldError as exc:
        raise _invalid(exc) from None


@router.delete("/customer-fields/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer_field(slug: BusinessSlug, field_id: str, user: CurrentUser, service: Fields) -> Response:
    service.delete(user, slug, field_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/customers/{conversation_id}/fields")
def set_customer_field_values(slug: BusinessSlug, conversation_id: str, body: CustomerFieldValues, user: CurrentUser, service: Fields) -> dict[str, Any]:
    """Cambia los valores que llegan, todos o ninguno, y devuelve todos los campos del cliente."""
    try:
        return {"fields": [field_value_payload(item) for item in service.set_values(user, slug, conversation_id, body.values)]}
    except FieldError as exc:
        raise _invalid(exc) from None
