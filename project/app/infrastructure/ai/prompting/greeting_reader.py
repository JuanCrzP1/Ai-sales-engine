"""El lector del saludo: lo que se le envía al modelo para que diga si el primer mensaje del cliente es solo un saludo.

Si el negocio escribió su saludo (Mensajes → Bienvenida) y el cliente solo saluda, le llega ese saludo tal cual. Decidir si «solo
saluda» es entender al cliente, y eso es trabajo de la IA: hasta el 26 nov 2026 lo decidía una lista de palabras colombianas
(«parce», «qué más»), que no reconocía «qué onda», «buen día, ¿cómo están?» ni un 👋. Aquí solo se arma el texto; quién lo usa y qué
se hace con la respuesta está en `application/pipeline/greeting_reading.py`. Los ejemplos son de varios países a propósito.
"""
from __future__ import annotations

GREETING_READER = """
Lees el primer mensaje de un cliente en el chat de ventas de un negocio y dices si solo saluda. No le respondes al cliente.
Responde solo con un objeto JSON, sin texto antes ni después:
{"solo_saluda": false}

- solo_saluda: true si solo saluda, aunque pregunte por cortesía cómo está: «hola», «buenas tardes», «qué onda», «buen día, ¿cómo
  están?», «holaaa 👋». Preguntar «¿qué tal?» o «¿cómo estás?» es parte del saludo.
  Es false si además pide algo, pregunta algo del negocio o cuenta algo de sí, aunque empiece saludando: «hola, ¿cuánto cuesta?»,
  «buenas, quiero hacer un pedido», «hola, soy Laura».
""".strip()
GREETING_MESSAGE = "Mensaje del cliente: «{message}»"


def greeting_turn(user_message: str) -> str:
    return GREETING_MESSAGE.format(message=str(user_message or "").strip())
