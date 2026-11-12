"""Clientes, ventas y reportes (área «Clientes y ventas»): ver en qué etapa va cada cliente, las ventas y los reportes, y registrar o
anular una venta.

Usa el MISMO servicio que el panel (`CommerceService`). Una venta que registra un agente queda a su nombre («Agente «…» (dueño)»).
Una venta ligada a una conversación pasa a ese cliente a «cliente», igual que en el panel; la conversación debe ser del negocio.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from app.business_config_application.access import BusinessAccess
from app.business_config_application.commerce import CommerceService
from app.business_config_application.mcp.access import McpAccess, McpBusinesses
from app.business_config_application.mcp.tool import McpTool, obj, text
from app.domain.business_config.commerce import MAX_REPORT_DAYS, STAGES, Customer, ReportTotals, Sale, SaleError
from app.domain.business_config.errors import FieldIssue, InvalidFieldsError
from app.domain.business_config.key_permissions import SCOPE_SALES_READ, SCOPE_SALES_WRITE

BUSINESS = {"business": text("Identificador del negocio (de list_businesses).")}
STAGE_NAMES = {"new": "nuevo", "interested": "interesado", "ready": "listo para comprar", "payment": "pagando", "customer": "cliente"}
MAX_CUSTOMERS = 100


def _iso(moment: datetime | None) -> str | None:
    return moment.isoformat().replace("+00:00", "Z") if moment else None


def _money(values: dict[str, Decimal]) -> dict[str, str]:
    return {currency: f"{amount:.2f}" for currency, amount in sorted(values.items())}


def _customer(item: Customer) -> dict[str, Any]:
    return {
        "conversation_id": item.conversation_id,
        "name": item.name,
        "contact": item.contact_ref,
        "channel": item.channel,
        "stage": item.stage,
        "first_contact_at": _iso(item.first_contact_at),
        "last_message_at": _iso(item.last_message_at),
        "messages": item.message_count,
        "waiting_human": item.needs_human,
        "purchases": item.purchases,
        "spent": _money(item.spent),
    }


def _sale(item: Sale) -> dict[str, Any]:
    return {
        "sale_id": item.id,
        "customer_name": item.customer_name,
        "description": item.description,
        "amount": f"{item.amount:.2f}",
        "currency": item.currency,
        "status": item.status,
        "created_at": _iso(item.created_at),
        "created_by": item.created_by,
        "conversation_id": item.conversation_id,
    }


def _totals(totals: ReportTotals) -> dict[str, Any]:
    return {
        "conversations": totals.conversations,
        "customer_messages": totals.customer_messages,
        "assistant_messages": totals.assistant_messages,
        "team_messages": totals.agent_messages,
        "handoffs": totals.handoffs,
        "sales": totals.sales,
        "revenue": _money(totals.revenue),
    }


def _days(args: dict[str, Any], default: int) -> int:
    return max(1, min(int(args.get("days") or default), MAX_REPORT_DAYS))


def commerce_tools(commerce: CommerceService, access: BusinessAccess) -> list[McpTool]:
    businesses = McpBusinesses(access)

    def customers(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        slug = businesses.require(caller, args["business"])
        found = commerce.customers(caller.principal, slug, stage=args.get("stage"), query=args.get("query"))
        return {"business": slug, "customers": [_customer(item) for item in found[:MAX_CUSTOMERS]], "total": len(found), "stages": STAGE_NAMES}

    def sales(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        slug = businesses.require(caller, args["business"])
        days = _days(args, 90)
        return {"business": slug, "days": days, "sales": [_sale(item) for item in commerce.sales(caller.principal, slug, days=days)]}

    def report(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        slug = businesses.require(caller, args["business"])
        result = commerce.report(caller.principal, slug, days=_days(args, 30))
        return {
            "business": slug,
            "since": result.since.isoformat(),
            "until": result.until.isoformat(),
            "totals": _totals(result.totals),
            "previous_period": _totals(result.previous),
            "funnel": result.funnel,
            "handoffs_by_reason": result.handoffs_by_reason,
            "ai_replies": result.ai_replies,
            "ai_cost_usd": result.ai_cost_usd,
            "by_day": [
                {"day": day.day.isoformat(), "new_conversations": day.new_conversations, "customer_messages": day.customer_messages, "sales": day.sales}
                for day in result.days
            ],
            "note": "previous_period es el mismo número de días justo antes, para comparar.",
        }

    def record(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        slug = businesses.require(caller, args["business"])
        try:
            sale = commerce.record_sale(
                caller.principal, slug, customer_name=args["customer_name"], description=args["description"], amount=args["amount"],
                currency=args["currency"], conversation_id=args.get("conversation_id"), created_by=caller.author,
            )
        except SaleError as exc:
            raise InvalidFieldsError(str(exc), [FieldIssue(exc.field, str(exc))]) from None
        return {"business": slug, "sale": _sale(sale), "message": "Venta registrada: ya cuenta en los reportes."}

    def cancel(args: dict[str, Any], caller: McpAccess) -> dict[str, Any]:
        slug = businesses.require(caller, args["business"])
        try:
            sale = commerce.cancel_sale(caller.principal, slug, str(args["sale_id"]))
        except SaleError as exc:
            raise InvalidFieldsError(str(exc), [FieldIssue("sale_id", "Usa un sale_id de list_sales.")]) from None
        return {"business": slug, "sale": _sale(sale), "message": "Venta anulada: ya no cuenta en los reportes."}

    return [
        McpTool(
            "list_customers",
            "Ver los clientes",
            "Los clientes de un negocio (cada conversación es uno), con su etapa (nuevo → interesado → listo para comprar → pagando → cliente), si espera a una persona y lo que ha comprado. Filtra por etapa o busca por nombre o teléfono.",
            SCOPE_SALES_READ,
            obj({**BUSINESS, "stage": text("Solo de esta etapa (opcional).", enum=list(STAGES)), "query": text("Buscar por nombre o teléfono (opcional).")}, ("business",)),
            customers,
            read_only=True,
        ),
        McpTool(
            "list_sales",
            "Ver las ventas",
            "Las ventas registradas de un negocio en los últimos días (por defecto 90), confirmadas y anuladas, con quién las registró.",
            SCOPE_SALES_READ,
            obj({**BUSINESS, "days": {"type": "integer", "description": f"Cuántos días atrás (1 a {MAX_REPORT_DAYS})."}}, ("business",)),
            sales,
            read_only=True,
        ),
        McpTool(
            "get_report",
            "Ver el reporte",
            "Conversaciones, mensajes, pasos a una persona, ventas e ingresos de los últimos días (por defecto 30), comparados con el período anterior; el embudo de clientes por etapa y el costo de la IA.",
            SCOPE_SALES_READ,
            obj({**BUSINESS, "days": {"type": "integer", "description": f"Cuántos días (1 a {MAX_REPORT_DAYS}; por defecto 30)."}}, ("business",)),
            report,
            read_only=True,
        ),
        McpTool(
            "record_sale",
            "Registrar una venta",
            "Registra una venta que la persona CONFIRMÓ (nunca inventes montos ni la deduzcas de un chat sin preguntarle). Con conversation_id, ese cliente pasa a «cliente» y deja de esperar la verificación del pago. Queda a nombre de esta clave.",
            SCOPE_SALES_WRITE,
            obj({
                **BUSINESS,
                "customer_name": text("Nombre del cliente."),
                "description": text("Qué compró (hasta 200 caracteres)."),
                "amount": {"type": ["string", "number"], "description": "El valor, con punto decimal y sin separador de miles (por ejemplo 45000 o \"19.90\")."},
                "currency": text("Moneda de 3 letras (por ejemplo COP, USD, MXN)."),
                "conversation_id": text("La conversación de ese cliente (opcional; de list_conversations o list_customers)."),
            }, ("business", "customer_name", "description", "amount", "currency")),
            record,
        ),
        McpTool(
            "cancel_sale",
            "Anular una venta",
            "Anula una venta registrada (de list_sales): deja de contar en los reportes. Confírmalo con la persona antes.",
            SCOPE_SALES_WRITE,
            obj({**BUSINESS, "sale_id": text("El sale_id de list_sales.")}, ("business", "sale_id")),
            cancel,
            destructive=True,
        ),
    ]
