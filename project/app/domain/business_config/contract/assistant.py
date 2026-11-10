"""Cómo atiende el asistente: capacidades, mensajes, estilo y preguntas frecuentes."""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.domain.business_config.engine_policy import (
    DEFAULT_RESPONSE_LENGTH,
    MAX_FAQ_ANSWER_CHARS,
    MAX_FAQ_QUESTION_CHARS,
    MAX_FAQS,
    MAX_MESSAGE_CHARS,
    MAX_TONE_CHARS,
    MIN_MAX_WORDS,
    RESPONSE_LENGTH_MAX_WORDS,
    RESPONSE_LENGTH_WORD_RANGES,
    ResponseLength,
)
from app.domain.business_config.primitives import ADVANCED, CONNECTED, ContractModel, MessageText, Phrases, Text, ensure_unique


class ClosingMethods(ContractModel):
    payment_link: bool
    human_handoff: bool
    data_collection: bool

    @model_validator(mode="after")
    def _at_least_one(self) -> "ClosingMethods":
        if not (self.payment_link or self.human_handoff or self.data_collection):
            raise ValueError("debe haber al menos un método de cierre activo")
        return self


class DataCollection(ContractModel):
    enabled: bool = Field(json_schema_extra=CONNECTED)
    # Lista abierta: los YAML no la limitan y el motor usa cualquier valor (p. ej. nombre, telefono, direccion).
    fields: Phrases = Field(default_factory=list, description="Datos que el asistente puede pedir al cliente; solo esos.", json_schema_extra=CONNECTED)

    @model_validator(mode="after")
    def _fields_when_enabled(self) -> "DataCollection":
        if self.enabled and not self.fields:
            raise ValueError("data_collection activo requiere campos")
        return self


class Restrictions(ContractModel):
    disallowed_channels: list[Text] = Field(default_factory=list, description="Canales por los que el negocio no atiende.")
    disallowed_actions: list[Text] = Field(default_factory=list, description="Acciones que el negocio no realiza (p. ej. llamadas).")


class Capabilities(ContractModel):
    """Canales, acciones, métodos de cierre y datos que se piden al cliente."""

    service_channels: list[Text] = Field(default_factory=list, description="Canales de atención al cliente.", json_schema_extra=CONNECTED)
    product_channels: list[Text] = Field(
        default_factory=list, description="Canales por los que funciona el producto que se vende.", json_schema_extra=CONNECTED
    )
    actions_primary: list[Text] = Field(default_factory=list, description="Acciones de venta.", json_schema_extra=CONNECTED)
    actions_support: list[Text] = Field(default_factory=list, description="Acciones de apoyo.", json_schema_extra=CONNECTED)
    closing_methods: ClosingMethods = Field(description="Cómo puede cerrar el asistente una venta.", json_schema_extra=CONNECTED)
    data_collection: DataCollection = Field(description="Datos que el asistente pide al cliente.")
    restrictions: Restrictions | None = Field(default=None, description="Lo que el negocio no hace.")

    @model_validator(mode="after")
    def _coherent(self) -> "Capabilities":
        if not (self.actions_primary or self.actions_support):
            raise ValueError("debe haber al menos una acción")
        if self.closing_methods.data_collection and not self.data_collection.enabled:
            raise ValueError("el cierre pidiendo datos requiere data_collection activo")
        return self


class WelcomeMessage(ContractModel):
    """Las dos modalidades de saludo, según `enabled`.

    - `true`: ante un saludo sin más en una conversación nueva, el sistema envía `text` tal cual, sin IA.
    - `false`: no envía el mensaje fijo y responde la IA. El texto se conserva para cuando se reactive.

    Un saludo con una intención ("hola, ¿qué precio tiene?") siempre lo responde la IA.
    """

    enabled: bool = Field(description="true: envía el mensaje inicial fijo, sin IA. false: no lo envía y responde la IA.")
    text: str = Field(default="", max_length=MAX_MESSAGE_CHARS, description="Mensaje de apertura que recibe el cliente.")

    @model_validator(mode="after")
    def _text_when_enabled(self) -> "WelcomeMessage":
        if self.enabled and not self.text.strip():
            raise ValueError("el mensaje de bienvenida activo requiere texto")
        return self


class Messages(ContractModel):
    welcome: WelcomeMessage = Field(description="Saludo de cada conversación nueva: mensaje fijo o respuesta de la IA.", json_schema_extra=CONNECTED)
    payment_reported: MessageText | None = Field(default=None, description="Respuesta exacta cuando el cliente reporta un pago.", json_schema_extra=CONNECTED)
    payment_confirmed: MessageText | None = Field(default=None, description="Mensaje cuando el pago queda confirmado.", json_schema_extra=CONNECTED)
    after_sale: MessageText | None = Field(default=None, description="Mensaje después de una compra.")
    data_request: MessageText | None = Field(default=None, description="Mensaje para pedir los datos del cliente.")
    follow_up: MessageText | None = Field(default=None, description="Mensaje de seguimiento a un cliente que no respondió.")
    human_handoff: MessageText | None = Field(default=None, description="Mensaje al pasar la conversación a una persona.")


class ResponseStyle(ContractModel):
    """Cómo se comunica el asistente.

    Longitud (en el prompt y al recortar la respuesta, en todos los canales): short = cortas,
    medium = equilibradas, long = detalladas; límites en `engine_policy`.
    """

    tone: Annotated[Text, Field(max_length=MAX_TONE_CHARS)] | None = Field(default=None, description="Tono del asistente (p. ej. cercano y claro).", json_schema_extra=CONNECTED)
    voice: Annotated[Text, Field(max_length=MAX_TONE_CHARS)] | None = Field(default=None, description="Personalidad de la marca.")
    formality: Literal["informal", "neutral", "formal"] | None = Field(default=None, description="informal (tutea), neutral o formal (usted).")
    emojis: bool | None = Field(default=None, description="Si el asistente puede usar emojis.")
    instructions: Phrases | None = Field(default=None, description="Cómo debe expresarse el asistente en este negocio.")
    length: ResponseLength = Field(
        default=DEFAULT_RESPONSE_LENGTH, description="short (cortas), medium (equilibradas) o long (detalladas).", json_schema_extra=CONNECTED
    )
    max_words: Annotated[int, Field(ge=MIN_MAX_WORDS)] | None = Field(
        default=None,
        description="Ajuste dentro del rango de la opción elegida. Si falta, el límite de la opción.",
        json_schema_extra={**CONNECTED, **ADVANCED},
    )

    @model_validator(mode="after")
    def _max_words_matches_length(self) -> "ResponseStyle":
        if self.max_words is not None:
            low, high = RESPONSE_LENGTH_WORD_RANGES[self.length]
            if self.max_words < low or (high is not None and self.max_words > high):
                allowed = f"{low}-{high}" if high is not None else f"{low} o más"
                raise ValueError(f"max_words={self.max_words} no corresponde a length={self.length} (permitido {allowed})")
        return self

    def effective_max_words(self) -> int:
        return self.max_words if self.max_words is not None else RESPONSE_LENGTH_MAX_WORDS[self.length]


class Faq(ContractModel):
    question: Annotated[Text, Field(max_length=MAX_FAQ_QUESTION_CHARS)] = Field(description="Pregunta tal como la haría el cliente.")
    answer: Annotated[Text, Field(max_length=MAX_FAQ_ANSWER_CHARS)] = Field(description="Respuesta oficial del negocio.")


class Knowledge(ContractModel):
    faqs: list[Faq] = Field(default_factory=list, max_length=MAX_FAQS, description="Preguntas frecuentes con su respuesta oficial.", json_schema_extra=CONNECTED)

    @model_validator(mode="after")
    def _unique_questions(self) -> "Knowledge":
        ensure_unique([faq.question for faq in self.faqs], "preguntas frecuentes")
        return self
