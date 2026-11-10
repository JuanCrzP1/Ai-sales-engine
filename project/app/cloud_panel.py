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
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.secrets_key import find_secrets_key


def build_cloud_panel_api(auth_url: str) -> FastAPI:
    from app.application.assistant_lab.engine_runner import EngineAssistantRunner
    from app.infrastructure.ai.openrouter_key_verifier import OpenRouterKeyVerifier

    engine = create_business_config_engine()
    key = find_secrets_key()
    service = build_business_config_service(engine, secrets_key=key)
    lab = build_assistant_lab_service(engine, service, secrets_key=key, verifier=OpenRouterKeyVerifier(), runner=EngineAssistantRunner())
    access = BusinessAccess(service, BusinessMembersStore(engine))
    return create_app(service, lab, access=access, verifier=NeonAuthVerifier(auth_url), conversations=ConversationStore(engine))
