"""
Phase 7B — UsageRepository tests.
All tests mock DBRepository and get_engine to exercise real logic without a live DB.
The conftest autouse fixture bypasses SaaSGuard for these tests automatically.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock, call, patch

import pytest

from app.infrastructure.persistence.usage_repository import UsageRepository

_MOCK_TENANT = {"id": "tenant-uuid-001", "slug": "test_tenant", "status": "active"}
_TODAY = datetime.now(timezone.utc).date()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_engine_begin(rows=None):
    """Engine whose .begin() context manager records execute() calls."""
    mock_conn = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_conn)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    engine = MagicMock()
    engine.begin.return_value = mock_ctx
    return engine, mock_conn


def _mock_engine_connect(row):
    """Engine whose .connect() context manager returns a fetchone row."""
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = row
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_conn)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    engine = MagicMock()
    engine.connect.return_value = mock_ctx
    return engine, mock_conn


def _usage_row(messages: int, ai_calls: int) -> MagicMock:
    row = MagicMock()
    row._mapping = {"messages_count": messages, "ai_calls": ai_calls}
    return row


# ---------------------------------------------------------------------------
# 1. increment() crea la fila inicial (ejecuta SQL con los valores correctos)
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.usage_repository.get_engine")
@patch("app.infrastructure.persistence.usage_repository.DBRepository")
def test_increment_creates_initial_row(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    engine, mock_conn = _mock_engine_begin()
    mock_get_engine.return_value = engine

    UsageRepository().increment("test_tenant", messages=1, ai_calls=0)

    mock_conn.execute.assert_called_once()
    call_kwargs = mock_conn.execute.call_args[0][1]
    assert call_kwargs["tenant_id"] == "tenant-uuid-001"
    assert call_kwargs["messages"] == 1
    assert call_kwargs["ai_calls"] == 0
    assert call_kwargs["date"] == _TODAY


# ---------------------------------------------------------------------------
# 2. increment() acumula con llamadas sucesivas
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.usage_repository.get_engine")
@patch("app.infrastructure.persistence.usage_repository.DBRepository")
def test_increment_accumulates(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    engine, mock_conn = _mock_engine_begin()
    mock_get_engine.return_value = engine

    repo = UsageRepository()
    repo.increment("test_tenant", messages=1)
    repo.increment("test_tenant", messages=1)

    assert mock_conn.execute.call_count == 2


# ---------------------------------------------------------------------------
# 3. increment() con tenant inexistente: no falla, no ejecuta SQL
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.usage_repository.get_engine")
@patch("app.infrastructure.persistence.usage_repository.DBRepository")
def test_increment_ignores_unknown_tenant(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = None
    engine, mock_conn = _mock_engine_begin()
    mock_get_engine.return_value = engine

    UsageRepository().increment("ghost_tenant")

    mock_conn.execute.assert_not_called()


# ---------------------------------------------------------------------------
# 4. get_usage() retorna ceros cuando no hay fila
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.usage_repository.get_engine")
@patch("app.infrastructure.persistence.usage_repository.DBRepository")
def test_get_usage_returns_zero_when_no_row(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    engine, _ = _mock_engine_connect(None)
    mock_get_engine.return_value = engine

    result = UsageRepository().get_usage("test_tenant")

    assert result == {"messages_count": 0, "ai_calls": 0}


# ---------------------------------------------------------------------------
# 5. get_usage() retorna valores correctos desde la fila
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.usage_repository.get_engine")
@patch("app.infrastructure.persistence.usage_repository.DBRepository")
def test_get_usage_returns_correct_values(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    engine, _ = _mock_engine_connect(_usage_row(42, 7))
    mock_get_engine.return_value = engine

    result = UsageRepository().get_usage("test_tenant")

    assert result == {"messages_count": 42, "ai_calls": 7}


# ---------------------------------------------------------------------------
# 6. can_send(max_messages=None) → siempre True (sin límite configurado)
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.usage_repository.get_engine")
@patch("app.infrastructure.persistence.usage_repository.DBRepository")
def test_can_send_no_limit_is_always_true(mock_db_cls, mock_get_engine):
    # No debe ni consultar la DB
    assert UsageRepository().can_send("test_tenant", max_messages=None) is True
    mock_get_engine.assert_not_called()


# ---------------------------------------------------------------------------
# 7. can_send() permite cuando el uso está bajo el límite
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.usage_repository.get_engine")
@patch("app.infrastructure.persistence.usage_repository.DBRepository")
def test_can_send_allows_below_limit(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    engine, _ = _mock_engine_connect(_usage_row(49, 0))
    mock_get_engine.return_value = engine

    assert UsageRepository().can_send("test_tenant", max_messages=50) is True


# ---------------------------------------------------------------------------
# 8. can_send() bloquea al alcanzar el límite
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.usage_repository.get_engine")
@patch("app.infrastructure.persistence.usage_repository.DBRepository")
def test_can_send_blocks_at_limit(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    engine, _ = _mock_engine_connect(_usage_row(50, 0))
    mock_get_engine.return_value = engine

    assert UsageRepository().can_send("test_tenant", max_messages=50) is False


# ---------------------------------------------------------------------------
# 9. can_send() bloquea cuando ya superó el límite
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.usage_repository.get_engine")
@patch("app.infrastructure.persistence.usage_repository.DBRepository")
def test_can_send_blocks_above_limit(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    engine, _ = _mock_engine_connect(_usage_row(100, 0))
    mock_get_engine.return_value = engine

    assert UsageRepository().can_send("test_tenant", max_messages=50) is False


# ---------------------------------------------------------------------------
# 10. get_usage() con tenant_slug vacío → ceros sin tocar DB
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.usage_repository.get_engine")
@patch("app.infrastructure.persistence.usage_repository.DBRepository")
def test_get_usage_empty_slug_returns_zero(mock_db_cls, mock_get_engine):
    result = UsageRepository().get_usage("")

    assert result == {"messages_count": 0, "ai_calls": 0}
    mock_get_engine.assert_not_called()
