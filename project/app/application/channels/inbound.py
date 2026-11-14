"""Un mensaje de un cliente por WhatsApp (código QR, uazapi) o por Telegram (el bot del negocio), de punta a punta, como lo haría un
equipo de atención. Los dos canales siguen el mismo camino; solo cambian quién lee los avisos (`parse`) y el cliente del canal
(`server`, que recibe la conexión del negocio: `ChannelSecrets`).

En el webhook, enseguida (`receive`):
1. El estado de la conexión y los recibos de entregado y leído se anotan y listo (Telegram no los manda). Lo que el negocio escribe
   desde su celular en el chat de un cliente de WhatsApp queda en la bandeja como respuesta del equipo y pausa la IA en ese chat, como
   si respondiera desde el panel.
2. El mensaje del cliente se guarda en la bandeja apenas llega, con su tipo y el id del canal: si el aviso se repite, no se guarda
   ni se responde dos veces (lo garantiza la base, no la memoria de un proceso: en la nube hay muchos).
3. Si la IA está pausada en ese chat (la atiende una persona), no se responde: el equipo lo ve en vivo.

Después de contestarle al canal (`process`), porque responder toma unos segundos:
4. La bandeja y el chat del cliente dicen «escribiendo…».
5. Si es una foto o un audio, se descarga y se guarda (el enlace del canal vence), y la IA lo entiende con la clave del negocio:
   describe la foto (y si es un comprobante de pago) o transcribe la nota de voz. Eso es lo que lee el asistente.
6. El asistente responde con lo publicado del negocio. Si en ese momento alguien del equipo tomó el chat, no se envía nada.
7. La respuesta sale por el canal y queda en la bandeja con su id, para sus recibos. Si no sale, queda «no enviada»; si el canal dice
   que la conexión ya no sirve (Telegram rechazó el código del bot), se avisa con `on_lost`.
8. Si el cliente pidió una persona, reclamó o reportó un pago, la conversación pasa al equipo y le llega un aviso (en la campana, por
   correo y como notificación). Dentro del horario del equipo la IA se pausa y el cliente sabe cuánto suele tardar; fuera del horario
   la IA sigue ayudándole y le dice cuándo lo atienden (`domain/business_config/attention.py`).

Si nadie del equipo responde a tiempo, la revisión periódica retoma el chat (`application/attention/resume_sweep.py`) y aquí se le
pide disculpas al cliente y el asistente responde lo que quedó pendiente (`continue_after_resume`).

Todo lo que se guarda va con los datos de pago ocultos. Las dependencias entran por el constructor (las pruebas las cambian).
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from app.application.channels.handoff_plan import plan_handoff
from app.domain.business_config.attention import DEFAULT_RESUMED_NOTICE, AttentionSettings, HandoffPlan, published_attention
from app.domain.business_config.channels import ChannelError, ChannelSecrets, IncomingMessage
from app.domain.business_config.conversations import MEDIA_KINDS, TYPING_SECONDS, AppendResult, MediaFile, NewMessage
from app.domain.business_config.payment_data import redact_payment_values
from app.utils.logger import logger


class ChannelClient(Protocol):
    """El canal del negocio: su instancia de WhatsApp en uazapi o su bot de Telegram. `phone` es el contacto en el canal."""

    def send_text(self, token: str, phone: str, text: str) -> str | None: ...

    def presence(self, token: str, phone: str, presence: str = "composing", delay_ms: int = 30_000) -> None: ...

    def download(self, token: str, message_id: str) -> MediaFile | None: ...


class ConversationGateway(Protocol):
    """La bandeja, vista desde el motor (`runtime_access`)."""

    def append(self, tenant_slug: str, *, channel: str, contact_ref: str, contact_name: str | None, message: NewMessage, media: MediaFile | None = None) -> AppendResult: ...

    def update_entry(self, entry_id: str, *, status: str | None = None, provider_message_id: str | None = None, media: MediaFile | None = None, media_note: str | None = None) -> None: ...

    def set_typing(self, conversation_id: str, until: datetime | None) -> None: ...

    def request_handoff(
        self, conversation_id: str, reason: str, detail: str | None = None, *, pause_ai: bool = True, summary: str | None = None
    ) -> str | None: ...

    def ai_paused(self, conversation_id: str) -> bool: ...

    def team_replied(self, conversation_id: str) -> None: ...


class MediaUnderstanding(Protocol):
    """Entiende fotos y audios con la clave de IA del negocio (`infrastructure/ai/media_interpreter.py`)."""

    def describe_image(self, api_key: str, media: MediaFile, *, on_usage: Any = None) -> Any: ...

    def transcribe_audio(self, api_key: str, media: MediaFile, *, on_usage: Any = None) -> str | None: ...


# El asistente del negocio: (negocio, teléfono del cliente, texto) → (respuesta, metadatos: intent, handoff, handoff_reason).
Responder = Callable[[str, str, str], tuple[str, dict]]
# La clave de IA del negocio (o None) y quién anota su consumo.
KeyLoader = Callable[[str], str | None]
UsageRecorder = Callable[[str], Any]
# Lo publicado del negocio, para ocultar sus datos de pago en lo que se guarda (y leer su horario y sus mensajes de atención).
SectionsLoader = Callable[[str], dict]
# Los ajustes de atención humana del negocio (Configuración → Atención humana).
AttentionLoader = Callable[[str], AttentionSettings]
# Avisa al equipo por correo y notificación (`TeamAlerts.deliver`): recibe el id del aviso, o None si no hubo aviso nuevo.
AlertSender = Callable[[str | None], None]


@dataclass(frozen=True)
class Received:
    """Qué pasó con un aviso del webhook y, si hace falta, el mensaje guardado que hay que procesar después de contestar."""

    status: str
    message: IncomingMessage | None = None
    stored: AppendResult | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


_CHANNEL_NAMES = {"whatsapp": "WhatsApp", "telegram": "Telegram"}


def assistant_text(message: IncomingMessage, *, note: str | None = None, payment_proof: bool = False, payment_details: str = "") -> str | None:
    """Lo que lee el asistente de un mensaje: el texto, o lo que se entendió de un archivo. None: no se responde (un sticker)."""
    caption = message.text.strip()
    said = f" con el texto «{caption}»" if caption else ""
    if message.kind == "text":
        return caption or None
    if message.kind == "audio":
        return note or "[El cliente envió una nota de voz que no se pudo escuchar. Pídele con amabilidad que la escriba.]"
    if message.kind == "image":
        if payment_proof:
            return f"Ya pagué, te envío el comprobante{f' ({payment_details})' if payment_details else ''}.{f' {caption}' if caption else ''}"
        if note:
            return f"[El cliente envió una foto{said}. En la foto se ve: {note}]"
        return f"[El cliente envió una foto{said} que no se pudo ver.]{f' {caption}' if caption else ''}"
    if message.kind == "video":
        return f"[El cliente envió un video{said}.]"
    if message.kind == "document":
        name = f" «{message.file_name}»" if message.file_name else ""
        return f"[El cliente envió un documento{name}{said}.]"
    if message.kind == "location":
        return "[El cliente compartió una ubicación.]"
    if message.kind == "contact":
        return "[El cliente compartió un contacto.]"
    return caption or None


class ChannelInbound:
    def __init__(
        self,
        *,
        conversations: ConversationGateway,
        server: Callable[[ChannelSecrets], ChannelClient],
        responder: Responder,
        media: MediaUnderstanding,
        api_key: KeyLoader,
        usage: UsageRecorder,
        sections: SectionsLoader,
        set_status: Callable[..., None],
        mark_delivery: Callable[[str, list[str], str], int],
        attention: AttentionLoader | None = None,
        alerts: AlertSender | None = None,
        clock: Callable[[], datetime] | None = None,
        on_lost: Callable[[ChannelSecrets], None] | None = None,
    ) -> None:
        self._conversations = conversations
        self._server = server
        self._responder = responder
        self._media = media
        self._api_key = api_key
        self._usage = usage
        self._sections = sections
        self._set_status = set_status
        self._mark_delivery = mark_delivery
        self._attention = attention or (lambda _slug: AttentionSettings())
        self._alerts = alerts or (lambda _notification: None)
        self._clock = clock or _now
        self._on_lost = on_lost or (lambda _secrets: None)

    # ------------------------------------------------------------------ en el webhook

    def receive(self, secrets: ChannelSecrets, payload: dict, *, parse: Any) -> Received:
        """Lo que se hace antes de contestarle al canal. `parse` trae los lectores de sus avisos (conexión, recibos, mensajes propios y
        del cliente)."""
        slug = secrets.tenant_slug
        connection = parse.connection_event(payload)
        if connection is not None:
            self._set_status(slug, connection.status, phone=connection.phone, profile_name=connection.profile_name)
            return Received("ok")
        receipt = parse.parse_receipt(payload)
        if receipt is not None:
            self._mark_delivery(slug, list(receipt.message_ids), receipt.status)
            return Received("ok")
        own = parse.parse_own_message(payload)
        if own is not None:
            saved = self._conversations.append(
                slug, channel=secrets.channel, contact_ref=own.phone, contact_name=None,
                message=NewMessage("agent", self._hide_payments(slug, own.text), kind=own.kind, provider_message_id=own.message_id, status="sent"),
            )
            if saved.created:
                # Alguien del equipo respondió desde el celular: el chat es suyo y la IA no habla encima de esa persona.
                self._conversations.team_replied(saved.conversation_id)
                logger.info("whatsapp_qr_respuesta_desde_el_celular", extra={"tenant": slug})
            return Received("team_reply" if saved.created else "duplicate")
        message = parse.parse_incoming(payload)
        if message is None:
            return Received("ignored")
        stored = self._conversations.append(
            slug, channel=secrets.channel, contact_ref=message.phone, contact_name=message.contact_name,
            message=NewMessage("customer", self._hide_payments(slug, message.text), kind=message.kind, provider_message_id=message.message_id),
        )
        if not stored.created:
            return Received("duplicate")
        return Received("stored" if stored.ai_paused else "accepted", message, stored)

    # ------------------------------------------------------------------ después de contestar

    def process(self, secrets: ChannelSecrets, message: IncomingMessage, stored: AppendResult) -> None:
        """Entiende el mensaje, responde con el asistente y pasa la conversación a una persona si hace falta. Nunca lanza."""
        answering = not stored.ai_paused
        try:
            if answering:
                self._typing(secrets, message, stored)
            understanding = self._understand(secrets, message, stored) if message.kind in MEDIA_KINDS else {}
            if answering:
                self._answer(secrets, message, stored, understanding)
        except Exception as exc:  # noqa: BLE001 - un fallo aquí no puede tumbar el webhook; se registra el tipo, nunca el contenido
            logger.error("whatsapp_qr_proceso_fallido", extra={"tenant": secrets.tenant_slug, "error": type(exc).__name__})
        finally:
            if answering:
                self._quiet(stored.conversation_id)

    def _typing(self, secrets: ChannelSecrets, message: IncomingMessage, stored: AppendResult) -> None:
        self._conversations.set_typing(stored.conversation_id, _now() + timedelta(seconds=TYPING_SECONDS))
        try:
            self._server(secrets).presence(secrets.instance_token, message.phone, "composing", 30_000)
        except ChannelError:
            pass  # El «escribiendo…» en el teléfono del cliente es un detalle: la respuesta sale igual.

    def _quiet(self, conversation_id: str) -> None:
        try:
            self._conversations.set_typing(conversation_id, None)
        except Exception as exc:  # noqa: BLE001
            logger.warning("whatsapp_qr_escribiendo_no_apagado", extra={"error": type(exc).__name__})

    def _understand(self, secrets: ChannelSecrets, message: IncomingMessage, stored: AppendResult) -> dict:
        """Descarga y guarda el archivo, y lo que la IA entendió de él (foto o audio)."""
        try:
            media = self._server(secrets).download(secrets.instance_token, message.media_ref or message.message_id)
        except ChannelError as exc:
            logger.warning("whatsapp_qr_archivo_no_descargado", extra={"tenant": secrets.tenant_slug, "error": str(exc)})
            media = None
        if media is None:
            self._conversations.update_entry(stored.entry_id, media_note=f"El archivo no se pudo descargar o es muy grande: míralo en el {_CHANNEL_NAMES.get(secrets.channel, 'canal')} del negocio.")
            return {}
        if message.file_name and not media.file_name:
            media = MediaFile(media.mime_type, media.content, message.file_name)
        result: dict = {}
        key = self._api_key(secrets.tenant_slug) if message.kind in ("image", "audio") else None
        if key and message.kind == "image":
            seen = self._media.describe_image(key, media, on_usage=self._usage(secrets.tenant_slug))
            if seen is not None:
                result = {"note": seen.description, "payment_proof": seen.payment_proof, "payment_details": seen.payment_details}
        elif key and message.kind == "audio":
            heard = self._media.transcribe_audio(key, media, on_usage=self._usage(secrets.tenant_slug))
            if heard:
                result = {"note": heard}
        note = result.get("note")
        self._conversations.update_entry(stored.entry_id, media=media, media_note=self._hide_payments(secrets.tenant_slug, note) if note else None)
        return result

    def _answer(self, secrets: ChannelSecrets, message: IncomingMessage, stored: AppendResult, understanding: dict) -> None:
        slug = secrets.tenant_slug
        text = assistant_text(
            message, note=understanding.get("note"), payment_proof=bool(understanding.get("payment_proof")),
            payment_details=str(understanding.get("payment_details") or ""),
        )
        if not text:
            return
        reply, metadata = self._responder(slug, message.phone, text)
        reply = str(reply or "").strip()
        if not reply:
            return
        # Mientras el asistente pensaba, alguien del equipo pudo tomar el chat: entonces no se envía nada.
        if self._conversations.ai_paused(stored.conversation_id):
            logger.info("whatsapp_qr_respuesta_descartada", extra={"tenant": slug, "reason": "chat_tomado_por_el_equipo"})
            return
        intent = str(metadata.get("intent") or "").strip() or None
        if not self._say(secrets, message.phone, reply, intent):
            return
        logger.info("whatsapp_qr_respuesta", extra={"tenant": slug})
        if metadata.get("handoff"):
            detail = message.text or understanding.get("note") or None
            self._hand_off(
                secrets, message.phone, stored.conversation_id, str(metadata.get("handoff_reason") or "assistant"), detail,
                summary=str(metadata.get("handoff_summary") or "") or None,
            )

    def _say(self, secrets: ChannelSecrets, phone: str, text: str, intent: str | None = None) -> bool:
        """Envía un mensaje del asistente por WhatsApp y lo deja en la bandeja (o «no enviado» si no salió). Dice si salió."""
        slug = secrets.tenant_slug
        hidden = self._hide_payments(slug, text)
        try:
            provider_id = self._server(secrets).send_text(secrets.instance_token, phone, text)
        except ChannelError as exc:
            logger.error("whatsapp_qr_envio_fallido", extra={"tenant": slug, "channel": secrets.channel, "error": str(exc)})
            if exc.gone:
                self._lost(secrets)
            self._conversations.append(
                slug, channel=secrets.channel, contact_ref=phone, contact_name=None, message=NewMessage("assistant", hidden, intent, status="failed")
            )
            return False
        self._conversations.append(
            slug, channel=secrets.channel, contact_ref=phone, contact_name=None,
            message=NewMessage("assistant", hidden, intent, provider_message_id=provider_id, status="sent"),
        )
        return True

    def _lost(self, secrets: ChannelSecrets) -> None:
        try:
            self._on_lost(secrets)
        except Exception as exc:  # noqa: BLE001 - anotar el estado es un extra: el mensaje ya quedó como no enviado
            logger.warning("canal_estado_no_anotado", extra={"tenant": secrets.tenant_slug, "error": type(exc).__name__})

    def _hand_off(
        self, secrets: ChannelSecrets, phone: str, conversation_id: str, reason: str, detail: str | None, *, summary: str | None = None
    ) -> None:
        """El chat pasa a una persona: según el horario del equipo, la IA se pausa o sigue; el cliente sabe qué esperar y el equipo
        recibe el aviso (campana, correo y notificación)."""
        slug = secrets.tenant_slug
        plan = self._handoff_plan(slug)
        notification = self._conversations.request_handoff(
            conversation_id, reason, self._hide_payments(slug, detail) if detail else None, pause_ai=plan.pause_ai,
            summary=self._hide_payments(slug, summary) if summary else None,
        )
        if plan.notice:
            self._say(secrets, phone, plan.notice)
        logger.info("whatsapp_qr_paso_a_una_persona", extra={"tenant": slug, "team_available": plan.team_available, "ai_paused": plan.pause_ai})
        self._alerts(notification)

    def _handoff_plan(self, slug: str) -> HandoffPlan:
        """Qué pasa al pasar el chat a una persona (la misma regla en todos los canales: `handoff_plan.py`)."""
        return plan_handoff(slug, attention=self._attention, sections=self._sections, now=self._clock())

    # ------------------------------------------------------------------ la IA retoma un chat que nadie atendió

    def continue_after_resume(self, secrets: ChannelSecrets, conversation_id: str, phone: str, pending_text: str) -> None:
        """La IA retomó el chat porque nadie del equipo respondió a tiempo: pide disculpas (con el mensaje del negocio, si lo escribió)
        y responde lo que el cliente escribió mientras esperaba. Nunca lanza."""
        slug = secrets.tenant_slug
        try:
            try:
                notice = published_attention(self._sections(slug)).ai_resumed or DEFAULT_RESUMED_NOTICE
            except Exception:  # noqa: BLE001 - sin lo publicado, el mensaje de la plataforma
                notice = DEFAULT_RESUMED_NOTICE
            self._say(secrets, phone, notice)
            if pending_text.strip():
                waiting = IncomingMessage(message_id="", phone=phone, contact_name=None, text=pending_text.strip())
                self._answer(secrets, waiting, AppendResult(conversation_id, "", True, False), {})
        except Exception as exc:  # noqa: BLE001
            logger.error("whatsapp_qr_retomar_fallido", extra={"tenant": slug, "error": type(exc).__name__})

    def _hide_payments(self, slug: str, text: str) -> str:
        if not text:
            return text
        try:
            sections = self._sections(slug)
        except Exception:  # noqa: BLE001 - sin lo publicado no hay datos de pago que ocultar
            sections = {}
        return redact_payment_values(text, sections)
