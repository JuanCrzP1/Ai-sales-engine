"""Lo que la aplicación necesita de la persistencia, sin depender de una base de datos.

`BusinessConfigStorage` y `PaymentSecretStorage` los implementan hoy `BusinessConfigRepository` y `PaymentSecretStore` sobre
SQLAlchemy, con SQLite en local. Pasar a PostgreSQL es cambiar la URL de conexión y aplicar la migración SQL, sin tocar a
quien usa estos puertos. Toda operación recibe el negocio y solo alcanza sus datos.
"""
from __future__ import annotations

from collections.abc import Callable, Collection
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from app.domain.business_config.access import Principal
from app.domain.business_config.ai_settings import AICredentials, AISettings, AssistantTurn, KeyCheck
from app.domain.business_config.ai_models import AIModel
from app.domain.business_config.api_keys import ApiKey, ApiKeyIdentity, CreatedApiKey
from app.domain.business_config.key_permissions import KeyReach
from app.domain.business_config.oauth import AuthorizationCode, OAuthClient, TokenGrant
from app.domain.business_config.attention import AttentionSettings
from app.domain.business_config.quick_replies import QuickReply, QuickReplyDraft
from app.domain.business_config.team import Invitation, Member
from app.domain.business_config.ai_usage import AIUsageSummary
from app.domain.business_config.commerce import Customer, NewSale, ReportDay, ReportTotals, Sale
from app.domain.business_config.channels import ConnectionStatus, ProviderStatus, WhatsAppConnection, WhatsAppSecrets
from app.domain.business_config.contract import BusinessConfig, SecretRef
from app.domain.business_config.conversations import (
    AppendResult,
    BusinessActivity,
    ChatMessage,
    ConversationSummary,
    ConversationTarget,
    MediaFile,
    NewMessage,
    Notification,
)
from app.domain.business_config.push import PushMessage, PushSubscription
from app.domain.business_config.records import BusinessSummary, ConfigVersion, StoredConfig


class _VersionCheck(Enum):
    ANY = "any"


ANY_VERSION = _VersionCheck.ANY
# La versión más reciente que conocía quien guarda (None: ninguna). `ANY_VERSION` guarda sin comprobarlo.
ExpectedVersion = int | None | _VersionCheck
PublishCheck = Callable[[BusinessConfig], None]


@runtime_checkable
class BusinessConfigStorage(Protocol):
    def create_business(self, tenant_slug: str, name: str, *, owner_id: str | None = None) -> BusinessSummary:
        """Registra el negocio y, si se indica, a su dueño, en la misma transacción: nunca queda un negocio sin dueño."""
        ...

    def business(self, tenant_slug: str) -> BusinessSummary: ...

    def list_businesses(self) -> list[BusinessSummary]: ...

    def delete_business(self, tenant_slug: str) -> None: ...

    def save_draft(
        self,
        tenant_slug: str,
        document: dict[str, Any],
        *,
        created_by: str | None = None,
        expected_version: ExpectedVersion = ANY_VERSION,
        payment_secrets: dict[str, str] | None = None,
    ) -> ConfigVersion:
        """Guarda una versión y sus datos de pago de forma atómica: o queda todo o no queda nada."""
        ...

    def latest_draft(self, tenant_slug: str) -> StoredConfig | None: ...

    def version(self, tenant_slug: str, version: int) -> StoredConfig: ...

    def published(self, tenant_slug: str) -> BusinessConfig: ...

    def publish(self, tenant_slug: str, version: int, *, check: PublishCheck | None = None) -> None: ...

    def rollback(self, tenant_slug: str, *, check: PublishCheck | None = None) -> int: ...

    def history(self, tenant_slug: str) -> list[ConfigVersion]: ...

    def save_engine_settings(self, tenant_slug: str, document: dict[str, Any]) -> None: ...


@runtime_checkable
class PaymentSecretStorage(Protocol):
    def resolver(self, tenant_slug: str) -> Callable[[SecretRef], str]: ...

    def known_values(self, tenant_slug: str) -> list[str]: ...

    def verify_key(self) -> None: ...


@runtime_checkable
class AISettingsStorage(Protocol):
    """La inteligencia artificial de cada negocio, con su clave cifrada. Cada negocio solo alcanza la suya."""

    def ai_settings(self, tenant_slug: str) -> AISettings: ...

    def ai_credentials(self, tenant_slug: str) -> AICredentials | None: ...

    def save_ai_settings(self, tenant_slug: str, *, model: str | None, api_key: str | None, clear_key: bool) -> AISettings: ...


@runtime_checkable
class AIUsageStorage(Protocol):
    """El consumo de IA de cada negocio. Lo escribe el motor en cada respuesta; el panel solo lo lee."""

    def summary(self, tenant_slug: str, *, since: date) -> AIUsageSummary: ...


@runtime_checkable
class AIModelCatalog(Protocol):
    """Los modelos que se pueden elegir. Si no se pueden cargar, falla con `ModelCatalogUnavailableError`."""

    def models(self) -> list[AIModel]: ...


@runtime_checkable
class AIKeyVerifier(Protocol):
    """Pregunta al proveedor si la clave es válida, sin gastar créditos."""

    def verify(self, credentials: AICredentials) -> KeyCheck: ...


@runtime_checkable
class AssistantRunner(Protocol):
    """El motor respondiendo con una configuración concreta, en una conversación de prueba aislada de los clientes reales.

    `sections` es lo compilado de esa versión: puede llevar datos de pago descifrados y no se guarda ni se registra.
    """

    def reply(self, *, tenant_slug: str, sections: dict[str, dict], credentials: AICredentials, session_id: str, message: str) -> AssistantTurn: ...

    def reset(self, *, tenant_slug: str, session_id: str) -> None: ...


@runtime_checkable
class BusinessMembers(Protocol):
    """Qué usuarios son miembros de cada negocio. Lo consulta la API de la nube antes de tocar cualquier negocio."""

    def slugs_of(self, user_id: str) -> set[str]: ...

    def is_member(self, tenant_slug: str, user_id: str) -> bool: ...

    def is_owner(self, tenant_slug: str, user_id: str) -> bool: ...

    def role_of(self, tenant_slug: str, user_id: str) -> str | None: ...

    def roles_of(self, user_id: str) -> dict[str, str]:
        """Sus negocios (por slug) con su rol en cada uno."""
        ...


@runtime_checkable
class AccessTokenVerifier(Protocol):
    """Comprueba el token de la sesión: quién es el usuario, o None si el token no es válido o venció."""

    def verify(self, token: str) -> Principal | None: ...


@runtime_checkable
class ConversationStorage(Protocol):
    """Las conversaciones de cada negocio. Toda consulta recibe los negocios que puede ver quien pregunta."""

    def record(
        self,
        tenant_slug: str,
        *,
        channel: str,
        contact_ref: str,
        contact_name: str | None,
        messages: list[NewMessage],
        handoff: bool = False,
        handoff_reason: str | None = None,
    ) -> str:
        """Agrega mensajes al hilo de ese contacto en ese canal (lo crea si no existe) y devuelve su identificador. Con `handoff`,
        la conversación queda esperando a una persona y el equipo recibe un aviso, en la misma transacción."""
        ...

    def append(
        self, tenant_slug: str, *, channel: str, contact_ref: str, contact_name: str | None, message: NewMessage, media: MediaFile | None = None
    ) -> AppendResult:
        """Un mensaje que llega o sale por un canal, apenas pasa. El mismo id del canal no se guarda dos veces."""
        ...

    def update_entry(
        self, entry_id: str, *, status: str | None = None, provider_message_id: str | None = None, media: MediaFile | None = None, media_note: str | None = None
    ) -> None: ...

    def recent(self, tenant_slugs: Collection[str], *, channel: str | None, limit: int, needs_human: bool | None = None) -> list[ConversationSummary]: ...

    def thread(self, conversation_id: str) -> tuple[ConversationSummary, list[ChatMessage]]: ...

    def changes(self, conversation_id: str, since: datetime | None) -> tuple[ConversationSummary, list[ChatMessage]]: ...

    def business_of(self, conversation_id: str) -> str: ...

    def target(self, conversation_id: str) -> ConversationTarget: ...

    def media(self, conversation_id: str, media_id: str) -> MediaFile: ...

    def resolve_handoff(self, conversation_id: str) -> None: ...

    def delete(self, conversation_id: str) -> ConversationTarget:
        """Borra la conversación con sus mensajes, archivos y avisos (las ventas se conservan sin el enlace) y dice de quién era."""
        ...

    def delete_channel(self, tenant_slug: str, channel: str) -> int:
        """Borra todas las conversaciones de un canal de ese negocio y dice cuántas eran."""
        ...

    def set_ai_paused(self, conversation_id: str, paused: bool) -> None: ...

    def mark_read(self, conversation_id: str) -> None: ...

    def activity(self, tenant_slug: str, *, since: datetime) -> BusinessActivity: ...


class ContactMemory(Protocol):
    """Lo que el asistente recuerda de cada cliente (su historial y su memoria comercial, que guarda el motor)."""

    def forget(self, business_slug: str, contact_ref: str) -> None:
        """Lo olvida todo: si el cliente vuelve a escribir, el asistente empieza de cero. Si no puede, lanza la excepción."""
        ...

    def forget_business(self, business_slug: str) -> None:
        """Al eliminar el negocio: lo que el motor tenga en memoria de sus clientes (lo guardado se borra con el negocio)."""
        ...


class CommerceStorage(Protocol):
    """Clientes (las conversaciones de canales reales con su etapa), ventas y los datos de los reportes de cada negocio."""

    def customers(self, tenant_slug: str, *, stage: str | None = None, query: str | None = None) -> list[Customer]: ...

    def record_sale(self, tenant_slug: str, sale: NewSale, *, created_by: str | None) -> Sale: ...

    def cancel_sale(self, tenant_slug: str, sale_id: str) -> Sale: ...

    def sales(self, tenant_slug: str, *, since: date) -> list[Sale]: ...

    def report_data(self, tenant_slug: str, *, since: date, until: date) -> tuple[list[ReportDay], ReportTotals, dict[str, int], dict[str, int]]: ...


class OutboundMessenger(Protocol):
    """Envía por su canal lo que el equipo responde desde el panel y devuelve el id que le dio el canal (o None).
    Si el canal no puede enviarlo, lanza `ChannelError` con un mensaje para el negocio."""

    def send_text(self, business_slug: str, channel: str, contact_ref: str, text: str) -> str | None: ...


@runtime_checkable
class UsageCounter(Protocol):
    """Contadores de uso por ventana de tiempo, compartidos por todas las instancias del servidor."""

    def hit(self, bucket: str, window_start: datetime) -> int:
        """Suma uno al contador de `bucket` en la ventana que empieza en `window_start` y devuelve el total, de forma atómica.
        Puede borrar las ventanas anteriores de ese contador."""
        ...


@runtime_checkable
class NotificationStorage(Protocol):
    """Los avisos de los negocios. Lo leído es de cada persona."""

    def recent(self, tenant_slugs: Collection[str], user_id: str, *, limit: int) -> tuple[list[Notification], int]: ...

    def mark_read(self, tenant_slugs: Collection[str], user_id: str, ids: Collection[str] | None = None) -> int: ...


class WhatsAppProvider(Protocol):
    """El servidor de WhatsApp por código QR (uazapi) de la plataforma. Los errores se informan con `ChannelError`."""

    def status(self, token: str) -> ProviderStatus: ...

    def create_instance(self, admin_token: str, name: str) -> str: ...

    def connect(self, token: str) -> ProviderStatus: ...

    def disconnect(self, token: str) -> None: ...

    def delete_instance(self, token: str) -> None: ...

    def set_webhook(self, token: str, url: str) -> None: ...

    def send_text(self, token: str, phone: str, text: str) -> str | None: ...


class ChannelStorage(Protocol):
    """La conexión de WhatsApp de cada negocio, con sus tokens cifrados."""

    def whatsapp(self, tenant_slug: str) -> WhatsAppConnection | None: ...

    def whatsapp_secrets(self, tenant_slug: str) -> WhatsAppSecrets | None: ...

    def save_whatsapp(self, tenant_slug: str, *, server_url: str, instance_token: str) -> None: ...

    def set_status(self, tenant_slug: str, status: ConnectionStatus, *, phone: str | None = None, profile_name: str | None = None) -> None: ...

    def delete_whatsapp(self, tenant_slug: str) -> None: ...


# ---------------------------------------------------------------------------------------------------------- atención humana


class EmailNotSent(RuntimeError):
    """El correo no salió. El mensaje es para el negocio (nunca trae claves)."""


@dataclass(frozen=True)
class PushOutcome:
    """Cómo le fue a una notificación: `sent`, `gone` (la suscripción ya no existe: se olvida) o `failed`."""

    status: str
    detail: str | None = None


class EmailSender(Protocol):
    """Envía correos de la plataforma (`infrastructure/notifications/resend_email.py`)."""

    @property
    def configured(self) -> bool: ...

    def send(self, *, to: list[str], subject: str, html: str, text: str, idempotency_key: str | None = None) -> str | None: ...


class PushSender(Protocol):
    """Envía una notificación a un navegador o celular (`infrastructure/notifications/web_push.py`)."""

    def send(self, subscription: PushSubscription, message: PushMessage) -> PushOutcome: ...


class QuickReplyStorage(Protocol):
    """Las respuestas rápidas de cada negocio (`quick_reply_store.py`). Una de otro negocio se trata como inexistente."""

    def list(self, tenant_slug: str) -> list[QuickReply]: ...

    def create(self, tenant_slug: str, draft: QuickReplyDraft, *, created_by: str | None) -> QuickReply: ...

    def update(self, tenant_slug: str, reply_id: str, draft: QuickReplyDraft) -> QuickReply: ...

    def delete(self, tenant_slug: str, reply_id: str) -> None: ...

    def mark_used(self, tenant_slug: str, reply_id: str) -> QuickReply: ...


class TeamStorage(Protocol):
    """El equipo de cada negocio y sus invitaciones (`team_store.py`). Cambiar un rol, quitar a alguien y aceptar una invitación
    se deciden y se aplican en una sola transacción: `decide` recibe lo que hay en la base en ese momento (el rol de la persona y
    cuántos dueños quedan) y falla si la regla no se cumple."""

    def members(self, tenant_slug: str) -> list[Member]: ...

    def change_role(self, tenant_slug: str, user_id: str, decide: Callable[[str, int], str]) -> Member: ...

    def remove(self, tenant_slug: str, user_id: str, decide: Callable[[str, int], None]) -> None: ...

    def invitations(self, tenant_slug: str) -> list[Invitation]:
        """Las que no se aceptaron ni se retiraron (las vencidas también: se pueden renovar)."""
        ...

    def invite(self, tenant_slug: str, *, email: str, role: str, token_hash: str, invited_by: str, now: datetime, expires_at: datetime) -> Invitation:
        """La crea; si ese correo ya tenía una pendiente, la reemplaza."""
        ...

    def renew(self, tenant_slug: str, invitation_id: str, *, token_hash: str, now: datetime, expires_at: datetime) -> Invitation: ...

    def revoke(self, tenant_slug: str, invitation_id: str, *, now: datetime) -> None: ...

    def invitation_by_token(self, token_hash: str) -> Invitation | None: ...

    def accept(self, token_hash: str, *, user_id: str, email: str | None, now: datetime, check: Callable[[Invitation | None], Invitation]) -> str:
        """Lo pone en el equipo con el rol de la invitación (si ya estaba, conserva el suyo) y devuelve el negocio."""
        ...


class AttentionStorage(Protocol):
    """Los ajustes de atención humana, el equipo de cada negocio y el envío de sus avisos (`attention_store.py`)."""

    def attention_settings(self, tenant_slug: str) -> AttentionSettings: ...

    def save_attention_settings(self, tenant_slug: str, settings: AttentionSettings) -> AttentionSettings: ...

    def owner_emails(self, tenant_slug: str) -> list[str]: ...

    def member_ids(self, tenant_slug: str) -> list[str]: ...

    def remember_email(self, user_id: str, email: str) -> None: ...

    def alert(self, notification_id: str) -> Any: ...

    def claim_delivery(self, notification_id: str, channel: str) -> bool: ...

    def finish_delivery(self, notification_id: str, channel: str, status: str, detail: str | None = None) -> None: ...


class PushStorage(Protocol):
    """Las suscripciones a notificaciones de cada persona y la clave pública de la plataforma (`push_store.py`)."""

    def vapid_public_key(self) -> str: ...

    def subscribe(self, subscription: PushSubscription) -> None: ...

    def unsubscribe(self, user_id: str, endpoint: str) -> bool: ...

    def is_subscribed(self, user_id: str, endpoint: str) -> bool: ...

    def subscriptions_for(self, user_ids: Collection[str]) -> list[PushSubscription]: ...

    def forget(self, endpoint: str) -> None: ...

    def mark_delivered(self, endpoint: str) -> None: ...


class ApiKeyStorage(Protocol):
    """Las claves de API: de un negocio o de una cuenta (`api_key_store.py`). `local` es este equipo, sin cuentas."""

    def create(
        self,
        *,
        name: str,
        scopes: tuple[str, ...],
        reach: KeyReach,
        created_by: str | None,
        owner_user_id: str | None,
        expires_at: datetime | None = None,
    ) -> CreatedApiKey: ...

    def list_keys(self, tenant_slug: str, *, owner_user_id: str | None = None, local: bool = False) -> list[ApiKey]: ...

    def revoke(self, tenant_slug: str, key_id: str, *, owner_user_id: str | None = None, local: bool = False) -> ApiKey: ...

    def authenticate(self, secret: str) -> ApiKeyIdentity | None: ...

    def connect(
        self, *, name: str, scopes: tuple[str, ...], reach: KeyReach, created_by: str | None, owner_user_id: str | None, client_id: str
    ) -> ApiKey:
        """Una conexión por OAuth (clave `oauth`, sin valor fijo). Reemplaza la que ese dueño ya tenía con el mismo agente."""
        ...

    def identity(self, key_id: str) -> ApiKeyIdentity | None:
        """Quién llama con esa clave o conexión, si sigue activa y sin vencer (lo usan los tokens de OAuth)."""
        ...


@runtime_checkable
class OAuthStorage(Protocol):
    """Los agentes registrados, los códigos de autorización y los tokens del OAuth del servidor MCP (`oauth_store.py`). Solo
    huellas: nunca un código ni un token."""

    def create_client(self, client: OAuthClient) -> None: ...

    def find_client(self, client_id: str) -> OAuthClient | None: ...

    def save_code(self, code: AuthorizationCode) -> None: ...

    def take_code(self, code_hash: str) -> AuthorizationCode | None:
        """El código, borrándolo: sirve una sola vez."""
        ...

    def save_grant(self, grant: TokenGrant, *, now: datetime) -> None:
        """Guarda los tokens nuevos y, de paso, borra los vencidos."""
        ...

    def take_refresh(self, refresh_hash: str) -> TokenGrant | None:
        """Los tokens de ese token de renovación, borrándolos: al renovar, los anteriores dejan de servir."""
        ...

    def key_for_access(self, access_hash: str, now: datetime) -> str | None:
        """La conexión de un token de acceso vigente."""
        ...
