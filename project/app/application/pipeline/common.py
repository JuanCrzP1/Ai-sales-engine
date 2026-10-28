from __future__ import annotations

from app.utils.logger import logger


def tenant_slug(tenant) -> str:
    return str(getattr(tenant, "slug", "") or "").strip().lower()


def log_trace(*, tenant_slug_value: str, user_id: str, intent: str, user_message: str, final_response: str) -> None:
    logger.info(
        "conversation_trace",
        extra={
            "tenant": tenant_slug_value,
            "user": user_id,
            "intent": intent,
            "user_message": user_message,
            "ai_response": final_response,
        },
    )
