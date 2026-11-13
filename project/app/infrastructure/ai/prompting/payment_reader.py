"""El lector de pagos: lo que se le envía al modelo para que diga qué pide el cliente sobre el pago, en una llamada corta.

Entender al cliente es trabajo de la IA, no de reglas de palabras. El asesor (la llamada grande, `composer.py`) atiende muchas cosas a
la vez y un modelo pequeño se confunde al decidir; una pregunta corta y enfocada sí la responde bien (medido con la IA real: 117 de
120 con el modelo más pequeño y 40 de 40 con los demás). Aquí solo se arma el texto; quién lo usa y qué se hace con la respuesta
está en `application/pipeline/payment_reading.py`.
"""
from __future__ import annotations

from app.infrastructure.ai.prompting import instructions
from app.infrastructure.ai.prompting.history import recent_messages
from app.infrastructure.ai.prompting.sections.payments import payment_methods
from app.infrastructure.ai.prompting.view import PromptView

# Lo que se muestra de la última respuesta del asesor: el contexto del mensaje del cliente, no la conversación entera.
MAX_LAST_REPLY_CHARS = 400


def reader_prompt(runtime: dict) -> str:
    """Las instrucciones del lector, con los medios de pago del negocio (solo sus nombres)."""
    return instructions.PAYMENT_READER.format(methods=", ".join(payment_methods(PromptView(runtime=runtime))))


def reader_turn(runtime: dict, user_message: str, *, sent: str = "") -> str:
    """El mensaje del cliente con su contexto: si ya se le enviaron datos de pago (`sent`: de qué medio) y lo último que le dijo el
    asesor. Sin datos de pago: el historial ya los trae ocultos."""
    replies = [message["content"] for message in recent_messages(runtime) if message["role"] == "assistant"]
    last_reply = replies[-1][:MAX_LAST_REPLY_CHARS] if replies else ""
    lines = [
        instructions.READER_SENT.format(method=sent) if sent else instructions.READER_NOT_SENT,
        instructions.READER_LAST_REPLY.format(reply=last_reply) if last_reply else "",
        instructions.READER_MESSAGE.format(message=str(user_message or "").strip()),
    ]
    return "\n".join(line for line in lines if line)
