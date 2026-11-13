"""Acceso del motor al almacén de BusinessConfig: lee lo publicado, anota el consumo de IA y atiende los canales.

El motor lee la misma base que escribe el panel (`database_url()`: `BUSINESS_CONFIG_DATABASE_URL` o el SQLite local) con la misma
clave de cifrado (`find_secrets_key()`): lo publicado, los datos de pago, la clave de IA y la conexión de WhatsApp y de Telegram de cada negocio.
Lo único que escribe es el consumo de cada respuesta (`record_ai_usage`), el estado de la conexión de WhatsApp que avisa su servidor y
la bandeja de conversaciones: cada mensaje de un canal apenas llega o sale, sus archivos y recibos, el «escribiendo…» y el paso a una
persona. Nunca crea la base, las tablas ni la clave: si algo falta, lo informa con
una excepción y el llamador decide.

Es la única puerta del motor hacia este almacén: el motor no conoce tablas, conexiones ni cifrado.
"""
from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy.engine import Engine

from app.domain.business_config.ai_settings import AICredentials
from app.domain.business_config.ai_usage import AIUsage
from app.domain.business_config.channels import ConnectionStatus, ChannelSecrets
from app.domain.business_config.contract import BusinessConfig, SecretRef
from app.business_config_application.usage_limits import UsageGuard
from app.domain.business_config.api_keys import ApiKeyIdentity
from app.domain.business_config.attention import AttentionSettings
from app.domain.business_config.conversations import AppendResult, MediaFile, NewMessage, WaitingChat
from app.domain.business_config.errors import BusinessConfigError
from app.infrastructure.business_config.ai_settings_store import AISettingsStore
from app.infrastructure.business_config.ai_usage_store import AIUsageStore
from app.infrastructure.business_config.api_key_store import ApiKeyStore
from app.infrastructure.business_config.attention_store import AttentionStore
from app.infrastructure.business_config.channel_store import ChannelStore
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import create_business_config_engine, database_url, sqlite_file
from app.infrastructure.business_config.payment_secret_store import SECRET_STORE_SOURCE, PaymentSecretStore
from app.infrastructure.business_config.push_store import PushStore
from app.infrastructure.business_config.repository import BusinessConfigRepository
from app.infrastructure.business_config.idempotency_store import IdempotencyStore
from app.infrastructure.business_config.secrets_key import find_secrets_key
from app.infrastructure.business_config.usage_store import UsageCounterStore

__all__ = [
    "SECRET_STORE_SOURCE",
    "PublishedConfigReader",
    "dispose_shared_engines",
    "open_published_reader",
    "reader_for",
    "append_conversation_message",
    "conversation_ai_paused",
    "idempotency_store",
    "conversation_stage",
    "authenticate_api_key",
    "usage_guard",
    "conversation_team_replied",
    "mark_conversation_delivery",
    "record_ai_usage",
    "request_conversation_handoff",
    "alert_stores",
    "attention_settings",
    "pending_customer_text",
    "resume_waiting_chat",
    "waiting_chats",
    "whatsapp_secrets",
    "channel_secrets",
    "channel_for_webhook",
    "set_channel_status",
    "set_conversation_typing",
    "set_whatsapp_status",
    "update_conversation_entry",
    "whatsapp_for_webhook",
]


@dataclass(frozen=True)
class PublishedConfigReader:
    """Lo publicado de cada negocio, el resolutor de sus datos de pago cifrados y su propia clave de IA."""

    _repository: BusinessConfigRepository
    _secrets: PaymentSecretStore
    _ai_settings: AISettingsStore

    def published(self, tenant_slug: str) -> BusinessConfig:
        return self._repository.published(tenant_slug)

    def payment_resolver(self, tenant_slug: str) -> Callable[[SecretRef], str]:
        return self._secrets.resolver(tenant_slug)

    def ai_credentials(self, tenant_slug: str) -> AICredentials | None:
        """La clave de OpenRouter y el modelo de este negocio, o None si no tiene clave."""
        return self._ai_settings.ai_credentials(tenant_slug)


def reader_for(engine: Engine, key: str | None = None) -> PublishedConfigReader:
    """Un lector sobre una conexión ya abierta. Sin `key`, la clave sale de `BUSINESS_CONFIG_SECRETS_KEY`."""
    secrets = PaymentSecretStore(engine, key)
    return PublishedConfigReader(BusinessConfigRepository(engine, secrets), secrets, AISettingsStore(engine, key))


# Una conexión por URL para todo el proceso: el motor consulta el almacén en cada mensaje.
_engines: dict[str, Engine] = {}
_engines_lock = threading.Lock()


def _shared_engine(url: str) -> Engine:
    with _engines_lock:
        if url not in _engines:
            _engines[url] = create_business_config_engine(url)
        return _engines[url]


def _store_engine() -> Engine:
    url = database_url()
    path = sqlite_file(url)
    if path is not None and not path.is_file():
        # Sin esta comprobación, SQLite crearía un archivo vacío: el motor nunca debe crear el almacén.
        raise BusinessConfigError("no existe el almacén de BusinessConfig: se crea con scripts/init_local_business_config.py")
    return _shared_engine(url)


def open_published_reader() -> PublishedConfigReader:
    """El lector del almacén que usa el panel en este equipo, o en la nube cuando `BUSINESS_CONFIG_DATABASE_URL` apunte allí."""
    return reader_for(_store_engine(), find_secrets_key())


def record_ai_usage(tenant_slug: str, usage: AIUsage, *, day: date | None = None) -> None:
    """Suma una respuesta al consumo de IA del negocio (día en UTC)."""
    AIUsageStore(_store_engine()).add(tenant_slug, day or datetime.now(timezone.utc).date(), usage)


def whatsapp_for_webhook(webhook_id: str) -> ChannelSecrets | None:
    """La conexión de WhatsApp (negocio, servidor y token) del webhook con ese identificador secreto, o None si no existe."""
    return ChannelStore(_store_engine(), find_secrets_key()).secrets_for_webhook(webhook_id)


def set_whatsapp_status(tenant_slug: str, status: ConnectionStatus, *, phone: str | None = None, profile_name: str | None = None) -> None:
    """El estado de la conexión que avisa el servidor de WhatsApp (se conectó, se desconectó)."""
    ChannelStore(_store_engine(), find_secrets_key()).set_status(tenant_slug, status, phone=phone, profile_name=profile_name)


def append_conversation_message(
    tenant_slug: str, *, channel: str, contact_ref: str, contact_name: str | None, message: NewMessage, media: MediaFile | None = None
) -> AppendResult:
    """Un mensaje de un canal en la bandeja, apenas llega o sale. Los datos de pago ya deben venir ocultos."""
    return ConversationStore(_store_engine()).append(
        tenant_slug, channel=channel, contact_ref=contact_ref, contact_name=contact_name, message=message, media=media
    )


def update_conversation_entry(
    entry_id: str, *, status: str | None = None, provider_message_id: str | None = None, media: MediaFile | None = None, media_note: str | None = None
) -> None:
    """Completa un mensaje de la bandeja: su estado al salir, o su archivo y lo que la IA entendió de él."""
    ConversationStore(_store_engine()).update_entry(entry_id, status=status, provider_message_id=provider_message_id, media=media, media_note=media_note)


def mark_conversation_delivery(tenant_slug: str, provider_message_ids: list[str], status: str) -> int:
    """Los recibos de entregado y leído que avisa el canal."""
    return ConversationStore(_store_engine()).mark_delivery(tenant_slug, provider_message_ids, status)


def set_conversation_typing(conversation_id: str, until: datetime | None) -> None:
    """El asistente está «escribiendo…» en esa conversación hasta `until` (None lo apaga)."""
    ConversationStore(_store_engine()).set_typing(conversation_id, until)


def request_conversation_handoff(conversation_id: str, reason: str, detail: str | None = None, *, pause_ai: bool = True) -> str | None:
    """La conversación pasa a una persona y el equipo recibe un aviso (su id, o None si ya esperaba). Con `pause_ai`, la IA se pausa."""
    return ConversationStore(_store_engine()).request_handoff(conversation_id, reason, detail, pause_ai=pause_ai)


def attention_settings(tenant_slug: str) -> AttentionSettings:
    """Los ajustes de atención humana del negocio (sin guardar, los de por defecto)."""
    return AttentionStore(_store_engine()).attention_settings(tenant_slug)


def waiting_chats(*, waiting_before: datetime, limit: int = 100) -> list[WaitingChat]:
    """Los chats con la IA pausada y un cliente esperando desde antes de `waiting_before`."""
    return ConversationStore(_store_engine()).waiting_chats(waiting_before=waiting_before, limit=limit)


def resume_waiting_chat(conversation_id: str, *, waiting_before: datetime, minutes: int) -> str | None:
    """La IA retoma el chat (una sola vez) si su cliente sigue esperando: el id del aviso al equipo, o None si ya no hacía falta."""
    return ConversationStore(_store_engine()).resume_waiting(conversation_id, waiting_before=waiting_before, minutes=minutes)


def pending_customer_text(conversation_id: str, *, since: datetime) -> str:
    """Lo que escribió el cliente desde `since` sin respuesta, en un solo texto."""
    return ConversationStore(_store_engine()).pending_customer_text(conversation_id, since=since)


def whatsapp_secrets(tenant_slug: str) -> ChannelSecrets | None:
    """La conexión de WhatsApp del negocio (servidor y token), o None si no está conectado."""
    return ChannelStore(_store_engine(), find_secrets_key()).whatsapp_secrets(tenant_slug)


def channel_secrets(tenant_slug: str, channel: str) -> ChannelSecrets | None:
    """La conexión de ese canal del negocio (WhatsApp o Telegram), o None si no lo tiene."""
    return ChannelStore(_store_engine(), find_secrets_key()).channel_secrets(tenant_slug, channel)


def channel_for_webhook(webhook_id: str, channel: str) -> ChannelSecrets | None:
    """La conexión de ese canal con ese identificador secreto de webhook, o None si no existe."""
    return ChannelStore(_store_engine(), find_secrets_key()).secrets_for_webhook(webhook_id, channel)


def set_channel_status(tenant_slug: str, channel: str, status: ConnectionStatus) -> None:
    """El estado de un canal que descubre el motor (en Telegram: que el código del bot ya no sirve)."""
    ChannelStore(_store_engine(), find_secrets_key()).set_channel_status(tenant_slug, channel, status)


def alert_stores() -> tuple[AttentionStore, PushStore]:
    """Lo que hace falta para avisar al equipo: sus ajustes y correos, y las suscripciones a notificaciones."""
    engine = _store_engine()
    return AttentionStore(engine), PushStore(engine, find_secrets_key())


def conversation_team_replied(conversation_id: str) -> None:
    """Alguien del equipo respondió desde el celular del negocio: la IA se pausa en ese chat y el cliente deja de esperar."""
    ConversationStore(_store_engine()).team_replied(conversation_id)


def conversation_stage(conversation_id: str) -> str:
    """La etapa a la que llegó el cliente de esa conversación."""
    return ConversationStore(_store_engine()).stage_of(conversation_id)


def idempotency_store() -> IdempotencyStore:
    """Las respuestas ya dadas a cada `Idempotency-Key` de la API del asistente, cifradas."""
    return IdempotencyStore(_store_engine(), find_secrets_key())


def authenticate_api_key(secret: str) -> ApiKeyIdentity | None:
    """El negocio, los permisos y el alcance de una clave de API activa y sin vencer, o None."""
    return ApiKeyStore(_store_engine()).authenticate(secret)


def usage_guard() -> UsageGuard:
    """Los límites de uso con el contador compartido de la base (todas las instancias cuentan juntas)."""
    return UsageGuard(UsageCounterStore(_store_engine()))


def conversation_ai_paused(conversation_id: str) -> bool:
    """Si la IA está pausada en esa conversación (la atiende una persona)."""
    return ConversationStore(_store_engine()).is_ai_paused(conversation_id)


def dispose_shared_engines() -> None:
    """Cierra las conexiones compartidas (al terminar el proceso o entre pruebas)."""
    with _engines_lock:
        for engine in _engines.values():
            engine.dispose()
        _engines.clear()
