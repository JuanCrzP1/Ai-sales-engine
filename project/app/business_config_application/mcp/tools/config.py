"""La configuración del asistente de un negocio (área «Asistente IA»): verla, editarla por partes, revisar lo que cambia al
publicar, probar el asistente, publicar y volver atrás.

Usa el MISMO servicio que el panel (`BusinessConfigService`): cada guardado pasa por el contrato y crea una versión en borrador;
publicar comprueba que compila. Los datos de pago entran como `{"value": ...}` (con el permiso «Datos de pago») y nunca salen:
el agente solo ve si están puestos y su final enmascarado.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.business_config_application.access import BusinessAccess
from app.business_config_application.assistant_lab import AssistantLabService
from app.business_config_application.mcp.access import McpAccess, McpBusinesses
from app.business_config_application.mcp.tool import McpTool, obj, text
from app.business_config_application.mcp.tools.guide import SECTIONS
from app.business_config_application.service import BusinessConfigService
from app.domain.business_config.agent_edits import merged, with_new_payment_values
from app.domain.business_config.config_changes import config_changes
from app.domain.business_config.errors import AssistantUnavailableError, FieldIssue, InvalidFieldsError, VersionConflictError
from app.domain.business_config.key_permissions import SCOPE_CONFIG_READ, SCOPE_CONFIG_WRITE, SCOPE_PAYMENTS_WRITE

BUSINESS = {"business": text("Identificador del negocio (de list_businesses).")}
NEXT_AFTER_SAVE = "Guardado en BORRADOR: tus clientes aún no lo ven. Revisa con review_business_config y publica cuando la persona lo confirme."


def _document(config) -> dict[str, Any]:
    return config.model_dump(mode="json", exclude_none=True)


def config_tools(
    configs: BusinessConfigService,
    access: BusinessAccess,
    lab: AssistantLabService | None = None,
    before_test: Callable[[McpAccess, str], None] = lambda caller, business: None,
) -> list[McpTool]:
    businesses = McpBusinesses(access)

    def editable(caller: McpAccess, business: str):
        slug = businesses.require(caller, business)
        return slug, configs.get_editable(slug)

    def published_document(slug: str, summary) -> dict[str, Any] | None:
        return _document(configs.get_published(slug)) if summary.published_version is not None else None

    def get_config(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        slug, current = editable(caller, args["business"])
        summary = current.summary
        document = _document(current.stored.config) if current.stored else {}
        pending = bool(config_changes(published_document(slug, summary), document)) if summary.published_version is not None else None
        if args.get("section"):
            document = {key: document[key] for key in SECTIONS[args["section"]]["keys"] if key in document}
        return {
            "business": slug,
            "name": summary.name,
            "editing_version": current.stored.version.version if current.stored else None,
            "latest_version": summary.latest_version,
            "published_version": summary.published_version,
            "publication": "never" if summary.published_version is None else "pending" if pending else "published",
            # Solo si cada dato está puesto y su final enmascarado: nunca el valor.
            "payment_fields": {ref: {"status": state.status, "masked": state.masked} for ref, state in current.payment_fields.items()},
            "document": document,
        }

    def update(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        slug, current = editable(caller, args["business"])
        if args.get("base_version") is not None and args["base_version"] != current.summary.latest_version:
            raise VersionConflictError(f"{slug}: el negocio cambió desde la versión {args['base_version']}; vuelve a leerlo con get_business_config")
        base = _document(current.stored.config) if current.stored else {"tenant_slug": slug}
        document = merged(base, args["changes"])
        document["tenant_slug"] = slug
        document, values = with_new_payment_values(document)
        if values and not caller.has(SCOPE_PAYMENTS_WRITE):
            raise InvalidFieldsError("Esta clave no puede escribir datos de pago.", [FieldIssue("payments", "Pídele a la persona el permiso «Datos de pago» o que los escriba en el panel.")])
        saved = configs.save_changes(slug, document, payment_values=values, created_by=caller.author, expected_version=current.summary.latest_version)
        review = configs.review(slug)
        return {
            "business": slug,
            "saved_version": saved.version,
            "status": "borrador",
            "payment_values_saved": len(values),
            "warnings": [diagnostic.message for diagnostic in review.diagnostics],
            "next": NEXT_AFTER_SAVE,
        }

    def review(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        slug, current = editable(caller, args["business"])
        summary = current.summary
        report = configs.review(slug)
        document = _document(current.stored.config) if current.stored else {}
        changes = config_changes(published_document(slug, summary), document)
        problem = "Falta un dato de pago o no se puede leer: escríbelo de nuevo." if report.payment_data_missing else report.compile_problem
        return {
            "business": slug,
            "editing_version": report.version,
            "published_version": summary.published_version,
            "first_publication": summary.published_version is None,
            "can_publish": report.compiles,
            "blocking_problem": problem,
            "warnings": [diagnostic.message for diagnostic in report.diagnostics],
            "changes": changes,
            "how_to_present": "Muéstrale a la persona lo que cambia, en sus palabras, y pídele que confirme antes de publish_business_config.",
        }

    def test(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        slug = businesses.require(caller, args["business"])
        if lab is None:
            raise AssistantUnavailableError("probar el asistente no está disponible en este servidor")
        before_test(caller, slug)
        result = lab.talk(slug, message=args["message"], source=args.get("version") or "draft", session_id=args.get("conversation_id"))
        turn = result.turn
        return {
            "conversation_id": result.session_id,
            "version": result.version,
            "reply": turn.reply,
            "handoff": turn.handoff,
            "handoff_reason": turn.handoff_reason,
            "intent": turn.intent,
            "ai_answered": turn.ai_answered,
            "note": "Para seguir la misma conversación, manda el mismo conversation_id.",
        }

    def publish(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        slug, current = editable(caller, args["business"])
        version = args.get("version") or (current.stored.version.version if current.stored else None)
        if version is None:
            raise InvalidFieldsError("No hay nada que publicar.", [FieldIssue("version", "Guarda la configuración primero.")])
        configs.publish(slug, int(version))
        return {"business": slug, "published_version": int(version), "message": "Publicado: el asistente ya responde así a los clientes."}

    def rollback(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        slug = businesses.require(caller, args["business"])
        version = configs.rollback(slug)
        return {"business": slug, "published_version": version, "message": "Se volvió a publicar la versión anterior."}

    def versions(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        slug = businesses.require(caller, args["business"])
        return {"business": slug, "versions": [{"version": item.version, "status": item.status, "created_at": item.created_at, "created_by": item.created_by, "published_at": item.published_at} for item in configs.history(slug)]}

    def restore(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        slug = businesses.require(caller, args["business"])
        created = configs.restore_version(slug, int(args["version"]), created_by=caller.author)
        return {"business": slug, "saved_version": created.version, "status": "borrador", "next": NEXT_AFTER_SAVE}

    return [
        McpTool("get_business_config", "Ver la configuración", "La configuración que se edita de un negocio (el borrador; si no hay, lo publicado), entera o de una sección, con sus versiones y si hay cambios sin publicar. Los datos de pago solo dicen si están puestos.", SCOPE_CONFIG_READ, obj({**BUSINESS, "section": text("Solo una sección (opcional).", enum=list(SECTIONS))}, ("business",)), get_config, read_only=True),
        McpTool("review_business_config", "Revisar antes de publicar", "Si se puede publicar, qué falta o conviene revisar, y LO QUE CAMBIA frente a lo que reciben hoy los clientes. Úsala antes de publicar y muéstrasela a la persona.", SCOPE_CONFIG_READ, obj(BUSINESS, ("business",)), review, read_only=True),
        McpTool("list_versions", "Ver el historial de versiones", "Las versiones guardadas de la configuración: borradores, la publicada y las anteriores, con quién las guardó.", SCOPE_CONFIG_READ, obj(BUSINESS, ("business",)), versions, read_only=True),
        McpTool(
            "update_business_config",
            "Editar la configuración",
            "Cambia la configuración por partes y la guarda en BORRADOR (los clientes no la ven hasta publicar). `changes` es un objeto con las partes del documento a cambiar: los objetos se combinan clave por clave, una lista se reemplaza ENTERA y null quita el dato. Un dato de pago se escribe como {\"value\": \"...\"} (necesita el permiso «Datos de pago»). Si algo no cumple las reglas, NO se guarda nada y la respuesta dice qué corregir. Lee antes get_config_guide de la sección. Nunca inventes precios, datos de pago ni políticas.",
            SCOPE_CONFIG_WRITE,
            obj({**BUSINESS, "changes": {"type": "object", "description": "Las partes del documento a cambiar (por ejemplo {\"identity\": {\"brand_name\": \"...\"}})."}, "base_version": {"type": "integer", "description": "La latest_version que leíste (opcional): si alguien guardó después, no pisa su cambio."}}, ("business", "changes")),
            update,
        ),
        McpTool(
            "test_assistant",
            "Probar el asistente",
            "Le escribe al asistente como si fueras un cliente y devuelve su respuesta. Por defecto prueba el borrador; con version=published, lo que reciben hoy los clientes. Gasta la clave de IA del negocio y queda en Conversaciones como prueba.",
            SCOPE_CONFIG_WRITE,
            obj({**BUSINESS, "message": text("Lo que escribiría un cliente."), "version": text("draft (por defecto) o published.", enum=["draft", "published"]), "conversation_id": text("Para seguir una conversación de prueba (opcional).")}, ("business", "message")),
            test,
        ),
        McpTool("publish_business_config", "Publicar la configuración", "Publica la versión que se edita (o la indicada): desde el siguiente mensaje, el asistente responde así a los CLIENTES REALES. Pide confirmación a la persona antes, mostrándole lo que cambia (review_business_config).", SCOPE_CONFIG_WRITE, obj({**BUSINESS, "version": {"type": "integer", "description": "La versión a publicar (opcional: por defecto, la que se edita)."}}, ("business",)), publish, destructive=True),
        McpTool("rollback_business_config", "Volver a la versión publicada anterior", "Vuelve a publicar la versión que estaba publicada antes. Cambia lo que reciben los clientes: confírmalo con la persona.", SCOPE_CONFIG_WRITE, obj(BUSINESS, ("business",)), rollback, destructive=True),
        McpTool("restore_version", "Restaurar una versión", "Crea un borrador con el contenido de una versión anterior (de list_versions). No publica nada.", SCOPE_CONFIG_WRITE, obj({**BUSINESS, "version": {"type": "integer", "description": "La versión a restaurar."}}, ("business", "version")), restore),
    ]
