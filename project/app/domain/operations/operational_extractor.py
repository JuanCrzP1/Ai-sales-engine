"""Extract the active operational process from an assistant response text.

Kept intentionally small: no workflow engine, no state machine.
Only pattern-matching on the text the AI already produced.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from app.domain.operations.operational_state import OperationalState

# Static signal vocabulary: what the AI naturally writes for each known method type.
# Only consulted for methods the tenant has configured — never applied globally.
# Unknown types fall back to their type string as a literal match.
_METHOD_SIGNALS: dict[str, str] = {
    "nequi": r"nequi",
    "daviplata": r"daviplata",
    "link": r"link de pago|enlace de pago",
    "bank": r"bancolombia|transferencia bancaria|cuenta bancaria|cuenta de ahorros",
    "breb": r"bre-?b",
}

_PAYMENT_GENERIC = re.compile(
    r"avance(?:mos)? con el (?:siguiente paso|pago)"
    r"|m[eé]todo de pago"
    r"|link o transfer(?:encia)?"
    r"|(?:pagar?|transfer(?:encia)?) (?:que|cuando|para|por|con)",
)

_ACTIVATION = re.compile(
    r"para activar"
    r"|datos de arranque"
    r"|datos para (?:empezar|activar|iniciar)"
    r"|empezamos con la configuraci[oó]n"
    r"|gu[ií]a de integraci[oó]n",
)

_ONBOARDING = re.compile(
    r"configuraci[oó]n inicial"
    r"|vamos a dejarlo listo"
    r"|dejar(?:emos|lo) listo para empezar",
)

_HANDOFF = re.compile(
    r"te paso con"
    r"|te pongo con"
    r"|te conecto con"
    r"|te comunica(?:mos)? con",
)

def _expiry(hours: int = 6) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def extract_op_state(
    response_text: str,
    *,
    route_source: str = "",
    payment_methods: list[str] | None = None,
) -> OperationalState:
    """Derive an OperationalState from the assistant response text.

    payment_methods: list of method type strings configured for the current tenant
      (e.g. ["nequi", "bank"]). Only those methods will be recognized as active options.
      If None or empty, specific option detection is skipped.

    Returns an empty OperationalState when no active process is detected.
    AI-first: no intent logic, no keyword hacks — only reads what the AI wrote.
    """
    normalized = str(response_text or "").strip().lower()
    if not normalized:
        return OperationalState()

    # Payment with specific option — only tenant-configured methods are checked.
    if payment_methods:
        matched = [
            m for m in payment_methods
            if re.search(_METHOD_SIGNALS.get(m, re.escape(m)), normalized)
        ]
        if len(matched) == 1:
            return OperationalState(
                active_process="payment",
                active_option=matched[0],
                pending_action="confirm_method",
                expires_at=_expiry(),
            )
        # len > 1 → AI is listing multiple methods; no specific option active yet.

    # Payment generic (option not yet chosen)
    if _PAYMENT_GENERIC.search(normalized):
        return OperationalState(
            active_process="payment",
            pending_action="choose_payment_option",
            expires_at=_expiry(),
        )

    if _ACTIVATION.search(normalized):
        return OperationalState(
            active_process="activation",
            pending_action="share_startup_data",
            expires_at=_expiry(),
        )

    if _ONBOARDING.search(normalized):
        return OperationalState(
            active_process="onboarding",
            pending_action="share_startup_data",
            expires_at=_expiry(),
        )

    if _HANDOFF.search(normalized):
        return OperationalState(
            active_process="handoff",
            pending_action="wait_handoff",
            expires_at=_expiry(2),
        )

    return OperationalState()
