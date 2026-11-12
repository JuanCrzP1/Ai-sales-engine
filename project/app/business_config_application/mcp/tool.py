"""Una herramienta del servidor MCP: lo que ve el agente (nombre, título, descripción y esquema de entrada), el permiso que exige y
cómo se ejecuta. `run` usa los MISMOS servicios que el panel: aquí no hay reglas de negocio.

Las pistas (`read_only`, `destructive`) le dicen al agente qué puede hacer sin preguntar: lo que solo lee, sin confirmar; lo que
cambia lo que reciben los clientes (publicar, volver atrás), siempre confirmando con la persona.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.business_config_application.mcp.access import McpAccess

ToolArgs = dict[str, Any]


@dataclass(frozen=True)
class McpTool:
    name: str
    title: str
    description: str
    # El permiso que exige; None si no toca datos de ningún negocio (la guía).
    scope: str | None
    input_schema: dict[str, Any]
    run: Callable[[ToolArgs, McpAccess], Any]
    read_only: bool = False
    destructive: bool = False

    def listing(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "inputSchema": self.input_schema,
            "annotations": {
                "title": self.title,
                "readOnlyHint": self.read_only,
                "destructiveHint": self.destructive,
                "idempotentHint": self.read_only,
                "openWorldHint": False,
            },
        }


def obj(properties: dict[str, dict[str, Any]], required: tuple[str, ...] = ()) -> dict[str, Any]:
    """El esquema de entrada de una herramienta: un objeto con sus propiedades."""
    schema: dict[str, Any] = {"type": "object", "properties": properties, "additionalProperties": False}
    if required:
        schema["required"] = list(required)
    return schema


def text(description: str, **extra: Any) -> dict[str, Any]:
    return {"type": "string", "description": description, **extra}


_TYPES: dict[str, Callable[[Any], bool]] = {
    "string": lambda value: isinstance(value, str),
    "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
    "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
    "boolean": lambda value: isinstance(value, bool),
    "object": lambda value: isinstance(value, dict),
    "array": lambda value: isinstance(value, list),
}


def invalid_arguments(schema: dict[str, Any], args: Any, path: str = "") -> str | None:
    """None si los argumentos cumplen el esquema; si no, por qué (para que el agente se corrija). Revisa tipos, obligatorios,
    opciones, propiedades desconocidas y los elementos de las listas."""
    expected = schema.get("type")
    where = f"«{path}»" if path else "Los argumentos"
    if expected and not _TYPES[expected](args):
        return f"{where} debe ser de tipo {expected}."
    if "enum" in schema and args not in schema["enum"]:
        return f"{where} debe ser uno de: {', '.join(map(str, schema['enum']))}."
    if expected == "object" and "properties" in schema:
        for name in schema.get("required", ()):
            if args.get(name) in (None, ""):
                return f"Falta «{f'{path}.{name}' if path else name}»."
        if schema.get("additionalProperties") is False:
            unknown = sorted(set(args) - set(schema["properties"]))
            if unknown:
                return f"No conozco {', '.join(f'«{name}»' for name in unknown)}. Usa: {', '.join(schema['properties'])}."
        for name, value in args.items():
            if value is None or name not in schema["properties"]:
                continue
            problem = invalid_arguments(schema["properties"][name], value, f"{path}.{name}" if path else name)
            if problem:
                return problem
    if expected == "array" and "items" in schema:
        for index, item in enumerate(args):
            problem = invalid_arguments(schema["items"], item, f"{path}[{index}]")
            if problem:
                return problem
    return None
