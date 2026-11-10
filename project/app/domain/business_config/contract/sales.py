"""Estrategia comercial del asistente."""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.domain.business_config.engine_policy import MAX_CUSTOMER_PROBLEMS, MAX_PROFILE_ITEMS
from app.domain.business_config.primitives import ADVANCED, CONNECTED, ContractModel, Identifier, Phrase, Phrases, Text, ensure_unique


class BuyingMotivation(ContractModel):
    primary: Text
    secondary: str | None = None


class SalesAngle(ContractModel):
    signals: list[Text] = Field(default_factory=list, description="Cuándo usar el ángulo: frases del cliente.")
    messages: list[Text] = Field(default_factory=list, description="Qué decir con este ángulo.")


class Motivation(ContractModel):
    """Un motivo de compra: qué significa, cómo reconocerlo y cómo venderle a quien lo tiene."""

    motivation: Identifier = Field(description="Motivo de compra (p. ej. tiempo, dinero).")
    description: Text | None = Field(default=None, description="Qué significa este motivo para el cliente.")
    signals: list[Text] | None = Field(default=None, description="Frases del cliente que revelan este motivo.")
    angle: SalesAngle | None = Field(default=None, description="Ángulo de venta para este motivo.")

    @model_validator(mode="after")
    def _has_content(self) -> "Motivation":
        if self.description is None and self.angle is None:
            raise ValueError(f"el motivo {self.motivation} necesita una descripción o un ángulo de venta")
        return self


UrgencyLevel = Literal["alto", "medio", "bajo"]


class CustomerProblem(ContractModel):
    id: Identifier = Field(json_schema_extra=CONNECTED)
    impacts: list[Text] | None = Field(default=None, description="Qué le causa el problema al cliente.", json_schema_extra=CONNECTED)
    signals: list[Text] | None = Field(default=None, description="Frases del cliente que revelan el problema.", json_schema_extra=ADVANCED)
    monetization: list[Text] | None = Field(default=None, description="Cómo el problema le cuesta dinero al cliente.", json_schema_extra=ADVANCED)
    urgency_levels: dict[UrgencyLevel, list[Text]] | None = Field(default=None, description="Mensajes según la urgencia.", json_schema_extra=ADVANCED)
    recommended_angles: list[Identifier] | None = Field(default=None, description="Ángulos de venta para este problema.", json_schema_extra=ADVANCED)
    solutions: Annotated[list[Text], Field(min_length=1)] | None = Field(
        default=None, description="Qué parte de la solución atiende este problema.", json_schema_extra=ADVANCED
    )


class UseCase(ContractModel):
    name: Text = Field(json_schema_extra=CONNECTED)
    signals: list[Text] = Field(default_factory=list)
    approach: Text = Field(description="Enfoque de la solución para este caso.")


class Solution(ContractModel):
    process_steps: Phrases | None = Field(default=None, description="Pasos que sigue el cliente para comprar o recibir el servicio.")
    requirements: Phrases | None = Field(default=None, description="Requisitos que debe cumplir el cliente.")


class OfferMix(ContractModel):
    """Tipos de oferta en texto libre (no son ids de la oferta)."""

    core: list[Text] = Field(default_factory=list, description="Ofertas principales.")
    upsell: list[Text] = Field(default_factory=list, description="Mejoras para vender más.")
    cross_sell: list[Text] = Field(default_factory=list, description="Complementos para vender junto.")


class OfferPresentation(ContractModel):
    single_offer: Phrases | None = Field(default=None, description="Cómo presentar cuando hay una sola opción.")
    multiple_offers: Phrases | None = Field(default=None, description="Cómo presentar cuando hay varias opciones.")


class RecommendationRule(ContractModel):
    when: Phrase = Field(description="Situación o necesidad del cliente.")
    recommend: Identifier = Field(description="Plan, producto o categoría que se recomienda. Si no está en la oferta, el diagnóstico lo señala.")


class Discovery(ContractModel):
    questions: Phrases | None = Field(default=None, description="Preguntas para entender al cliente.", json_schema_extra=CONNECTED)
    objectives: Phrases | None = Field(default=None, description="Qué debe averiguar el asistente.", json_schema_extra={**CONNECTED, **ADVANCED})


class Qualification(ContractModel):
    detect_offer_fit: bool | None = Field(default=None, description="true: valida si la oferta encaja antes de empujar el cierre.")


class SupportPolicy(ContractModel):
    explain_first: bool | None = Field(default=None, description="true: primero aclara la duda. false: vende directo.")
    sell_after: bool | None = Field(default=None, description="true: después de explicar, vuelve a llevar al cliente a avanzar.")
    rules: Phrases | None = Field(default=None, description="Reglas de atención del negocio.")


class ConversationFlow(ContractModel):
    """Cómo avanza la conversación comercial."""

    # Lista abierta: cada negocio puede tener sus pasos (p. ej. validate_requirements, de la escuela de conducción).
    steps: Annotated[list[Identifier], Field(min_length=1)] | None = Field(default=None, description="Pasos que idealmente sigue la conversación, en orden.")
    required_flow: list[Identifier] | None = Field(default=None, description="Secuencia mínima que debe respetar la conversación.")
    forbid: list[Identifier] | None = Field(default=None, description="Lo que el asistente no debe hacer en este negocio (p. ej. responder_sin_solucion).")
    no_skip_steps: bool | None = Field(default=None, description="true: no se saltan pasos de la conversación.")
    guided_process: bool | None = Field(default=None, description="true: guía al cliente paso a paso en un proceso (trámites, matrículas).")


class ObjectionHandling(ContractModel):
    topic: Identifier = Field(description="Objeción que se atiende (p. ej. price).")
    acknowledge: Phrases | None = Field(default=None, description="Cómo reconocer la objeción.")
    reframe: Phrases | None = Field(default=None, description="Cómo replantearla.")
    proof: Phrases | None = Field(default=None, description="Pruebas que la desmienten.")
    redirect: Phrases | None = Field(default=None, description="Cómo volver al siguiente paso.")
    rules: Phrases | None = Field(default=None, description="Reglas al responder esta objeción.")


ClosingStrategy = Literal["direct_sale", "lead_capture", "booking", "checkout"]


class Closing(ContractModel):
    strategy: ClosingStrategy = Field(
        description="Tipo de cierre: direct_sale (confirmar la compra), lead_capture (capturar datos), booking (agendar) o checkout (enviar el pago)."
    )
    required_data: list[Identifier] | None = Field(default=None, description="Datos que necesita el cierre (name, phone, address...).")
    purchase_signals: Phrases | None = Field(default=None, description="Frases que indican intención de compra.")
    high_intent_actions: Phrases | None = Field(default=None, description="Qué hacer ante una intención de compra alta.")
    next_steps: Phrases | None = Field(default=None, description="Siguientes pasos que el asistente propone.")
    micro_commitments: Phrases | None = Field(default=None, description="Compromisos pequeños para avanzar.")
    rules: Phrases | None = Field(default=None, description="Reglas de cierre del negocio.")


class Sales(ContractModel):
    """Estrategia comercial.

    Básica (el cliente la escribe en lenguaje natural): motivos de compra, problemas e impactos,
    beneficios, argumentos, preguntas, recomendaciones e instrucciones. Avanzada (opcional): el resto.
    """

    buying_motivation: BuyingMotivation | None = Field(default=None, description="Motivo principal y secundario de compra.", json_schema_extra=CONNECTED)
    motivations: list[Motivation] | None = Field(
        default=None, description="Cada motivo de compra: qué significa, cómo reconocerlo y con qué ángulo venderle.", json_schema_extra={**CONNECTED, **ADVANCED}
    )
    customer_problems: list[CustomerProblem] | None = Field(
        default=None, max_length=MAX_CUSTOMER_PROBLEMS, description="Problemas del cliente que el negocio resuelve.", json_schema_extra=CONNECTED
    )
    pain_points: Phrases | None = Field(default=None, description="Problemas del cliente en sus palabras.", json_schema_extra=CONNECTED)
    use_cases: list[UseCase] | None = Field(default=None, description="Casos de uso típicos.", json_schema_extra={**CONNECTED, **ADVANCED})
    benefits: Phrases | None = Field(default=None, description="Resultados que obtiene el cliente.", json_schema_extra=CONNECTED)
    arguments: Phrases | None = Field(default=None, description="Argumentos de venta.", json_schema_extra=CONNECTED)
    solution: Solution | None = Field(default=None, description="Qué pasos sigue el cliente y qué requisitos debe cumplir.", json_schema_extra=CONNECTED)
    offer_mix: OfferMix | None = Field(default=None, description="Ofertas principales, mejoras y complementos.", json_schema_extra={**CONNECTED, **ADVANCED})
    offer_presentation: OfferPresentation | None = Field(default=None, description="Cómo presentar las opciones.", json_schema_extra={**CONNECTED, **ADVANCED})
    recommendation_rules: Annotated[list[RecommendationRule], Field(max_length=MAX_PROFILE_ITEMS)] | None = Field(
        default=None, description="Qué recomendar en cada situación.", json_schema_extra=CONNECTED
    )
    discovery: Discovery | None = None
    qualification: Qualification | None = Field(default=None, description="Cómo calificar al cliente.", json_schema_extra={**CONNECTED, **ADVANCED})
    support: SupportPolicy | None = Field(default=None, description="Cómo atender preguntas de información.", json_schema_extra={**CONNECTED, **ADVANCED})
    conversation_flow: ConversationFlow | None = Field(default=None, description="Pasos de la conversación y reglas para avanzar.", json_schema_extra={**CONNECTED, **ADVANCED})
    objections: list[ObjectionHandling] | None = Field(default=None, description="Manejo de objeciones (precio y otras).", json_schema_extra={**CONNECTED, **ADVANCED})
    closing: Closing | None = Field(default=None, description="Estrategia y reglas de cierre.", json_schema_extra={**CONNECTED, **ADVANCED})
    instructions: Phrases | None = Field(default=None, description="Cómo debe vender el asistente en este negocio.", json_schema_extra=CONNECTED)

    @model_validator(mode="after")
    def _references_exist(self) -> "Sales":
        ensure_unique([problem.id for problem in self.customer_problems or []], "ids de problema")
        motivations = self.motivations or []
        ensure_unique([entry.motivation for entry in motivations], "motivos de compra")
        ensure_unique([objection.topic for objection in self.objections or []], "objeciones")
        angles = {entry.motivation for entry in motivations if entry.angle is not None}
        recommended = {angle for problem in self.customer_problems or [] for angle in problem.recommended_angles or []}
        if angles and recommended - angles:
            raise ValueError(f"problemas que recomiendan ángulos inexistentes: {sorted(recommended - angles)}")
        # Si el negocio explica sus motivos, todo motivo que use debe estar explicado.
        explained = {entry.motivation for entry in motivations if entry.description is not None}
        if explained:
            buying = [m for m in (self.buying_motivation.primary, self.buying_motivation.secondary) if m] if self.buying_motivation else []
            orphans = sorted((set(buying) | angles) - explained)
            if orphans:
                raise ValueError(f"motivos de compra sin descripción: {orphans}")
        return self
