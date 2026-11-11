"""Peticiones y respuestas de la API. El documento comercial se valida con el contrato, no aquí."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.admin_api.errors import PAYMENT_PROBLEM
from app.business_config_application.assistant_lab import PlaygroundReply
from app.business_config_application.channels import WhatsAppView
from app.business_config_application.service import ConfigReview, EditableConfig
from app.domain.business_config.ai_settings import AISettings, KeyCheck
from app.domain.business_config.ai_models import ModelCatalog
from app.domain.business_config.ai_usage import AIUsageSummary
from app.domain.business_config.conversations import BusinessActivity, ChatMessage, ConversationSummary, Notification
from app.domain.business_config.records import BusinessSummary, ConfigVersion
from app.domain.business_config.templates import BusinessTemplate


class _Request(BaseModel):
    # Los errores de validación no repiten el valor recibido: podría ser un dato de pago.
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class CreateBusiness(_Request):
    slug: str
    name: str
    # Plantilla con la que empieza (restaurante, tienda...). Sin plantilla, empieza de cero.
    template: str | None = None


class SaveConfig(_Request):
    document: dict[str, Any]
    # Valores nuevos de datos de pago, por su referencia en el documento. Nunca se devuelven.
    payment_values: dict[str, str] = Field(default_factory=dict)
    # La versión más reciente que conocía quien edita: detecta cambios hechos en otra pestaña.
    base_version: int | None = None


class ValidateConfig(_Request):
    document: dict[str, Any]


class PublishVersion(_Request):
    version: int


class SaveAISettings(_Request):
    model: str | None = None
    # La clave nueva, solo cuando cambia. Nunca se devuelve.
    api_key: str | None = None
    clear_key: bool = False


class PlaygroundMessage(_Request):
    message: str
    # Lo que se está editando (para probar antes de publicar) o lo publicado.
    source: Literal["draft", "published"] = "draft"
    session_id: str | None = None


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def summary_payload(summary: BusinessSummary) -> dict[str, Any]:
    return asdict(summary)


def whatsapp_payload(view: WhatsAppView) -> dict[str, Any]:
    """La conexión de WhatsApp para el panel: nunca el servidor ni los tokens, que son de la plataforma."""
    connection = view.connection
    return {
        "available": view.available,
        "status": connection.status if connection else "disconnected",
        "phone": connection.phone if connection else None,
        "profile_name": connection.profile_name if connection else None,
        "qrcode": view.qrcode,
        "paircode": view.paircode,
    }


def template_payload(template: BusinessTemplate) -> dict[str, Any]:
    """Lo que el panel muestra de una plantilla; el documento se usa al crear el negocio y no viaja al panel."""
    return {"id": template.id, "title": template.title, "description": template.description, "icon": template.icon}


def version_payload(version: ConfigVersion) -> dict[str, Any]:
    return {
        "version": version.version,
        "status": version.status,
        "published_at": _iso(version.published_at),
        "created_at": _iso(version.created_at),
        "created_by": version.created_by,
    }


def config_payload(editable: EditableConfig) -> dict[str, Any]:
    """El documento lleva referencias `secret_store:`; de cada dato de pago solo sale su estado y una versión enmascarada."""
    stored = editable.stored
    return {
        **summary_payload(editable.summary),
        "document": stored.config.model_dump(mode="json", exclude_none=True) if stored else None,
        "version": version_payload(stored.version) if stored else None,
        "payment_fields": {ref: asdict(state) for ref, state in editable.payment_fields.items()},
    }


def review_payload(review: ConfigReview) -> dict[str, Any]:
    if review.version is None:
        compile_error = "Todavía no hay una versión guardada."
    else:
        compile_error = PAYMENT_PROBLEM if review.payment_data_missing else review.compile_problem
    return {
        "version": review.version,
        "diagnostics": [asdict(item) for item in review.diagnostics],
        "compiles": review.compiles,
        "compile_error": compile_error,
    }


def ai_settings_payload(settings: AISettings) -> dict[str, Any]:
    """Nunca incluye la clave: solo si está configurada y sus últimos caracteres."""
    return {"provider": settings.provider, "model": settings.model, "key": {"configured": settings.key_configured, "hint": settings.key_hint}}


def ai_models_payload(catalog: ModelCatalog) -> dict[str, Any]:
    return {
        "default_model": catalog.default_model,
        "models": [
            {
                "id": model.id,
                "name": model.name,
                "provider": model.provider,
                "prompt_usd_per_million": model.prompt_usd_per_million,
                "completion_usd_per_million": model.completion_usd_per_million,
                "context_length": model.context_length,
                "recommended": model.recommended,
                "free": model.free,
            }
            for model in catalog.models
        ],
    }


def ai_usage_payload(summary: AIUsageSummary) -> dict[str, Any]:
    return {
        "since": summary.since.isoformat(),
        "replies": summary.replies,
        "prompt_tokens": summary.prompt_tokens,
        "completion_tokens": summary.completion_tokens,
        "cost_usd": summary.cost_usd,
        "days": [
            {"day": day.day.isoformat(), "replies": day.replies, "tokens": day.prompt_tokens + day.completion_tokens} for day in summary.days
        ],
    }


def key_check_payload(check: KeyCheck) -> dict[str, Any]:
    return {"valid": check.valid, "message": check.message}


def playground_payload(reply: PlaygroundReply) -> dict[str, Any]:
    return {
        "session_id": reply.session_id,
        "source": reply.source,
        "version": reply.version,
        "reply": reply.turn.reply,
        "intent": reply.turn.intent,
        "ai_answered": reply.turn.ai_answered,
    }


def conversation_payload(summary: ConversationSummary) -> dict[str, Any]:
    return {
        "id": summary.id,
        "business": {"slug": summary.business_slug, "name": summary.business_name},
        "channel": summary.channel,
        "contact_name": summary.contact_name,
        "status": summary.status,
        "started_at": _iso(summary.started_at),
        "last_message_at": _iso(summary.last_message_at),
        "last_message_preview": summary.last_message_preview,
        "message_count": summary.message_count,
        "needs_human": summary.needs_human,
        "handoff_requested_at": _iso(summary.handoff_requested_at),
    }


def chat_message_payload(message: ChatMessage) -> dict[str, Any]:
    return {"id": message.id, "author": message.author, "body": message.body, "intent": message.intent, "created_at": _iso(message.created_at)}


def activity_payload(activity: BusinessActivity) -> dict[str, Any]:
    return {
        "conversations": activity.conversations,
        "conversations_today": activity.conversations_since,
        "messages_today": activity.messages_since,
        "test_conversations": activity.test_conversations,
        "waiting_human": activity.waiting_human,
    }


def notification_payload(item: Notification) -> dict[str, Any]:
    return {
        "id": item.id,
        "business": {"slug": item.business_slug, "name": item.business_name},
        "conversation_id": item.conversation_id,
        "kind": item.kind,
        "title": item.title,
        "body": item.body,
        "created_at": _iso(item.created_at),
        "read": item.read,
    }


class MarkNotificationsRead(BaseModel):
    """Sin `ids`, marca como leídos todos los avisos de quien pregunta."""

    model_config = ConfigDict(extra="forbid")
    ids: list[str] | None = Field(default=None, max_length=100)
