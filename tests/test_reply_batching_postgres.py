"""Esperar a que el cliente termine de escribir, contra un PostgreSQL de verdad (`TEST_POSTGRES_URL`, como `test_memory_postgres.py`).

En la nube, cada mensaje del cliente lo procesa su propia función, quizá en otro servidor, y varias pueden reclamar a la vez los
mensajes pendientes de un chat. La base decide: cada mensaje lo reclama una sola. En SQLite eso no se puede probar (escribe uno a la
vez); aquí sí, con varios hilos que reclaman al mismo tiempo. También se aplica la migración 0022 como la aplica la nube.
"""
from __future__ import annotations

import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.domain.business_config.conversations import NewMessage
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.migrations import MIGRATIONS, run_sql_file

URL = os.getenv("TEST_POSTGRES_URL", "").strip()
pytestmark = pytest.mark.skipif(not URL, reason="requiere TEST_POSTGRES_URL (una base PostgreSQL vacía para pruebas)")
SCHEMA = Path(__file__).resolve().parents[1] / "project" / "docs" / "postgresql_schema.sql"
SLUG, PHONE = "espera_pruebas", "573001112233"


@pytest.fixture(scope="module")
def engine():
    database = create_engine(URL)
    with database.begin() as conn:
        if conn.execute(text("SELECT to_regclass('public.tenants')")).scalar() is None:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            conn.exec_driver_sql(SCHEMA.read_text(encoding="utf-8"))
    # Todas las migraciones, como las aplica la nube (se pueden repetir).
    for migration in MIGRATIONS:
        run_sql_file(database, migration)
    yield database
    database.dispose()


@pytest.fixture
def store(engine):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM conversations WHERE tenant_id IN (SELECT id FROM tenants WHERE slug = :slug)"), {"slug": SLUG})
        conn.execute(text("DELETE FROM tenants WHERE slug = :slug"), {"slug": SLUG})
        conn.execute(text("INSERT INTO tenants (slug, name, status) VALUES (:slug, 'Espera de pruebas', 'active')"), {"slug": SLUG})
    return ConversationStore(engine)


def _arrives(store: ConversationStore, text_: str, number: int):
    return store.append(SLUG, channel="whatsapp", contact_ref=PHONE, contact_name="Laura",
                        message=NewMessage("customer", text_, provider_message_id=f"MSG{number}"))


def test_many_processes_claiming_at_once_never_take_the_same_message(store):
    stored = [_arrives(store, text_, n) for n, text_ in enumerate(["Hola", "quiero el plan", "¿cuánto vale?"], start=1)]
    conversation, ids = stored[0].conversation_id, [item.entry_id for item in stored]
    start, results = threading.Barrier(8), []

    def claim():
        start.wait()
        results.append(store.claim(conversation, ids))

    workers = [threading.Thread(target=claim) for _ in range(8)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    claimed = [entry_id for result in results for entry_id in result]
    assert sorted(claimed) == sorted(ids)


def test_pending_messages_come_in_order_with_what_the_assistant_reads(store):
    first, second = _arrives(store, "Hola", 1), _arrives(store, "", 2)
    store.set_reading(first.entry_id, "Hola")
    since = datetime.now(timezone.utc) - timedelta(minutes=2)
    pending = store.pending_messages(first.conversation_id, since=since)
    assert [(item.entry_id, item.reads_as) for item in pending] == [(first.entry_id, "Hola"), (second.entry_id, None)]
    assert all(item.created_at.tzinfo is not None for item in pending)
    store.claim(first.conversation_id, [first.entry_id])
    assert [item.entry_id for item in store.pending_messages(first.conversation_id, since=since)] == [second.entry_id]
