"""El documento completo de un negocio: reúne las secciones y comprueba las referencias entre ellas."""
from __future__ import annotations

from typing import Literal

from pydantic import Field, PrivateAttr, model_validator

from app.domain.business_config.contract.assistant import Capabilities, Knowledge, Messages, ResponseStyle
from app.domain.business_config.contract.escalation import Escalation
from app.domain.business_config.contract.fulfillment import Fulfillment
from app.domain.business_config.contract.identity import Identity
from app.domain.business_config.contract.inventory import Inventory
from app.domain.business_config.contract.offer import Offer
from app.domain.business_config.contract.payments import PaymentProfile
from app.domain.business_config.contract.sales import Sales
from app.domain.business_config.contract.terms import Terms
from app.domain.business_config.engine_settings import EngineSettings
from app.domain.business_config.primitives import ADVANCED, CLIENT, CONNECTED, SCHEMA_VERSION, SYSTEM, ContractModel, Slug, ensure_unique


BusinessModel = Literal["catalog", "saas", "services", "service_booking"]
# Opciones que se retiraron de «Qué vendes» y a cuál equivalen: un documento guardado con ellas se sigue leyendo.
# «Checkout» repetía la estrategia de cierre «Enviar el pago»; «Proceso», el paso a paso de `sales.conversation_flow`.
RETIRED_BUSINESS_MODELS = {"checkout": "catalog", "process": "services"}


class Features(ContractModel):
    """Cómo vende el negocio. Los valores se conservan tal cual; las contradicciones con la oferta las señala el diagnóstico.

    El antiguo «modo catálogo» (`catalog_mode`) ya no se escribe: el motor lo recibe deducido de lo que vende el negocio y de su oferta.
    """

    pricing_enabled: bool = Field(description="true: permite usar precios en la conversación. false: el asistente no da valores.", json_schema_extra=CONNECTED)
    multi_currency: bool | None = Field(
        default=None, description="true: da los precios en todas sus monedas. false: solo en la primera de cada precio.", json_schema_extra=CONNECTED
    )
    multi_plan: bool | None = Field(
        default=None, description="true: puede ofrecer varios planes. false: recomienda uno solo, el que mejor encaje.", json_schema_extra=CONNECTED
    )
    business_model: BusinessModel | None = Field(
        default=None,
        description=(
            "Qué vende el negocio: catalog (productos), saas (planes o suscripción), services (servicios) o service_booking "
            "(servicios con cita). El asistente usa el manual de venta de ese tipo; sin indicar, se deduce de la oferta."
        ),
        json_schema_extra=CONNECTED,
    )

    @model_validator(mode="before")
    @classmethod
    def _read_retired_options(cls, data: object) -> object:
        """Un documento guardado antes de unificar «Qué vendes» se sigue leyendo: sin `catalog_mode` y con la opción equivalente."""
        if not isinstance(data, dict):
            return data
        data = {key: value for key, value in data.items() if key != "catalog_mode"}
        if data.get("business_model") in RETIRED_BUSINESS_MODELS:
            data["business_model"] = RETIRED_BUSINESS_MODELS[data["business_model"]]
        return data


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
    escalation: Escalation = Field(default_factory=Escalation, json_schema_extra=CLIENT)
    fulfillment: Fulfillment | None = Field(default=None, json_schema_extra={**CLIENT, **CONNECTED})
    inventory: Inventory = Field(default_factory=Inventory, json_schema_extra={**CLIENT, **CONNECTED})
    features: Features | None = Field(
        default=None, description="Interruptores comerciales. Si faltan, se derivan de la oferta (catálogo o planes).", json_schema_extra=ADVANCED
    )

    # Ajustes técnicos del negocio: se cargan aparte y nunca forman parte del documento comercial.
    _engine_settings: EngineSettings | None = PrivateAttr(default=None)

    @property
    def engine_settings(self) -> EngineSettings | None:
        return self._engine_settings

    def with_engine_settings(self, settings: EngineSettings | None) -> "BusinessConfig":
        self._engine_settings = settings
        return self

    @model_validator(mode="after")
    def _cross_references_exist(self) -> "BusinessConfig":
        ids = [profile.id for profile in self.payments]
        ensure_unique(ids, "ids de perfil de pago")
        referenced = [plan.payment_profile for plan in self.offer.plans or []]
        if self.offer.catalog is not None:
            referenced.append(self.offer.catalog.payment_profile)
        unknown = sorted({ref for ref in referenced if ref is not None} - set(ids))
        if unknown:
            raise ValueError(f"perfiles de pago inexistentes: {unknown}")
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


def business_config_json_schema() -> dict:
    """El esquema publicado del contrato. Única definición: lo usan la API del panel y `scripts/export_business_config_schema.py`."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://ai-sales-engine/contracts/business-config/v{SCHEMA_VERSION}",
        **BusinessConfig.model_json_schema(),
    }
