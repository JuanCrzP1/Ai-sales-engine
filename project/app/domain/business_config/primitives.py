"""Piezas comunes del contrato: tipos de valor, marcas del esquema y el modelo base."""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.domain.business_config.engine_policy import (
    MAX_MESSAGE_CHARS,
    MAX_POLICY_CHARS,
    MAX_PROFILE_ITEM_CHARS,
    MAX_PROFILE_ITEMS,
)

SCHEMA_VERSION = "1.0"

Audience = Literal["cliente", "avanzado", "sistema"]
EngineStatus = Literal["conectado", "pendiente", "programado", "solo panel"]

CLIENT = {"x-audience": "cliente"}
ADVANCED = {"x-audience": "avanzado"}
SYSTEM = {"x-audience": "sistema"}
CONNECTED = {"x-engine": "conectado"}
PENDING = {"x-engine": "pendiente"}
# Lo enviará la plataforma cuando exista el evento que lo dispara (p. ej. el equipo confirma un pago): se guarda y no va a la IA.
SCHEDULED = {"x-engine": "programado"}
# Solo para el equipo en el panel (una etiqueta, un código interno): nunca va al motor ni al cliente.
PANEL_ONLY = {"x-engine": "solo panel"}


def _not_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("no puede estar vacío")
    return value


# Los textos se conservan tal cual (incluidos saltos de línea de los YAML) para no alterar el prompt.
Text = Annotated[str, AfterValidator(_not_blank)]
Slug = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_]*$")]
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")]
CurrencyCode = Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
Amount = Annotated[int | float, Field(ge=0)]
# Frase corta (un diferenciador, una pregunta, una regla...). Todas las listas de frases comparten límites.
Phrase = Annotated[Text, Field(max_length=MAX_PROFILE_ITEM_CHARS)]
Phrases = Annotated[list[Phrase], Field(max_length=MAX_PROFILE_ITEMS)]
PolicyText = Annotated[Text, Field(max_length=MAX_POLICY_CHARS)]
MessageText = Annotated[Text, Field(max_length=MAX_MESSAGE_CHARS)]
Scope = Literal["local", "nacional", "internacional"]


class ContractModel(BaseModel):
    # Los errores de validación no repiten el valor recibido: podría ser un dato de pago escrito en claro.
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class SecretRef(ContractModel):
    """Referencia a un dato sensible guardado fuera del contrato (`<origen>:<clave>`)."""

    secret_ref: Annotated[str, Field(pattern=r"^[a-z_]+:.+$")]


def ensure_unique(values: list[str], label: str) -> None:
    repeated = sorted({value for value in values if values.count(value) > 1})
    if repeated:
        raise ValueError(f"{label} repetidos: {repeated}")
