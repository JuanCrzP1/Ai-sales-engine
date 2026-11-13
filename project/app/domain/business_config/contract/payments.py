"""Pagos del negocio, no de la plataforma. Los datos sensibles son referencias (`SecretRef`), nunca valores."""
from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from app.domain.business_config.primitives import CONNECTED, PANEL_ONLY, ContractModel, Identifier, Phrase, SecretRef


class TransferMethod(ContractModel):
    type: Literal["nequi", "daviplata", "bank", "breb"]
    number: SecretRef | None = None
    bank: str | None = None
    account_type: str | None = None
    account_number: SecretRef | None = None
    reference: SecretRef | None = None
    label: Phrase | None = Field(
        default=None, description="Etiqueta para reconocer la cuenta en el panel. No se comparte con el cliente.", json_schema_extra=PANEL_ONLY
    )
    holder: Phrase | None = Field(
        default=None,
        description="A nombre de quién está la cuenta. Se le muestra al cliente con los datos de pago, para que sepa que paga al negocio correcto.",
        json_schema_extra=CONNECTED,
    )
    # Sin indicar equivale a activa: los documentos que no lo usan no cambian.
    enabled: bool | None = Field(default=None, description="Si es false, la cuenta se conserva pero no se ofrece.")

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
    # Sin indicar equivale a activo: los documentos que no lo usan no cambian.
    link_enabled: bool | None = Field(default=None, description="Si es false, el enlace se conserva pero no se ofrece.", json_schema_extra=CONNECTED)
    transfer_enabled: bool = Field(json_schema_extra=CONNECTED)
    transfer_methods: list[TransferMethod] = Field(default_factory=list, json_schema_extra=CONNECTED)

    @model_validator(mode="after")
    def _transfer_has_methods(self) -> "PaymentProfile":
        if self.transfer_enabled and not self.transfer_methods:
            raise ValueError(f"el perfil de pago {self.id} activa transferencias sin métodos")
        return self
