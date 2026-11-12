"""El Centro de ayuda para el agente: los MISMOS artículos que lee la persona en el panel. Sirven para responder «¿cómo hago…?»
con la forma real de hacerlo y para mandarla a la pantalla correcta. No piden permiso: no tocan datos de ningún negocio."""
from __future__ import annotations

from app.business_config_application.help import HelpService
from app.business_config_application.mcp.tool import McpTool, obj, text
from app.domain.business_config.help import MAX_QUERY, SEARCH_LIMIT


def help_tools(help_center: HelpService) -> list[McpTool]:
    return [
        McpTool(
            name="search_help",
            title="Buscar en el Centro de ayuda",
            description=(
                "Busca en el Centro de ayuda de la plataforma (lo mismo que ve la persona en el panel, en Ayuda): cómo se conecta "
                "WhatsApp, qué hace cada sección del asistente, la atención humana, las respuestas rápidas, las ventas, las "
                f"integraciones… Devuelve hasta {SEARCH_LIMIT} artículos con su resumen; lee el que sirva con read_help_article. "
                "Úsala cuando la persona pregunte cómo hacer algo o dónde está algo en el panel."
            ),
            scope=None,
            input_schema=obj({"query": text("Lo que se busca, en palabras de la persona («conectar whatsapp», «pausar la IA»).", maxLength=MAX_QUERY)}, ("query",)),
            run=lambda args, access: help_center.search(args["query"]),
            read_only=True,
        ),
        McpTool(
            name="read_help_article",
            title="Leer un artículo de ayuda",
            description=(
                "Un artículo del Centro de ayuda, completo y en Markdown, con sus artículos relacionados. Los enlaces «panel:ruta» "
                "son pantallas del panel (por ejemplo, panel:canales es Canales). Úsalo con el slug que devuelve search_help."
            ),
            scope=None,
            input_schema=obj({"slug": text("El slug del artículo, tal como lo devuelve search_help.", maxLength=80)}, ("slug",)),
            run=lambda args, access: help_center.read(args["slug"]),
            read_only=True,
        ),
    ]
