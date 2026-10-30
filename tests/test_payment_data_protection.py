"""
Datos de pago sensibles según el contrato (links, números, cuentas y referencias): detección y redacción.

Prueba unitaria de `app/domain/business_config/payment_data.py`. Que ningún documento del contrato
contenga estos valores lo prueban `test_business_config_contract.py` y la migración; que tampoco
lleguen al prompt ni al registro de la conversación depende del motor y está en
`test_business_config_engine_pending.py`.
"""
from __future__ import annotations

from app.domain.business_config.payment_data import (
    REDACTED_PAYMENT_VALUE,
    payment_values,
    redact_payment_values,
)


def test_redaction_replaces_exact_values_longest_first():
    runtime = {
        "pricing": {
            "plans": [{"payment": {"link": "https://pagos.example/abc", "transfer": {"enabled": False, "methods": [{"type": "nequi", "number": "3001112233"}]}}}],
            "catalog": {"payment": {"transfer": {"enabled": True, "methods": [{"type": "breb", "reference": "300"}, {"type": "bank", "account_number": "3001112233-9"}]}}},
        }
    }
    # Los métodos desactivados también se protegen; los valores muy cortos no se tocan.
    assert payment_values(runtime) == ["https://pagos.example/abc", "3001112233-9", "3001112233"]
    text = "Link https://pagos.example/abc, cuenta 3001112233-9, nequi 3001112233, código 300."
    assert redact_payment_values(text, runtime) == (
        f"Link {REDACTED_PAYMENT_VALUE}, cuenta {REDACTED_PAYMENT_VALUE}, nequi {REDACTED_PAYMENT_VALUE}, código 300."
    )
    assert redact_payment_values("sin datos", {}) == "sin datos"
