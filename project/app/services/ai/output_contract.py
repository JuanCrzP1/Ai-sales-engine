"""El formato con el que el modelo responde cada mensaje, en una sola llamada.

Primero decide y después habla: la intención y las acciones van antes del mensaje, así lo que le dice al cliente cuadra con lo que
decidió (si marca que le envía los datos de pago, su mensaje lo dice; si no, no lo promete).

Va con las instrucciones fijas de la plataforma, al principio del prompt (`prompting/composer.py`), y la llamada pide JSON al
proveedor (`response_format`), así el modelo responde bien a la primera. Antes este formato solo se pedía al repetir la llamada:
casi cada mensaje costaba dos.

Los medios de pago se nombran como aparecen en los medios del negocio («Nequi», «Yape», «transferencia a Bancolombia»): el motor los
reconoce (`payment_names.py`), sean del país que sean. `send_payment` es la acción con la que el modelo pide que el sistema le
envíe al cliente los datos de pago de un medio; si el negocio no lo tiene, no sale nada.
"""
from __future__ import annotations

INTENTS = ("pain", "info", "objection", "buy")
PAYMENT_REPORTED = "reportado"
# Cuándo la conversación pasa a una persona del equipo: lo que escribe el modelo → el motivo que guarda la bandeja. «tema» y «estancado»
# solo se le piden a la IA cuando el negocio los configuró («Cuándo pasar a una persona», `prompting/sections/escalation.py`).
HANDOFF_VALUES = {"persona": "human_request", "reclamo": "complaint", "tema": "business_topic", "estancado": "stuck"}

OUTPUT_CONTRACT = f"""
FORMATO DE RESPUESTA (obligatorio):
Responde solo con un objeto JSON, sin texto antes ni después. Primero decide y al final escribe tu mensaje:
{{"intent": "...", "metadata": {{"send_payment": "", "payment_status": "", "handoff": ""}}, "response": "..."}}
- intent: una sola de estas:
  - "pain": el cliente cuenta un problema o una necesidad.
  - "info": pregunta por productos, precios, horarios o cómo funciona.
  - "objection": duda, compara o pone un reparo (precio, confianza, tiempo).
  - "buy": quiere comprar, reservar, agendar o pagar.
- metadata.send_payment: casi siempre "". El medio (como aparece en los medios del negocio) cuyos datos de pago recibe el cliente
  ahora, debajo de tu mensaje: solo si te los pide (también otra vez) o dice con qué medio paga. Si solo pregunta por un medio o
  ya los tiene y no los pide: "".
- metadata.payment_status: "{PAYMENT_REPORTED}" solo si el cliente dice que ya pagó, consignó o transfirió, o que envía el
  comprobante. Si no, "".
- metadata.handoff: "persona" si pide hablar con alguien del equipo; "reclamo" si reclama por un pago, un pedido o el servicio.
  Si no, "".
- response: el mensaje para el cliente, tal como lo leerá en el chat.
""".strip()
