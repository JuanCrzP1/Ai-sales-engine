"""El lector de pagos: lo que se le envía al modelo para que diga qué pide el cliente sobre el pago, en una llamada corta.

Entender al cliente es trabajo de la IA, no de reglas de palabras. El asesor (la llamada grande, `composer.py`) atiende muchas cosas a
la vez y un modelo pequeño se confunde al decidir; una pregunta corta y enfocada sí la responde bien (medido con la IA real: 117 de
120 con el modelo más pequeño y 40 de 40 con los demás). Aquí solo se arma el texto; quién lo usa y qué se hace con la respuesta
está en `application/pipeline/payment_reading.py`.
"""
from __future__ import annotations

from app.infrastructure.ai.prompting.history import recent_messages
from app.infrastructure.ai.prompting.sections.payments import payment_methods
from app.infrastructure.ai.prompting.view import PromptView

# Las instrucciones del lector. Los ejemplos no nombran medios de ningún país: sirven para cualquier negocio.
# Querer comprar no es pedir los datos: «Me convence, lo quiero» se leía como «pide los datos» (0 de 18 en 6 casos así,
# `lector_antes_20261119`) y el motor le indicaba al asesor preguntar con qué medio paga, también en un negocio que solo capta datos.
PAYMENT_READER = """
Lees el último mensaje de un cliente en el chat de ventas de un negocio y dices qué pide sobre el pago. No le respondes al cliente.
Responde solo con un objeto JSON, sin texto antes ni después:
{{"recibe_datos_de_pago": false, "medio": "", "dice_que_ya_pago": false}}

- recibe_datos_de_pago: true si con este mensaje el cliente debe recibir los datos para pagar (el número, la cuenta o el link):
  - los pide, o pide que se los envíen otra vez: «pásame el número», «¿a qué cuenta te consigno?», «se me borró, envíamelo de
    nuevo», «no me llegó», «¿cuál era el número?»;
  - dice con cuál de los medios va a pagar o prefiere pagar: «te pago por transferencia», «mejor en efectivo», «prefiero el
    link», o responde con un medio cuando el asesor le pregunta con cuál paga;
  - o acepta cuando el asesor le ofreció enviarle los datos para pagar («¿le envío los datos?»): «sí, envíamelos», «dale».
  Querer comprar no es pedir los datos: si dice que lo compra o que quiere empezar («me convence», «listo, avancemos»), o acepta
  cuando el asesor le preguntó si quiere avanzar o empezar, es false.
  Es false si solo pregunta si puede pagar con un medio o cuáles hay, aunque no escriba los signos de pregunta («y puedo
  transferir», «y con tarjeta no», «¿cómo pago?»), si quiere pagar y no dice con qué medio, si avisa que va a pagar o que ya pagó,
  si no entiende algo («¿cómo así?») o si habla de otra cosa (pide otro número, información, un precio).
- medio: el medio de pago del que debe recibir los datos, como aparece en los medios del negocio. Si no dice cuál, "".
- dice_que_ya_pago: true solo si dice que ya pagó, consignó o transfirió, o que envía el comprobante de un pago hecho. Es false si
  todavía no ha pagado: va a pagar ahora o después («ya voy a pagar», «ahorita te consigno», «mañana pago»).

Medios de pago del negocio: {methods}
""".strip()
READER_SENT = "Al cliente ya se le enviaron los datos para pagar por {method}."
READER_NOT_SENT = "Al cliente todavía no se le han enviado datos de pago (aunque el asesor diga otra cosa)."
READER_LAST_REPLY = "Lo último que le dijo el asesor: «{reply}»"
READER_MESSAGE = "Mensaje del cliente: «{message}»"
# Lo que se muestra de la última respuesta del asesor: el contexto del mensaje del cliente, no la conversación entera.
MAX_LAST_REPLY_CHARS = 400


def reader_prompt(runtime: dict) -> str:
    """Las instrucciones del lector, con los medios de pago del negocio (solo sus nombres)."""
    return PAYMENT_READER.format(methods=", ".join(payment_methods(PromptView(runtime=runtime))))


def reader_turn(runtime: dict, user_message: str, *, sent: str = "") -> str:
    """El mensaje del cliente con su contexto: si ya se le enviaron datos de pago (`sent`: de qué medio) y lo último que le dijo el
    asesor. Sin datos de pago: el historial ya los trae ocultos."""
    replies = [message["content"] for message in recent_messages(runtime) if message["role"] == "assistant"]
    last_reply = replies[-1][:MAX_LAST_REPLY_CHARS] if replies else ""
    lines = [
        READER_SENT.format(method=sent) if sent else READER_NOT_SENT,
        READER_LAST_REPLY.format(reply=last_reply) if last_reply else "",
        READER_MESSAGE.format(message=str(user_message or "").strip()),
    ]
    return "\n".join(line for line in lines if line)
