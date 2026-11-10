"""Condiciones comerciales: promociones, financiación y políticas."""
from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.domain.business_config.engine_policy import MAX_PROMOTIONS
from app.domain.business_config.primitives import ADVANCED, CONNECTED, ContractModel, Phrase, PolicyText, Text, ensure_unique


class Promotion(ContractModel):
    name: Phrase = Field(description="Nombre con el que se presenta la promoción.")
    details: Phrase = Field(description="Qué incluye la promoción y a qué aplica.")
    valid_until: date | None = Field(default=None, description="Último día de vigencia.")


class Financing(ContractModel):
    available: bool
    providers: list[Text] = Field(default_factory=list, description="Entidades con las que se financia.")
    options: list[Text] = Field(default_factory=list, description="Modalidades (abono, cuotas...).")


class Policies(ContractModel):
    """Políticas oficiales que el asistente comunica tal cual cuando el cliente las pregunta."""

    warranty: PolicyText | None = Field(default=None, description="Garantía: qué cubre y por cuánto tiempo.")
    returns: PolicyText | None = Field(default=None, description="Cambios y devoluciones.")
    cancellation: PolicyText | None = Field(default=None, description="Cancelaciones y reembolsos (citas, reservas, suscripciones).")


class Terms(ContractModel):
    """Condiciones comerciales y políticas del negocio."""

    conditions: list[Text] | None = Field(default=None, description="Condiciones reales de compra.", json_schema_extra=CONNECTED)
    price_framing: Literal["directo", "comparativo"] | None = Field(
        default=None, description="Cómo responder si el cliente duda del precio.", json_schema_extra={**CONNECTED, **ADVANCED}
    )
    roi_break_even_sales: Annotated[int, Field(ge=1)] | None = Field(
        default=None, description="Ventas al mes con las que el cliente recupera la inversión.", json_schema_extra={**CONNECTED, **ADVANCED}
    )
    roi_break_even_bookings: Annotated[int, Field(ge=1)] | None = Field(
        default=None, description="Reservas con las que el cliente recupera la inversión.", json_schema_extra={**CONNECTED, **ADVANCED}
    )
    roi_hints: list[Text] | None = Field(
        default=None, description="Argumentos de retorno de la inversión.", json_schema_extra={**CONNECTED, **ADVANCED}
    )
    price_note: Text | None = Field(default=None, description="Aclaración sobre cómo se confirma el precio.", json_schema_extra=CONNECTED)
    promotions: Annotated[list[Promotion], Field(max_length=MAX_PROMOTIONS)] | None = Field(
        default=None, description="Únicas promociones o descuentos que el asistente puede ofrecer.", json_schema_extra=CONNECTED
    )
    financing: Financing | None = Field(default=None, description="Financiación disponible.", json_schema_extra=CONNECTED)
    policies: Policies | None = Field(default=None, description="Garantía, devoluciones y cancelaciones.", json_schema_extra=CONNECTED)

    @model_validator(mode="after")
    def _unique_promotions(self) -> "Terms":
        ensure_unique([promotion.name for promotion in self.promotions or []], "promociones")
        return self
