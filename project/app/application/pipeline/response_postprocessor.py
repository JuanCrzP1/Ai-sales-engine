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
