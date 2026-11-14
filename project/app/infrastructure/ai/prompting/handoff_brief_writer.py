"""El que escribe el resumen para el equipo cuando un chat pasa a una persona: lo que se le pide al modelo, en una llamada corta.

El equipo recibe el aviso (campana, correo, celular) y lo ve en el chat del panel (`application/pipeline/handoff_brief.py`). Aquí solo
el texto.
"""
from __future__ import annotations

# Para alguien del equipo que llega al chat sin haberlo leído: qué necesita el cliente y por qué pasa a una persona, sin inventar. Lo
# que el equipo debe verificar (un pago) lo dice el motivo del aviso; el resumen dice qué pidió el cliente.
BRIEF_WRITER = """
Escribes una nota para una persona del equipo de un negocio que va a atender un chat que el asistente le pasa. Esa persona no ha leído
la conversación. No le respondes al cliente.
Escribe en español, en tercera persona («El cliente quiere…», o con su nombre si lo dijo), en máximo 3 frases cortas y en un solo
párrafo. Cuenta solo lo que dijo el cliente:
- quién es, solo si lo dijo (su nombre, a qué se dedica su negocio); si no lo dijo, no lo menciones;
- qué le interesaba en la conversación (producto, plan, medio de pago), si lo dijo;
- qué pidió o reclamó para que lo pasaran con una persona; si dijo que ya pagó, dilo.
No agregues nada que no haya dicho: ni cargos (dueño, gerente), ni datos, ni intenciones. No copies sus mensajes tal cual. No copies
números de cuenta, teléfonos de pago, referencias ni links. No saludes ni des instrucciones al equipo.
El asistente lo pasa porque cree que {reason}: úsalo solo como pista; lo que escribes sale de los mensajes del cliente.
Responde solo con un objeto JSON, sin texto antes ni después: {{"nota": "..."}}
""".strip()
BRIEF_SUMMARY = "Lo que pasó antes en la conversación (resumen): {summary}"
BRIEF_MESSAGES = "Los últimos mensajes:"
