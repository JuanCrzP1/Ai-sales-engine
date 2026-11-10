"""Las conversaciones de cada negocio con sus clientes: la bandeja del panel.

Cada conversación es el hilo de un contacto en un canal (un número de WhatsApp, un chat de Telegram...) y pertenece a un solo
negocio. Las del área de pruebas del panel se guardan con el canal `prueba`, para distinguirlas de las de clientes reales.
Los datos de pago se guardan ocultos (`[dato de pago]`): la bandeja nunca los muestra, igual que el resto del panel.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

CHANNELS = ("whatsapp", "instagram", "telegram", "web", "prueba")
AUTHORS = ("customer", "assistant", "agent")
# Lo que se muestra de la última línea en la lista de conversaciones.
PREVIEW_CHARS = 140
MAX_PAGE = 100


@dataclass(frozen=True)
class ConversationSummary:
    """Una conversación en la bandeja: de qué negocio y canal viene, con quién y cuándo fue lo último."""

    id: str
    business_slug: str
    business_name: str
    channel: str
    contact_name: str | None
    status: str
    started_at: datetime
    last_message_at: datetime
    last_message_preview: str | None
    message_count: int


@dataclass(frozen=True)
class ChatMessage:
    id: str
    author: str
    body: str
    created_at: datetime
    intent: str | None = None


@dataclass(frozen=True)
class NewMessage:
    author: str
    body: str
    intent: str | None = None


@dataclass(frozen=True)
class BusinessActivity:
    """El resumen de actividad de un negocio para su inicio. `since` es el comienzo del día."""

    conversations: int
    conversations_since: int
    messages_since: int
    test_conversations: int


def preview(text: str) -> str:
    line = " ".join(str(text or "").split())
    return line if len(line) <= PREVIEW_CHARS else f"{line[: PREVIEW_CHARS - 1]}…"
