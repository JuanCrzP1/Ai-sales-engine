"""Aplicación de la API del panel. Recibe los servicios ya construidos: no conoce la base de datos.

Dos modos, según reciba o no `verifier`:
- En la nube (`app/cloud_panel.py`): cada petición trae el token de la sesión de Neon Auth y cada usuario solo llega a sus
  negocios. Sin token válido, 401.
- En este equipo (`scripts/run_admin_api.py`, limitada a `127.0.0.1`), sin cuentas. Aunque alguien la sirviera en otra
  interfaz, solo atiende peticiones que vengan de este equipo. El `Host` y el `Origin` se comprueban porque un sitio web abierto en el navegador también
corre en este equipo: sin estas comprobaciones podría llamar a la API (falsificación de peticiones o `DNS rebinding`). No hay
CORS: el panel llega a través del proxy de Vite.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.admin_api.assistant_routes import router as assistant_router
from app.admin_api.attention_routes import router as attention_router
from app.admin_api.quick_reply_routes import router as quick_reply_router
from app.admin_api.help_routes import router as help_router
from app.admin_api.integration_routes import router as integration_router
from app.admin_api.mcp_routes import audit_tool_call, router as mcp_router
from app.admin_api.oauth_routes import router as oauth_router
from app.admin_api.channel_routes import router as channel_router
from app.admin_api.commerce_routes import router as commerce_router
from app.admin_api.conversation_routes import router as conversation_router
from app.admin_api.errors import register_error_handlers
from app.admin_api.routes import router
from app.business_config_application.access import BusinessAccess
from app.business_config_application.assistant_lab import AssistantLabService
from app.business_config_application.attention import AttentionService, PushService
from app.business_config_application.quick_replies import QuickRepliesService
from app.business_config_application.help import HelpService
from app.business_config_application.integrations import IntegrationsService
from app.business_config_application.mcp.oauth import McpOAuthService
from app.domain.business_config.oauth import oauth_addresses
from app.business_config_application.mcp.server import build_mcp_server
from app.business_config_application.channels import WhatsAppChannelService
from app.business_config_application.business_deletion import BusinessDeletionService
from app.business_config_application.commerce import CommerceService
from app.business_config_application.conversations import ConversationsService, NotificationsService
from app.business_config_application.ports import (
    AccessTokenVerifier,
    AIUsageStorage,
    ApiKeyStorage,
    OAuthStorage,
    AttentionStorage,
    QuickReplyStorage,
    CommerceStorage,
    EmailSender,
    ContactMemory,
    ConversationStorage,
    NotificationStorage,
    OutboundMessenger,
    PushSender,
    PushStorage,
    UsageCounter,
)
from app.business_config_application.service import BusinessConfigService
from app.business_config_application.templates import BusinessTemplateCatalog
from app.business_config_application.usage_limits import MemoryUsageCounter, UsageGuard
from app.domain.business_config.contract import business_config_json_schema

logger = logging.getLogger("admin-api")

LOOPBACK_CLIENTS = {"127.0.0.1", "::1", "::ffff:127.0.0.1"}
LOOPBACK_HOSTNAMES = {"127.0.0.1", "localhost", "[::1]"}
# El puerto de la interfaz del panel (`apps/admin-web/vite.config.ts`). El 4173 es el de su vista previa.
ADMIN_WEB_PORT = 5180
PANEL_ORIGINS = {
    f"http://127.0.0.1:{ADMIN_WEB_PORT}",
    f"http://localhost:{ADMIN_WEB_PORT}",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
}


def _hostname(host_header: str) -> str:
    """El nombre sin el puerto: `localhost:5180`, `127.0.0.1:8010` o `[::1]:8010`."""
    if host_header.startswith("["):
        return host_header.split("]", 1)[0] + "]"
    return host_header.split(":", 1)[0]


def _refusal(request: Request) -> str | None:
    if request.client is None or request.client.host not in LOOPBACK_CLIENTS:
        return "client"
    if _hostname(request.headers.get("host", "")) not in LOOPBACK_HOSTNAMES:
        return "host"
    origin = request.headers.get("origin")
    if origin is not None and origin not in PANEL_ORIGINS:
        return "origin"
    return None


def create_app(
    service: BusinessConfigService,
    assistant_lab: AssistantLabService | None = None,
    *,
    access: BusinessAccess | None = None,
    verifier: AccessTokenVerifier | None = None,
    conversations: ConversationStorage | None = None,
    notifications: NotificationStorage | None = None,
    usage: UsageCounter | None = None,
    templates: BusinessTemplateCatalog | None = None,
    whatsapp: WhatsAppChannelService | None = None,
    messenger: OutboundMessenger | None = None,
    commerce: CommerceStorage | None = None,
    ai_usage: AIUsageStorage | None = None,
    examples: Callable[[BusinessConfigService], Any] | None = None,
    contact_memory: ContactMemory | None = None,
    attention: AttentionStorage | None = None,
    push_storage: PushStorage | None = None,
    email: EmailSender | None = None,
    push: PushSender | None = None,
    api_keys: ApiKeyStorage | None = None,
    assistant_api_url: Callable[[], str | None] | None = None,
    mcp_url: Callable[[], str | None] | None = None,
    oauth: OAuthStorage | None = None,
    quick_replies: QuickReplyStorage | None = None,
    help_center: HelpService | None = None,
) -> FastAPI:
    """La API del panel. Sin `assistant_lab`, la inteligencia artificial y el área de pruebas responden que no están disponibles.

    Con `verifier` es la de la nube y necesita `access` con los miembros de cada negocio y `usage` con contadores compartidos
    por todas sus instancias; sin él, la local, que cuenta en memoria."""
    cloud = verifier is not None
    if cloud and access is None:
        raise ValueError("la API de la nube necesita saber a qué negocios llega cada usuario")
    if cloud and usage is None:
        raise ValueError("la API de la nube necesita contadores de uso compartidos (`rate_limits`)")
    # Sin /docs ni /openapi.json: el único cliente es el panel y no hace falta anunciar las rutas.
    app = FastAPI(title="AI Sales Engine: API del panel", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.service = service
    app.state.assistant_lab = assistant_lab
    app.state.access = access or BusinessAccess(service)
    app.state.verifier = verifier
    app.state.usage = UsageGuard(usage or MemoryUsageCounter())
    # Con `messenger`, el equipo responde desde el panel y el mensaje sale por el canal del cliente.
    # Con `contact_memory`, eliminar un chat también borra lo que el asistente recuerda de ese cliente (lo guarda el motor).
    app.state.conversations = ConversationsService(conversations, app.state.access, messenger, contact_memory) if conversations is not None else None
    app.state.notifications = NotificationsService(notifications, app.state.access) if notifications is not None else None
    # Clientes, ventas y reportes; con `ai_usage`, los reportes suman el costo de la IA.
    app.state.commerce = CommerceService(commerce, app.state.access, ai_usage) if commerce is not None else None
    app.state.contract_schema = business_config_json_schema()
    # Las plantillas para empezar un negocio: se validan aquí, al arrancar.
    app.state.templates = templates if templates is not None else BusinessTemplateCatalog.from_directory()
    # Atención humana (Configuración) y notificaciones del navegador: sin almacén, sus rutas responden que no están disponibles.
    app.state.attention = AttentionService(attention, app.state.access, service, email) if attention is not None else None
    app.state.push = PushService(push_storage, push) if push_storage is not None else None
    # Respuestas rápidas (Configuración y el chat): sin almacén, sus rutas responden que no están disponibles.
    app.state.quick_replies = QuickRepliesService(quick_replies, app.state.access) if quick_replies is not None else None
    # El Centro de ayuda: los artículos de `content/help`, los mismos para el panel y para los agentes (MCP).
    app.state.help = help_center if help_center is not None else HelpService.from_directory()
    # Integraciones: las claves de API del negocio y la API del asistente (su dirección y una prueba con lo publicado).
    app.state.integrations = (
        IntegrationsService(
            api_keys, app.state.access, assistant_api_url=assistant_api_url or (lambda: None), mcp_url=mcp_url or (lambda: None), lab=assistant_lab,
        )
        if api_keys is not None
        else None
    )
    # Conectar un agente con inicio de sesión (OAuth): solo en la nube, con cuentas y una dirección pública del servidor MCP.
    public_mcp = mcp_url() if mcp_url is not None else None
    mcp_oauth = (
        McpOAuthService(oauth, api_keys, app.state.access, oauth_addresses(public_mcp))
        if oauth is not None and api_keys is not None and cloud and public_mcp
        else None
    )
    # El servidor MCP: los agentes de IA trabajan con una clave de API y los MISMOS servicios del panel.
    app.state.mcp = (
        build_mcp_server(
            service,
            app.state.access,
            api_keys,
            templates=app.state.templates.list,
            schema=app.state.contract_schema,
            lab=assistant_lab,
            conversations=app.state.conversations,
            commerce=app.state.commerce,
            attention=app.state.attention,
            help=app.state.help,
            local=not cloud,
            # Probar el asistente y responder a un cliente cuentan como si lo hiciera el dueño de la clave desde el panel.
            before_test=lambda caller, business: app.state.usage.playground_message(caller.principal, business),
            before_reply=lambda caller: app.state.usage.conversation_reply(caller.principal),
            on_created=lambda caller, business: app.state.attention.remember_account(caller.principal, force=True) if app.state.attention is not None and caller.principal.email else None,
            on_tool_call=audit_tool_call,
            oauth=mcp_oauth,
        )
        if api_keys is not None
        else None
    )
    # WhatsApp por código QR: sin el servicio, sus rutas responden que los canales no están disponibles.
    app.state.whatsapp = whatsapp
    # Eliminar un negocio: primero WhatsApp (fuera de la base), luego todo lo suyo en una transacción y su memoria en RAM.
    app.state.deletion = BusinessDeletionService(service, app.state.access, whatsapp=whatsapp, memory=contact_memory)
    # Solo la API de este equipo importa los negocios de ejemplo (`POST /api/businesses/import`).
    app.state.examples = examples

    @app.middleware("http")
    async def guard(request: Request, call_next):
        refusal = None if cloud else _refusal(request)
        if refusal is not None:
            logger.warning("peticion_rechazada", extra={"reason": refusal})
            return JSONResponse({"code": "forbidden", "message": "Esta API solo atiende al panel en este equipo.", "issues": []}, status.HTTP_403_FORBIDDEN)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    register_error_handlers(app)
    app.include_router(router)
    app.include_router(assistant_router)
    app.include_router(conversation_router)
    app.include_router(channel_router)
    app.include_router(commerce_router)
    app.include_router(attention_router)
    app.include_router(quick_reply_router)
    app.include_router(help_router)
    app.include_router(integration_router)
    app.include_router(mcp_router)
    app.include_router(oauth_router)
    return app
