"""Render one short human-language anchor line from an OperationalState.

Single responsibility: given a state, return one sentence or empty string.
No side effects. No external dependencies beyond the dataclass.
"""
from __future__ import annotations

from app.domain.business_config.payment_catalog import method_kind
from app.domain.operations.operational_state import OperationalState

_OPTION_LABELS: dict[str, str] = {
    "nequi": "Nequi",
    "daviplata": "Daviplata",
    "link": "el link de pago",
    "transferencia": "transferencia",
    "bank": "transferencia bancaria",
    "breb": "Bre-B",
}


_CASH = "cash"


def render_op_anchor(state: OperationalState | None) -> str:
    """Return one short natural sentence for active operational context.

    Returns empty string when the state is None, inactive, or unknown.
    """
    if state is None or not state.is_active():
        return ""

    option = str(state.active_option or "").strip().lower()
    # Una cuenta concreta («bank:davivienda»): se nombra por su tipo; un medio de otro país, por su nombre en el catálogo.
    kind = option.split(":", 1)[0]
    catalog = method_kind(kind)
    opt_label = _OPTION_LABELS.get(kind, "") or (catalog.name if catalog is not None and not catalog.custom else "")
    p = str(state.active_process or "").strip().lower()

    if p == "payment":
        if state.pending_action == "report_payment":
            if kind == _CASH:
                # El efectivo no tiene comprobante que enviar.
                return "Ya le enviaste cómo pagar en efectivo."
            by = f" por {opt_label}" if opt_label else ""
            return f"Ya le enviaste los datos para pagar{by}: falta que pague y te envíe el comprobante."
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
    if state.active_process == "payment" and state.pending_action == "report_payment":
        # Qué explicar, con todas las letras y con un ejemplo: con «explícaselo con tus palabras», un modelo pequeño respondía «¿te los
        # envío de nuevo?» o repetía su mensaje anterior ante un «cómo así» (medido con la IA real, 13 nov 2026). Sin prohibiciones:
        # con «no le ofrezcas reenviarlos» llegó a decir «no puedo reenviar los datos».
        if str(state.active_option or "").strip().lower().split(":", 1)[0] == _CASH:
            return (
                "Si no entiende algo o pregunta qué sigue, explícale paso a paso cómo paga, con las indicaciones que ya tiene arriba "
                "en el chat. Por ejemplo: «Te explico: arriba te dejé cómo pagar en efectivo. Sigues esos pasos y con eso continuamos.»"
            )
        return (
            "Si no entiende algo o pregunta qué sigue, explícale paso a paso qué hacer. Por ejemplo: «Te explico: arriba, en este chat, "
            "te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.» "
            "Si te pide los datos otra vez, se le envían."
        )
    if str(state.active_option or "").strip():
        return "Si el usuario responde brevemente, continúa naturalmente desde ahí sin reabrir la opción."
    return "Si el usuario responde brevemente, continúa desde el paso activo sin reiniciarlo."
