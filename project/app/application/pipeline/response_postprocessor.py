from __future__ import annotations

import re


def _split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", str(text or "").strip()) if part.strip()]


def _is_conversational_closing(text: str) -> bool:
    lowered = str(text or "").lower()
    if "?" in lowered:
        return True

    return any(token in lowered for token in ["avanz", "siguiente paso", "empez", "te muestro", "quieres"])


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


_WARM_OPENERS = re.compile(
    r"^[\s¡!¿?]*(hola|perfecto|listo|claro|gracias|entendido|excelente|genial|buenas|ok\b|dale|super)\b",
    flags=re.IGNORECASE,
)


def _has_warm_opener(text: str) -> bool:
    return bool(_WARM_OPENERS.match(str(text or "").strip()))


def ensure_micro_greeting(text: str, *, user_message: str) -> str:
    response = str(text or "").strip()
    if not response:
        return response
    if is_pure_greeting(user_message):
        return response
    if _has_warm_opener(response):
        return response
    return f"Hola, {response}"


def enforce_max_words(text: str, max_words: int) -> str:
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

    last_sentence = sentences[-1] if sentences else ""
    if last_sentence and _is_conversational_closing(last_sentence) and last_sentence not in result:
        last_words = last_sentence.split()
        while result and total_words + len(last_words) > max_words:
            removed = result.pop()
            total_words -= len(removed.split())
        if len(last_words) <= max_words:
            result.append(last_sentence)

    if not result:
        trimmed = " ".join(words[:max_words])
        return trimmed

    return " ".join(result).strip()
