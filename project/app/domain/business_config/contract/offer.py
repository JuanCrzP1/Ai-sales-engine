"""Productos y servicios: planes o catálogo, con sus precios por moneda."""
from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from app.domain.business_config.engine_policy import MAX_CATEGORIES, MAX_OFFER_DESCRIPTION_CHARS

from app.domain.business_config.primitives import (
    CONNECTED,
    PENDING,
    Amount,
    ContractModel,
    CurrencyCode,
    Identifier,
    Phrases,
    Text,
    ensure_unique,
)


PLAN_AMOUNT_FIELDS = ("implementation", "monthly", "first_payment", "price", "annual")


class PlanPrice(ContractModel):
    """Importes de un plan en una moneda. Se usan solo los que correspondan al plan."""

    currency: CurrencyCode
    implementation: Amount | None = Field(default=None, description="Pago único inicial (instalación, implementación, inscripción).")
    monthly: Amount | None = Field(default=None, description="Cobro mensual.")
    first_payment: Amount | None = Field(default=None, description="Valor del primer pago, si difiere de los siguientes.")
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
    description: str | None = Field(default=None, max_length=MAX_OFFER_DESCRIPTION_CHARS, description="Detalle del plan.", json_schema_extra=CONNECTED)
    prices: list[PlanPrice] = Field(min_length=1, json_schema_extra=CONNECTED)
    includes: list[Text] | None = Field(default=None, json_schema_extra=CONNECTED)
    not_included: list[Text] | None = Field(default=None, json_schema_extra=CONNECTED)
    payment_profile: Identifier | None = Field(default=None, description="Perfil de pago con el que se cobra.", json_schema_extra=CONNECTED)
    target: Text | None = Field(default=None, description="Para quién es este plan.")
    available: bool = Field(default=True, description="Si es false, el plan se conserva pero no se ofrece.", json_schema_extra=CONNECTED)

    @model_validator(mode="after")
    def _unique_currencies(self) -> "Plan":
        ensure_unique([price.currency for price in self.prices], f"monedas del plan {self.id}")
        return self


class CatalogCategory(ContractModel):
    id: Identifier
    name: Text


class ItemPrice(ContractModel):
    currency: CurrencyCode = Field(description="Moneda (código ISO de tres letras).")
    amount: Amount = Field(description="Precio en esa moneda.")


class CatalogItem(ContractModel):
    """Producto del catálogo."""

    id: Identifier = Field(json_schema_extra=CONNECTED)
    name: Text = Field(json_schema_extra=CONNECTED)
    category: Identifier = Field(
        description="Id de su categoría; una categoría sin productos disponibles no se ofrece.", json_schema_extra=CONNECTED
    )
    description: str | None = Field(default=None, max_length=MAX_OFFER_DESCRIPTION_CHARS, description="Detalle del producto.", json_schema_extra=CONNECTED)
    prices: list[ItemPrice] = Field(min_length=1, json_schema_extra=CONNECTED)
    features: Phrases | None = Field(default=None, description="Características del producto.", json_schema_extra=CONNECTED)
    available: bool = Field(
        default=True,
        description="Si es false, el producto se conserva pero no se ofrece (ni su categoría, si se queda sin productos).",
        json_schema_extra=CONNECTED,
    )

    @model_validator(mode="after")
    def _unique_currencies(self) -> "CatalogItem":
        ensure_unique([price.currency for price in self.prices], f"monedas del producto {self.id}")
        return self


class Catalog(ContractModel):
    categories: list[CatalogCategory] = Field(min_length=1, max_length=MAX_CATEGORIES, json_schema_extra=CONNECTED)
    items: list[CatalogItem] = Field(min_length=1)
    payment_profile: Identifier | None = Field(default=None, description="Perfil de pago con el que se cobra.", json_schema_extra=CONNECTED)

    @model_validator(mode="after")
    def _items_use_known_categories(self) -> "Catalog":
        ensure_unique([category.id for category in self.categories], "ids de categoría")
        ensure_unique([item.id for item in self.items], "ids de producto")
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
            ensure_unique([plan.id for plan in self.plans], "ids de plan")
        if not any(entry.available for entry in entries):
            raise ValueError("la oferta necesita al menos un plan o producto disponible")
        return self
