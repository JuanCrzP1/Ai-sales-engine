"""El consumo de inteligencia artificial de cada negocio, en la tabla `ai_usage` (implementa `AIUsageStorage`).

Cada respuesta suma a la fila de su negocio, día y modelo con un `INSERT ... ON CONFLICT DO UPDATE` atómico, en PostgreSQL y en
SQLite: varias instancias pueden responder a la vez sin perder cuentas.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.engine import Engine

from app.domain.business_config.ai_usage import AIUsage, AIUsageSummary, DailyAIUsage
from app.infrastructure.business_config.tables import ai_usage
from app.infrastructure.business_config.tenancy import tenant_of


class AIUsageStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._insert = postgresql.insert if engine.dialect.name == "postgresql" else sqlite.insert

    def add(self, tenant_slug: str, day: date, usage: AIUsage) -> None:
        with self._engine.begin() as conn:
            row = {
                "tenant_id": tenant_of(conn, tenant_slug).id,
                "day": day,
                "model": usage.model[:200],
                "replies": 1,
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "cost_usd": usage.cost_usd,
            }
            statement = self._insert(ai_usage).values(**row)
            added = statement.excluded
            conn.execute(
                statement.on_conflict_do_update(
                    index_elements=[ai_usage.c.tenant_id, ai_usage.c.day, ai_usage.c.model],
                    set_={
                        "replies": ai_usage.c.replies + 1,
                        "prompt_tokens": ai_usage.c.prompt_tokens + added.prompt_tokens,
                        "completion_tokens": ai_usage.c.completion_tokens + added.completion_tokens,
                        # Sin costo informado se conserva el acumulado; con costo, se suma.
                        "cost_usd": case(
                            (added.cost_usd.is_(None), ai_usage.c.cost_usd),
                            else_=func.coalesce(ai_usage.c.cost_usd, 0) + added.cost_usd,
                        ),
                    },
                )
            )

    def summary(self, tenant_slug: str, *, since: date) -> AIUsageSummary:
        query = (
            select(
                ai_usage.c.day,
                func.sum(ai_usage.c.replies).label("replies"),
                func.sum(ai_usage.c.prompt_tokens).label("prompt_tokens"),
                func.sum(ai_usage.c.completion_tokens).label("completion_tokens"),
                func.sum(ai_usage.c.cost_usd).label("cost_usd"),
            )
            .where(ai_usage.c.day >= since)
            .group_by(ai_usage.c.day)
            .order_by(ai_usage.c.day)
        )
        with self._engine.connect() as conn:
            tenant_id = tenant_of(conn, tenant_slug).id
            rows = conn.execute(query.where(ai_usage.c.tenant_id == tenant_id)).all()
        days = [DailyAIUsage(row.day, int(row.replies), int(row.prompt_tokens), int(row.completion_tokens)) for row in rows]
        costs = [float(row.cost_usd) for row in rows if row.cost_usd is not None]
        return AIUsageSummary(
            since=since,
            replies=sum(day.replies for day in days),
            prompt_tokens=sum(day.prompt_tokens for day in days),
            completion_tokens=sum(day.completion_tokens for day in days),
            cost_usd=round(sum(costs), 6) if costs else None,
            days=days,
        )
