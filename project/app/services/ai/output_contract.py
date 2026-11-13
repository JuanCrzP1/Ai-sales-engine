"""El formato con el que el modelo responde cada mensaje, en una sola llamada.

Va con las instrucciones fijas de la plataforma, al principio del prompt (`prompting/composer.py`), y la llamada pide JSON al
proveedor (`response_format`), así el modelo responde bien a la primera. Antes este formato solo se pedía al repetir la llamada:
casi cada mensaje costaba dos.

Los medios de pago son los tipos que la plataforma sabe entregar (`payment_delivery.py`). `send_payment` es la acción con la que el
modelo pide que el sistema le envíe al cliente los datos de pago de un medio; si el negocio no lo tiene, no sale nada.
"""
from __future__ import annotations

INTENTS = ("pain", "info", "objection", "buy")
PAYMENT_METHOD_TYPES = ("link", "nequi", "daviplata", "bank", "breb")
PAYMENT_REPORTED = "reportado"
# Cuándo la conversación pasa a una persona del equipo: lo que escribe el modelo → el motivo que guarda la bandeja.
HANDOFF_VALUES = {"persona": "human_request", "reclamo": "complaint"}

OUTPUT_CONTRACT = f"""
FORMATO DE RESPUESTA (obligatorio):
Responde solo con un objeto JSON, sin texto antes ni después:
{{"response": "...", "intent": "...", "metadata": {{"payment_method": "", "send_payment": "", "payment_status": "", "handoff": ""}}}}
- response: el mensaje para el cliente, tal como lo leerá en el chat.
- intent: una sola de estas:
  - "pain": el cliente cuenta un problema o una necesidad.
  - "info": pregunta por productos, precios, horarios o cómo funciona.
  - "objection": duda, compara o pone un reparo (precio, confianza, tiempo).
  - "buy": quiere comprar, reservar, agendar o pagar.
- metadata.payment_method: solo si el cliente ya eligió cómo pagar: {", ".join(f'"{name}"' for name in PAYMENT_METHOD_TYPES)}. Si no, "".
- metadata.send_payment: el medio cuyos datos de pago le envía el sistema ahora. Si no, "".
- metadata.payment_status: "{PAYMENT_REPORTED}" solo si el cliente dice que ya pagó. Si no, "".
- metadata.handoff: "persona" si pide hablar con alguien del equipo; "reclamo" si reclama por un pago, un pedido o el servicio.
  Si no, "".
""".strip()
