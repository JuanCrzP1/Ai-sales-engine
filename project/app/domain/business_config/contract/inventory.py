"""Variantes y existencias de los productos del catálogo."""
from __future__ import annotations

from typing import Annotated

from pydantic import Field, model_validator

from app.domain.business_config.contract.offer import ItemPrice
from app.domain.business_config.primitives import PANEL_ONLY, ContractModel, Identifier, Text, ensure_unique


class Variant(ContractModel):
    sku: Text = Field(description="Código interno de la variante, para el equipo.", json_schema_extra=PANEL_ONLY)
    attributes: dict[str, str | int] = Field(default_factory=dict, description="Talla, color u otras características.")
    stock: Annotated[int, Field(ge=0)]
    prices: list[ItemPrice] | None = Field(default=None, description="Precio de la variante, solo si difiere del precio del producto.")

    @model_validator(mode="after")
    def _unique_currencies(self) -> "Variant":
        ensure_unique([price.currency for price in self.prices or []], f"monedas de la variante {self.sku}")
        return self


class InventoryItem(ContractModel):
    product_id: Identifier = Field(description="Id de un producto del catálogo.")
    variants: list[Variant] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_skus(self) -> "InventoryItem":
        ensure_unique([variant.sku for variant in self.variants], f"sku del producto {self.product_id}")
        return self


class Inventory(ContractModel):
    """Variantes y existencias de los productos del catálogo."""

    items: list[InventoryItem] = Field(default_factory=list)
    track_stock: bool | None = Field(default=None, description="Si el negocio controla existencias.")
