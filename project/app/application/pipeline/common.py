from __future__ import annotations

from app.utils.logger import logger


def tenant_key(tenant) -> str:
    tenant_id = getattr(tenant, "id", None)
    if tenant_id not in (None, ""):
        return str(tenant_id).strip().lower()
    return str(getattr(tenant, "slug", "") or "").strip().lower()


def tenant_slug(tenant) -> str:
    return str(getattr(tenant, "slug", "") or "").strip().lower()


def blocked_response(reason: str | None) -> str:
    if reason == "subscription_inactive":
        return "En este momento no tienes el servicio activo, si quieres lo activamos y lo dejas trabajando ya contigo."
    if reason == "usage_limit":
        return "Ya llegaste al límite del plan. Si quieres seguimos de una y no paras las ventas."
    return "No puedo procesar tu solicitud en este momento."


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
