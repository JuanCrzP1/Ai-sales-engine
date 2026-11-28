"""El pago confirmado: lo que le llega al cliente cuando alguien del equipo verifica su pago y toca «Confirmar pago» en el chat.

Solo el equipo puede confirmar un pago: el cliente avisa que pagó, la IA le dice que el equipo lo verifica y el chat pasa a una
persona (`payment_outcome.py`). Cuando el equipo lo verifica, el cliente recibe el mensaje que el negocio escribió para ese momento
(Mensajes → Pagos, `messages.payment_confirmed`) tal cual. Si no escribió uno, sale el de la plataforma, con el trato y los emojis
del negocio (`formality.py`). Hasta el 27 nov 2026 ese mensaje se guardaba en el panel, pero nunca se enviaba.

Quién lo envía y qué más pasa al confirmar (el chat queda atendido, la venta, lo que sabe la IA) está en
`business_config_application/payment_confirmation.py`.
"""
from __future__ import annotations

from app.domain.business_config.contract import BusinessConfig
from app.domain.business_config.conversations import ConversationSummary
from app.domain.business_config.formality import Phrase

# Un pago está por confirmar si el cliente avisó que pagó (el chat pasó al equipo por eso) o si va en la etapa «pago». El almacén
# aplica la misma regla al tomarlo (`ConversationStore.claim_payment`).
PAYMENT_REVIEW = "payment_review"
PAYMENT_STAGE = "payment"
DEFAULT_PAYMENT_CONFIRMED = Phrase(
    tu="¡Listo! Tu pago quedó confirmado. Gracias por tu compra. ✅",
    usted="¡Listo! Su pago quedó confirmado. Gracias por su compra. ✅",
)
_EMOJI = " ✅"


def payment_confirmed_message(config: BusinessConfig | None) -> str:
    """El mensaje del negocio para el pago confirmado o, si no escribió uno (o no hay nada publicado), el de la plataforma."""
    own = str(config.messages.payment_confirmed or "").strip() if config is not None else ""
    if own:
        return own
    style = config.response_style if config is not None else None
    text = DEFAULT_PAYMENT_CONFIRMED.to(style.formality if style is not None else None)
    return text.replace(_EMOJI, "") if style is not None and style.emojis is False else text


def payment_pending(summary: ConversationSummary) -> bool:
    """Si la conversación tiene un pago por confirmar (el panel muestra «Confirmar pago»)."""
    return summary.handoff_reason == PAYMENT_REVIEW or summary.stage == PAYMENT_STAGE
