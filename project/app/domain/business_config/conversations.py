"""Las conversaciones de cada negocio con sus clientes: la bandeja del panel.

Cada conversación es el hilo de un contacto en un canal (un número de WhatsApp, un chat de Telegram...) y pertenece a un solo
negocio. Las del área de pruebas del panel se guardan con el canal `prueba`, para distinguirlas de las de clientes reales.
Los datos de pago se guardan ocultos (`[dato de pago]`): la bandeja nunca los muestra, igual que el resto del panel.

Cuando el asistente pasa una conversación a una persona, la conversación queda marcada («espera a una persona») y el equipo del
negocio recibe una notificación. Cada persona marca como leídas las suyas; la conversación deja de esperar cuando alguien la atiende.
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
    # El asistente la pasó a una persona y nadie del equipo la ha atendido todavía.
    needs_human: bool = False
    handoff_requested_at: datetime | None = None


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
    waiting_human: int = 0


NOTIFICATION_KINDS = ("handoff",)


@dataclass(frozen=True)
class Notification:
    """Un aviso para el equipo del negocio. `read` es de quien lo consulta: cada persona marca los suyos."""

    id: str
    business_slug: str
    business_name: str
    conversation_id: str | None
    kind: str
    title: str
    body: str | None
    created_at: datetime
    read: bool


def preview(text: str) -> str:
    line = " ".join(str(text or "").split())
    return line if len(line) <= PREVIEW_CHARS else f"{line[: PREVIEW_CHARS - 1]}…"
