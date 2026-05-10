"""
Phase 7D/7E — SQLMemoryRepository tests.
Tests exercise the PostgreSQL-backed methods via mocks of DBRepository,
ClientRepository, and get_engine.  The conftest autouse fixture isolates
these tests from the SaaS subscription layer.

Persistence guarantees tested here:
- save_message writes to conversation_messages
- get_history reads from conversation_messages (cross-instance)
- scalar memory fields are upserted into conversation_memory JSONB
- reset_conversation clears both tables
- role is preserved in save_message / get_history
- fallback to RAM when DB is unavailable
- DB errors are logged via _log_db_fallback (Phase 7E)
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.persistence.memory_repository import SQLMemoryRepository

_TENANT_SLUG = "test_tenant"
_USER_ID = "user_ext_001"
_TENANT_DB_ID = "tenant-db-uuid"
_CLIENT_DB_ID = "client-db-uuid"
_MOCK_TENANT = {"id": _TENANT_DB_ID, "slug": _TENANT_SLUG, "status": "active"}


# ---------------------------------------------------------------------------
# Patch helpers
# ---------------------------------------------------------------------------

def _patch_resolve(tenant_id=_TENANT_DB_ID, client_id=_CLIENT_DB_ID):
    """Patch _resolve_ids to return fixed UUIDs."""
    return patch.object(
        SQLMemoryRepository,
        "_resolve_ids",
        return_value=(tenant_id, client_id),
    )


def _make_engine_begin():
    mock_conn = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_conn)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    engine = MagicMock()
    engine.begin.return_value = mock_ctx
    return engine, mock_conn


def _make_engine_connect(rows=None):
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchall.return_value = rows or []
    mock_conn.execute.return_value.fetchone.return_value = rows[0] if rows else None
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_conn)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    engine = MagicMock()
    engine.connect.return_value = mock_ctx
    return engine, mock_conn


def _msg_row(role: str, content: str) -> MagicMock:
    row = MagicMock()
    row._mapping = {"role": role, "content": content}
    return row


def _mem_row(data: dict) -> MagicMock:
    row = MagicMock()
    row._mapping = {"memory": data}
    return row


# ---------------------------------------------------------------------------
# 1. save_message persiste en conversation_messages
# ---------------------------------------------------------------------------

def test_save_message_writes_to_db():
    with _patch_resolve():
        engine, mock_conn = _make_engine_begin()
        with patch.object(SQLMemoryRepository, "_engine", return_value=engine):
            repo = SQLMemoryRepository()
            repo.save_message(
                tenant_slug=_TENANT_SLUG,
                user_id=_USER_ID,
                message_text="hola mundo",
                role="user",
            )
            mock_conn.execute.assert_called_once()
            params = mock_conn.execute.call_args[0][1]
            assert params["content"] == "hola mundo"
            assert params["role"] == "user"
            assert params["tid"] == _TENANT_DB_ID
            assert params["cid"] == _CLIENT_DB_ID


# ---------------------------------------------------------------------------
# 2. get_history lee desde conversation_messages con orden ASC
# ---------------------------------------------------------------------------

def test_get_history_reads_from_db():
    rows = [_msg_row("user", "hola"), _msg_row("assistant", "buenas")]
    with _patch_resolve():
        engine, _ = _make_engine_connect(rows)
        with patch.object(SQLMemoryRepository, "_engine", return_value=engine):
            repo = SQLMemoryRepository()
            history = repo.get_history(tenant_slug=_TENANT_SLUG, user_id=_USER_ID)
            assert len(history) == 2
            assert history[0] == {"role": "user", "text": "hola"}
            assert history[1] == {"role": "assistant", "text": "buenas"}


# ---------------------------------------------------------------------------
# 3. persistencia cross-instancia: segunda instancia lee lo que guardó la primera
# ---------------------------------------------------------------------------

def test_cross_instance_persistence():
    """Simulates a server restart: new instance reads persisted messages."""
    rows = [_msg_row("user", "mensaje persistido")]
    with _patch_resolve():
        write_engine, _ = _make_engine_begin()
        read_engine, _ = _make_engine_connect(rows)

        with patch.object(SQLMemoryRepository, "_engine", side_effect=[write_engine, read_engine]):
            repo1 = SQLMemoryRepository()
            repo1.save_message(
                tenant_slug=_TENANT_SLUG,
                user_id=_USER_ID,
                message_text="mensaje persistido",
            )

            repo2 = SQLMemoryRepository()
            history = repo2.get_history(tenant_slug=_TENANT_SLUG, user_id=_USER_ID)

        assert any(m["text"] == "mensaje persistido" for m in history)


# ---------------------------------------------------------------------------
# 4. reset_conversation limpia ambas tablas
# ---------------------------------------------------------------------------

def test_reset_conversation_clears_db():
    with _patch_resolve():
        engine, mock_conn = _make_engine_begin()
        with patch.object(SQLMemoryRepository, "_engine", return_value=engine):
            repo = SQLMemoryRepository()
            repo.reset_conversation(tenant_slug=_TENANT_SLUG, user_id=_USER_ID)
            assert mock_conn.execute.call_count == 2  # DELETE + UPDATE


# ---------------------------------------------------------------------------
# 5. role se preserva en save_message y get_history
# ---------------------------------------------------------------------------

def test_role_preserved_in_history():
    rows = [_msg_row("assistant", "respuesta del bot")]
    with _patch_resolve():
        engine, _ = _make_engine_connect(rows)
        with patch.object(SQLMemoryRepository, "_engine", return_value=engine):
            repo = SQLMemoryRepository()
            history = repo.get_history(tenant_slug=_TENANT_SLUG, user_id=_USER_ID)
            assert history[0]["role"] == "assistant"


# ---------------------------------------------------------------------------
# 6. set_last_intent / get_last_intent persiste en JSONB
# ---------------------------------------------------------------------------

def test_last_intent_persisted_in_jsonb():
    with _patch_resolve():
        engine, mock_conn = _make_engine_begin()
        with patch.object(SQLMemoryRepository, "_engine", return_value=engine):
            repo = SQLMemoryRepository()
            repo.set_last_intent(tenant_slug=_TENANT_SLUG, user_id=_USER_ID, intent="buy")
            # Should have called upsert
            mock_conn.execute.assert_called()
            upsert_params = mock_conn.execute.call_args[0][1]
            blob = json.loads(upsert_params["blob"])
            assert blob.get("last_intent") == "buy"


# ---------------------------------------------------------------------------
# 7. get_last_intent desde DB cuando RAM está vacía (nueva instancia)
# ---------------------------------------------------------------------------

def test_get_last_intent_from_db_on_new_instance():
    mem_data = {"last_intent": "pain"}
    rows = [_mem_row(mem_data)]
    with _patch_resolve():
        engine, _ = _make_engine_connect(rows)
        with patch.object(SQLMemoryRepository, "_engine", return_value=engine):
            repo = SQLMemoryRepository()
            # RAM is empty for this new instance
            result = repo.get_last_intent(tenant_slug=_TENANT_SLUG, user_id=_USER_ID)
            assert result == "pain"


# ---------------------------------------------------------------------------
# 8. fallback a RAM cuando DB no está disponible
# ---------------------------------------------------------------------------

def test_fallback_to_ram_when_db_unavailable():
    with _patch_resolve():
        with patch.object(SQLMemoryRepository, "_engine", side_effect=Exception("no db")):
            repo = SQLMemoryRepository()
            repo.save_message(
                tenant_slug=_TENANT_SLUG,
                user_id=_USER_ID,
                message_text="fallback test",
            )
            # Should not raise; RAM contains the message
            history = repo.get_history(tenant_slug=_TENANT_SLUG, user_id=_USER_ID)
            assert any(m["text"] == "fallback test" for m in history)


# ---------------------------------------------------------------------------
# 9. API pública idéntica a MemoryRepository (contrato)
# ---------------------------------------------------------------------------

def test_public_api_contract():
    from app.infrastructure.persistence.memory_repository import MemoryRepository
    repo = SQLMemoryRepository()
    # Verify all public methods exist and have matching signatures
    for method in [
        "save_message", "get_history", "reset_conversation",
        "set_last_intent", "get_last_intent",
        "set_detected_intent", "get_detected_intent",
        "set_payment_method", "get_payment_method",
        "set_payment_status", "get_payment_status",
        "set_last_pain", "get_last_pain",
        "set_last_response", "get_last_response",
        "set_conversation_state", "get_conversation_state",
        "set_last_user_message_at", "get_last_user_message_at",
        "set_initial_message_last_sent_at", "get_initial_message_last_sent_at",
        "get_memory", "update_last_user_message_at", "update_initial_message_last_sent_at",
    ]:
        assert hasattr(repo, method), f"Missing method: {method}"


# ---------------------------------------------------------------------------
# 10. tenant inexistente: _resolve_ids devuelve None → no lanza excepción
# ---------------------------------------------------------------------------

def test_save_message_with_unknown_tenant_does_not_raise():
    with patch.object(SQLMemoryRepository, "_resolve_ids", return_value=None):
        with patch.object(SQLMemoryRepository, "_engine") as mock_engine:
            repo = SQLMemoryRepository()
            repo.save_message(
                tenant_slug="nonexistent",
                user_id="u",
                message_text="safe",
            )
            mock_engine.assert_not_called()


# ---------------------------------------------------------------------------
# 11. save_message registra el error cuando la DB falla (Phase 7E)
# ---------------------------------------------------------------------------

def test_save_message_logs_error_on_db_failure():
    with _patch_resolve():
        with patch.object(SQLMemoryRepository, "_engine", side_effect=RuntimeError("db down")):
            with patch.object(SQLMemoryRepository, "_log_db_fallback") as mock_log:
                repo = SQLMemoryRepository()
                repo.save_message(
                    tenant_slug=_TENANT_SLUG,
                    user_id=_USER_ID,
                    message_text="test",
                )
                mock_log.assert_called_once()
                call_args = mock_log.call_args[0]
                assert call_args[0] == "save_message"
                assert call_args[1] == _TENANT_SLUG
                assert call_args[2] == _USER_ID


# ---------------------------------------------------------------------------
# 12. get_history registra el error y retorna datos de RAM (Phase 7E)
# ---------------------------------------------------------------------------

def test_get_history_logs_error_on_db_failure():
    with _patch_resolve():
        with patch.object(SQLMemoryRepository, "_engine", side_effect=RuntimeError("db down")):
            with patch.object(SQLMemoryRepository, "_log_db_fallback") as mock_log:
                repo = SQLMemoryRepository()
                # Pre-load RAM with a message via parent
                repo.save_message(
                    tenant_slug=_TENANT_SLUG,
                    user_id=_USER_ID,
                    message_text="ram message",
                )
                # get_history will fail DB and fall back to RAM
                history = repo.get_history(tenant_slug=_TENANT_SLUG, user_id=_USER_ID)
                mock_log.assert_called()
                assert any(m["text"] == "ram message" for m in history)


# ---------------------------------------------------------------------------
# 13. set_last_intent registra el error y conserva el valor en RAM (Phase 7E)
# ---------------------------------------------------------------------------

def test_set_last_intent_logs_error_on_db_failure():
    with _patch_resolve():
        with patch.object(SQLMemoryRepository, "_engine", side_effect=RuntimeError("db down")):
            with patch.object(SQLMemoryRepository, "_log_db_fallback") as mock_log:
                repo = SQLMemoryRepository()
                repo.set_last_intent(
                    tenant_slug=_TENANT_SLUG,
                    user_id=_USER_ID,
                    intent="buy",
                )
                mock_log.assert_called()
                # Value persisted in RAM via super()
                ram_val = repo.get_last_intent(tenant_slug=_TENANT_SLUG, user_id=_USER_ID)
                assert ram_val == "buy"


# ===========================================================================
# Hotfix 8C — validación de SQL generado por _upsert_memory_key
# No debe contener ::jsonb (causa SyntaxError en psycopg3)
# ===========================================================================

def _capture_sql_calls(repo: SQLMemoryRepository, method: str, **kwargs) -> list[str]:
    """Invoke a method and return list of SQL strings passed to conn.execute."""
    sql_statements: list[str] = []
    engine, mock_conn = _make_engine_begin()

    original_execute = mock_conn.execute.side_effect

    def capture_execute(statement, *args, **kw):
        sql_statements.append(str(statement))
        m = MagicMock()
        return m

    mock_conn.execute.side_effect = capture_execute

    with patch.object(SQLMemoryRepository, "_engine", return_value=engine):
        getattr(repo, method)(**kwargs)

    return sql_statements


# ---------------------------------------------------------------------------
# 14. _upsert_memory_key no usa ::jsonb (hotfix psycopg3 compat)
# ---------------------------------------------------------------------------

def test_upsert_memory_key_uses_cast_not_pg_shorthand():
    """SQL generado no debe contener ::jsonb — incompatible con psycopg3."""
    with _patch_resolve():
        engine, mock_conn = _make_engine_begin()
        sql_seen: list[str] = []

        def capture(statement, *args, **kw):
            sql_seen.append(str(statement))
            return MagicMock()

        mock_conn.execute.side_effect = capture

        with patch.object(SQLMemoryRepository, "_engine", return_value=engine):
            repo = SQLMemoryRepository()
            repo.set_last_intent(tenant_slug=_TENANT_SLUG, user_id=_USER_ID, intent="close")

        upsert_sqls = [s for s in sql_seen if "conversation_memory" in s]
        assert upsert_sqls, "Expected at least one SQL targeting conversation_memory"
        for sql in upsert_sqls:
            assert "::jsonb" not in sql, f"Found forbidden ::jsonb cast in SQL: {sql}"
            assert "CAST(:blob AS JSONB)" in sql or "cast(:blob as jsonb)" in sql.lower(), (
                f"Expected CAST(:blob AS JSONB) in SQL: {sql}"
            )


# ---------------------------------------------------------------------------
# 15. múltiples claves de memoria no usan ::jsonb
# ---------------------------------------------------------------------------

def test_multiple_memory_keys_use_cast_syntax():
    """last_pain, conversation_state, last_user_message_at tampoco usan ::jsonb."""
    from datetime import datetime, timezone

    with _patch_resolve():
        engine, mock_conn = _make_engine_begin()
        sql_seen: list[str] = []

        def capture(statement, *args, **kw):
            sql_seen.append(str(statement))
            return MagicMock()

        mock_conn.execute.side_effect = capture

        with patch.object(SQLMemoryRepository, "_engine", return_value=engine):
            repo = SQLMemoryRepository()
            repo.set_last_pain(tenant_slug=_TENANT_SLUG, user_id=_USER_ID, pain="precio")
            repo.set_conversation_state(
                tenant_slug=_TENANT_SLUG,
                user_id=_USER_ID,
                state={"stage": "closing"},
            )
            repo.set_last_user_message_at(
                tenant_slug=_TENANT_SLUG,
                user_id=_USER_ID,
                sent_at=datetime.now(timezone.utc),
            )

        memory_sqls = [s for s in sql_seen if "conversation_memory" in s]
        assert memory_sqls, "Expected SQL targeting conversation_memory"
        for sql in memory_sqls:
            assert "::jsonb" not in sql, f"Found forbidden ::jsonb in SQL: {sql}"


# ---------------------------------------------------------------------------
# 16. blob enviado es JSON válido con la clave correcta
# ---------------------------------------------------------------------------

def test_upsert_blob_is_valid_json_with_correct_key():
    """El parámetro :blob enviado al SQL debe ser JSON válido con la clave esperada."""
    import json as _json

    with _patch_resolve():
        engine, mock_conn = _make_engine_begin()
        captured_params: list[dict] = []

        def capture(statement, params=None, *args, **kw):
            if params:
                captured_params.append(dict(params))
            return MagicMock()

        mock_conn.execute.side_effect = capture

        with patch.object(SQLMemoryRepository, "_engine", return_value=engine):
            repo = SQLMemoryRepository()
            repo.set_last_intent(tenant_slug=_TENANT_SLUG, user_id=_USER_ID, intent="pain")

        blob_params = [p for p in captured_params if "blob" in p]
        assert blob_params, "No blob parameter captured"
        for p in blob_params:
            parsed = _json.loads(p["blob"])
            assert "last_intent" in parsed, f"Expected 'last_intent' key in blob: {parsed}"
            assert parsed["last_intent"] == "pain"


# ===========================================================================
# Phase 9B — identity cache tests
# ===========================================================================

# ---------------------------------------------------------------------------
# 17. múltiples set_* para el mismo par (tenant, user) resuelven IDs una sola vez
# ---------------------------------------------------------------------------

def test_identity_cache_avoids_redundant_db_lookups():
    """After the first resolution, subsequent set_* calls for the same (tenant, user)
    must NOT hit DBRepository or ClientRepository again."""
    mock_db_instance = MagicMock()
    mock_db_instance.get_tenant_by_key.return_value = _MOCK_TENANT
    mock_cr_instance = MagicMock()
    mock_cr_instance.get_or_create.return_value = _CLIENT_DB_ID

    engine, mock_conn = _make_engine_begin()

    with patch("app.infrastructure.db.repository.DBRepository", return_value=mock_db_instance), \
         patch("app.infrastructure.persistence.client_repository.ClientRepository", return_value=mock_cr_instance), \
         patch.object(SQLMemoryRepository, "_engine", return_value=engine):
        repo = SQLMemoryRepository()
        repo.set_last_intent(tenant_slug=_TENANT_SLUG, user_id=_USER_ID, intent="buy")
        repo.set_detected_intent(tenant_slug=_TENANT_SLUG, user_id=_USER_ID, intent="close")
        repo.set_last_pain(tenant_slug=_TENANT_SLUG, user_id=_USER_ID, pain="precio")
        repo.set_payment_status(tenant_slug=_TENANT_SLUG, user_id=_USER_ID, status="none")

    assert mock_db_instance.get_tenant_by_key.call_count == 1, (
        f"Expected 1 tenant DB lookup, got {mock_db_instance.get_tenant_by_key.call_count}"
    )
    assert mock_cr_instance.get_or_create.call_count == 1, (
        f"Expected 1 client DB lookup, got {mock_cr_instance.get_or_create.call_count}"
    )


# ---------------------------------------------------------------------------
# 18. pares distintos tienen entradas de cache independientes
# ---------------------------------------------------------------------------

def test_identity_cache_is_isolated_per_user_pair():
    """Two distinct (tenant_slug, user_id) pairs each resolve once; a repeated
    call for the first pair uses the cache and does NOT issue additional DB queries."""
    mock_db_instance = MagicMock()
    mock_db_instance.get_tenant_by_key.return_value = _MOCK_TENANT
    mock_cr_instance = MagicMock()
    mock_cr_instance.get_or_create.side_effect = lambda tenant_slug, external_id: f"client-{external_id}"

    engine, mock_conn = _make_engine_begin()

    with patch("app.infrastructure.db.repository.DBRepository", return_value=mock_db_instance), \
         patch("app.infrastructure.persistence.client_repository.ClientRepository", return_value=mock_cr_instance), \
         patch.object(SQLMemoryRepository, "_engine", return_value=engine):
        repo = SQLMemoryRepository()
        repo.set_last_intent(tenant_slug=_TENANT_SLUG, user_id="user_a", intent="buy")
        repo.set_last_intent(tenant_slug=_TENANT_SLUG, user_id="user_b", intent="info")
        # Third call — same pair as first — should come from cache
        repo.set_last_intent(tenant_slug=_TENANT_SLUG, user_id="user_a", intent="close")

    # 2 distinct pairs → exactly 2 lookups, not 3
    assert mock_db_instance.get_tenant_by_key.call_count == 2, (
        f"Expected 2 tenant lookups (one per distinct user pair), "
        f"got {mock_db_instance.get_tenant_by_key.call_count}"
    )
    assert mock_cr_instance.get_or_create.call_count == 2, (
        f"Expected 2 client lookups (one per distinct user pair), "
        f"got {mock_cr_instance.get_or_create.call_count}"
    )

