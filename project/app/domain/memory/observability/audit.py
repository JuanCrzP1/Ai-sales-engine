"""Memory Signal Audit — compact observability per turn.

One structured log event per turn, after signal generation, before prompt assembly.
No full text dumps. No prompt content. No message transcripts.
Only structural metadata about what was selected and why.
"""
from __future__ import annotations

from app.domain.memory.contracts import CommercialMemorySignal
from app.utils.logger import logger


def emit_memory_audit(
    *,
    tenant: str,
    user_id: str,
    signal: CommercialMemorySignal,
    pricing_mode: str = "normal",
) -> None:
    """Emit a compact structured audit log for the memory signal used in this turn.

    Fields:
        context_weight      — how much memory influenced this turn
        candidates_used     — which memory fields contributed
        candidates_dropped  — how many were scored and rejected
        *_len               — char length of each rendered block (not the text itself)
        pricing_mode        — "normal" | "compact" (budget decision)
        memory_changed_response — null in production; filled in lab A/B experiments
    """
    logger.info(
        {
            "event": "memory_signal_audit",
            "tenant": str(tenant or "").strip().lower(),
            "user_id": str(user_id or "").strip().lower(),
            "context_weight": signal.context_weight,
            "candidates_evaluated": signal.candidates_evaluated,
            "candidates_used": signal.memory_used,
            "candidates_dropped": signal.candidates_dropped,
            "continuity_brief_len": len(signal.continuity_brief),
            "anchor_active_len": len(signal.commercial_anchor_active),
            "episodic_hook_len": len(signal.episodic_hook),
            "pricing_mode": pricing_mode,
            "memory_changed_response": None,
        }
    )
