"""La documentación para el agente: la guía de la plataforma (qué es cada parte, las reglas y la receta para montar un negocio
completo) y la guía de campos de cada sección de la configuración, generada del MISMO contrato que valida al guardar (con un
ejemplo de una plantilla). No piden permiso: no tocan datos de ningún negocio.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from app.business_config_application.mcp.tool import McpTool, obj, text
from app.domain.business_config.templates import BusinessTemplate

# Las secciones del panel (Asistente IA) y las partes del documento que edita cada una.
SECTIONS: dict[str, dict[str, Any]] = {
    "negocio": {"title": "Mi negocio", "keys": ("identity",), "about": "Quién es el negocio, a qué se dedica, dónde está, su horario y por qué elegirlo."},
    "productos": {"title": "Productos y servicios", "keys": ("offer", "inventory", "fulfillment"), "about": "Lo que vende (planes o catálogo) con precios, existencias y cómo lo recibe el cliente (domicilio, envío, recogida, citas)."},
    "pagos": {"title": "Pagos y cierre", "keys": ("payments", "terms", "capabilities"), "about": "Cómo le pagan (enlace, Nequi, Daviplata, cuentas, Bre-B), promociones, políticas, condiciones y qué hace al cerrar una venta."},
    "atencion": {"title": "Cómo atiende", "keys": ("response_style", "knowledge", "sales", "escalation", "features"), "about": "Tono y largo de las respuestas, preguntas frecuentes, instrucciones, estrategia de venta y cuándo pasa el chat a una persona del equipo."},
    "mensajes": {"title": "Mensajes y canales", "keys": ("messages",), "about": "Bienvenida y lo que dice al recibir un pago, al pasar a una persona, fuera del horario, al retomar un chat y si la IA no puede responder."},
}


def _referenced_defs(node: Any, defs: dict[str, Any], found: dict[str, Any]) -> None:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/$defs/"):
            name = ref.rsplit("/", 1)[1]
            if name not in found and name in defs:
                found[name] = defs[name]
                _referenced_defs(defs[name], defs, found)
        for value in node.values():
            _referenced_defs(value, defs, found)
    elif isinstance(node, list):
        for value in node:
            _referenced_defs(value, defs, found)


def section_guide(section: str, schema: dict[str, Any], example: dict[str, Any] | None) -> dict[str, Any]:
    """Los campos de una sección (su esquema con las definiciones que usa) y un ejemplo de esas partes."""
    spec = SECTIONS[section]
    properties = {key: schema["properties"][key] for key in spec["keys"] if key in schema["properties"]}
    defs: dict[str, Any] = {}
    _referenced_defs(properties, schema.get("$defs", {}), defs)
    guide: dict[str, Any] = {
        "section": section,
        "title": spec["title"],
        "about": spec["about"],
        "document_keys": list(spec["keys"]),
        "schema": {"properties": properties, "$defs": defs},
        "how_to_edit": (
            "Cambia solo lo que quieras con update_business_config: los objetos se combinan clave por clave, una lista se "
            "reemplaza ENTERA (manda la lista completa) y null quita el dato. Los datos de pago se escriben como {\"value\": \"...\"} "
            "en el enlace o en el número, la cuenta o la referencia de un medio de pago."
        ),
    }
    if example:
        guide["example"] = {key: example[key] for key in spec["keys"] if key in example}
    return guide


def guide_tools(guide_text: Callable[[], str], schema: dict[str, Any], templates: Callable[[], Sequence[BusinessTemplate]]) -> list[McpTool]:
    def example() -> dict[str, Any] | None:
        available = list(templates())
        return available[0].instantiate("ejemplo", "Negocio de ejemplo") if available else None

    return [
        McpTool(
            name="read_platform_guide",
            title="Leer la guía de AI Sales Engine",
            description=(
                "Léela ANTES de actuar: qué es la plataforma, cómo se arma la configuración de un negocio, las reglas que no se "
                "pueden romper (no inventar precios ni datos de pago, borrador y publicar) y la receta paso a paso para montar un "
                "negocio completo."
            ),
            scope=None,
            input_schema=obj({}),
            run=lambda args, access: {"guide": guide_text()},
            read_only=True,
        ),
        McpTool(
            name="get_config_guide",
            title="Ver los campos de una sección",
            description=(
                "Los campos de una sección de la configuración (negocio, productos, pagos, atencion, mensajes): qué es cada uno, "
                "cuáles son obligatorios, sus opciones y un ejemplo completo. Úsala antes de escribir esa sección."
            ),
            scope=None,
            input_schema=obj({"section": text("La sección.", enum=list(SECTIONS))}, ("section",)),
            run=lambda args, access: section_guide(args["section"], schema, example()),
            read_only=True,
        ),
    ]
