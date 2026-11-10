"""Qué decir cuando el cliente reporta un pago: el mensaje exacto del negocio, sin confirmarlo nunca."""
from __future__ import annotations

from app.infrastructure.ai.prompting import instructions
from app.infrastructure.ai.prompting.text import as_dict, as_text
from app.infrastructure.ai.prompting.view import PromptView

NOT_CONFIGURED = "sin mensaje configurado"


def render(view: PromptView) -> str:
    """Solo cuando hay un pago en curso en la memoria (método elegido o estado de pago)."""
    if not str(view.memory.get("metodo_pago_elegido") or "").strip() and not str(view.memory.get("estado_pago") or "").strip():
        return ""
    post_payment = view.post_payment
    on_report = as_text(as_dict(post_payment.get("on_user_report")).get("message", ""))
    on_confirmed = as_text(as_dict(post_payment.get("on_payment_confirmed")).get("message", ""))
    return instructions.POST_PAYMENT.format(on_user_report_message=on_report or NOT_CONFIGURED, on_payment_confirmed_message=on_confirmed or NOT_CONFIGURED)
