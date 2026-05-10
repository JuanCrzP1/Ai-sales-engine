from __future__ import annotations

from datetime import date, timezone, datetime

from sqlalchemy import text

from app.infrastructure.db.connection import get_engine
from app.infrastructure.db.repository import DBRepository


class UsageRepository:
    def increment(self, tenant_slug: str, messages: int = 1, ai_calls: int = 0) -> None:
        """Upsert into usage_daily, accumulating messages and ai_calls for today (UTC)."""
        normalized = str(tenant_slug or "").strip().lower()
        if not normalized:
            return

        tenant = DBRepository().get_tenant_by_key(normalized)
        if not tenant:
            return

        today = datetime.now(timezone.utc).date()
        tenant_id = str(tenant.get("id") or "")

        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO usage_daily (tenant_id, date, messages_count, ai_calls)
                    VALUES (:tenant_id, :date, :messages, :ai_calls)
                    ON CONFLICT (tenant_id, date) DO UPDATE
                        SET messages_count = usage_daily.messages_count + EXCLUDED.messages_count,
                            ai_calls       = usage_daily.ai_calls       + EXCLUDED.ai_calls
                    """
                ),
                {
                    "tenant_id": tenant_id,
                    "date": today,
                    "messages": messages,
                    "ai_calls": ai_calls,
                },
            )

    def get_usage(self, tenant_slug: str) -> dict:
        """Return today's usage totals for the tenant, or zeros if no data."""
        normalized = str(tenant_slug or "").strip().lower()
        if not normalized:
            return {"messages_count": 0, "ai_calls": 0}

        tenant = DBRepository().get_tenant_by_key(normalized)
        if not tenant:
            return {"messages_count": 0, "ai_calls": 0}

        today = datetime.now(timezone.utc).date()
        tenant_id = str(tenant.get("id") or "")

        engine = get_engine()
        with engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT messages_count, ai_calls
                    FROM usage_daily
                    WHERE tenant_id = :tenant_id AND date = :date
                    LIMIT 1
                    """
                ),
                {"tenant_id": tenant_id, "date": today},
            ).fetchone()

        if not row:
            return {"messages_count": 0, "ai_calls": 0}

        return {
            "messages_count": int(row._mapping.get("messages_count") or 0),
            "ai_calls": int(row._mapping.get("ai_calls") or 0),
        }

    def can_send(self, tenant_slug: str, max_messages: int | None = None) -> bool:
        """Return True when no limit is configured or messages_count is below max_messages."""
        if max_messages is None:
            return True

        usage = self.get_usage(tenant_slug)
        return usage["messages_count"] < max_messages
