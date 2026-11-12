"""`POST /api/mcp`: el servidor MCP (transporte HTTP «Streamable», sin estado ni flujo de eventos: cada petición JSON-RPC recibe
su respuesta JSON).

Lo usan los agentes de IA con `Authorization: Bearer <clave de API>` o un token de acceso de OAuth. Sin uno válido, 401 (con la
dirección de los metadatos de OAuth, para que el agente sepa dónde iniciar sesión). Límite: 300 peticiones por minuto
por clave (429 con `Retry-After`). Acepta un mensaje o varios a la vez (lote); solo notificaciones, 202 sin cuerpo. Cada llamada
a una herramienta queda en el registro (clave, herramienta, resultado y duración; nunca los datos).
"""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Request, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response

from app.business_config_application.mcp.server import McpServer
from app.domain.business_config.errors import UsageLimitExceededError
from app.domain.business_config.oauth import resource_metadata_url

logger = logging.getLogger("mcp")

router = APIRouter(prefix="/api")
MAX_BODY_BYTES = 1024 * 1024


def _rpc_error(code: int, message: str, http_status: int, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": None, "error": {"code": code, "message": message}}, http_status, headers=headers)


@router.get("/mcp")
def mcp_get() -> Response:
    # Sin flujo de eventos (GET) ni sesiones: todo es una petición POST.
    return JSONResponse({"message": "El servidor MCP recibe peticiones POST."}, status.HTTP_405_METHOD_NOT_ALLOWED, headers={"Allow": "POST"})


@router.post("/mcp")
async def mcp_post(request: Request) -> Response:
    server: McpServer | None = getattr(request.app.state, "mcp", None)
    if server is None:
        return JSONResponse({"message": "El servidor MCP no está disponible."}, status.HTTP_503_SERVICE_UNAVAILABLE)
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    caller = await run_in_threadpool(server.authenticate, token.strip()) if scheme.lower() == "bearer" and token.strip() else None
    if caller is None:
        # Con OAuth, el agente (Claude, ChatGPT) sigue `resource_metadata` para descubrir dónde iniciar sesión (RFC 9728).
        challenge = 'Bearer realm="ai-sales-engine"'
        if server.oauth is not None:
            challenge += f', resource_metadata="{resource_metadata_url(server.oauth.addresses.resource)}"'
        if token.strip():
            challenge += ', error="invalid_token"'
        return JSONResponse(
            {"message": "Falta una clave válida: Authorization: Bearer <tu clave de API>. Créala en Integraciones → Claves de API, o conecta el agente iniciando sesión."},
            status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": challenge},
        )
    try:
        await run_in_threadpool(request.app.state.usage.mcp_request, caller.key_id)
    except UsageLimitExceededError as exc:
        wait = str(exc.retry_after_seconds)
        return _rpc_error(-32000, f"Demasiadas peticiones seguidas: espera {wait} segundos.", status.HTTP_429_TOO_MANY_REQUESTS, {"Retry-After": wait})

    raw = await request.body()
    if len(raw) > MAX_BODY_BYTES:
        return _rpc_error(-32600, "La petición es demasiado grande.", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    try:
        body: Any = json.loads(raw or b"null")
    except ValueError:
        return _rpc_error(-32700, "El cuerpo no es JSON válido.", status.HTTP_400_BAD_REQUEST)
    messages = body if isinstance(body, list) else [body]
    replies = []
    for message in messages:
        reply = await run_in_threadpool(server.protocol.handle, message, caller)
        if reply is not None:
            replies.append(reply)
    if not replies:
        return Response(status_code=status.HTTP_202_ACCEPTED)
    return JSONResponse(replies if isinstance(body, list) else replies[0])


def audit_tool_call(caller, report) -> None:
    """El registro de cada acción de un agente: qué clave, qué herramienta, si salió bien y cuánto tardó. Sin los datos."""
    logger.info("mcp_llamada", extra={"key": caller.key_id, "tool": report.tool, "ok": report.ok, "ms": report.ms, "error": report.error})
