"""El lector del seguimiento: lo que se le envía al modelo para que diga si conviene escribirle a un cliente que dejó de responder.

El negocio programó mensajes de seguimiento (Mensajes → Seguimiento). Antes de cada uno, la IA lee el final de la conversación y dice
si el cliente la dejó abierta (no respondió, lo iba a pensar) o la cerró (no le interesa, ya compró en otro lado, que no le escriban,
lo que pedía quedó resuelto). Decidirlo es entender al cliente, y eso es trabajo de la IA, no de una lista de palabras. Aquí solo se
arma el texto; quién lo usa y qué se hace con la respuesta está en `application/follow_up/follow_up_reading.py`.
"""
from __future__ import annotations

FOLLOW_UP_READER = """
Lees el final de una conversación por chat entre un negocio y un cliente que dejó de responder. El negocio quiere enviarle un mensaje
de seguimiento y tú dices si conviene enviarlo. No le escribes al cliente.
Responde solo con un objeto JSON, sin texto antes ni después:
{"enviar": true}

- enviar: true si el cliente dejó la conversación abierta: no respondió a lo último del negocio, dijo que lo iba a pensar, que lo
  revisaba o que escribía después, o quedó a mitad de camino (preguntó un precio, pidió información, iba a comprar).
  Es false si el cliente la cerró: dijo que no le interesa, que ya lo resolvió o compró en otro lado, que no le escriban más, se
  quejó o se molestó, o lo que pedía ya quedó resuelto y se despidió («gracias, era solo eso»).
""".strip()
FOLLOW_UP_TURN = "Conversación (lo más reciente al final):\n{conversation}\n\nMensaje de seguimiento que se enviaría: «{message}»"
# Cuántos mensajes del final de la conversación lee, y hasta cuántos caracteres de cada uno.
MAX_MESSAGES = 12
MAX_MESSAGE_CHARS = 400
_WHO = {"customer": "Cliente", "assistant": "Negocio", "agent": "Negocio"}


def follow_up_turn(messages: list[tuple[str, str]], message: str) -> str:
    """`messages`: (autor, texto) del más antiguo al más reciente; autor «customer», «assistant» o «agent»."""
    lines = []
    for author, text in messages[-MAX_MESSAGES:]:
        clean = " ".join(str(text or "").split())
        if not clean:
            continue
        if len(clean) > MAX_MESSAGE_CHARS:
            clean = clean[:MAX_MESSAGE_CHARS].rsplit(" ", 1)[0] + "…"
        lines.append(f"{_WHO.get(author, 'Negocio')}: {clean}")
    return FOLLOW_UP_TURN.format(conversation="\n".join(lines) or "(sin mensajes)", message=" ".join(str(message or "").split()))
