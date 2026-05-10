"""
Phase 7A — SaaS subscription enforcement tests.
Policy: only 'active' and 'trialing' with a valid future current_period_end are allowed.
All other states (missing tenant, missing subscription, canceled, expired, suspended, past_due) are blocked.

Phase 8A — Plan limit enforcement tests.
Policy: each plan_code has a message limit; SaaSGuard enforces it via UsageRepository.can_send().

All tests patch DBRepository and get_engine directly to exercise the real is_active() logic.
The conftest autouse fixture does NOT apply to this file, so production code runs unmodified.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.persistence.subscription_repository import SubscriptionRepository
from app.application.pipeline.saas_guard import SaaSGuard, PLAN_LIMITS

_MOCK_TENANT = {"id": "tenant-uuid-001", "slug": "test_tenant", "status": "active"}


def _sub_row(status: str, expires_in_days: int = 30) -> MagicMock:
    row = MagicMock()
    row._mapping = {
        "status": status,
        "current_period_end": datetime.now(timezone.utc) + timedelta(days=expires_in_days),
    }
    return row


def _mock_engine(sub_row) -> MagicMock:
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = sub_row

    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_conn)
    mock_ctx.__exit__ = MagicMock(return_value=False)

    engine = MagicMock()
    engine.connect.return_value = mock_ctx
    return engine


# ---------------------------------------------------------------------------
# 1. tenant inexistente → bloqueado
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.subscription_repository.get_engine")
@patch("app.infrastructure.persistence.subscription_repository.DBRepository")
def test_unknown_tenant_is_blocked(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = None
    assert SubscriptionRepository().is_active("nonexistent") is False


# ---------------------------------------------------------------------------
# 2. tenant_id vacío → bloqueado (sin llegar a DB)
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.subscription_repository.get_engine")
@patch("app.infrastructure.persistence.subscription_repository.DBRepository")
def test_empty_tenant_id_is_blocked(mock_db_cls, mock_get_engine):
    repo = SubscriptionRepository()
    assert repo.is_active("") is False
    assert repo.is_active("   ") is False


# ---------------------------------------------------------------------------
# 3. tenant existe pero sin fila en subscriptions → bloqueado
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.subscription_repository.get_engine")
@patch("app.infrastructure.persistence.subscription_repository.DBRepository")
def test_no_subscription_row_is_blocked(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    mock_get_engine.return_value = _mock_engine(None)
    assert SubscriptionRepository().is_active("test_tenant") is False


# ---------------------------------------------------------------------------
# 4. status = active → permitido
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.subscription_repository.get_engine")
@patch("app.infrastructure.persistence.subscription_repository.DBRepository")
def test_active_status_is_allowed(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    mock_get_engine.return_value = _mock_engine(_sub_row("active"))
    assert SubscriptionRepository().is_active("test_tenant") is True


# ---------------------------------------------------------------------------
# 5. status = trialing → permitido
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.subscription_repository.get_engine")
@patch("app.infrastructure.persistence.subscription_repository.DBRepository")
def test_trialing_status_is_allowed(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    mock_get_engine.return_value = _mock_engine(_sub_row("trialing"))
    assert SubscriptionRepository().is_active("test_tenant") is True


# ---------------------------------------------------------------------------
# 6. status = canceled → bloqueado
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.subscription_repository.get_engine")
@patch("app.infrastructure.persistence.subscription_repository.DBRepository")
def test_canceled_status_is_blocked(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    mock_get_engine.return_value = _mock_engine(_sub_row("canceled"))
    assert SubscriptionRepository().is_active("test_tenant") is False


# ---------------------------------------------------------------------------
# 7. status = expired → bloqueado
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.subscription_repository.get_engine")
@patch("app.infrastructure.persistence.subscription_repository.DBRepository")
def test_expired_status_is_blocked(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    mock_get_engine.return_value = _mock_engine(_sub_row("expired"))
    assert SubscriptionRepository().is_active("test_tenant") is False


# ---------------------------------------------------------------------------
# 8. status = suspended → bloqueado
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.subscription_repository.get_engine")
@patch("app.infrastructure.persistence.subscription_repository.DBRepository")
def test_suspended_status_is_blocked(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    mock_get_engine.return_value = _mock_engine(_sub_row("suspended"))
    assert SubscriptionRepository().is_active("test_tenant") is False


# ---------------------------------------------------------------------------
# 9. status = past_due → bloqueado
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.subscription_repository.get_engine")
@patch("app.infrastructure.persistence.subscription_repository.DBRepository")
def test_past_due_status_is_blocked(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    mock_get_engine.return_value = _mock_engine(_sub_row("past_due"))
    assert SubscriptionRepository().is_active("test_tenant") is False


# ---------------------------------------------------------------------------
# 10. active con current_period_end en el futuro → permitido
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.subscription_repository.get_engine")
@patch("app.infrastructure.persistence.subscription_repository.DBRepository")
def test_active_with_future_expiry_is_allowed(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    mock_get_engine.return_value = _mock_engine(_sub_row("active", expires_in_days=30))
    assert SubscriptionRepository().is_active("test_tenant") is True


# ---------------------------------------------------------------------------
# 11. active con current_period_end ya expirado → bloqueado
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.subscription_repository.get_engine")
@patch("app.infrastructure.persistence.subscription_repository.DBRepository")
def test_active_with_expired_period_end_is_blocked(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    expired_row = MagicMock()
    expired_row._mapping = {
        "status": "active",
        "current_period_end": datetime.now(timezone.utc) - timedelta(days=1),
    }
    mock_get_engine.return_value = _mock_engine(expired_row)
    assert SubscriptionRepository().is_active("test_tenant") is False


# ---------------------------------------------------------------------------
# 12. active con current_period_end = None → bloqueado
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.subscription_repository.get_engine")
@patch("app.infrastructure.persistence.subscription_repository.DBRepository")
def test_active_with_null_period_end_is_blocked(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    null_row = MagicMock()
    null_row._mapping = {"status": "active", "current_period_end": None}
    mock_get_engine.return_value = _mock_engine(null_row)
    assert SubscriptionRepository().is_active("test_tenant") is False


# ===========================================================================
# Phase 8A — Plan limit enforcement via SaaSGuard
# ===========================================================================

def _make_sub_repo(is_active=True, plan_code="starter"):
    repo = MagicMock()
    repo.is_active.return_value = is_active
    repo.get_plan_code.return_value = plan_code
    return repo


def _make_usage_repo(can_send=True):
    repo = MagicMock()
    repo.can_send.return_value = can_send
    return repo


# ---------------------------------------------------------------------------
# 13. starter bajo el límite → permite
# ---------------------------------------------------------------------------

def test_starter_below_limit_allows():
    sub_repo = _make_sub_repo(plan_code="starter")
    usage_repo = _make_usage_repo(can_send=True)
    guard = SaaSGuard(subscription_repo=sub_repo, usage_repo=usage_repo)
    allowed, reason = guard.check_access("test_tenant")
    assert allowed is True
    assert reason is None
    usage_repo.can_send.assert_called_once_with("test_tenant", max_messages=PLAN_LIMITS["starter"])


# ---------------------------------------------------------------------------
# 14. starter en el límite → bloquea con metadata correcta
# ---------------------------------------------------------------------------

def test_starter_at_limit_blocks_with_metadata():
    sub_repo = _make_sub_repo(plan_code="starter")
    usage_repo = _make_usage_repo(can_send=False)
    guard = SaaSGuard(subscription_repo=sub_repo, usage_repo=usage_repo)
    allowed, reason = guard.check_access("test_tenant")
    assert allowed is False
    assert isinstance(reason, dict)
    assert reason["source"] == "saas_guard_limit_reached"
    assert reason["plan_code"] == "starter"
    assert reason["limit"] == PLAN_LIMITS["starter"]


# ---------------------------------------------------------------------------
# 15. pro bajo el límite → permite
# ---------------------------------------------------------------------------

def test_pro_below_limit_allows():
    sub_repo = _make_sub_repo(plan_code="pro")
    usage_repo = _make_usage_repo(can_send=True)
    guard = SaaSGuard(subscription_repo=sub_repo, usage_repo=usage_repo)
    allowed, reason = guard.check_access("test_tenant")
    assert allowed is True
    usage_repo.can_send.assert_called_once_with("test_tenant", max_messages=PLAN_LIMITS["pro"])


# ---------------------------------------------------------------------------
# 16. enterprise → siempre permite (None = sin límite)
# ---------------------------------------------------------------------------

def test_enterprise_always_allows():
    sub_repo = _make_sub_repo(plan_code="enterprise")
    usage_repo = _make_usage_repo(can_send=True)
    guard = SaaSGuard(subscription_repo=sub_repo, usage_repo=usage_repo)
    allowed, reason = guard.check_access("test_tenant")
    assert allowed is True
    usage_repo.can_send.assert_called_once_with("test_tenant", max_messages=None)


# ---------------------------------------------------------------------------
# 17. plan desconocido → sin límite, permite
# ---------------------------------------------------------------------------

def test_unknown_plan_allows():
    sub_repo = _make_sub_repo(plan_code="ultra_custom_plan")
    usage_repo = _make_usage_repo(can_send=True)
    guard = SaaSGuard(subscription_repo=sub_repo, usage_repo=usage_repo)
    allowed, reason = guard.check_access("test_tenant")
    assert allowed is True
    usage_repo.can_send.assert_called_once_with("test_tenant", max_messages=None)


# ---------------------------------------------------------------------------
# 18. metadata correcta cuando se bloquea (verificación completa)
# ---------------------------------------------------------------------------

def test_metadata_complete_when_blocked():
    sub_repo = _make_sub_repo(plan_code="pro")
    usage_repo = _make_usage_repo(can_send=False)
    guard = SaaSGuard(subscription_repo=sub_repo, usage_repo=usage_repo)
    allowed, reason = guard.check_access("test_tenant")
    assert allowed is False
    assert reason == {
        "source": "saas_guard_limit_reached",
        "plan_code": "pro",
        "limit": 10000,
    }
    # increment must NOT be called when blocked
    usage_repo.increment.assert_not_called()


# ---------------------------------------------------------------------------
# 19. get_plan_code() retorna el valor esperado
# ---------------------------------------------------------------------------

def _plan_row(plan_code: str) -> MagicMock:
    row = MagicMock()
    row._mapping = {"plan_code": plan_code}
    return row


@patch("app.infrastructure.persistence.subscription_repository.get_engine")
@patch("app.infrastructure.persistence.subscription_repository.DBRepository")
def test_get_plan_code_returns_expected_value(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = _plan_row("pro")
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_conn)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    engine = MagicMock()
    engine.connect.return_value = mock_ctx
    mock_get_engine.return_value = engine
    result = SubscriptionRepository().get_plan_code("test_tenant")
    assert result == "pro"


@patch("app.infrastructure.persistence.subscription_repository.get_engine")
@patch("app.infrastructure.persistence.subscription_repository.DBRepository")
def test_get_plan_code_returns_none_for_unknown_tenant(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = None
    result = SubscriptionRepository().get_plan_code("nonexistent")
    assert result is None

