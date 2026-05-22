"""Continuity Composer — Phase 2.

Transforms selected memory pieces into human-readable operational context
for the AI seller.

Rules:
- NO backend labels ("last_intent", "dolor detectado", "dato previo relevante")
- NO templates with {{variable}} substitution
- Natural language only — reads like a briefing from a colleague, not a system log
- If there is nothing worth saying, return empty string (better nothing than noise)
"""
from __future__ import annotations

from app.domain.memory.contracts import CommercialMemorySignal
from app.domain.memory.episodic.retrieval import Episode


def compose_signal(
    *,
    selected_pain: str,
    pain_score: float,
    episodes: list[Episode],
    payment_active: bool,
    estado_pago: str,
    metodo_pago: str,
    conversation_state: str,
    last_response: str,
    context_weight: str,
    memory_used: list[str],
    candidates_evaluated: int,
    candidates_dropped: int,
) -> CommercialMemorySignal:
    """Assemble the CommercialMemorySignal from scored memory pieces."""
    continuity_brief = _compose_continuity(
        conversation_state=conversation_state,
        has_pain=bool(selected_pain),
        has_response=bool(last_response),
        payment_active=payment_active,
        context_weight=context_weight,
    )
    commercial_anchor = _compose_anchor(
        selected_pain=selected_pain,
        pain_score=pain_score,
        payment_active=payment_active,
        estado_pago=estado_pago,
        metodo_pago=metodo_pago,
        episodes=episodes,
    )
    episodic_hook = _compose_episodic_hook(
        episodes=episodes,
        context_weight=context_weight,
        commercial_anchor=commercial_anchor,
    )
    return CommercialMemorySignal(
        continuity_brief=continuity_brief,
        commercial_anchor_active=commercial_anchor,
        episodic_hook=episodic_hook,
        context_weight=context_weight,
        memory_used=memory_used,
        candidates_evaluated=candidates_evaluated,
        candidates_dropped=candidates_dropped,
    )


def _compose_continuity(
    *,
    conversation_state: str,
    has_pain: bool,
    has_response: bool,
    payment_active: bool,
    context_weight: str,
) -> str:
    """Temporal/relational cue — minimal or empty.

    The anchor and episodic hook carry the actual context.
    Adding 'this person already spoke to you' type sentences makes the
    model sound like a CRM system. Keep this empty; let the anchor speak.
    """
    del conversation_state, has_pain, has_response, payment_active, context_weight
    return ""


def _compose_anchor(
    *,
    selected_pain: str,
    pain_score: float,
    payment_active: bool,
    estado_pago: str,
    metodo_pago: str,
    episodes: list[Episode],
) -> str:
    """The single most relevant commercial pressure point for this turn."""

    # Payment context always wins as anchor when active
    if payment_active and metodo_pago:
        if estado_pago and estado_pago not in ("none", ""):
            return f"Quedamos en avanzar con {metodo_pago}. {estado_pago}."
        return f"Quedamos en avanzar con {metodo_pago}."

    # Active pain anchor (scored above threshold)
    if selected_pain and pain_score > 0.18:
        return f"Comentó que {selected_pain}."

    # Fallback: lift anchor from episodic signals
    for ep in episodes:
        if ep.signal_type in ("pain", "objection") and ep.role == "user":
            excerpt = ep.text[:120].rstrip()
            if len(ep.text) > 120:
                excerpt += "..."
            return f'"{excerpt}"'

    return ""


def _compose_episodic_hook(
    *,
    episodes: list[Episode],
    context_weight: str,
    commercial_anchor: str,
) -> str:
    """A second specific episode — only in strong context. Avoids repeating the anchor."""
    if context_weight != "strong":
        return ""

    for ep in episodes:
        if ep.signal_type in ("pain", "objection", "buy_signal") and ep.role == "user":
            excerpt = ep.text[:100].rstrip()
            if len(ep.text) > 100:
                excerpt += "..."
            # Don't duplicate what's already in the anchor
            if excerpt[:40] in commercial_anchor:
                continue
            return f'"{excerpt}"'

    return ""
