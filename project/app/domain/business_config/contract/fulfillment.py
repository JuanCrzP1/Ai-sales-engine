"""Entrega: domicilio, envío, recogida y agenda."""
from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from app.domain.business_config.primitives import Amount, ContractModel, Scope, Text


class Cost(ContractModel):
    type: Literal["fijo", "variable", "gratis"]
    value: Amount

    @model_validator(mode="after")
    def _free_costs_nothing(self) -> "Cost":
        if self.type == "gratis" and self.value != 0:
            raise ValueError(f"un costo gratis no puede valer {self.value}")
        return self


class TimeWindow(ContractModel):
    min: str = Field(default="", description="Tiempo mínimo, en texto (p. ej. 30 min, 2 dias).")
    max: str = ""


class Delivery(ContractModel):
    available: bool
    type: Literal["propio", "tercero"] | None = None
    zones: list[Text] = Field(default_factory=list)
    cost: Cost | None = None
    time: TimeWindow | None = None


class Shipping(ContractModel):
    available: bool
    scope: Scope | None = None
    providers: list[Text] = Field(default_factory=list)
    cost: Cost | None = None
    time: TimeWindow | None = None


class Pickup(ContractModel):
    available: bool
    instructions: str = ""


class Scheduling(ContractModel):
    required: bool = Field(description="Si el servicio requiere agendar una cita o reserva.")


class Fulfillment(ContractModel):
    """Cómo recibe el cliente lo que compra. Los modos que no aplican se omiten."""

    delivery: Delivery | None = None
    shipping: Shipping | None = None
    pickup: Pickup | None = None
    scheduling: Scheduling | None = None
