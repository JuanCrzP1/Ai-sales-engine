"""Inteligencia artificial de cada negocio: el modelo que usa su asistente y su propia clave de OpenRouter.

No es parte del contrato comercial: la clave es un secreto y el modelo es técnico. Se guarda aparte, cifrada, y nunca sale del
servidor completa: hacia fuera solo viaja si está configurada y sus últimos caracteres (`AISettings`). La clave solo la recibe el
motor (`AICredentials`), y siempre la de ese negocio.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.domain.business_config.errors import FieldIssue, InvalidFieldsError

AI_PROVIDER = "openrouter"
MASK = "••••"
MAX_MODEL_CHARS = 120
MAX_KEY_CHARS = 300
MIN_KEY_CHARS = 20
# Últimos caracteres visibles de la clave, para reconocerla; con menos de esto se mostraría casi toda.
KEY_HINT_CHARS = 4

# `proveedor/modelo`, con variante opcional: `openai/gpt-4o-mini`, `meta-llama/llama-3.3-70b-instruct:free`.
_MODEL = re.compile(r"[a-z0-9][a-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._:-]*")


@dataclass(frozen=True)
class AISettings:
    """Lo que se puede mostrar: proveedor, modelo y si hay clave, con sus últimos caracteres."""

    provider: str = AI_PROVIDER
    model: str | None = None
    key_configured: bool = False
    key_hint: str | None = None


@dataclass(frozen=True)
class AICredentials:
    """Lo que necesita el motor para responder por este negocio. Nunca se serializa hacia el panel ni aparece en un registro."""

    provider: str
    model: str | None
    api_key: str = field(repr=False)


@dataclass(frozen=True)
class KeyCheck:
    """Resultado de comprobar la clave con el proveedor, en palabras para quien administra el negocio."""

    valid: bool
    message: str


@dataclass(frozen=True)
class AssistantTurn:
    """Una respuesta del asistente en el área de pruebas. `ai_answered` es falso si respondió el motor sin la IA (por ejemplo,
    porque el proveedor rechazó la clave o el modelo)."""

    reply: str
    intent: str | None = None
    ai_answered: bool = True
    # El asistente pasó la conversación a una persona del equipo.
    handoff: bool = False


def key_hint(api_key: str) -> str:
    return f"{MASK}{api_key[-KEY_HINT_CHARS:]}"


def is_model_id(text: str) -> bool:
    """`proveedor/modelo`, como los escribe OpenRouter (por ejemplo `openai/gpt-4o-mini` o `meta-llama/llama-3.3-70b-instruct:free`)."""
    return len(text) <= MAX_MODEL_CHARS and _MODEL.fullmatch(text) is not None


def clean_model(model: str | None) -> str | None:
    """El modelo escrito por el negocio, o None para usar el del motor. Falla si no tiene la forma `proveedor/modelo`."""
    text = str(model or "").strip()
    if not text:
        return None
    if not is_model_id(text):
        raise InvalidFieldsError(
            "Revisa el modelo.", [FieldIssue("model", "Escribe el modelo como aparece en OpenRouter, por ejemplo openai/gpt-4o-mini.")]
        )
    return text


def clean_api_key(api_key: str) -> str:
    """La clave pegada por el negocio, sin espacios. El mensaje de error nunca la repite."""
    text = str(api_key or "").strip()
    if not MIN_KEY_CHARS <= len(text) <= MAX_KEY_CHARS or any(char.isspace() for char in text):
        raise InvalidFieldsError(
            "Revisa la clave de OpenRouter.", [FieldIssue("api_key", "Pega la clave completa de OpenRouter, sin espacios.")]
        )
    return text
