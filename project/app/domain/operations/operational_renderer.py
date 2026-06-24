"""Render one short human-language anchor line from an OperationalState.

Single responsibility: given a state, return one sentence or empty string.
No side effects. No external dependencies beyond the dataclass.
"""
from __future__ import annotations

from app.domain.operations.operational_state import OperationalState

_OPTION_LABELS: dict[str, str] = {
    "nequi": "Nequi",
    "daviplata": "Daviplata",
    "link": "el link de pago",
    "transferencia": "transferencia",
    "bank": "transferencia bancaria",
    "breb": "Bre-B",
}


def render_op_anchor(state: OperationalState | None) -> str:
    """Return one short natural sentence for active operational context.

    Returns empty string when the state is None, inactive, or unknown.
    """
    if state is None or not state.is_active():
        return ""

    opt_label = _OPTION_LABELS.get(str(state.active_option or "").strip().lower(), "")
    p = str(state.active_process or "").strip().lower()

    if p == "payment":
        if opt_label:
            return f"Venían avanzando por {opt_label}."
        return "Venían avanzando con el pago."

    if p in ("activation", "onboarding"):
        return "Ya iban dejando todo listo para empezar."

    if p == "handoff":
        return "Ya iban coordinando el siguiente paso."

    return ""


def render_op_rule(state: OperationalState | None) -> str:
    """Return a one-line continuation rule for active operational states.

    Injected into the prompt so the model continues rather than restarts.
    """
    if state is None or not state.is_active():
        return ""
    if str(state.active_option or "").strip():
        return "Si el usuario responde brevemente, continúa naturalmente desde ahí sin reabrir la opción."
    return "Si el usuario responde brevemente, continúa desde el paso activo sin reiniciarlo."
