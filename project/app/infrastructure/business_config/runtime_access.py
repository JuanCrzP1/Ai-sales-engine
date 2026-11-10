"""Acceso del motor al almacén de BusinessConfig: lee lo publicado, anota el consumo de IA y atiende los canales.

El motor lee la misma base que escribe el panel (`database_url()`: `BUSINESS_CONFIG_DATABASE_URL` o el SQLite local) con la misma
clave de cifrado (`find_secrets_key()`): lo publicado, los datos de pago, la clave de IA y la conexión de WhatsApp de cada negocio.
Lo único que escribe es el consumo de cada respuesta (`record_ai_usage`), el estado de la conexión de WhatsApp que avisa su servidor y
cada intercambio de un canal en la bandeja de conversaciones. Nunca crea la base, las tablas ni la clave: si algo falta, lo informa con
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
from app.domain.business_config.channels import ConnectionStatus, WhatsAppSecrets
from app.domain.business_config.contract import BusinessConfig, SecretRef
from app.domain.business_config.conversations import NewMessage
from app.domain.business_config.errors import BusinessConfigError
from app.infrastructure.business_config.ai_settings_store import AISettingsStore
from app.infrastructure.business_config.ai_usage_store import AIUsageStore
from app.infrastructure.business_config.channel_store import ChannelStore
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import create_business_config_engine, database_url, sqlite_file
from app.infrastructure.business_config.payment_secret_store import SECRET_STORE_SOURCE, PaymentSecretStore
from app.infrastructure.business_config.repository import BusinessConfigRepository
from app.infrastructure.business_config.secrets_key import find_secrets_key

__all__ = [
    "SECRET_STORE_SOURCE",
    "PublishedConfigReader",
    "dispose_shared_engines",
    "open_published_reader",
    "reader_for",
    "record_ai_usage",
    "record_conversation",
    "set_whatsapp_status",
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


def whatsapp_for_webhook(webhook_id: str) -> WhatsAppSecrets | None:
    """La conexión de WhatsApp (negocio, servidor y token) del webhook con ese identificador secreto, o None si no existe."""
    return ChannelStore(_store_engine(), find_secrets_key()).secrets_for_webhook(webhook_id)


def set_whatsapp_status(tenant_slug: str, status: ConnectionStatus, *, phone: str | None = None, profile_name: str | None = None) -> None:
    """El estado de la conexión que avisa el servidor de WhatsApp (se conectó, se desconectó)."""
    ChannelStore(_store_engine(), find_secrets_key()).set_status(tenant_slug, status, phone=phone, profile_name=profile_name)


def record_conversation(
    tenant_slug: str, *, channel: str, contact_ref: str, contact_name: str | None, messages: list[NewMessage], handoff: bool = False
) -> str:
    """Agrega un intercambio de un canal al hilo de ese contacto en la bandeja. Los datos de pago ya deben venir ocultos."""
    return ConversationStore(_store_engine()).record(
        tenant_slug, channel=channel, contact_ref=contact_ref, contact_name=contact_name, messages=messages, handoff=handoff
    )


def dispose_shared_engines() -> None:
    """Cierra las conexiones compartidas (al terminar el proceso o entre pruebas)."""
    with _engines_lock:
        for engine in _engines.values():
            engine.dispose()
        _engines.clear()
