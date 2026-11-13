"""Pagos del negocio, no de la plataforma. Los datos sensibles son referencias (`SecretRef`), nunca valores."""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.domain.business_config.payment_catalog import PAYMENT_METHOD_IDS, method_kind
from app.domain.business_config.primitives import CONNECTED, PANEL_ONLY, ContractModel, Identifier, Phrase, SecretRef, Text

# Lo más largo de la instrucción de un medio de pago.
MAX_PAYMENT_INSTRUCTIONS_CHARS = 300


class TransferMethod(ContractModel):
    """Un medio para pagar: Nequi, una cuenta bancaria, Yape, PayPal, efectivo u «otro medio» (`payment_catalog.py`). Lo que se paga
    va cifrado en `number`, `account_number` o `reference`, según el medio."""

    type: Literal[PAYMENT_METHOD_IDS] = Field(description="El medio, del catálogo de medios de pago (`payment_catalog.py`).")  # type: ignore[valid-type]
    number: SecretRef | None = None
    bank: str | None = None
    account_type: str | None = None
    account_number: SecretRef | None = None
    reference: SecretRef | None = None
    name: Phrase | None = Field(default=None, description="«Otro medio»: su nombre, como lo verá el cliente (por ejemplo, «Nu»).")
    data_label: Phrase | None = Field(default=None, description="«Otro medio»: cómo se llama su dato (por ejemplo, «Alias» o «Número»).")
    instructions: Annotated[Text, Field(max_length=MAX_PAYMENT_INSTRUCTIONS_CHARS)] | None = Field(
        default=None,
        description="Lo que el cliente debe saber al pagar por este medio (por ejemplo, «envía el comprobante con tu nombre»). Sale con los datos; la IA no lo ve.",
    )
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
        kind = method_kind(self.type)
        assert kind is not None  # `type` ya se validó contra el catálogo
        required = [kind.data.slot] if kind.data else []
        if kind.needs_bank:
            required += ["bank", "account_type"]
        if kind.custom:
            required += ["name"]
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
