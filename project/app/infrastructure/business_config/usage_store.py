"""Contadores de uso en la tabla `rate_limits` (implementa `UsageCounter`), compartidos por todas las instancias del servidor.

Cada visita es un `INSERT ... ON CONFLICT DO UPDATE` atómico en PostgreSQL y en SQLite. En la misma transacción se borran las
ventanas viejas de ese contador, así la tabla no crece.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, delete
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.engine import Engine

from app.infrastructure.business_config.tables import rate_limits


class UsageCounterStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._insert = postgresql.insert if engine.dialect.name == "postgresql" else sqlite.insert

    def hit(self, bucket: str, window_start: datetime) -> int:
        statement = self._insert(rate_limits).values(bucket=bucket, window_start=window_start, hits=1)
        statement = statement.on_conflict_do_update(
            index_elements=[rate_limits.c.bucket, rate_limits.c.window_start], set_={"hits": rate_limits.c.hits + 1}
        ).returning(rate_limits.c.hits)
        with self._engine.begin() as conn:
            conn.execute(delete(rate_limits).where(and_(rate_limits.c.bucket == bucket, rate_limits.c.window_start < window_start)))
            return int(conn.execute(statement).scalar_one())
