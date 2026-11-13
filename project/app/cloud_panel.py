"""La API del panel en la nube: la misma API que en este equipo, con cuentas de Neon Auth.

Cada petición trae el token de la sesión y cada usuario solo llega a sus negocios (`business_members`). Usa la base de la
plataforma (`BUSINESS_CONFIG_DATABASE_URL`) y su clave de cifrado (`BUSINESS_CONFIG_SECRETS_KEY`). La publica el motor bajo
`/panel` cuando está definida `NEON_AUTH_URL` (ver `app/main.py`); el panel llega a ella por `/api`, con la reescritura de
`apps/admin-web/vercel.json`.
"""
from __future__ import annotations

from fastapi import FastAPI

from app.admin_api.main import create_app
from app.business_config_application.access import BusinessAccess
from app.infrastructure.auth.neon_auth import NeonAuthVerifier
from app.infrastructure.business_config.database import (
    build_assistant_lab_service,
    build_business_config_service,
    create_business_config_engine,
)
from app.infrastructure.business_config.api_key_store import ApiKeyStore
from app.infrastructure.business_config.attention_store import AttentionStore
from app.infrastructure.business_config.quick_reply_store import QuickReplyStore
from app.infrastructure.business_config.team_store import TeamStore
from app.infrastructure.business_config.migrations import ensure_migrations
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.notification_store import NotificationStore
from app.infrastructure.business_config.push_store import PushStore
from app.infrastructure.business_config.secrets_key import find_secrets_key
from app.infrastructure.business_config.usage_store import UsageCounterStore
from app.services.ai_service import GLOBAL_MEMORY_REPOSITORY


def build_cloud_panel_api(auth_url: str) -> FastAPI:
    from app.application.assistant_lab.engine_runner import EngineAssistantRunner
    from app.application.channels.contact_memory import EngineContactMemory
    from app.config import settings
    from app.infrastructure.ai.openrouter_key_verifier import OpenRouterKeyVerifier
    from app.infrastructure.ai.openrouter_models import OpenRouterModelCatalog
    from app.infrastructure.business_config.database import build_channel_messenger, build_telegram_channel_service, build_whatsapp_channel_service
    from app.infrastructure.business_config.ai_usage_store import AIUsageStore
    from app.infrastructure.business_config.commerce_store import CommerceStore
    from app.infrastructure.business_config.oauth_store import OAuthStore
    from app.infrastructure.channels.platform import uazapi_platform
    from app.infrastructure.channels.public_url import assistant_api_url, mcp_url, telegram_webhook_base, webhook_base
    from app.infrastructure.channels.telegram import TelegramClient
    from app.infrastructure.channels.uazapi import UazapiClient
    from app.infrastructure.notifications.resend_email import ResendEmailSender
    from app.infrastructure.notifications.web_push import WebPushSender

    engine = create_business_config_engine()
    # Como en Auream: cada despliegue deja la base al día solo, sin correr nada a mano.
    ensure_migrations(engine)
    key = find_secrets_key()
    service = build_business_config_service(engine, secrets_key=key)
    lab = build_assistant_lab_service(
        engine,
        service,
        secrets_key=key,
        verifier=OpenRouterKeyVerifier(),
        # «Probar» guarda su memoria en la base: en Vercel cada mensaje puede caer en otra instancia (A6).
        runner=EngineAssistantRunner(memory=GLOBAL_MEMORY_REPOSITORY),
        catalog=OpenRouterModelCatalog(),
        default_model=settings.openrouter_model,
    )
    access = BusinessAccess(service, BusinessMembersStore(engine))
    push_store = PushStore(engine, key)
    return create_app(
        service,
        lab,
        access=access,
        verifier=NeonAuthVerifier(auth_url),
        conversations=ConversationStore(engine),
        notifications=NotificationStore(engine),
        usage=UsageCounterStore(engine),
        whatsapp=build_whatsapp_channel_service(
            engine, UazapiClient, platform=uazapi_platform(), webhook_base=webhook_base(settings.api_prefix), secrets_key=key
        ),
        telegram=build_telegram_channel_service(engine, TelegramClient(), webhook_base=telegram_webhook_base(settings.api_prefix), secrets_key=key),
        messenger=build_channel_messenger(engine, UazapiClient, telegram=TelegramClient, secrets_key=key),
        commerce=CommerceStore(engine),
        ai_usage=AIUsageStore(engine),
        contact_memory=EngineContactMemory(),
        attention=AttentionStore(engine),
        push_storage=push_store,
        email=ResendEmailSender(),
        push=WebPushSender(push_store.vapid_keys),
        api_keys=ApiKeyStore(engine),
        assistant_api_url=lambda: assistant_api_url(settings.api_prefix),
        mcp_url=mcp_url,
        # Claude (web y app) y ChatGPT se conectan pegando la dirección e iniciando sesión en el panel.
        oauth=OAuthStore(engine),
        quick_replies=QuickReplyStore(engine),
        team=TeamStore(engine),
    )
