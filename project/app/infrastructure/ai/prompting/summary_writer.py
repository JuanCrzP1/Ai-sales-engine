"""El que resume: lo que se le pide al modelo para resumir una conversación larga, en una llamada corta.

La IA ve los últimos mensajes; lo anterior le llega resumido (`application/pipeline/conversation_summary.py`). Aquí solo el texto.
"""
from __future__ import annotations

# Solo hechos que no cambian: con «qué quedó pendiente», el resumen decía «pendiente: su teléfono» cuando el cliente ya lo había dado en
# los mensajes recientes, y confundía al asesor (medido con la IA real, 13 nov 2026). El paso en curso lo sabe el motor por su lado.
SUMMARY_WRITER = """
Resumes una conversación de ventas por chat para que el asesor no olvide lo importante cuando ya no vea esos mensajes. No le
respondes al cliente.
Escribe en español, en máximo 4 frases cortas, solo hechos que dijo el cliente: quién es (su nombre, su negocio), qué necesita o le
preocupa, qué le interesó o eligió (producto, plan, medio de pago) y qué datos suyos dio. No escribas qué está pendiente, qué sigue,
qué datos no ha dado ni qué se le envió: eso cambia (puede darlos después) y el asesor lo ve en los mensajes recientes. Si hay un resumen anterior, intégralo: el resultado lo
reemplaza. No inventes nada ni agregues lo que no dijo (cargos como dueño o gerente, datos, intenciones). No copies números de
cuenta, teléfonos de pago, referencias ni links.
Responde solo con un objeto JSON, sin texto antes ni después: {{"resumen": "..."}}
""".strip()
SUMMARY_PREVIOUS = "Resumen anterior: {summary}"
SUMMARY_NEW_MESSAGES = "Mensajes nuevos que debe cubrir el resumen:"
