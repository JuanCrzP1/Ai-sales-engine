from __future__ import annotations

from app.domain.business_config.payment_data import redact_payment_values
from app.utils.logger import logger


def tenant_slug(tenant) -> str:
    return str(getattr(tenant, "slug", "") or "").strip().lower()


def log_trace(*, tenant_slug_value: str, user_id: str, intent: str, user_message: str, final_response: str, runtime_yaml: dict) -> None:
    """Registro de cada turno. Los datos de pago del negocio no se registran: el cliente los recibe, el registro guarda el marcador."""
    logger.info(
        "conversation_trace",
        extra={
            "tenant": tenant_slug_value,
            "user": user_id,
            "intent": intent,
            "user_message": redact_payment_values(user_message, runtime_yaml),
            "ai_response": redact_payment_values(final_response, runtime_yaml),
        },
    )
