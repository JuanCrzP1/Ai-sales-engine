"""Límites de uso: lo que gasta la clave de IA de un negocio tiene un techo por ventana de tiempo.

El contador vive en la base (`rate_limits`) porque en la nube cada petición puede caer en una instancia distinta; cada visita
es atómica y borra las ventanas viejas de su contador.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.business_config_application.usage_limits import MemoryUsageCounter, UsageGuard
from app.domain.business_config.access import Principal
from app.domain.business_config.errors import UsageLimitExceededError
from app.domain.business_config.usage_limits import PLAYGROUND_PER_BUSINESS, PLAYGROUND_PER_USER, UsageLimit
from app.infrastructure.business_config.database import create_business_config_engine, create_local_schema
from app.infrastructure.business_config.tables import rate_limits
from app.infrastructure.business_config.usage_store import UsageCounterStore

ROOT_DIR = Path(__file__).resolve().parents[1]
ANA = Principal(user_id="usuario-ana", email="ana@example.com")
START = datetime(2026, 11, 10, 15, 0, 0, tzinfo=timezone.utc)


class Clock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def store(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'limites.sqlite3').as_posix()}")
    create_local_schema(engine)
    yield engine, UsageCounterStore(engine)
    engine.dispose()


def test_the_store_counts_per_window_and_forgets_old_windows(store):
    engine, counter = store
    assert [counter.hit("playground_user:ana", START) for _ in range(3)] == [1, 2, 3]
    assert counter.hit("playground_user:beto", START) == 1
    later = START + timedelta(minutes=1)
    assert counter.hit("playground_user:ana", later) == 1
    with engine.connect() as conn:
        windows = conn.execute(select(rate_limits.c.bucket, rate_limits.c.window_start)).all()
    # La ventana vieja de Ana se borró al contar en la nueva; la de Beto sigue (se borra cuando Beto vuelva).
    assert {(row.bucket, row.window_start.replace(tzinfo=timezone.utc)) for row in windows} == {
        ("playground_user:ana", later),
        ("playground_user:beto", START),
    }


@pytest.mark.parametrize("make_counter", [MemoryUsageCounter, None], ids=["memoria", "base"])
def test_the_guard_stops_at_the_limit_and_says_when_to_come_back(store, make_counter):
    counter = make_counter() if make_counter else store[1]
    clock = Clock(START + timedelta(seconds=15))
    guard = UsageGuard(counter, clock=clock)
    limit = UsageLimit("prueba", limit=3, window_seconds=60)
    for _ in range(3):
        guard.spend(limit, "ana")
    with pytest.raises(UsageLimitExceededError) as error:
        guard.spend(limit, "ana")
    assert error.value.retry_after_seconds == 45
    guard.spend(limit, "beto")  # cada quien tiene su contador
    clock.now = START + timedelta(seconds=60)
    guard.spend(limit, "ana")  # ventana nueva


def test_a_business_has_its_own_ceiling_shared_by_its_whole_team():
    guard = UsageGuard(MemoryUsageCounter(), clock=Clock(START))
    team = [Principal(user_id=f"persona-{index}", email=None) for index in range(PLAYGROUND_PER_BUSINESS.limit // PLAYGROUND_PER_USER.limit + 1)]
    sent = 0
    with pytest.raises(UsageLimitExceededError):
        for person in team:
            for _ in range(PLAYGROUND_PER_USER.limit):
                guard.playground_message(person, "restaurant")
                sent += 1
    assert sent == PLAYGROUND_PER_BUSINESS.limit
    guard.playground_message(ANA, "otro_negocio")


def test_a_limit_needs_positive_values():
    with pytest.raises(ValueError):
        UsageLimit("roto", limit=0, window_seconds=60)


def test_the_migration_matches_the_table(store):
    sql = (ROOT_DIR / "project" / "db" / "migrations" / "0006_rate_limits.sql").read_text(encoding="utf-8")
    body = re.search(r"CREATE TABLE IF NOT EXISTS rate_limits \((.*?)\n\);", sql, re.S).group(1)
    columns = {match.group(1) for match in re.finditer(r"^\s+([a-z_]+)\s+[A-Z]+", body, re.M)} - {"primary"}
    assert columns == {column.name for column in rate_limits.columns}
    assert "PRIMARY KEY (bucket, window_start)" in sql
    engine, _counter = store
    with engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(rate_limits)).scalar_one() == 0
