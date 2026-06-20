from __future__ import annotations

from app.utils.logger import logger


def tenant_key(tenant) -> str:
    tenant_id = getattr(tenant, "id", None)
    if tenant_id not in (None, ""):
        return str(tenant_id).strip().lower()
    return str(getattr(tenant, "slug", "") or "").strip().lower()


def tenant_slug(tenant) -> str:
    return str(getattr(tenant, "slug", "") or "").strip().lower()


_LIMIT_MESSAGE = "Ya llegaste al límite del plan. Si quieres seguimos de una y no paras las ventas."
_INACTIVE_MESSAGE = "En este momento no tienes el servicio activo, si quieres lo activamos y lo dejas trabajando ya contigo."
_GENERIC_BLOCKED_MESSAGE = "No puedo procesar tu solicitud en este momento."
_SERVICE_UNAVAILABLE_MESSAGE = (
    "Estoy teniendo un problema técnico momentáneo para procesar tu mensaje. "
    "Por favor escríbeme de nuevo en un momento."
)


def blocked_response(reason: str | dict | None) -> str:
    # SaaSGuard retorna un dict cuando se alcanza el límite del plan
    # (source="saas_guard_limit_reached") y un string en el resto de casos.
    if isinstance(reason, dict):
        if str(reason.get("source") or "").strip().lower() == "saas_guard_limit_reached":
            return _LIMIT_MESSAGE
        return _GENERIC_BLOCKED_MESSAGE
    if reason == "subscription_inactive":
        return _INACTIVE_MESSAGE
    if reason in ("usage_limit", "saas_guard_limit_reached"):
        return _LIMIT_MESSAGE
    return _GENERIC_BLOCKED_MESSAGE


def service_unavailable_response() -> str:
    """Respuesta controlada cuando una dependencia crítica (ej. PostgreSQL) falla.

    No expone traceback al usuario; el detalle técnico se registra en logs.
    """
    return _SERVICE_UNAVAILABLE_MESSAGE


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
