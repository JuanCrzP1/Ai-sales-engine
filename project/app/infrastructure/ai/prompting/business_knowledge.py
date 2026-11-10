"""Bloque de preguntas frecuentes del prompt.

Sale de `config.knowledge`, que solo existe cuando la configuración del negocio viene del contrato y tiene preguntas frecuentes.

Si todas caben en `FAQ_PROMPT_MAX_CHARS`, van todas. Si no, van primero las que más palabras comparten con el mensaje del cliente,
hasta llenar ese espacio: un negocio con muchas preguntas no infla cada prompt. Siempre se escriben en el orden del negocio.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.domain.business_config.engine_policy import FAQ_PROMPT_MAX_CHARS

KNOWLEDGE_HEADER = "CONOCIMIENTO DEL NEGOCIO (preguntas frecuentes):"

# Palabras que no distinguen una pregunta de otra.
_STOPWORDS = frozenset(
    "a al como con cual cuales cuando de del donde el en es esta este hay la las le les lo los me mi mis no o para por que se si sin "
    "su sus te tu tus un una uno unos unas y ya".split()
)


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


def _stem(word: str) -> str:
    """Singular aproximado: «domingos» y «domingo» cuentan como la misma palabra."""
    if len(word) > 4 and word.endswith("es"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s"):
        return word[:-1]
    return word


def _words(text: str) -> set[str]:
    plain = "".join(char for char in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(char))
    return {_stem(word) for word in re.findall(r"[a-z0-9]+", plain) if word not in _STOPWORDS}


def select_faqs(faqs: list[tuple[str, str]], user_message: str, *, max_chars: int = FAQ_PROMPT_MAX_CHARS) -> list[tuple[str, str]]:
    """Las preguntas que van al prompt, en el orden del negocio."""
    sizes = [len(_entry(question, answer)) + 1 for question, answer in faqs]
    if sum(sizes) <= max_chars:
        return list(faqs)
    message = _words(user_message)
    by_relevance = sorted(range(len(faqs)), key=lambda index: (-len(message & _words(" ".join(faqs[index]))), index))
    chosen: set[int] = set()
    used = 0
    for index in by_relevance:
        if used + sizes[index] <= max_chars:
            chosen.add(index)
            used += sizes[index]
    return [faq for index, faq in enumerate(faqs) if index in chosen]


def build_knowledge_context(runtime: dict[str, Any], *, user_message: str = "") -> str:
    """El bloque de preguntas frecuentes, o "" si el negocio no tiene."""
    faqs = _faqs(runtime)
    if not faqs:
        return ""
    return "\n".join([KNOWLEDGE_HEADER, *(_entry(question, answer) for question, answer in select_faqs(faqs, user_message))])
