"""El paso de la conversación, en una frase para la IA: qué ya hizo el sistema y qué falta.

Solo hechos: el paso lo marca el sistema cuando de verdad pasa algo (envió los datos de pago: `payment_delivery.sent_state`), nunca
las palabras de la IA. Hasta el 13 nov 2026 también se sacaba de lo que escribía la IA («Nequi», «datos de arranque», «te paso
con…»), y unas palabras sueltas cambiaban el paso o pasaban el chat a una persona. Lo demás de la conversación lo da la memoria: los
mensajes recientes y el resumen de lo anterior.
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


def _sent_payment(state: OperationalState | None) -> bool:
    return bool(state and state.is_active() and state.active_process == "payment" and state.pending_action == "report_payment")


def render_op_anchor(state: OperationalState | None) -> str:
    """Qué ya hizo el sistema: «Ya le enviaste los datos para pagar por Nequi…», o "" si no hay un paso en curso."""
    if not _sent_payment(state):
        return ""
    kind = str(state.active_option or "").strip().lower().split(":", 1)[0]
    if kind == _CASH:
        # El efectivo no tiene comprobante que enviar.
        return "Ya le enviaste cómo pagar en efectivo."
    catalog = method_kind(kind)
    label = _OPTION_LABELS.get(kind, "") or (catalog.name if catalog is not None and not catalog.custom else "")
    by = f" por {label}" if label else ""
    return f"Ya le enviaste los datos para pagar{by}: falta que pague y te envíe el comprobante."


def render_op_rule(state: OperationalState | None) -> str:
    """Qué hacer en ese paso, o "" si no hay un paso en curso."""
    if not _sent_payment(state):
        return ""
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
