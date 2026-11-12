"""El protocolo MCP del servidor (JSON-RPC 2.0, sin estado: cada petición trae su clave).

Métodos: `initialize` (negocia la versión y da las instrucciones), `ping`, `tools/list` (solo las herramientas que la clave
permite) y `tools/call` (vuelve a comprobar el permiso y revisa los argumentos). Las notificaciones (`notifications/*`) no
responden.

Un error del negocio («ese plan no existe», «falta el precio») es un RESULTADO con `isError`: el agente lo lee y se corrige. Un
error del protocolo (método o argumentos) es un error JSON-RPC. Un error interno se informa sin detalles.
"""
from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from typing import Any

from app.business_config_application.mcp.access import McpAccess
from app.business_config_application.mcp.tool import McpTool, invalid_arguments
from app.domain.business_config.errors import BusinessConfigError, BusinessNotFoundError, InvalidDocumentError, InvalidFieldsError
from app.domain.business_config.validation_messages import validation_issues

logger = logging.getLogger("mcp")

SUPPORTED_PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
SERVER_INSTRUCTIONS = (
    "Servidor MCP de AI Sales Engine: asistentes de ventas con IA para negocios que venden por WhatsApp. Todo ocurre en los "
    "negocios de la cuenta dueña de la clave y solo con sus permisos. ANTES de cambiar algo lee la guía (read_platform_guide) y, "
    "para cada sección, su guía de campos (get_config_guide). Lee antes de escribir (get_business_config) y usa los ids que "
    "devuelve. Nunca inventes precios, datos de pago ni políticas: pídeselos a la persona. Lo que guardas queda en BORRADOR: tus "
    "clientes no lo ven hasta publicar. Antes de publicar, muestra a la persona lo que cambia (review_business_config) y pide su "
    "confirmación."
)

# Errores JSON-RPC.
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602


@dataclass(frozen=True)
class ToolCallReport:
    tool: str
    ok: bool
    ms: int
    error: str | None = None


def _error(message_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}


def _plain(value: Any) -> Any:
    """Lo que devuelve una herramienta, en JSON: dataclasses, fechas y tuplas incluidas."""
    if is_dataclass(value) and not isinstance(value, type):
        return _plain(asdict(value))
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_plain(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _result(value: Any) -> dict[str, Any]:
    plain = _plain(value)
    structured = plain if isinstance(plain, dict) else {"result": plain}
    return {"content": [{"type": "text", "text": json.dumps(plain, ensure_ascii=False, indent=2)}], "structuredContent": structured}


def _business_error(exc: BusinessConfigError) -> dict[str, Any]:
    """Un error del negocio, como resultado que el agente puede leer para corregirse (con los problemas por campo)."""
    issues: list[dict[str, str]] = []
    if isinstance(exc, InvalidDocumentError):
        issues = validation_issues(exc.errors, with_options=True)
        message = "La configuración tiene datos por corregir."
    elif isinstance(exc, BusinessNotFoundError):
        # Igual para uno que no existe y uno ajeno: no revela que existe.
        message = "Ese negocio no existe o esta clave no entra a él. Usa list_businesses."
    elif isinstance(exc, InvalidFieldsError):
        issues = [asdict(issue) for issue in exc.issues]
        message = str(exc)
    else:
        text = str(exc)
        message = text.split(": ", 1)[1] if ": " in text and " " not in text.split(": ", 1)[0] else text
        message = message[:1].upper() + message[1:]
    body = {"error": message, "issues": issues} if issues else {"error": message}
    return {"content": [{"type": "text", "text": json.dumps(body, ensure_ascii=False, indent=2)}], "structuredContent": body, "isError": True}


class McpProtocol:
    def __init__(
        self,
        tools: Sequence[McpTool],
        *,
        server_name: str = "ai-sales-engine",
        server_version: str = "1.0.0",
        on_tool_call: Callable[[McpAccess, ToolCallReport], None] = lambda access, report: None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        names = [tool.name for tool in tools]
        if len(names) != len(set(names)):
            raise ValueError("hay herramientas MCP con el mismo nombre")
        self._tools = {tool.name: tool for tool in tools}
        self._server = {"name": server_name, "version": server_version}
        self._on_tool_call = on_tool_call
        self._clock = clock

    @property
    def tools(self) -> list[McpTool]:
        return list(self._tools.values())

    def allowed(self, access: McpAccess) -> list[McpTool]:
        return [tool for tool in self._tools.values() if tool.scope is None or access.has(tool.scope)]

    def handle(self, message: Any, access: McpAccess) -> dict[str, Any] | None:
        """La respuesta a un mensaje JSON-RPC, o None si es una notificación."""
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            return _error(None, INVALID_REQUEST, "Petición JSON-RPC inválida.")
        method = message.get("method")
        if not isinstance(method, str):
            return _error(message.get("id"), INVALID_REQUEST, "Falta el método.")
        if "id" not in message:
            return None
        message_id = message["id"]
        params = message.get("params") if isinstance(message.get("params"), dict) else {}
        if method == "initialize":
            requested = params.get("protocolVersion")
            version = requested if requested in SUPPORTED_PROTOCOL_VERSIONS else SUPPORTED_PROTOCOL_VERSIONS[0]
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "protocolVersion": version,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": self._server,
                    "instructions": SERVER_INSTRUCTIONS,
                },
            }
        if method == "ping":
            return {"jsonrpc": "2.0", "id": message_id, "result": {}}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": message_id, "result": {"tools": [tool.listing() for tool in self.allowed(access)]}}
        if method == "tools/call":
            return self._call(message_id, params, access)
        return _error(message_id, METHOD_NOT_FOUND, f"Método no disponible: {method}.")

    def _call(self, message_id: Any, params: dict[str, Any], access: McpAccess) -> dict[str, Any]:
        tool = self._tools.get(params.get("name"))
        if tool is None:
            return _error(message_id, INVALID_PARAMS, f"Herramienta desconocida: {params.get('name')}.")
        if tool.scope is not None and not access.has(tool.scope):
            return _error(message_id, INVALID_PARAMS, f"La clave no tiene permiso para «{tool.name}». Pídele a la persona que lo dé en Integraciones → Claves de API.")
        args = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        problem = invalid_arguments(tool.input_schema, args)
        if problem:
            return _error(message_id, INVALID_PARAMS, problem)
        started = self._clock()
        try:
            value = tool.run(args, access)
        except BusinessConfigError as exc:
            self._report(access, tool, started, ok=False, error=type(exc).__name__)
            return {"jsonrpc": "2.0", "id": message_id, "result": _business_error(exc)}
        except Exception as exc:  # noqa: BLE001 — un fallo interno nunca llega al agente con detalles
            logger.exception("mcp_herramienta_fallo", extra={"tool": tool.name, "key": access.key_id})
            self._report(access, tool, started, ok=False, error=type(exc).__name__)
            text = "No se pudo completar. Inténtalo de nuevo en unos segundos."
            return {"jsonrpc": "2.0", "id": message_id, "result": {"content": [{"type": "text", "text": text}], "isError": True}}
        self._report(access, tool, started, ok=True)
        return {"jsonrpc": "2.0", "id": message_id, "result": _result(value)}

    def _report(self, access: McpAccess, tool: McpTool, started: float, *, ok: bool, error: str | None = None) -> None:
        report = ToolCallReport(tool.name, ok, int((self._clock() - started) * 1000), error)
        try:
            self._on_tool_call(access, report)
        except Exception:  # noqa: BLE001 — el registro nunca rompe la respuesta
            logger.exception("mcp_registro_fallo")
