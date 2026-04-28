from __future__ import annotations

from app.infrastructure.db.repository import DBRepository


class UsageRepository:
    def increment(self, tenant_id: str) -> None:
        normalized = str(tenant_id or "").strip().lower()
        if not normalized:
            return

        DBRepository().get_tenant_by_key(normalized)

    def get_usage(self, tenant_id: str) -> int:
        normalized = str(tenant_id or "").strip().lower()
        if not normalized:
            return 0

        DBRepository().get_tenant_by_key(normalized)
        return 0

    def can_send(self, tenant_id: str) -> bool:
        normalized = str(tenant_id or "").strip().lower()
        if not normalized:
            return True

        DBRepository().get_tenant_by_key(normalized)
        return True
