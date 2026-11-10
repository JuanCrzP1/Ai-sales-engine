"""Lo que responde el asistente cuando la IA no puede: el negocio no tiene clave, el proveedor falló o la respuesta no sirvió.

Es el mensaje que el negocio escribió en el panel (Mensajes → «Si el asistente no puede responder»), compilado en
`config.fallback_message`. Sin él, uno neutro de la plataforma. Nunca sale de otra fuente ni repite lo que escribió el cliente.
"""
from __future__ import annotations

from app.utils.logger import logger

PLATFORM_FALLBACK_REPLY = "Gracias por escribirnos. En este momento no puedo responderte; por favor escríbenos de nuevo en unos minutos."


def business_fallback_message(runtime_yaml: dict) -> str:
    """El mensaje del negocio, o "" si no lo configuró."""
    config = runtime_yaml.get("config") if isinstance(runtime_yaml, dict) and isinstance(runtime_yaml.get("config"), dict) else {}
    return str(config.get("fallback_message") or "").strip()


def build_fallback_response(user_message: str, tenant_config: dict) -> str:
    del user_message
    safe_tenant = tenant_config if isinstance(tenant_config, dict) else {}
    runtime_yaml = safe_tenant.get("runtime_yaml") if isinstance(safe_tenant.get("runtime_yaml"), dict) else {}
    message = business_fallback_message(runtime_yaml)
    logger.warning(
        "assistant_fallback_used",
        extra={
            "tenant": str(safe_tenant.get("tenant_slug") or "").strip().lower(),
            "source": str(safe_tenant.get("source") or "fallback_runtime").strip().lower(),
            "configured": bool(message),
        },
    )
    return message or PLATFORM_FALLBACK_REPLY
