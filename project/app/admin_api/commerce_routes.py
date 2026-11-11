"""Rutas de clientes, ventas y reportes de cada negocio. Solo llegan a los negocios del usuario.

Los valores de dinero salen como texto con dos decimales (no se pierden centavos con números de punto flotante).
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field

from app.admin_api.errors import ApiError
from app.admin_api.routes import BusinessSlug, CurrentUser
from app.business_config_application.commerce import CommerceService
from app.domain.business_config.commerce import Customer, Report, ReportTotals, Sale, SaleError
from app.domain.business_config.errors import AssistantUnavailableError

router = APIRouter(prefix="/api/businesses/{slug}")


def _commerce(request: Request) -> CommerceService:
    service = getattr(request.app.state, "commerce", None)
    if service is None:
        raise AssistantUnavailableError("los clientes y las ventas no están disponibles en este servidor")
    return service


Commerce = Annotated[CommerceService, Depends(_commerce)]


class RecordSale(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    customer_name: str = Field(max_length=200)
    description: str = Field(max_length=400)
    amount: str = Field(max_length=20)
    currency: str = Field(max_length=3)
    conversation_id: str | None = Field(default=None, max_length=40)


def _money(values: dict) -> dict[str, str]:
    return {currency: f"{amount:.2f}" for currency, amount in sorted(values.items())}


def _iso(moment) -> str | None:
    return moment.isoformat().replace("+00:00", "Z") if moment else None


def customer_payload(item: Customer) -> dict[str, Any]:
    return {
        "conversation_id": item.conversation_id, "name": item.name, "contact": item.contact_ref, "channel": item.channel, "stage": item.stage,
        "first_contact_at": _iso(item.first_contact_at), "last_message_at": _iso(item.last_message_at), "message_count": item.message_count,
        "needs_human": item.needs_human, "purchases": item.purchases, "spent": _money(item.spent),
    }


def sale_payload(item: Sale) -> dict[str, Any]:
    return {
        "id": item.id, "customer_name": item.customer_name, "description": item.description, "amount": f"{item.amount:.2f}",
        "currency": item.currency, "status": item.status, "created_at": _iso(item.created_at), "created_by": item.created_by,
        "conversation_id": item.conversation_id,
    }


def _totals(totals: ReportTotals) -> dict[str, Any]:
    return {
        "conversations": totals.conversations, "customer_messages": totals.customer_messages, "assistant_messages": totals.assistant_messages,
        "agent_messages": totals.agent_messages, "handoffs": totals.handoffs, "sales": totals.sales, "revenue": _money(totals.revenue),
    }


def report_payload(report: Report) -> dict[str, Any]:
    return {
        "since": report.since.isoformat(), "until": report.until.isoformat(),
        "days": [
            {"day": day.day.isoformat(), "new_conversations": day.new_conversations, "customer_messages": day.customer_messages,
             "assistant_messages": day.assistant_messages, "agent_messages": day.agent_messages, "sales": day.sales}
            for day in report.days
        ],
        "totals": _totals(report.totals), "previous": _totals(report.previous), "funnel": report.funnel,
        "handoffs_by_reason": report.handoffs_by_reason, "ai_cost_usd": report.ai_cost_usd, "ai_replies": report.ai_replies,
    }


def _invalid(exc: SaleError) -> ApiError:
    return ApiError(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc), code="invalid", issues=[{"path": exc.field, "message": str(exc)}])


@router.get("/customers")
def customers(
    slug: BusinessSlug, user: CurrentUser, commerce: Commerce,
    stage: Annotated[str | None, Query(max_length=20)] = None, q: Annotated[str | None, Query(max_length=80)] = None,
) -> list[dict[str, Any]]:
    return [customer_payload(item) for item in commerce.customers(user, slug, stage=stage, query=q)]


@router.get("/sales")
def list_sales(slug: BusinessSlug, user: CurrentUser, commerce: Commerce, days: Annotated[int, Query(ge=1, le=366)] = 90) -> list[dict[str, Any]]:
    return [sale_payload(item) for item in commerce.sales(user, slug, days=days)]


@router.post("/sales", status_code=status.HTTP_201_CREATED)
def record_sale(slug: BusinessSlug, body: RecordSale, user: CurrentUser, commerce: Commerce) -> dict[str, Any]:
    try:
        return sale_payload(commerce.record_sale(user, slug, **body.model_dump()))
    except SaleError as exc:
        raise _invalid(exc) from None


@router.post("/sales/{sale_id}/cancel")
def cancel_sale(slug: BusinessSlug, sale_id: str, user: CurrentUser, commerce: Commerce) -> dict[str, Any]:
    try:
        return sale_payload(commerce.cancel_sale(user, slug, sale_id))
    except SaleError as exc:
        raise ApiError(status.HTTP_404_NOT_FOUND, str(exc), code="not_found") from None


@router.get("/reports")
def report(slug: BusinessSlug, user: CurrentUser, commerce: Commerce, days: Annotated[int, Query(ge=1, le=366)] = 30) -> dict[str, Any]:
    return report_payload(commerce.report(user, slug, days=days))
