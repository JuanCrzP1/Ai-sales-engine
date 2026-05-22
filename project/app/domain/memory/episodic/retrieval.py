"""Episodic Memory Retrieval — Phase 2.

Recovers 1-2 concrete relevant moments from conversation history.

Rules:
- Prefers user-origin messages (the client's own words)
- Scores by keyword overlap with the current message
- Boosts commercial signals: pain, objection, buy intent
- Skips the 2 most recent entries (already in session memory)
- No embeddings for Phase 2 — text overlap is sufficient and fast

SIZE GUARD: This module must stay small and dumb.
- Do NOT grow the keyword sets beyond ~15 entries each.
- Do NOT add new signal types.
- Do NOT add heuristics that classify intent.
- Selection only — behavior stays with the model.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Commercial signal keyword sets (Spanish)
_PAIN_MARKERS: frozenset[str] = frozenset({
    "enfrían", "enfría", "pierdo", "perdiendo", "pierdes", "tardo", "demoro",
    "lento", "lenta", "problema", "problemas", "no puedo", "me cuesta", "difícil",
    "falla", "fallas", "mal", "malos", "malas", "no funciona", "no responde",
    "se van", "se escapan", "sin respuesta", "sin contestar", "se me van",
})

_OBJECTION_MARKERS: frozenset[str] = frozenset({
    "caro", "costoso", "costosa", "no tengo", "no me alcanza", "después",
    "luego", "lo pienso", "lo consulto", "no sé", "duda", "dudas",
    "no estoy seguro", "no estoy segura", "déjame pensar", "mejor otro",
    "lo voy a pensar", "me lo voy a pensar",
})

_BUY_SIGNAL_MARKERS: frozenset[str] = frozenset({
    "cómo pago", "como pago", "quiero empezar", "quiero comenzar",
    "cómo compro", "como compro", "cuándo empieza", "cuando empieza",
    "listo", "dale", "cómo inicio", "como inicio", "cómo arranco",
    "como arranco", "quiero el plan", "quiero acceso", "me apunto",
})

_STOPWORDS: frozenset[str] = frozenset({
    "de", "la", "el", "que", "y", "a", "en", "es", "no", "se", "me",
    "lo", "un", "una", "con", "por", "para", "mi", "te", "le", "los",
    "las", "al", "del", "su", "sus", "si", "ya", "más", "pero", "o",
    "como", "cuando", "qué", "cómo", "cuándo",
})


@dataclass
class Episode:
    text: str
    role: str             # "user" | "assistant"
    relevance_score: float
    signal_type: str      # "pain" | "objection" | "buy_signal" | "general"


def _tokenize(text: str) -> frozenset[str]:
    tokens = set(re.findall(r"\w+", text.lower()))
    return frozenset(tokens - _STOPWORDS)


def _overlap_score(tokens_a: frozenset[str], tokens_b: frozenset[str]) -> float:
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / max(len(tokens_a), len(tokens_b))


def _detect_signal(text: str) -> str:
    lower = text.lower()
    for marker in _BUY_SIGNAL_MARKERS:
        if marker in lower:
            return "buy_signal"
    for marker in _OBJECTION_MARKERS:
        if marker in lower:
            return "objection"
    for marker in _PAIN_MARKERS:
        if marker in lower:
            return "pain"
    return "general"


def retrieve_episodes(
    history: list[dict],
    current_message: str,
    *,
    max_episodes: int = 2,
    min_score: float = 0.12,
) -> list[Episode]:
    """Recover relevant concrete episodes from conversation history.

    Skips the 2 most recent entries (already captured in session memory).
    Returns at most max_episodes, sorted by relevance score descending.
    """
    if not history or not current_message.strip():
        return []

    current_tokens = _tokenize(current_message)

    # Skip the most recent 2 turns (those are in session/immediate context already)
    prior = history[:-2] if len(history) > 2 else []
    if not prior:
        return []

    candidates: list[Episode] = []

    for entry in prior:
        if isinstance(entry, dict):
            role = str(entry.get("role") or "user").strip().lower()
            text = str(entry.get("text") or "").strip()
        else:
            role = "user"
            text = str(entry or "").strip()

        if not text or len(text) < 8:
            continue

        signal_type = _detect_signal(text)
        entry_tokens = _tokenize(text)
        overlap = _overlap_score(current_tokens, entry_tokens)

        # Base: keyword overlap
        score = overlap * 0.40

        # User messages are more valuable (the client's words carry commercial weight)
        if role == "user":
            score += 0.12

        # Commercial signal boosts
        if signal_type == "pain":
            score += 0.22
        elif signal_type == "objection":
            score += 0.20
        elif signal_type == "buy_signal":
            score += 0.18

        if score >= min_score:
            candidates.append(
                Episode(
                    text=text,
                    role=role,
                    relevance_score=score,
                    signal_type=signal_type,
                )
            )

    # Sort descending; prefer user messages on score ties
    candidates.sort(
        key=lambda e: (round(e.relevance_score, 2), e.role == "user"),
        reverse=True,
    )
    return candidates[:max_episodes]
