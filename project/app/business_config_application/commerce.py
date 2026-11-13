"""Clientes, ventas y reportes del panel. Cada usuario solo llega a sus negocios (`BusinessAccess`)."""
from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta

from app.business_config_application.access import BusinessAccess
from app.business_config_application.ports import AIUsageStorage, CommerceStorage
from app.domain.business_config.access import Principal
from app.domain.business_config.commerce import MAX_REPORT_DAYS, STAGES, Customer, NewSale, Report, Sale
from app.domain.business_config.errors import FieldIssue, InvalidFieldsError
from app.domain.business_config.team import REPORTS

try:
    from zoneinfo import ZoneInfo

    _BOGOTA = ZoneInfo("America/Bogota")
except Exception:  # pragma: no cover - sin base de zonas horarias
    _BOGOTA = None


def _today() -> date:
    return datetime.now(_BOGOTA).date()


class CommerceService:
    def __init__(
        self, storage: CommerceStorage, access: BusinessAccess, usage: AIUsageStorage | None = None, *, today: Callable[[], date] = _today
    ) -> None:
        self._storage = storage
        self._access = access
        self._usage = usage
        self._today = today

    def customers(self, principal: Principal, business: str, *, stage: str | None = None, query: str | None = None) -> list[Customer]:
        self._access.require(principal, business)
        if stage is not None and stage not in STAGES:
            raise InvalidFieldsError("Revisa el filtro.", [FieldIssue("stage", "Esa etapa no existe.")])
        return self._storage.customers(business, stage=stage, query=query)

    def sales(self, principal: Principal, business: str, *, days: int = 90) -> list[Sale]:
        self._access.require(principal, business)
        return self._storage.sales(business, since=self._today() - timedelta(days=self._days(days) - 1))

    def record_sale(
        self, principal: Principal, business: str, *, customer_name: str, description: str, amount: object, currency: str,
        conversation_id: str | None = None, created_by: str | None = None,
    ) -> Sale:
        """`created_by`: quién la registró, si no es la persona misma (un agente con su clave)."""
        self._access.require(principal, business)
        sale = NewSale.checked(customer_name=customer_name, description=description, amount=amount, currency=currency, conversation_id=conversation_id)
        return self._storage.record_sale(business, sale, created_by=created_by or principal.label)

    def cancel_sale(self, principal: Principal, business: str, sale_id: str) -> Sale:
        self._access.require(principal, business, REPORTS)
        return self._storage.cancel_sale(business, sale_id)

    def report(self, principal: Principal, business: str, *, days: int = 30) -> Report:
        """Los últimos `days` días (hoy incluido), comparados con los `days` anteriores."""
        self._access.require(principal, business, REPORTS)
        span = self._days(days)
        until = self._today()
        since = until - timedelta(days=span - 1)
        daily, totals, funnel, reasons = self._storage.report_data(business, since=since, until=until)
        _, previous, _, _ = self._storage.report_data(business, since=since - timedelta(days=span), until=since - timedelta(days=1))
        usage = self._usage.summary(business, since=since) if self._usage is not None else None
        return Report(
            since=since, until=until, days=daily, totals=totals, previous=previous, funnel=funnel, handoffs_by_reason=reasons,
            ai_cost_usd=usage.cost_usd if usage else None, ai_replies=usage.replies if usage else 0,
        )

    @staticmethod
    def _days(days: int) -> int:
        return max(1, min(int(days), MAX_REPORT_DAYS))
