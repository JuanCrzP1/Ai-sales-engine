from __future__ import annotations

import re


def _split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", str(text or "").strip()) if part.strip()]


def _normalize_for_greeting(text: str) -> str:
    value = str(text or "").strip().lower()
    value = re.sub(r"[¡!¿?.,;:]", "", value)
    return " ".join(value.split())


def is_pure_greeting(text: str) -> bool:
    normalized = _normalize_for_greeting(text)
    if not normalized:
        return False

    greetings = {
        "hola",
        "holaa",
        "buenas",
        "buenos dias",
        "buen dia",
        "hey",
        "que mas",
        "q mas",
        "qlq",
        "parce",
        "parce que mas",
        "amigo",
        "bro",
    }
    if normalized in greetings:
        return True

    words = normalized.split()
    if len(words) > 3:
        return False

    intent_tokens = {"precio", "vale", "cuanto", "cuesta", "info", "informacion", "necesito", "quiero", "pedido", "comprar", "venden", "vendes"}
    if any(word in intent_tokens for word in words):
        return False

    soft_tokens = {"hola", "holaa", "buenas", "buenos", "dias", "buen", "dia", "hey", "que", "q", "mas", "qlq", "parce", "parcero", "amigo", "bro"}
    return all(word in soft_tokens for word in words)



def enforce_max_words(text: str, max_words: int, *, tenant: str = "", user_id: str = "") -> str:
    if not text:
        return text

    words = text.split()
    if len(words) <= max_words:
        return text

    sentences = _split_sentences(text)
    result = []
    total_words = 0

    for sentence in sentences:
        sentence_words = sentence.split()

        if total_words + len(sentence_words) > max_words:
            break

        result.append(sentence)
        total_words += len(sentence_words)

    if not result:
        trimmed = " ".join(words[:max_words])
        return trimmed

    return " ".join(result).strip()
