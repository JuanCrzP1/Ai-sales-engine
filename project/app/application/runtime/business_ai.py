"""La inteligencia artificial de cada negocio, mensaje a mensaje.

La plataforma no tiene clave propia: cada negocio responde con su clave de OpenRouter y su modelo, que el motor lee del almacén en
cada mensaje. Un negocio sin clave no responde con IA (contesta el respaldo del motor) y nunca usa la clave de otro negocio.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from sqlalchemy.exc import SQLAlchemyError

from app.domain.business_config.ai_settings import AICredentials
from app.domain.business_config.ai_usage import AIUsage
from app.domain.business_config.errors import BusinessConfigError, SecretResolutionError
from app.infrastructure.business_config.runtime_access import open_published_reader, record_ai_usage
from app.utils.logger import logger

# Quién recibe los tokens de cada respuesta: (modelo, tokens de entrada, tokens de salida, costo en dólares o None).
UsageCallback = Callable[[str, int, int, float | None], None]


@dataclass(frozen=True)
class MessageAI:
    """Con qué IA se responde un mensaje: la clave y el modelo del negocio que lo recibe, más los ajustes de generación."""

    api_key: str | None = field(default=None, repr=False)
    model_name: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    # Anota el consumo de cada respuesta en la cuenta de este negocio.
    on_usage: UsageCallback | None = field(default=None, repr=False, compare=False)


def load_business_ai(tenant_slug: str) -> AICredentials | None:
    """La clave y el modelo de este negocio, o None si no tiene clave o el almacén no se puede leer."""
    try:
        credentials = open_published_reader().ai_credentials(tenant_slug)
    except (BusinessConfigError, SecretResolutionError, SQLAlchemyError) as exc:
        # Solo el tipo: el texto de un error de base de datos puede incluir datos de conexión.
        logger.error("business_ai_unavailable", extra={"tenant": tenant_slug, "error": type(exc).__name__})
        return None
    if credentials is None:
        logger.warning("business_ai_key_missing", extra={"tenant": tenant_slug})
    return credentials


def message_ai(bot_config, credentials: AICredentials | None, *, on_usage: UsageCallback | None = None) -> MessageAI:
    """La IA de este mensaje: la del negocio. Del llamador solo se toman los ajustes de generación, nunca una clave."""
    return MessageAI(
        api_key=credentials.api_key if credentials else None,
        model_name=(credentials.model if credentials else None) or getattr(bot_config, "model_name", None),
        temperature=getattr(bot_config, "temperature", None),
        max_tokens=getattr(bot_config, "max_tokens", None),
        top_p=getattr(bot_config, "top_p", None),
        on_usage=on_usage,
    )


def business_usage_recorder(tenant_slug: str) -> UsageCallback:
    """Anota cada respuesta en el consumo del negocio. Si no se puede anotar, el cliente igual recibe su respuesta."""

    def record(model: str, prompt_tokens: int, completion_tokens: int, cost_usd: float | None) -> None:
        try:
            record_ai_usage(tenant_slug, AIUsage(model, prompt_tokens, completion_tokens, cost_usd))
        except (BusinessConfigError, SQLAlchemyError, ValueError) as exc:
            logger.error("ai_usage_not_recorded", extra={"tenant": tenant_slug, "error": type(exc).__name__})

    return record
