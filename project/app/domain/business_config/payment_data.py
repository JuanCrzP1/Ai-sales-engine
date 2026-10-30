"""Datos de pago sensibles dentro de las secciones compiladas: links, números, cuentas y referencias.

Define qué valores son sensibles según el contrato (los que se guardan como `SecretRef`). Lo usan la
migración y las pruebas para comprobar que ningún documento del contrato los contiene.

Integración pendiente (fuera del contrato): el motor actual sí escribe estos valores en el prompt de
la IA y en el registro `conversation_trace`. `redact_payment_values` es la redacción que esa
integración necesitará; las pruebas que la exigen están en `tests/test_business_config_engine_pending.py`.
"""
from __future__ import annotations

SENSITIVE_TRANSFER_FIELDS = ("number", "account_number", "reference")
REDACTED_PAYMENT_VALUE = "[dato de pago]"
# Valores más cortos no se redactan para no alterar palabras comunes del texto.
MIN_REDACTABLE_CHARS = 4


def iter_payment_blocks(pricing: dict) -> list[dict]:
    """Bloques `payment` de los planes, del catálogo y de la raíz de `pricing`, en ese orden."""
    blocks: list[dict] = []
    plans = pricing.get("plans") if isinstance(pricing.get("plans"), list) else []
    for plan in plans:
        if not isinstance(plan, dict):
            continue
        payment = plan.get("payment") if isinstance(plan.get("payment"), dict) else {}
        if payment:
            blocks.append(payment)

    catalog = pricing.get("catalog") if isinstance(pricing.get("catalog"), dict) else {}
    catalog_payment = catalog.get("payment") if isinstance(catalog.get("payment"), dict) else {}
    if catalog_payment:
        blocks.append(catalog_payment)

    root_payment = pricing.get("payment") if isinstance(pricing.get("payment"), dict) else {}
    if root_payment:
        blocks.append(root_payment)

    return blocks


def payment_values(runtime_yaml: dict) -> list[str]:
    """Valores sensibles configurados (incluidos los de métodos desactivados), del más largo al más corto."""
    pricing = runtime_yaml.get("pricing") if isinstance(runtime_yaml, dict) and isinstance(runtime_yaml.get("pricing"), dict) else {}
    values: set[str] = set()
    for block in iter_payment_blocks(pricing):
        values.add(str(block.get("link") or "").strip())
        transfer = block.get("transfer") if isinstance(block.get("transfer"), dict) else {}
        methods = transfer.get("methods") if isinstance(transfer.get("methods"), list) else []
        for method in methods:
            if isinstance(method, dict):
                values.update(str(method.get(field) or "").strip() for field in SENSITIVE_TRANSFER_FIELDS)
    return sorted((value for value in values if len(value) >= MIN_REDACTABLE_CHARS), key=len, reverse=True)


def redact_payment_values(text: str, runtime_yaml: dict) -> str:
    for value in payment_values(runtime_yaml):
        text = text.replace(value, REDACTED_PAYMENT_VALUE)
    return text
