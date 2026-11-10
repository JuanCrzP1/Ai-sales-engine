"""Bloque de preguntas frecuentes del prompt.

Sale de `config.knowledge`, que compila el contrato cuando el negocio tiene preguntas frecuentes.

Si todas caben en `FAQ_PROMPT_MAX_CHARS`, van todas. Si no, van primero las que más palabras comparten con el mensaje del cliente,
hasta llenar ese espacio (`relevance.py`): un negocio con muchas preguntas no infla cada prompt. Siempre en el orden del negocio.
"""
from __future__ import annotations

from typing import Any

from app.domain.business_config.engine_policy import FAQ_PROMPT_MAX_CHARS
from app.infrastructure.ai.prompting import relevance

KNOWLEDGE_HEADER = "CONOCIMIENTO DEL NEGOCIO (preguntas frecuentes):"


def _faqs(runtime: dict) -> list[tuple[str, str]]:
    config = runtime.get("config") if isinstance(runtime, dict) and isinstance(runtime.get("config"), dict) else {}
    knowledge = config.get("knowledge") if isinstance(config.get("knowledge"), dict) else {}
    entries = knowledge.get("faqs") if isinstance(knowledge.get("faqs"), list) else []
    return [
        (question, answer)
        for entry in entries
        if isinstance(entry, dict)
        and (question := str(entry.get("question") or "").strip())
        and (answer := str(entry.get("answer") or "").strip())
    ]


def _entry(question: str, answer: str) -> str:
    return f"- P: {question}\n  R: {answer}"


def select_faqs(faqs: list[tuple[str, str]], user_message: str, *, max_chars: int = FAQ_PROMPT_MAX_CHARS) -> list[tuple[str, str]]:
    """Las preguntas que van al prompt, en el orden del negocio."""
    return relevance.select(faqs, size=lambda faq: len(_entry(*faq)) + 1, text=" ".join, query=user_message, max_chars=max_chars)


def build_knowledge_context(runtime: dict[str, Any], *, user_message: str = "") -> str:
    """El bloque de preguntas frecuentes, o "" si el negocio no tiene."""
    faqs = _faqs(runtime)
    if not faqs:
        return ""
    return "\n".join([KNOWLEDGE_HEADER, *(_entry(question, answer) for question, answer in select_faqs(faqs, user_message))])
