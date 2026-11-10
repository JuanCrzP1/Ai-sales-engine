"""Los últimos mensajes de la conversación, para enviarlos al modelo como conversación (no resumidos dentro del prompt).

Así el modelo ve lo que dijo el cliente y lo que se le respondió, en orden, como lo vería una persona. Van los más recientes, cada uno
con un largo máximo, y sin datos de pago: si el motor le entregó al cliente un número de cuenta, el modelo ve solo su marcador.
"""
from __future__ import annotations

from app.domain.business_config.payment_data import redact_payment_values
from app.infrastructure.ai.prompting.text import as_list

MAX_MESSAGES = 8
MAX_MESSAGE_CHARS = 700
_ROLES = {"user": "user", "assistant": "assistant", "bot": "assistant", "ai": "assistant"}


def recent_messages(runtime: dict, *, max_messages: int = MAX_MESSAGES) -> list[dict[str, str]]:
    """Mensajes `{"role", "content"}` del historial guardado, del más antiguo al más reciente, sin el mensaje actual."""
    messages = []
    for entry in as_list((runtime or {}).get("conversation_history"))[-max_messages:]:
        if isinstance(entry, dict):
            role = _ROLES.get(str(entry.get("role") or "user").strip().lower())
            text = str(entry.get("text") or entry.get("message_text") or entry.get("content") or "").strip()
        else:
            role, text = "user", str(entry or "").strip()
        if role and text:
            if len(text) > MAX_MESSAGE_CHARS:
                text = text[:MAX_MESSAGE_CHARS].rsplit(" ", 1)[0] + "…"
            messages.append({"role": role, "content": redact_payment_values(text, runtime)})
    return messages
