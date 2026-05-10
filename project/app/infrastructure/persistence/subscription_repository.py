from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text

from app.infrastructure.db.connection import get_engine
from app.infrastructure.db.repository import DBRepository

_ALLOWED_STATUSES: frozenset[str] = frozenset({"active", "trialing"})


class SubscriptionRepository:
    def is_active(self, tenant_id: str) -> bool:
        normalized = str(tenant_id or "").strip().lower()
        if not normalized:
            return False

        tenant = DBRepository().get_tenant_by_key(normalized)
        if not tenant:
            return False

        engine = get_engine()
        with engine.connect() as conn:
            sub = conn.execute(
                text(
                    """
                    SELECT status, current_period_end
                    FROM subscriptions
                    WHERE tenant_id = :tenant_id
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                ),
                {"tenant_id": str(tenant.get("id") or "")}
            ).fetchone()

        if not sub:
            return False

        status = str(sub._mapping.get("status") or "").strip().lower()
        if status not in _ALLOWED_STATUSES:
            return False

        expires_at = sub._mapping.get("current_period_end")
        if not expires_at:
            return False

        return datetime.now(timezone.utc) <= expires_at.astimezone(timezone.utc)

    def get_plan_code(self, tenant_id: str) -> str | None:
        """Return the plan_code of the most recent subscription, or None."""
        normalized = str(tenant_id or "").strip().lower()
        if not normalized:
            return None

        tenant = DBRepository().get_tenant_by_key(normalized)
        if not tenant:
            return None

        engine = get_engine()
        with engine.connect() as conn:
            sub = conn.execute(
                text(
                    """
                    SELECT plan_code
                    FROM subscriptions
                    WHERE tenant_id = :tenant_id
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                ),
                {"tenant_id": str(tenant.get("id") or "")}
            ).fetchone()

        if not sub:
            return None

        raw = sub._mapping.get("plan_code")
        if raw is None:
            return None
        return str(raw).strip().lower() or None
