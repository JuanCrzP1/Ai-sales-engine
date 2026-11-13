from __future__ import annotations

import re


def _split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", str(text or "").strip()) if part.strip()]


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


# Lo que algunos modelos escriben dentro de su mensaje cuando intentan «llamar una función»: un bloque de etiquetas que no es para el
# cliente («<function_calls>[{"name": …}]</function_calls>»).
_TOOL_BLOCK = re.compile(r"<(function_calls|tool_call|tool_use|invoke|antml:[a-z_]+)\b[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)


def without_model_artifacts(text: str) -> str:
    """El mensaje del asesor sin los bloques de «llamada a función» que algunos modelos dejan dentro del texto."""
    if "<" not in str(text or ""):
        return str(text or "")
    return re.sub(r"\n{3,}", "\n\n", _TOOL_BLOCK.sub("", str(text))).strip()
