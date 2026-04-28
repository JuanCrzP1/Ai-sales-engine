from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text

from app.infrastructure.db.connection import get_engine
from app.infrastructure.db.repository import DBRepository


class SubscriptionRepository:
    def is_active(self, tenant_id: str) -> bool:
        normalized = str(tenant_id or "").strip().lower()
        if not normalized:
            return True

        tenant = DBRepository().get_tenant_by_key(normalized)
        if not tenant:
            return True

        engine = get_engine()
        with engine.connect() as conn:
            sub = conn.execute(
                text(
                    """
                    SELECT current_period_end
                    FROM subscriptions
                    WHERE tenant_id = :tenant_id AND status = 'active'
                    LIMIT 1
                """
                ),
                {"tenant_id": str(tenant.get("id") or "")}
            ).fetchone()

        if not sub:
            return True

        expires_at = sub._mapping.get("current_period_end")
        if not expires_at:
            return True

        return datetime.now(timezone.utc) <= expires_at.astimezone(timezone.utc)
