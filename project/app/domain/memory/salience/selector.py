"""Commercial Memory Salience Selector — Phase 2.

Evaluates all available memory pieces and decides which deserve to enter
the current turn's context. Produces a CommercialMemorySignal.

Design rules:
- Pure function: same inputs → same outputs (testable in isolation)
- No if/intent checks: evaluates semantic signals, not classified categories
- No hardcoded tenant thresholds: all weights are uniform across tenants
- No side effects: reads only, does not write to any store
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from app.domain.memory.composers.continuity import compose_signal
from app.domain.memory.contracts import CommercialMemorySignal
from app.domain.memory.episodic.retrieval import retrieve_episodes

_STOPWORDS: frozenset[str] = frozenset({
    "de", "la", "el", "que", "y", "a", "en", "es", "no", "se", "me",
    "lo", "un", "una", "con", "por", "para", "mi", "te", "le", "los",
    "las", "al", "del", "su", "sus", "si", "ya", "más", "pero", "o",
})


def _tokenize(text: str) -> frozenset[str]:
    tokens = set(re.findall(r"\w+", text.lower()))
    return frozenset(tokens - _STOPWORDS)


def _overlap_score(tokens_a: frozenset[str], tokens_b: frozenset[str]) -> float:
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / max(len(tokens_a), len(tokens_b))


def _temporal_weight(last_timestamp: datetime | None) -> float:
    """Soft temporal decay. Most recent = highest weight. Floor at 0.15.

    Decay rate: ~7% per day. At 12 days old → ~0.16 (near floor).
    """
    if last_timestamp is None:
        return 0.50
    now = datetime.now(tz=timezone.utc)
    ts = last_timestamp
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    days_old = max(0.0, (now - ts).total_seconds() / 86400)
    return max(0.15, 1.0 - days_old * 0.07)


def select(
    *,
    memory_context: dict,
    history: list[dict],
    current_message: str,
    last_timestamp: datetime | None = None,
) -> CommercialMemorySignal:
    """Select relevant memory and produce a CommercialMemorySignal.

    Scoring per memory piece:
        overlap(piece, current_message) × 0.35
        + base_pain_boost                 × 0.28   (pain is always commercially relevant)
        + temporal_weight                 × 0.22
        → user-origin pieces get an additional +0.15 multiplier on top

    Context weight thresholds:
        strong   → payment active OR strong pain score (>0.55) OR pain+episode
        moderate → moderate pain (>0.18) OR episode + returning conversation
        light    → everything else (first turn, no history, no pain)
    """
    candidates_evaluated: int = 0
    candidates_dropped: int = 0
    memory_used: list[str] = []

    current_tokens = _tokenize(current_message)
    t_weight = _temporal_weight(last_timestamp)

    # --- Extract raw memory fields ---
    active_pain = str(
        memory_context.get("last_pain") or memory_context.get("active_pain") or ""
    ).strip()
    pain_timeline_raw = memory_context.get("pain_timeline") or []
    pain_timeline = [str(p).strip() for p in pain_timeline_raw if str(p).strip()]
    estado_pago = str(memory_context.get("estado_pago") or "none").strip().lower()
    metodo_pago = str(memory_context.get("metodo_pago_elegido") or "").strip()
    last_response = str(
        memory_context.get("last_ai_response") or memory_context.get("last_response") or ""
    ).strip()
    conversation_state = str(
        memory_context.get("conversation_state") or "new"
    ).strip().lower()

    # --- Score pain anchors ---
    # Deduplicate: active_pain first, then timeline
    all_pains: list[str] = []
    seen_pains: set[str] = set()
    for p in [active_pain, *pain_timeline]:
        key = p.strip().lower()
        if p.strip() and key not in seen_pains:
            seen_pains.add(key)
            all_pains.append(p.strip())

    selected_pain = ""
    best_pain_score = 0.0

    for pain in all_pains:
        candidates_evaluated += 1
        pain_tokens = _tokenize(pain)
        overlap = _overlap_score(current_tokens, pain_tokens)
        # Pain always carries a base commercial weight (it's never irrelevant)
        score = (overlap * 0.35) + 0.28 + (t_weight * 0.22)

        if score > best_pain_score:
            best_pain_score = score
            selected_pain = pain
            source_key = "active_pain" if pain == active_pain else "pain_timeline"
            if source_key not in memory_used:
                memory_used.append(source_key)
        else:
            candidates_dropped += 1

    # --- Payment state ---
    payment_active = bool(
        estado_pago and estado_pago not in ("", "none") and metodo_pago
    )
    if payment_active:
        candidates_evaluated += 1
        if "estado_pago" not in memory_used:
            memory_used.append("estado_pago")

    # --- Episodic retrieval ---
    prior_count = max(0, len(history) - 2)
    candidates_evaluated += prior_count
    episodes = retrieve_episodes(history, current_message, max_episodes=2, min_score=0.12)
    candidates_dropped += max(0, prior_count - len(episodes))

    # --- Determine context_weight ---
    has_strong_pain = bool(selected_pain) and best_pain_score > 0.55
    has_moderate_pain = bool(selected_pain) and best_pain_score > 0.18
    has_episodes = bool(episodes)
    is_returning = conversation_state in ("active", "warm", "cold")

    if payment_active:
        context_weight = "strong"
    elif has_strong_pain or (has_moderate_pain and has_episodes):
        context_weight = "strong"
    elif has_moderate_pain or (has_episodes and is_returning):
        context_weight = "moderate"
    else:
        context_weight = "light"

    return compose_signal(
        selected_pain=selected_pain,
        pain_score=best_pain_score,
        episodes=episodes,
        payment_active=payment_active,
        estado_pago=estado_pago,
        metodo_pago=metodo_pago,
        conversation_state=conversation_state,
        last_response=last_response,
        context_weight=context_weight,
        memory_used=memory_used,
        candidates_evaluated=candidates_evaluated,
        candidates_dropped=candidates_dropped,
    )
