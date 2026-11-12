"""Los negocios de la cuenta (área «Negocios»): verlos, ver las plantillas y crear uno nuevo.

Crear exige una clave de todos los negocios: un negocio nuevo no está en una lista fija. Usa la MISMA creación que el panel: el
dueño es el de la clave y, con una plantilla, su primer borrador queda escrito (sin publicar).
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from app.business_config_application.access import BusinessAccess
from app.business_config_application.mcp.access import McpAccess, McpBusinesses
from app.business_config_application.mcp.tool import McpTool, obj, text
from app.business_config_application.service import BusinessConfigService
from app.domain.business_config.agent_edits import business_slug_for
from app.domain.business_config.errors import FieldIssue, InvalidFieldsError
from app.domain.business_config.key_permissions import SCOPE_BUSINESSES_CREATE, SCOPE_BUSINESSES_READ
from app.domain.business_config.records import BusinessSummary
from app.domain.business_config.templates import BusinessTemplate


def _summary(business: BusinessSummary) -> dict[str, Any]:
    return {
        "business": business.slug,
        "name": business.name,
        "latest_version": business.latest_version,
        "published_version": business.published_version,
        "status": "sin publicar" if business.published_version is None else "publicado",
    }


def business_tools(
    configs: BusinessConfigService,
    access: BusinessAccess,
    templates: Callable[[], Sequence[BusinessTemplate]],
    on_created: Callable[[McpAccess, str], None] = lambda caller, slug: None,
) -> list[McpTool]:
    businesses = McpBusinesses(access)

    def create(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        if caller.reach.kind != "all":
            raise InvalidFieldsError("Esta clave no puede crear negocios.", [FieldIssue("reach", "Para crear negocios, la clave debe entrar a todos los negocios de la cuenta.")])
        name = " ".join(str(args["name"]).split())
        document = None
        slug = business_slug_for(name, (business.slug for business in configs.list_businesses()))
        if args.get("template"):
            try:
                template = next(item for item in templates() if item.id == args["template"])
            except StopIteration:
                raise InvalidFieldsError("Esa plantilla no existe.", [FieldIssue("template", "Usa una de list_business_templates.")]) from None
            document = template.instantiate(slug, name)
        created = access.create_for(caller.principal, slug, name, document=document, created_by=caller.author)
        on_created(caller, created.slug)
        return {
            **_summary(created),
            "next": "Lee get_config_guide de cada sección, completa la configuración con update_business_config, revisa con "
            "review_business_config, prueba con test_assistant y publica cuando la persona lo confirme.",
        }

    return [
        McpTool(
            name="list_businesses",
            title="Listar negocios",
            description="Los negocios a los que entra esta clave, con su identificador (`business`, el que piden las demás herramientas) y si ya están publicados.",
            scope=SCOPE_BUSINESSES_READ,
            input_schema=obj({}),
            run=lambda args, caller: {"businesses": [_summary(item) for item in businesses.visible(caller)]},
            read_only=True,
        ),
        McpTool(
            name="list_business_templates",
            title="Ver plantillas de negocio",
            description="Las plantillas para empezar un negocio (restaurante, tienda, software, servicios con cita...). Traen ejemplos para reemplazar, nunca datos reales.",
            scope=SCOPE_BUSINESSES_READ,
            input_schema=obj({}),
            run=lambda args, caller: {"templates": [{"template": item.id, "title": item.title, "description": item.description} for item in templates()]},
            read_only=True,
        ),
        McpTool(
            name="create_business",
            title="Crear un negocio",
            description=(
                "Crea un negocio nuevo en la cuenta, vacío o desde una plantilla (list_business_templates). Queda en borrador: "
                "nada responde a clientes hasta publicar. Confirma el nombre con la persona antes de crearlo."
            ),
            scope=SCOPE_BUSINESSES_CREATE,
            input_schema=obj(
                {"name": text("Nombre comercial del negocio (hasta 80 caracteres)."), "template": text("Identificador de una plantilla (opcional).")},
                ("name",),
            ),
            run=create,
        ),
    ]
