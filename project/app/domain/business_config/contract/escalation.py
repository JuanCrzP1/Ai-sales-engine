"""Cuándo pasa el asistente una conversación a una persona del equipo (Asistente IA → Cómo atiende → «Cuándo pasar a una persona»).

Es comportamiento del asistente: se publica con el resto y queda en el historial de versiones. El horario del equipo y lo que pasa
después del traspaso son de la operación (Configuración → Atención humana, `domain/business_config/attention.py`).

Lo decide la IA con estas reglas como instrucciones, nunca reglas de palabras (`infrastructure/ai/prompting/sections/escalation.py`).
Con los valores por defecto el asistente se comporta igual que antes de existir esta sección: pasa el chat cuando el cliente pide una
persona, reclama o avisa que ya pagó.
"""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from app.domain.business_config.engine_policy import MAX_ESCALATION_TOPIC_CHARS, MAX_ESCALATION_TOPICS, MAX_MESSAGE_CHARS
from app.domain.business_config.primitives import CONNECTED, ContractModel, Text

EscalationTopic = Annotated[Text, Field(max_length=MAX_ESCALATION_TOPIC_CHARS)]
EscalationTopics = Annotated[list[EscalationTopic], Field(max_length=MAX_ESCALATION_TOPICS)]
OnRequest = Literal["always", "offer_help_first"]


def _key(topic: str) -> str:
    return " ".join(str(topic).split()).casefold()


class Escalation(ContractModel):
    on_request: OnRequest = Field(
        default="always",
        description=(
            "Si el cliente pide hablar con una persona: always (lo pasa) u offer_help_first (primero le ofrece resolverlo una vez; "
            "si insiste, lo pasa)."
        ),
        json_schema_extra=CONNECTED,
    )
    always_topics: EscalationTopics = Field(
        default_factory=list,
        description="Temas que siempre van al equipo (p. ej. reembolsos, garantías).",
        json_schema_extra=CONNECTED,
    )
    never_topics: EscalationTopics = Field(
        default_factory=list,
        description="Temas que resuelve el asistente sin pasar el chat, salvo que el cliente pida una persona (p. ej. precios, horarios).",
        json_schema_extra=CONNECTED,
    )
    when_stuck: bool = Field(
        default=False,
        description="Pasar el chat si la conversación se estanca: el cliente repite lo mismo o está frustrado y no se le puede ayudar.",
        json_schema_extra=CONNECTED,
    )
    instructions: Annotated[Text, Field(max_length=MAX_MESSAGE_CHARS)] | None = Field(
        default=None,
        description="Otras indicaciones del negocio sobre cuándo pasar el chat a una persona.",
        json_schema_extra=CONNECTED,
    )

    @field_validator("always_topics", "never_topics")
    @classmethod
    def _unique(cls, topics: list[str]) -> list[str]:
        keys = [_key(topic) for topic in topics]
        repeated = sorted({key for key in keys if keys.count(key) > 1})
        if repeated:
            raise ValueError(f"temas repetidos: {repeated}")
        return topics

    @model_validator(mode="after")
    def _not_in_both(self) -> "Escalation":
        both = sorted({_key(topic) for topic in self.always_topics} & {_key(topic) for topic in self.never_topics})
        if both:
            raise ValueError(f"un tema no puede ir siempre al equipo y nunca a la vez: {both}")
        return self

    @property
    def is_default(self) -> bool:
        """Si el negocio no cambió nada: el asistente se comporta como antes de existir esta sección."""
        return self == Escalation()
