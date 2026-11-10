"""Cómo responde el asistente: largo máximo y tono del negocio."""
from __future__ import annotations

from app.infrastructure.ai.prompting.sections.profile import response_tone
from app.infrastructure.ai.prompting.text import as_dict, as_text
from app.infrastructure.ai.prompting.view import PromptView

DEFAULT_MAX_WORDS = 80
MIN_MAX_WORDS = 20


def max_words(view: PromptView) -> int:
    response = as_dict(view.config.get("response"))
    try:
        return max(MIN_MAX_WORDS, int(view.runtime.get("response_max_words") or response.get("max_words") or DEFAULT_MAX_WORDS))
    except (TypeError, ValueError):
        return DEFAULT_MAX_WORDS


def render(view: PromptView) -> str:
    length = as_text(view.runtime.get("response_length") or "short") or "short"
    return f"ESTILO: {length}, máximo {max_words(view)} palabras, {response_tone(view.runtime)}."
