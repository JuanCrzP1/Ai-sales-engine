"""Identidad del negocio: quién es, dónde está, cómo atiende y a quién se dirige."""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.domain.business_config.engine_policy import MAX_PROFILE_ITEMS
from app.domain.business_config.primitives import CONNECTED, ContractModel, Phrases, Scope, Text, ensure_unique


class Coverage(ContractModel):
    type: Scope
    zones: list[Text] = Field(default_factory=list, max_length=MAX_PROFILE_ITEMS)


class Location(ContractModel):
    type: Literal["virtual", "fisico", "mixto"] = Field(description="virtual, fisico (local propio) o mixto.")
    address: str | None = None
    city: str | None = None
    coverage: Coverage | None = None


ServiceMode = Literal["virtual", "presencial", "domicilio", "recoger", "envio"]
Weekday = Literal["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
ClockTime = Annotated[str, Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")]


class OpeningHours(ContractModel):
    days: list[Weekday] = Field(min_length=1, max_length=7, description="Días en los que aplica este horario.")
    opens: ClockTime = Field(description="Hora de apertura (HH:MM, 24 h).")
    closes: ClockTime = Field(description="Hora de cierre (HH:MM, 24 h).")

    @model_validator(mode="after")
    def _opens_before_closes(self) -> "OpeningHours":
        ensure_unique(list(self.days), "días del horario")
        if self.opens >= self.closes:
            raise ValueError(f"el horario abre a las {self.opens} y cierra a las {self.closes}")
        return self


class TargetCustomer(ContractModel):
    segment: Text = Field(description="Tipo de cliente al que se dirige el negocio.")
    company_size: Text | None = None
    maturity: Text | None = Field(default=None, description="Situación típica del cliente al llegar.")
    roles: list[Text] | None = Field(default=None, description="Quién suele escribir o decidir la compra.")


class Identity(ContractModel):
    name: Text = Field(description="Nombre del negocio.")
    brand_name: Text | None = Field(default=None, description="Marca con la que el asistente presenta al negocio, si es distinta del nombre.")
    industry: Text = Field(description="Sector o tipo de negocio, en pocas palabras.", json_schema_extra=CONNECTED)
    description: Text = Field(description="Qué hace el negocio.")
    value_proposition: Text = Field(description="Promesa comercial: qué gana el cliente.", json_schema_extra=CONNECTED)
    positioning: Text | None = Field(default=None, description="A quién se dirige y qué problema resuelve.")
    differentiators: Phrases | None = Field(default=None, description="Por qué elegir este negocio y no otro.")
    location: Location | None = Field(default=None, description="Dónde está y a qué zonas atiende.")
    service_modes: Annotated[list[ServiceMode], Field(max_length=5)] | None = Field(
        default=None, description="Cómo recibe el cliente el servicio o producto."
    )
    target_customer: TargetCustomer | None = Field(default=None, description="Cliente ideal.")
    credibility: Phrases | None = Field(default=None, description="Pruebas de confianza: casos, resultados, trayectoria.")
    opening_hours: Annotated[list[OpeningHours], Field(max_length=14)] | None = Field(default=None, description="Horarios de atención.")
