"""Las conversaciones de cada negocio con sus clientes: la bandeja del panel, en vivo.

Cada conversación es el hilo de un contacto en un canal (un número de WhatsApp, un chat de Telegram...) y pertenece a un solo
negocio. Las del área de pruebas del panel se guardan con el canal `prueba`, para distinguirlas de las de clientes reales.
Los datos de pago se guardan ocultos (`[dato de pago]`): la bandeja nunca los muestra, igual que el resto del panel.

Cada mensaje tiene su tipo (texto, foto, audio...), su estado (lo que salió: enviando, enviado, entregado, leído o fallido) y el id
que le dio el canal, para no guardarlo dos veces y para que los recibos de entregado y leído encuentren su mensaje. Las fotos y los
audios se guardan con lo que la IA entendió de ellos (la descripción o la transcripción).

Cuando el cliente pide una persona, reclama o reporta un pago, la conversación pasa a una persona: queda marcada («espera a una
persona»), la IA se pausa en ese chat y el equipo recibe un aviso. Cuando alguien del equipo responde desde el panel, la IA también se
pausa: la conversación es suya hasta que la reanude.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

CHANNELS = ("whatsapp", "instagram", "telegram", "web", "prueba")
# Los canales a los que el equipo puede responder desde el panel (el mensaje sale por el canal).
REPLYABLE_CHANNELS = ("whatsapp",)
AUTHORS = ("customer", "assistant", "agent")
KINDS = ("text", "image", "audio", "video", "document", "sticker", "location", "contact", "other")
MEDIA_KINDS = ("image", "audio", "video", "document", "sticker")
STATUSES = ("received", "sending", "sent", "delivered", "read", "failed")
# Lo que salió solo avanza: un recibo de «entregado» que llega tarde no deshace un «leído».
DELIVERY_ORDER = {"sending": 0, "sent": 1, "delivered": 2, "read": 3}
# Por qué la conversación pasó a una persona.
HANDOFF_REASONS = ("human_request", "complaint", "payment_review", "assistant")
# Lo más grande que se guarda de un archivo: el panel lo sirve en una sola respuesta.
MAX_MEDIA_BYTES = 4 * 1024 * 1024
MAX_REPLY_CHARS = 4000
# Mientras el asistente responde, la conversación dice «escribiendo…» como mucho este tiempo.
TYPING_SECONDS = 90
# Lo que se muestra de la última línea en la lista de conversaciones.
PREVIEW_CHARS = 140
MAX_PAGE = 100

_MEDIA_PREVIEW = {
    "image": "📷 Foto",
    "audio": "🎤 Nota de voz",
    "video": "🎬 Video",
    "document": "📄 Documento",
    "sticker": "Sticker",
    "location": "📍 Ubicación",
    "contact": "👤 Contacto",
    "other": "Mensaje",
}

_HANDOFF_TITLES = {
    "human_request": "pidió hablar con una persona",
    "complaint": "tiene un reclamo",
    "payment_review": "reportó un pago para verificar",
    "assistant": "necesita a una persona",
}


@dataclass(frozen=True)
class ConversationSummary:
    """Una conversación en la bandeja: de qué negocio y canal viene, con quién, cuándo fue lo último y quién la atiende."""

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
    # Pasó a una persona y nadie del equipo la ha atendido todavía.
    needs_human: bool = False
    handoff_requested_at: datetime | None = None
    handoff_reason: str | None = None
    # La atiende una persona: la IA no responde en este chat hasta que la reanuden.
    ai_paused: bool = False
    unread_count: int = 0
    # El asistente está preparando una respuesta.
    assistant_typing: bool = False
    updated_at: datetime | None = None
    # La etapa a la que llegó el cliente (`commerce.STAGES`).
    stage: str = "new"


@dataclass(frozen=True)
class MediaInfo:
    """Un archivo guardado de la conversación (sin su contenido)."""

    id: str
    mime_type: str
    size_bytes: int
    file_name: str | None = None


@dataclass(frozen=True)
class MediaFile:
    """Un archivo con su contenido: lo que se guarda y lo que el panel descarga."""

    mime_type: str
    content: bytes
    file_name: str | None = None


@dataclass(frozen=True)
class ChatMessage:
    id: str
    author: str
    body: str
    created_at: datetime
    intent: str | None = None
    kind: str = "text"
    status: str = "received"
    media: MediaInfo | None = None
    # Lo que la IA entendió de una foto o un audio: la descripción o la transcripción.
    media_note: str | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class NewMessage:
    author: str
    body: str
    intent: str | None = None
    kind: str = "text"
    # El id que le dio el canal: el mismo mensaje no se guarda dos veces.
    provider_message_id: str | None = None
    # Sin estado: lo del cliente queda «recibido» y lo que sale, «enviado».
    status: str | None = None
    media_note: str | None = None

    @property
    def resolved_status(self) -> str:
        return self.status or ("received" if self.author == "customer" else "sent")


@dataclass(frozen=True)
class AppendResult:
    """Un mensaje que llegó por un canal: dónde quedó, si era nuevo (los avisos repetidos no) y si la IA está pausada en ese chat."""

    conversation_id: str
    entry_id: str
    created: bool
    ai_paused: bool


@dataclass(frozen=True)
class ConversationTarget:
    """A quién responde el equipo: el negocio, el canal y el contacto de una conversación."""

    business_slug: str
    channel: str
    contact_ref: str


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


def message_preview(kind: str, body: str) -> str:
    """La línea de la lista para un mensaje: el texto, o el tipo de archivo con su leyenda («📷 Foto: el comprobante»)."""
    if kind == "text":
        return preview(body)
    label = _MEDIA_PREVIEW.get(kind, _MEDIA_PREVIEW["other"])
    return preview(f"{label}: {body}" if str(body or "").strip() else label)


def handoff_title(reason: str | None, channel: str, contact_name: str | None) -> str:
    who = contact_name or "Un cliente"
    title = f"{who} {_HANDOFF_TITLES.get(reason or 'assistant', _HANDOFF_TITLES['assistant'])}"
    return f"Prueba: {title}" if channel == "prueba" else title


def advances(current: str, new: str) -> bool:
    """Si un estado de entrega nuevo avanza sobre el actual (un fallo siempre se anota)."""
    if new == "failed":
        return current in ("sending", "failed")
    return DELIVERY_ORDER.get(new, -1) > DELIVERY_ORDER.get(current, -1)
