"""OAuth del servidor MCP: conectar Claude (web y app) y ChatGPT pegando solo la dirección e iniciando sesión.

Sin sesión (los usa el agente):
    GET  /.well-known/oauth-protected-resource[/api/mcp]   qué servidor de autorización usar (RFC 9728)
    GET  /.well-known/oauth-authorization-server            dónde registrarse, autorizar y pedir tokens (RFC 8414)
    POST /api/oauth/register                                registro dinámico del agente (RFC 7591); 30 por hora por IP
    POST /api/oauth/token                                   código + PKCE, o renovación; 120 por minuto por IP

Con la sesión de la persona (los usa la pantalla `/oauth/authorize` del panel):
    GET  /api/oauth/authorize/request    qué agente pide acceso
    POST /api/oauth/authorize/decision   autorizar (con permisos y negocios) o rechazar; devuelve a dónde vuelve el navegador

En la nube el panel reenvía `/.well-known/*` y `/api/*` al motor (`apps/admin-web/vercel.json`): aquí viven bajo `/api`. Errores
con el formato de OAuth (`error`, `error_description`) y nunca en caché.
"""
from __future__ import annotations

import json
from typing import Annotated, Any
from urllib.parse import parse_qsl

from fastapi import APIRouter, Body, Depends, Request, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from app.admin_api.errors import ApiError
from app.admin_api.routes import CurrentUser
from app.admin_api.schemas import key_areas_payload
from app.business_config_application.mcp.oauth import McpOAuthService
from app.domain.business_config.errors import UsageLimitExceededError
from app.domain.business_config.key_permissions import KEY_AREAS, SCOPE_ASSISTANT_CHAT
from app.domain.business_config.oauth import OAuthError, authorization_server_metadata, protected_resource_metadata

router = APIRouter(prefix="/api")
MAX_BODY_BYTES = 16 * 1024
NO_STORE = {"Cache-Control": "no-store", "Pragma": "no-cache"}


def _oauth_or_none(request: Request) -> McpOAuthService | None:
    server = getattr(request.app.state, "mcp", None)
    return getattr(server, "oauth", None)


def _oauth(request: Request) -> McpOAuthService:
    service = _oauth_or_none(request)
    if service is None:
        raise ApiError(status.HTTP_404_NOT_FOUND, "Conectar con inicio de sesión no está disponible en este servidor.", code="oauth_unavailable")
    return service


OAuth = Annotated[McpOAuthService, Depends(_oauth)]


def _client_ip(request: Request) -> str:
    """La IP de quien llama: la primera que anota el proxy de Vercel; si no hay, la de la conexión."""
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.headers.get("x-real-ip", "").strip()
    return forwarded or (request.client.host if request.client else "desconocida")


def _oauth_json(body: dict[str, Any], http_status: int = status.HTTP_200_OK) -> JSONResponse:
    return JSONResponse(body, http_status, headers=NO_STORE)


def _oauth_error(exc: OAuthError) -> JSONResponse:
    return _oauth_json({"error": exc.code, "error_description": str(exc)}, status.HTTP_401_UNAUTHORIZED if exc.code == "invalid_client" else status.HTTP_400_BAD_REQUEST)


def _limited(exc: UsageLimitExceededError) -> JSONResponse:
    wait = str(exc.retry_after_seconds)
    return JSONResponse({"error": "slow_down", "error_description": f"Demasiadas peticiones: espera {wait} segundos."}, 429, headers={**NO_STORE, "Retry-After": wait})


async def _body(request: Request) -> dict[str, Any]:
    """Formulario (lo que manda OAuth) o JSON (lo que manda el registro)."""
    raw = await request.body()
    if len(raw) > MAX_BODY_BYTES:
        raise OAuthError("invalid_request", "La petición es demasiado grande.")
    if "application/json" in request.headers.get("content-type", ""):
        try:
            value = json.loads(raw or b"{}")
        except ValueError:
            raise OAuthError("invalid_request", "El cuerpo no es JSON válido.") from None
        return value if isinstance(value, dict) else {}
    try:
        return dict(parse_qsl(raw.decode("utf-8"), keep_blank_values=True))
    except UnicodeDecodeError:
        raise OAuthError("invalid_request", "El cuerpo no es un formulario válido.") from None


# ---------------------------------------------------------------------------- descubrimiento


@router.get("/.well-known/oauth-protected-resource")
@router.get("/.well-known/oauth-protected-resource/{rest:path}")
def protected_resource(request: Request, rest: str = "") -> JSONResponse:
    service = _oauth_or_none(request)
    if service is None:
        return JSONResponse({"error": "not_found"}, status.HTTP_404_NOT_FOUND)
    return JSONResponse(protected_resource_metadata(service.addresses), headers={"Cache-Control": "public, max-age=3600"})


@router.get("/.well-known/oauth-authorization-server")
@router.get("/.well-known/oauth-authorization-server/{rest:path}")
def authorization_server(request: Request, rest: str = "") -> JSONResponse:
    service = _oauth_or_none(request)
    if service is None:
        return JSONResponse({"error": "not_found"}, status.HTTP_404_NOT_FOUND)
    return JSONResponse(authorization_server_metadata(service.addresses), headers={"Cache-Control": "public, max-age=3600"})


# ---------------------------------------------------------------------------- el agente


@router.post("/oauth/register")
async def register(request: Request, service: OAuth) -> JSONResponse:
    try:
        await run_in_threadpool(request.app.state.usage.oauth_register, _client_ip(request))
        body = await _body(request)
        return _oauth_json(await run_in_threadpool(service.register, body), status.HTTP_201_CREATED)
    except UsageLimitExceededError as exc:
        return _limited(exc)
    except OAuthError as exc:
        return _oauth_error(exc)


@router.post("/oauth/token")
async def token(request: Request, service: OAuth) -> JSONResponse:
    try:
        await run_in_threadpool(request.app.state.usage.oauth_token, _client_ip(request))
        form = await _body(request)
        return _oauth_json(await run_in_threadpool(service.exchange, form))
    except UsageLimitExceededError as exc:
        return _limited(exc)
    except OAuthError as exc:
        return _oauth_error(exc)


# ---------------------------------------------------------------------------- la persona (pantalla de autorización)


def _agent_areas() -> list[dict[str, Any]]:
    """Las áreas que se le pueden dar a un agente: todas menos conversar con el asistente (eso es la API del asistente)."""
    chat = {area.id for area in KEY_AREAS if SCOPE_ASSISTANT_CHAT in area.write_scopes}
    return [area for area in key_areas_payload() if area["id"] not in chat]


@router.get("/oauth/authorize/request")
def authorization_request(request: Request, user: CurrentUser, service: OAuth) -> JSONResponse:
    prompt = service.describe(dict(request.query_params))
    return _oauth_json(
        {
            "ready": prompt.ready,
            "client_name": prompt.client_name,
            "redirect_host": prompt.redirect_host,
            "message": prompt.message,
            "redirect_to": prompt.redirect_to,
            "areas": _agent_areas() if prompt.ready else [],
        }
    )


@router.post("/oauth/authorize/decision")
def authorization_decision(user: CurrentUser, service: OAuth, body: Annotated[dict[str, Any], Body()]) -> JSONResponse:
    redirect_to = service.decide(
        user, body.get("params"), approve=body.get("approve") is True, permissions=body.get("permissions"), reach=body.get("reach"),
        businesses=body.get("businesses"),
    )
    return _oauth_json({"redirect_to": redirect_to})
