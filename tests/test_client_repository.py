"""
Phase 7C — ClientRepository tests.
All tests mock DBRepository and get_engine; no live DB required.
The conftest autouse fixture isolates these tests from the SaaS subscription layer.
"""
from __future__ import annotations

from unittest.mock import MagicMock, call, patch

from app.infrastructure.persistence.client_repository import ClientRepository

_MOCK_TENANT = {"id": "tenant-uuid-001", "slug": "test_tenant", "status": "active"}
_CLIENT_UUID = "client-uuid-abc"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_engine_begin(select_row=None, insert_row=None):
    """Engine whose .begin() supports one SELECT then optional INSERT/UPDATE."""
    mock_conn = MagicMock()

    # fetchone() returns select_row on first call, insert_row on second
    mock_conn.execute.return_value.fetchone.side_effect = [select_row, insert_row]

    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_conn)
    mock_ctx.__exit__ = MagicMock(return_value=False)

    engine = MagicMock()
    engine.begin.return_value = mock_ctx
    return engine, mock_conn


def _client_row(client_id: str, name: str | None = None) -> MagicMock:
    row = MagicMock()
    row._mapping = {"id": client_id, "name": name}
    return row


def _returning_row(client_id: str) -> MagicMock:
    row = MagicMock()
    row._mapping = {"id": client_id}
    return row


# ---------------------------------------------------------------------------
# 1. tenant_slug vacío → None
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.client_repository.get_engine")
@patch("app.infrastructure.persistence.client_repository.DBRepository")
def test_empty_tenant_slug_returns_none(mock_db_cls, mock_get_engine):
    result = ClientRepository().get_or_create("", "ext-001")
    assert result is None
    mock_get_engine.assert_not_called()


# ---------------------------------------------------------------------------
# 2. external_id vacío → None
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.client_repository.get_engine")
@patch("app.infrastructure.persistence.client_repository.DBRepository")
def test_empty_external_id_returns_none(mock_db_cls, mock_get_engine):
    result = ClientRepository().get_or_create("test_tenant", "")
    assert result is None
    mock_get_engine.assert_not_called()


# ---------------------------------------------------------------------------
# 3. tenant inexistente → None
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.client_repository.get_engine")
@patch("app.infrastructure.persistence.client_repository.DBRepository")
def test_unknown_tenant_returns_none(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = None
    result = ClientRepository().get_or_create("ghost", "ext-001")
    assert result is None
    mock_get_engine.assert_not_called()


# ---------------------------------------------------------------------------
# 4. cliente existente → retorna el mismo UUID
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.client_repository.get_engine")
@patch("app.infrastructure.persistence.client_repository.DBRepository")
def test_existing_client_returns_id(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    existing = _client_row(_CLIENT_UUID, name="Ana")
    engine, mock_conn = _mock_engine_begin(select_row=existing)
    mock_get_engine.return_value = engine

    result = ClientRepository().get_or_create("test_tenant", "ext-001")

    assert result == _CLIENT_UUID
    # Only the SELECT should have been called (no name change)
    assert mock_conn.execute.call_count == 1


# ---------------------------------------------------------------------------
# 5. cliente inexistente → inserta y retorna el UUID generado
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.client_repository.get_engine")
@patch("app.infrastructure.persistence.client_repository.DBRepository")
def test_new_client_is_inserted_and_id_returned(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    engine, mock_conn = _mock_engine_begin(
        select_row=None,
        insert_row=_returning_row(_CLIENT_UUID),
    )
    mock_get_engine.return_value = engine

    result = ClientRepository().get_or_create("test_tenant", "ext-new")

    assert result == _CLIENT_UUID
    # SELECT + INSERT
    assert mock_conn.execute.call_count == 2


# ---------------------------------------------------------------------------
# 6. nombre actualizado cuando cambia
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.client_repository.get_engine")
@patch("app.infrastructure.persistence.client_repository.DBRepository")
def test_name_is_updated_when_changed(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    existing = _client_row(_CLIENT_UUID, name="Ana")
    engine, mock_conn = _mock_engine_begin(select_row=existing)
    mock_get_engine.return_value = engine

    result = ClientRepository().get_or_create("test_tenant", "ext-001", name="Ana López")

    assert result == _CLIENT_UUID
    # SELECT + UPDATE
    assert mock_conn.execute.call_count == 2
    update_sql = str(mock_conn.execute.call_args_list[1][0][0])
    assert "UPDATE" in update_sql.upper()


# ---------------------------------------------------------------------------
# 7. nombre NO actualizado cuando no se envía
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.client_repository.get_engine")
@patch("app.infrastructure.persistence.client_repository.DBRepository")
def test_name_not_updated_when_not_provided(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    existing = _client_row(_CLIENT_UUID, name="Ana")
    engine, mock_conn = _mock_engine_begin(select_row=existing)
    mock_get_engine.return_value = engine

    result = ClientRepository().get_or_create("test_tenant", "ext-001")

    assert result == _CLIENT_UUID
    # Only SELECT, no UPDATE
    assert mock_conn.execute.call_count == 1


# ---------------------------------------------------------------------------
# 8. external_id se normaliza (strip) antes de buscar
# ---------------------------------------------------------------------------

@patch("app.infrastructure.persistence.client_repository.get_engine")
@patch("app.infrastructure.persistence.client_repository.DBRepository")
def test_external_id_is_stripped(mock_db_cls, mock_get_engine):
    mock_db_cls.return_value.get_tenant_by_key.return_value = _MOCK_TENANT
    engine, mock_conn = _mock_engine_begin(
        select_row=None,
        insert_row=_returning_row(_CLIENT_UUID),
    )
    mock_get_engine.return_value = engine

    ClientRepository().get_or_create("test_tenant", "  ext-whitespace  ")

    insert_params = mock_conn.execute.call_args_list[1][0][1]
    assert insert_params["external_id"] == "ext-whitespace"
