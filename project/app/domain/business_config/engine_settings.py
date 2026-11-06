"""Ajustes técnicos de cada negocio: lo que el motor necesita y no es una decisión comercial.

Se guardan aparte del documento comercial (`BusinessConfig`), en `engine-settings.json` o en la tabla
`business_engine_settings`. El negocio no los edita y el panel no los recibe. Si faltan, el motor usa
sus valores por defecto.

`legacy` conserva, con su ruta original, las estructuras antiguas de los YAML que aún no tienen lugar
propio. Se retira cuando se retiren los YAML.
"""
from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from app.domain.business_config.primitives import SCHEMA_VERSION, ContractModel, Slug

LEGACY_SECTIONS = ("business", "sales", "pricing", "inventory", "config")


class ConversationWindows(ContractModel):
    # Mínimo 1: el motor trata 0 como "sin valor" y aplica sus valores por defecto (15 min, 4 h).
    active_window_minutes: Annotated[int, Field(ge=1)] = Field(description="Minutos sin mensajes tras los que la conversación deja de estar activa.")
    reset_hours: Annotated[int, Field(ge=1)] = Field(description="Horas sin mensajes tras las que la conversación empieza de nuevo.")


class EngineFlags(ContractModel):
    ai_first: bool = Field(description="true: prioriza la respuesta generada por IA.")
    allow_fallback: bool = Field(description="true: permite la respuesta de respaldo automática.")
    log_level: Literal["debug", "info", "warning", "error"] = Field(description="Nivel de registros.")


class EngineSettings(ContractModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    tenant_slug: Slug
    conversation: ConversationWindows | None = None
    flags: EngineFlags | None = None
    legacy: dict[str, Any] = Field(default_factory=dict, description="Campos de los YAML sin lugar propio, con su ruta original.")

    @model_validator(mode="after")
    def _known_sections(self) -> "EngineSettings":
        unexpected = sorted(set(self.legacy) - set(LEGACY_SECTIONS))
        if unexpected:
            raise ValueError(f"secciones desconocidas en legacy: {unexpected}")
        return self
