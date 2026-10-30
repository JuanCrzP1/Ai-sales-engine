"""Contrato global de configuración de negocios (BusinessConfig v1).

Fuente canónica del contrato. Desde estos modelos se generan el JSON Schema publicado
(`project/config/contracts/v1/business-config.schema.json`, con `scripts/export_business_config_schema.py`),
los tipos TypeScript del panel (`apps/admin-web/src/contracts/businessConfig.v1.ts`, con
`scripts/generate_business_config_types.py`) y la referencia de campos de
`docs/business-config-traceability.md` (con `scripts/generate_traceability_matrix.py`).

Un único documento por negocio, con secciones comunes a todos los modelos comerciales; cada negocio
rellena solo las que necesita (las opcionales se omiten). Los modelos de oferta son `plans` (planes o
servicios, con pago único, mensual, anual o de instalación) y `catalog` (productos por categoría, con
variantes y precio por variante).

Marcas de cada campo en el esquema (se heredan: un campo sin marca toma la de su sección):
- `x-audience`: quién lo configura. `cliente` (el negocio, en lenguaje comercial), `avanzado`
  (estrategia comercial detallada, opcional), `operador` (ajustes internos del motor) o `sistema`
  (versión, dueño del documento y datos heredados).
- `x-engine`: `conectado` si el motor actual lo usa (con una prueba en
  `tests/test_business_config_engine_integration.py`), `pendiente` si solo está representado y
  conservado, `conservado` para `compatibility`. Sin marca en ningún nivel: `pendiente`.

Los datos sensibles de pago (links, números de cuenta, referencias) nunca se guardan en el contrato:
se representan con `SecretRef`.

Versionado: `schema_version` es "1.0". Los cambios compatibles (campos opcionales nuevos, validaciones
que todos los documentos publicados cumplen) se hacen dentro de v1; un cambio incompatible exige un
contrato v2 en `project/config/contracts/v2/` y una migración de los documentos.
"""
from __future__ import annotations

from datetime import date
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from app.domain.business_config.engine_policy import (
    DEFAULT_RESPONSE_LENGTH,
    MAX_FAQ_ANSWER_CHARS,
    MAX_FAQ_QUESTION_CHARS,
    MAX_FAQS,
    MAX_POLICY_CHARS,
    MAX_PROFILE_ITEM_CHARS,
    MAX_PROFILE_ITEMS,
    MAX_PROMOTIONS,
    MAX_TONE_CHARS,
    MIN_MAX_WORDS,
    RESPONSE_LENGTH_MAX_WORDS,
    RESPONSE_LENGTH_WORD_RANGES,
    ResponseLength,
)

SCHEMA_VERSION = "1.0"

Audience = Literal["cliente", "avanzado", "operador", "sistema"]
EngineStatus = Literal["conectado", "pendiente", "conservado"]

CLIENT = {"x-audience": "cliente"}
ADVANCED = {"x-audience": "avanzado"}
OPERATOR = {"x-audience": "operador"}
SYSTEM = {"x-audience": "sistema"}
CONNECTED = {"x-engine": "conectado"}
PENDING = {"x-engine": "pendiente"}


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
Scope = Literal["local", "nacional", "internacional"]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SecretRef(ContractModel):
    """Referencia a un dato sensible guardado fuera del contrato (`<origen>:<clave>`)."""

    secret_ref: Annotated[str, Field(pattern=r"^[a-z_]+:.+$")]


def _unique(values: list[str], label: str) -> None:
    repeated = sorted({value for value in values if values.count(value) > 1})
    if repeated:
        raise ValueError(f"{label} repetidos: {repeated}")


# ---------------------------------------------------------------------------
# Identidad del negocio
# ---------------------------------------------------------------------------

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
ClockTime = Annotated[str, Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$", description="Hora HH:MM (24 h).")]


class OpeningHours(ContractModel):
    days: list[Weekday] = Field(min_length=1, max_length=7)
    opens: ClockTime
    closes: ClockTime

    @model_validator(mode="after")
    def _opens_before_closes(self) -> "OpeningHours":
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


# ---------------------------------------------------------------------------
# Productos y servicios: planes o catálogo
# ---------------------------------------------------------------------------

PLAN_AMOUNT_FIELDS = ("implementation", "monthly", "first_payment", "price", "annual")


class PlanPrice(ContractModel):
    """Importes de un plan en una moneda. Se usan solo los que correspondan al plan."""

    currency: CurrencyCode
    implementation: Amount | None = Field(default=None, description="Pago único inicial (instalación, implementación, inscripción).")
    monthly: Amount | None = Field(default=None, description="Cobro mensual.")
    first_payment: Amount | None = Field(default=None, description="Valor del primer pago cuando difiere del mensual.")
    price: Amount | None = Field(default=None, description="Precio de pago único.")
    annual: Amount | None = Field(default=None, description="Cobro anual.", json_schema_extra=PENDING)

    @model_validator(mode="after")
    def _has_amount(self) -> "PlanPrice":
        if all(getattr(self, field) is None for field in PLAN_AMOUNT_FIELDS):
            raise ValueError(f"el precio en {self.currency} no tiene importes")
        return self


class Plan(ContractModel):
    """Plan o servicio."""

    id: Identifier = Field(json_schema_extra=CONNECTED)
    name: Text = Field(json_schema_extra=CONNECTED)
    description: str | None = Field(default=None, description="Detalle del plan.")
    prices: list[PlanPrice] = Field(min_length=1, json_schema_extra=CONNECTED)
    includes: list[Text] | None = Field(default=None, json_schema_extra=CONNECTED)
    not_included: list[Text] | None = Field(default=None, json_schema_extra=CONNECTED)
    payment_profile: Identifier | None = Field(default=None, description="Perfil de pago con el que se cobra.", json_schema_extra=CONNECTED)
    target: Text | None = Field(default=None, description="Para quién es este plan.")
    available: bool = Field(default=True, description="Si es false, el plan se conserva pero no se ofrece.", json_schema_extra=CONNECTED)

    @model_validator(mode="after")
    def _unique_currencies(self) -> "Plan":
        _unique([price.currency for price in self.prices], f"monedas del plan {self.id}")
        return self


class CatalogCategory(ContractModel):
    id: Identifier
    name: Text


class ItemPrice(ContractModel):
    currency: CurrencyCode
    amount: Amount


class CatalogItem(ContractModel):
    """Producto del catálogo."""

    id: Identifier
    name: Text
    category: Identifier = Field(
        description="Id de su categoría; una categoría sin productos disponibles no se ofrece.", json_schema_extra=CONNECTED
    )
    description: str | None = Field(default=None, description="Detalle del producto.")
    prices: list[ItemPrice] = Field(min_length=1)
    features: Phrases | None = Field(default=None, description="Características del producto.")
    available: bool = Field(
        default=True,
        description="Si es false, el producto se conserva pero no se ofrece (ni su categoría, si se queda sin productos).",
        json_schema_extra=CONNECTED,
    )

    @model_validator(mode="after")
    def _unique_currencies(self) -> "CatalogItem":
        _unique([price.currency for price in self.prices], f"monedas del producto {self.id}")
        return self


class Catalog(ContractModel):
    categories: list[CatalogCategory] = Field(min_length=1, json_schema_extra=CONNECTED)
    items: list[CatalogItem] = Field(min_length=1)
    payment_profile: Identifier | None = Field(default=None, description="Perfil de pago con el que se cobra.", json_schema_extra=CONNECTED)

    @model_validator(mode="after")
    def _items_use_known_categories(self) -> "Catalog":
        _unique([category.id for category in self.categories], "ids de categoría")
        _unique([item.id for item in self.items], "ids de producto")
        known = {category.id for category in self.categories}
        unknown = sorted({item.category for item in self.items} - known)
        if unknown:
            raise ValueError(f"ítems con categorías inexistentes: {unknown}")
        return self


class Offer(ContractModel):
    model: Literal["plans", "catalog"] = Field(
        description="plans: planes o servicios; catalog: productos de un catálogo.", json_schema_extra=CONNECTED
    )
    plans: list[Plan] | None = None
    catalog: Catalog | None = None

    @model_validator(mode="after")
    def _matches_model(self) -> "Offer":
        if self.model == "plans" and (not self.plans or self.catalog is not None):
            raise ValueError("model=plans requiere al menos un plan y ningún catálogo")
        if self.model == "catalog" and (self.catalog is None or self.plans):
            raise ValueError("model=catalog requiere un catálogo y ningún plan")
        entries = self.plans or (self.catalog.items if self.catalog else [])
        if self.plans:
            _unique([plan.id for plan in self.plans], "ids de plan")
        if not any(entry.available for entry in entries):
            raise ValueError("la oferta necesita al menos un plan o producto disponible")
        return self


# ---------------------------------------------------------------------------
# Precios, condiciones y políticas
# ---------------------------------------------------------------------------

class Promotion(ContractModel):
    name: Phrase
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
        default=None, description="Reservas con las que el cliente recupera la inversión.", json_schema_extra=ADVANCED
    )
    roi_hints: list[Text] | None = Field(
        default=None, description="Argumentos de retorno de la inversión.", json_schema_extra={**CONNECTED, **ADVANCED}
    )
    price_note: Text | None = Field(default=None, description="Aclaración sobre cómo se confirma el precio.")
    prices_include_taxes: bool | None = Field(default=None, description="Si los precios publicados ya incluyen los impuestos (IVA).")
    promotions: Annotated[list[Promotion], Field(max_length=MAX_PROMOTIONS)] | None = Field(
        default=None, description="Únicas promociones o descuentos que el asistente puede ofrecer."
    )
    financing: Financing | None = Field(default=None, description="Financiación disponible.")
    policies: Policies | None = Field(default=None, description="Garantía, devoluciones y cancelaciones.")


# ---------------------------------------------------------------------------
# Pagos del negocio (no de la plataforma)
# ---------------------------------------------------------------------------

class TransferMethod(ContractModel):
    type: Literal["nequi", "daviplata", "bank", "breb"]
    number: SecretRef | None = None
    bank: str | None = None
    account_type: str | None = None
    account_number: SecretRef | None = None
    reference: SecretRef | None = None

    @model_validator(mode="after")
    def _required_fields(self) -> "TransferMethod":
        required = {
            "nequi": ("number",),
            "daviplata": ("number",),
            "bank": ("bank", "account_type", "account_number"),
            "breb": ("reference",),
        }[self.type]
        missing = [field for field in required if not getattr(self, field)]
        if missing:
            raise ValueError(f"el método {self.type} requiere {missing}")
        return self


class PaymentProfile(ContractModel):
    """Cómo se cobra: link de pago y transferencias. El motor entrega los datos al cliente cuando elige el método."""

    id: Identifier = Field(json_schema_extra=CONNECTED)
    link: SecretRef | None = Field(default=None, json_schema_extra=CONNECTED)
    transfer_enabled: bool = Field(json_schema_extra=CONNECTED)
    transfer_methods: list[TransferMethod] = Field(default_factory=list, json_schema_extra=CONNECTED)
    instructions: Phrase | None = Field(default=None, description="Indicaciones para pagar, sin números ni links (esos datos son secretos).")

    @model_validator(mode="after")
    def _transfer_has_methods(self) -> "PaymentProfile":
        if self.transfer_enabled and not self.transfer_methods:
            raise ValueError(f"el perfil de pago {self.id} activa transferencias sin métodos")
        return self


# ---------------------------------------------------------------------------
# Estrategia comercial del asistente
# ---------------------------------------------------------------------------

class BuyingMotivation(ContractModel):
    primary: Text
    secondary: str | None = None


class MotivationDriver(ContractModel):
    motivation: Identifier = Field(description="Motivo de compra (p. ej. tiempo, dinero).")
    description: Text
    signals: list[Text] = Field(default_factory=list, description="Frases del cliente que revelan este motivo.")


UrgencyLevel = Literal["alto", "medio", "bajo"]


class CustomerProblem(ContractModel):
    id: Identifier = Field(json_schema_extra=CONNECTED)
    impacts: list[Text] | None = Field(default=None, description="Qué le causa el problema al cliente.", json_schema_extra=CONNECTED)
    signals: list[Text] | None = Field(default=None, description="Frases del cliente que revelan el problema.", json_schema_extra=ADVANCED)
    monetization: list[Text] | None = Field(default=None, description="Cómo el problema le cuesta dinero al cliente.", json_schema_extra=ADVANCED)
    urgency_levels: dict[UrgencyLevel, list[Text]] | None = Field(default=None, description="Mensajes según la urgencia.", json_schema_extra=ADVANCED)
    recommended_angles: list[Identifier] | None = Field(default=None, description="Ángulos de venta para este problema.", json_schema_extra=ADVANCED)


class UseCase(ContractModel):
    name: Text = Field(json_schema_extra=CONNECTED)
    signals: list[Text] = Field(default_factory=list)
    approach: Text = Field(description="Enfoque de la solución para este caso.")


class SolutionMapping(ContractModel):
    problem: Identifier = Field(description="Id de un problema de `customer_problems`.")
    solutions: list[Text] = Field(min_length=1)


class Solution(ContractModel):
    mapping: list[SolutionMapping] | None = Field(default=None, description="Qué parte de la solución atiende cada problema.", json_schema_extra=ADVANCED)
    process_steps: Phrases | None = Field(default=None, description="Pasos que sigue el cliente para comprar o recibir el servicio.")
    requirements: Phrases | None = Field(default=None, description="Requisitos que debe cumplir el cliente.")


class SalesAngle(ContractModel):
    motivation: Identifier = Field(description="Motivo de compra de `motivation_drivers` al que responde.")
    signals: list[Text] = Field(default_factory=list, description="Cuándo usar el ángulo: frases del cliente.")
    messages: list[Text] = Field(default_factory=list, description="Qué decir con este ángulo.")


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
    recommend: Identifier = Field(description="Id de un plan, producto o categoría de la oferta.")


class Discovery(ContractModel):
    questions: Phrases | None = Field(default=None, description="Preguntas para entender al cliente.")
    objectives: Phrases | None = Field(default=None, description="Qué debe averiguar el asistente.", json_schema_extra=ADVANCED)


class Qualification(ContractModel):
    detect_offer_fit: bool | None = Field(default=None, description="Si el asistente debe comprobar que la oferta encaja con el cliente.")
    criteria: Phrases | None = Field(default=None, description="Criterios para considerar a alguien un cliente potencial.")


class SupportPolicy(ContractModel):
    explain_first: bool | None = Field(default=None, description="Ante una pregunta, explicar antes de vender.")
    sell_after: bool | None = Field(default=None, description="Después de explicar, llevar la conversación a la venta.")
    rules: Phrases | None = Field(default=None, description="Reglas de atención del negocio.")


class ConversationFlow(ContractModel):
    steps: list[Identifier] = Field(min_length=1, description="Etapas internas del motor, en orden (p. ej. detect_pain, present_solution).")
    no_skip_steps: bool | None = None
    guided_process: bool | None = Field(default=None, description="Guiar al cliente paso a paso en un proceso (trámites, matrículas).")


class ObjectionHandling(ContractModel):
    topic: Identifier = Field(description="Objeción que se atiende (p. ej. price).")
    acknowledge: Phrases | None = Field(default=None, description="Cómo reconocer la objeción.")
    reframe: Phrases | None = Field(default=None, description="Cómo replantearla.")
    proof: Phrases | None = Field(default=None, description="Pruebas que la desmienten.")
    redirect: Phrases | None = Field(default=None, description="Cómo volver al siguiente paso.")
    rules: Phrases | None = Field(default=None, description="Reglas al responder esta objeción.")


ClosingStrategy = Literal["direct_sale", "lead_capture", "booking", "checkout"]


class Closing(ContractModel):
    strategy: ClosingStrategy = Field(description="Venta directa, captación de datos, reserva o compra con pago (checkout).")
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
    motivation_drivers: list[MotivationDriver] | None = Field(
        default=None, description="Qué significa cada motivo de compra y cómo reconocerlo.", json_schema_extra=ADVANCED
    )
    customer_problems: list[CustomerProblem] | None = Field(default=None, description="Problemas del cliente que el negocio resuelve.")
    pain_points: Phrases | None = Field(default=None, description="Problemas del cliente en sus palabras.")
    use_cases: list[UseCase] | None = Field(default=None, description="Casos de uso típicos.", json_schema_extra=ADVANCED)
    benefits: Phrases | None = Field(default=None, description="Resultados que obtiene el cliente.")
    arguments: Phrases | None = Field(default=None, description="Argumentos de venta.")
    solution: Solution | None = Field(default=None, description="Cómo resuelve el negocio cada problema y qué pasos sigue el cliente.")
    angles: list[SalesAngle] | None = Field(default=None, description="Ángulos de venta por motivo de compra.", json_schema_extra=ADVANCED)
    offer_mix: OfferMix | None = Field(default=None, description="Ofertas principales, mejoras y complementos.", json_schema_extra=ADVANCED)
    offer_presentation: OfferPresentation | None = Field(default=None, description="Cómo presentar las opciones.", json_schema_extra=ADVANCED)
    recommendation_rules: Annotated[list[RecommendationRule], Field(max_length=MAX_PROFILE_ITEMS)] | None = Field(
        default=None, description="Qué recomendar en cada situación."
    )
    discovery: Discovery | None = None
    qualification: Qualification | None = Field(default=None, description="Cómo calificar al cliente.", json_schema_extra=ADVANCED)
    support: SupportPolicy | None = Field(default=None, description="Cómo atender preguntas de información.", json_schema_extra=ADVANCED)
    conversation_flow: ConversationFlow | None = Field(
        default=None, description="Etapas de la conversación (identificadores internos del motor).", json_schema_extra=OPERATOR
    )
    objections: list[ObjectionHandling] | None = Field(default=None, description="Manejo de objeciones (precio y otras).", json_schema_extra=ADVANCED)
    closing: Closing | None = Field(default=None, description="Estrategia y reglas de cierre.", json_schema_extra=ADVANCED)
    instructions: Phrases | None = Field(default=None, description="Instrucciones de venta del negocio.")

    @model_validator(mode="after")
    def _references_exist(self) -> "Sales":
        problems = [problem.id for problem in self.customer_problems or []]
        _unique(problems, "ids de problema")
        drivers = [driver.motivation for driver in self.motivation_drivers or []]
        _unique(drivers, "motivos de compra")
        _unique([objection.topic for objection in self.objections or []], "objeciones")
        angles = [angle.motivation for angle in self.angles or []]
        _unique(angles, "ángulos de venta")
        mapping = self.solution.mapping if self.solution else None
        unknown = sorted({entry.problem for entry in mapping or []} - set(problems))
        if unknown:
            raise ValueError(f"la solución menciona problemas inexistentes: {unknown}")
        recommended = {angle for problem in self.customer_problems or [] for angle in problem.recommended_angles or []}
        if self.angles and recommended - set(angles):
            raise ValueError(f"problemas que recomiendan ángulos inexistentes: {sorted(recommended - set(angles))}")
        # Motivos, ángulos y explicaciones de motivos son una sola lista de motivos: no puede haber huérfanos.
        if drivers:
            motivations = [m for m in (self.buying_motivation.primary, self.buying_motivation.secondary) if m] if self.buying_motivation else []
            orphans = sorted((set(motivations) | set(angles)) - set(drivers))
            if orphans:
                raise ValueError(f"motivos de compra sin explicación en motivation_drivers: {orphans}")
        return self


# ---------------------------------------------------------------------------
# Capacidades, mensajes, estilo y conocimiento
# ---------------------------------------------------------------------------

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
    fields: list[Literal["nombre", "telefono", "direccion", "detalles"]] = Field(default_factory=list, json_schema_extra=CONNECTED)
    consent_notice: PolicyText | None = Field(
        default=None, description="Aviso de tratamiento de datos personales que el asistente comparte al pedirlos."
    )

    @model_validator(mode="after")
    def _fields_when_enabled(self) -> "DataCollection":
        if self.enabled and not self.fields:
            raise ValueError("data_collection activo requiere campos")
        return self


class Restrictions(ContractModel):
    disallowed_channels: list[Text] = Field(default_factory=list, description="Canales por los que el negocio no atiende.")
    disallowed_actions: list[Text] = Field(default_factory=list, description="Acciones que el negocio no realiza (p. ej. llamadas).")
    forbidden_claims: Phrases | None = Field(
        default=None, description="Promesas o afirmaciones que el asistente nunca debe hacer (resultados garantizados, diagnósticos...)."
    )


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
    human_handoff_when: Phrases | None = Field(default=None, description="Situaciones en las que el asistente pasa la conversación a una persona.")
    restrictions: Restrictions | None = Field(default=None, description="Lo que el negocio no hace ni promete.")

    @model_validator(mode="after")
    def _coherent(self) -> "Capabilities":
        if not (self.actions_primary or self.actions_support):
            raise ValueError("debe haber al menos una acción")
        if self.closing_methods.data_collection and not self.data_collection.enabled:
            raise ValueError("el cierre pidiendo datos requiere data_collection activo")
        if self.human_handoff_when and not self.closing_methods.human_handoff:
            raise ValueError("human_handoff_when requiere el cierre con una persona (closing_methods.human_handoff)")
        return self


class WelcomeMessage(ContractModel):
    enabled: bool
    text: str = ""

    @model_validator(mode="after")
    def _text_when_enabled(self) -> "WelcomeMessage":
        if self.enabled and not self.text.strip():
            raise ValueError("el mensaje de bienvenida activo requiere texto")
        return self


class Messages(ContractModel):
    welcome: WelcomeMessage = Field(description="Primer mensaje de cada conversación nueva, si está activo.", json_schema_extra=CONNECTED)
    payment_reported: Text | None = Field(default=None, description="Respuesta exacta cuando el cliente reporta un pago.", json_schema_extra=CONNECTED)
    payment_confirmed: Text | None = Field(default=None, description="Mensaje cuando el pago queda confirmado.", json_schema_extra=CONNECTED)
    after_sale: Text | None = Field(default=None, description="Mensaje después de una compra.")
    data_request: Text | None = Field(default=None, description="Mensaje para pedir los datos del cliente.")
    follow_up: Text | None = Field(default=None, description="Mensaje de seguimiento a un cliente que no respondió.")
    human_handoff: Text | None = Field(default=None, description="Mensaje al pasar la conversación a una persona.")


class ResponseStyle(ContractModel):
    """Cómo se comunica el asistente.

    Longitud (en el prompt y al recortar la respuesta, en todos los canales): short = cortas,
    medium = equilibradas, long = detalladas; límites en `engine_policy`.
    """

    tone: Annotated[Text, Field(max_length=MAX_TONE_CHARS)] | None = Field(default=None, description="Tono del asistente (p. ej. cercano y claro).")
    voice: Annotated[Text, Field(max_length=MAX_TONE_CHARS)] | None = Field(default=None, description="Personalidad de la marca.")
    formality: Literal["informal", "neutral", "formal"] | None = Field(default=None, description="informal (tutea), neutral o formal (usted).")
    emojis: bool | None = Field(default=None, description="Si el asistente puede usar emojis.")
    instructions: Phrases | None = Field(default=None, description="Indicaciones de comunicación del negocio.")
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
    question: Annotated[Text, Field(max_length=MAX_FAQ_QUESTION_CHARS)]
    answer: Annotated[Text, Field(max_length=MAX_FAQ_ANSWER_CHARS)]


class Knowledge(ContractModel):
    faqs: list[Faq] = Field(default_factory=list, max_length=MAX_FAQS, description="Preguntas frecuentes con su respuesta oficial.")


# ---------------------------------------------------------------------------
# Entrega: domicilio, envío, recogida y agenda
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Variantes e inventario
# ---------------------------------------------------------------------------

class Variant(ContractModel):
    sku: Text
    attributes: dict[str, str | int] = Field(default_factory=dict, description="Talla, color u otras características.")
    stock: Annotated[int, Field(ge=0)]
    prices: list[ItemPrice] | None = Field(default=None, description="Precio de la variante, solo si difiere del precio del producto.")

    @model_validator(mode="after")
    def _unique_currencies(self) -> "Variant":
        _unique([price.currency for price in self.prices or []], f"monedas de la variante {self.sku}")
        return self


class InventoryItem(ContractModel):
    product_id: Identifier = Field(description="Id de un producto del catálogo.")
    variants: list[Variant] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_skus(self) -> "InventoryItem":
        _unique([variant.sku for variant in self.variants], f"sku del producto {self.product_id}")
        return self


class Inventory(ContractModel):
    """Variantes y existencias de los productos del catálogo."""

    items: list[InventoryItem] = Field(default_factory=list)
    track_stock: bool | None = Field(default=None, description="Si el negocio controla existencias.")


# ---------------------------------------------------------------------------
# Ajustes internos del motor (los gestiona el operador, no el negocio)
# ---------------------------------------------------------------------------

class ConversationWindows(ContractModel):
    # Mínimo 1: el motor trata 0 como "sin valor" y aplica sus valores por defecto (15 min, 4 h).
    active_window_minutes: Annotated[int, Field(ge=1)] = Field(description="Minutos sin mensajes tras los que la conversación deja de estar activa.")
    reset_hours: Annotated[int, Field(ge=1)] = Field(description="Horas sin mensajes tras las que la conversación empieza de nuevo.")


class EngineFeatures(ContractModel):
    pricing_enabled: bool = Field(description="Bandera heredada: el motor solo la consulta si no hay precios ni pagos, y el contrato siempre los exige.")
    catalog_mode: bool = Field(description="Debe coincidir con `offer.model` (catalog).", json_schema_extra=CONNECTED)
    business_model: Literal["saas", "catalog", "checkout", "service_booking", "process"] | None = Field(
        default=None, description="Modelo de negocio con el que el motor decide cuándo mostrar precios.", json_schema_extra=CONNECTED
    )


class EngineSettings(ContractModel):
    conversation: ConversationWindows | None = Field(default=None, json_schema_extra=CONNECTED)
    features: EngineFeatures


# ---------------------------------------------------------------------------
# Documento completo
# ---------------------------------------------------------------------------

class BusinessConfig(ContractModel):
    schema_version: Literal["1.0"] = Field(default=SCHEMA_VERSION, json_schema_extra={**SYSTEM, **CONNECTED})
    tenant_slug: Slug = Field(json_schema_extra={**SYSTEM, **CONNECTED})
    identity: Identity = Field(json_schema_extra=CLIENT)
    offer: Offer = Field(json_schema_extra=CLIENT)
    terms: Terms = Field(default_factory=Terms, json_schema_extra=CLIENT)
    payments: list[PaymentProfile] = Field(default_factory=list, json_schema_extra=CLIENT)
    sales: Sales = Field(default_factory=Sales, json_schema_extra=CLIENT)
    capabilities: Capabilities = Field(json_schema_extra=CLIENT)
    messages: Messages = Field(json_schema_extra=CLIENT)
    response_style: ResponseStyle = Field(default_factory=ResponseStyle, json_schema_extra=CLIENT)
    knowledge: Knowledge = Field(default_factory=Knowledge, json_schema_extra=CLIENT)
    fulfillment: Fulfillment | None = Field(default=None, json_schema_extra=CLIENT)
    inventory: Inventory = Field(default_factory=Inventory, json_schema_extra=CLIENT)
    engine: EngineSettings | None = Field(
        default=None,
        description="Ajustes internos del motor. Si falta, se deriva de la oferta (catálogo o planes) con los valores por defecto.",
        json_schema_extra=OPERATOR,
    )
    compatibility: dict[str, Any] = Field(
        default_factory=dict,
        description="Datos de los YAML antiguos sin lugar en el contrato, conservados con su ruta original.",
        json_schema_extra={**SYSTEM, "x-engine": "conservado"},
    )

    @model_validator(mode="after")
    def _cross_references_exist(self) -> "BusinessConfig":
        ids = [profile.id for profile in self.payments]
        _unique(ids, "ids de perfil de pago")
        referenced = [plan.payment_profile for plan in self.offer.plans or []]
        if self.offer.catalog is not None:
            referenced.append(self.offer.catalog.payment_profile)
        unknown = sorted({ref for ref in referenced if ref is not None} - set(ids))
        if unknown:
            raise ValueError(f"perfiles de pago inexistentes: {unknown}")
        unexpected = sorted(set(self.compatibility) - {"business", "sales", "pricing", "inventory", "config"})
        if unexpected:
            raise ValueError(f"secciones de compatibilidad desconocidas: {unexpected}")
        missing = sorted({rule.recommend for rule in self.sales.recommendation_rules or []} - set(self.offer_names()))
        if missing:
            raise ValueError(f"reglas de recomendación con ofertas inexistentes: {missing}")
        items = {item.id: item for item in self.offer.catalog.items} if self.offer.catalog else {}
        orphans = sorted({entry.product_id for entry in self.inventory.items} - set(items))
        if orphans:
            raise ValueError(f"inventario de productos inexistentes en el catálogo: {orphans}")
        for entry in self.inventory.items:
            currencies = {price.currency for price in items[entry.product_id].prices}
            for variant in entry.variants:
                foreign = sorted({price.currency for price in variant.prices or []} - currencies)
                if foreign:
                    raise ValueError(f"la variante {variant.sku} tiene monedas que su producto no usa: {foreign}")
        return self

    def offer_names(self, *, available_only: bool = False) -> dict[str, str]:
        """Ids recomendables de la oferta (planes, productos y categorías) con su nombre visible."""
        if self.offer.plans:
            return {plan.id: plan.name for plan in self.offer.plans if plan.available or not available_only}
        catalog = self.offer.catalog
        if catalog is None:
            return {}
        items = [item for item in catalog.items if item.available or not available_only]
        used = {item.category for item in items}
        return {
            **{category.id: category.name for category in catalog.categories if category.id in used or not available_only},
            **{item.id: item.name for item in items},
        }
