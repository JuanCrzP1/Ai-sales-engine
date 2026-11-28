"""El seguimiento contra un PostgreSQL de verdad (`TEST_POSTGRES_URL`, como `test_reply_batching_postgres.py`).

La migración 0024 se aplica como la aplica la nube (se puede repetir) y varias revisiones a la vez nunca toman el mismo seguimiento:
el cliente no recibe el mismo mensaje dos veces aunque haya varios servidores.
"""
from __future__ import annotations

import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text, update

from app.domain.business_config.conversations import NewMessage
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.migrations import MIGRATIONS, run_sql_file
from app.infrastructure.business_config.tables import conversation_entries, conversations

URL = os.getenv("TEST_POSTGRES_URL", "").strip()
pytestmark = pytest.mark.skipif(not URL, reason="requiere TEST_POSTGRES_URL (una base PostgreSQL vacía para pruebas)")
SCHEMA = Path(__file__).resolve().parents[1] / "project" / "docs" / "postgresql_schema.sql"
SLUG, PHONE = "seguimiento_pruebas", "573005556677"


@pytest.fixture(scope="module")
def engine():
    database = create_engine(URL)
    with database.begin() as conn:
        if conn.execute(text("SELECT to_regclass('public.tenants')")).scalar() is None:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            conn.exec_driver_sql(SCHEMA.read_text(encoding="utf-8"))
    # Todas las migraciones, dos veces: como las aplica la nube, se pueden repetir.
    for _ in range(2):
        for migration in MIGRATIONS:
            run_sql_file(database, migration)
    yield database
    database.dispose()


@pytest.fixture
def store(engine):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM conversations WHERE tenant_id IN (SELECT id FROM tenants WHERE slug = :slug)"), {"slug": SLUG})
        conn.execute(text("DELETE FROM tenants WHERE slug = :slug"), {"slug": SLUG})
        conn.execute(text("INSERT INTO tenants (slug, name, status) VALUES (:slug, 'Seguimiento de pruebas', 'active')"), {"slug": SLUG})
    return ConversationStore(engine)


def _quiet_chat(store: ConversationStore) -> str:
    chat = store.append(SLUG, channel="whatsapp", contact_ref=PHONE, contact_name="Laura", message=NewMessage("customer", "¿Cuánto vale?"))
    store.append(SLUG, channel="whatsapp", contact_ref=PHONE, contact_name=None, message=NewMessage("assistant", "Vale $20.000", status="sent"))
    key, start = store._key(chat.conversation_id), datetime.now(timezone.utc) - timedelta(hours=2)
    with store._engine.begin() as conn:
        conn.execute(update(conversation_entries).where(conversation_entries.c.conversation_id == key, conversation_entries.c.author == "customer").values(created_at=start))
        conn.execute(update(conversation_entries).where(conversation_entries.c.conversation_id == key, conversation_entries.c.author == "assistant").values(created_at=start + timedelta(minutes=1)))
        conn.execute(update(conversations).where(conversations.c.id == key).values(last_message_at=start + timedelta(minutes=1)))
    return chat.conversation_id


def test_many_sweeps_at_once_take_each_follow_up_only_once(store):
    chat = _quiet_chat(store)
    now = datetime.now(timezone.utc)
    [candidate] = [item for item in store.follow_up_candidates(active_since=now - timedelta(days=40), quiet_before=now) if item.id == chat]
    assert candidate.sent_since_last_message == 0
    start, results = threading.Barrier(8), []

    def claim():
        start.wait()
        results.append(store.claim_follow_up(candidate, 1))

    threads = [threading.Thread(target=claim) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(results) == [False] * 7 + [True]
    [after] = [item for item in store.follow_up_candidates(active_since=now - timedelta(days=40), quiet_before=now) if item.id == chat]
    assert after.sent_since_last_message == 1 and after.anchor == candidate.last_customer_at


def test_a_stopped_follow_up_is_kept_and_only_team_or_customer_can_stop_it(store):
    chat = _quiet_chat(store)
    store.stop_follow_up(chat, "customer")
    assert store.thread(chat)[0].follow_up_stopped_by == "customer"
    with store._engine.begin() as conn, pytest.raises(Exception):
        conn.execute(update(conversations).where(conversations.c.id == store._key(chat)).values(follow_up_stopped_by="robot"))
