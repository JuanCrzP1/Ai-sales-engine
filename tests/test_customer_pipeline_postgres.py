"""El tablero de Clientes contra un PostgreSQL de verdad (`TEST_POSTGRES_URL`, como `test_follow_up_postgres.py`).

La migración 0025 se aplica como la aplica la nube (se puede repetir): la etapa admite «no compró», y el tablero cuenta, lista y
mueve con las consultas reales de PostgreSQL (agrupar por etapa y sumar las ventas por moneda).
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text, update
from sqlalchemy.exc import IntegrityError

from app.domain.business_config.commerce import NewSale
from app.domain.business_config.conversations import NewMessage
from app.domain.business_config.pipeline import StageMove
from app.infrastructure.business_config.commerce_store import CommerceStore
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.migrations import MIGRATIONS, run_sql_file
from app.infrastructure.business_config.tables import conversations

URL = os.getenv("TEST_POSTGRES_URL", "").strip()
pytestmark = pytest.mark.skipif(not URL, reason="requiere TEST_POSTGRES_URL (una base PostgreSQL vacía para pruebas)")
SCHEMA = Path(__file__).resolve().parents[1] / "project" / "docs" / "postgresql_schema.sql"
SLUG = "tablero_pruebas"


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
def stores(engine):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM sales WHERE tenant_id IN (SELECT id FROM tenants WHERE slug = :slug)"), {"slug": SLUG})
        conn.execute(text("DELETE FROM conversations WHERE tenant_id IN (SELECT id FROM tenants WHERE slug = :slug)"), {"slug": SLUG})
        conn.execute(text("DELETE FROM tenants WHERE slug = :slug"), {"slug": SLUG})
        conn.execute(text("INSERT INTO tenants (slug, name, status) VALUES (:slug, 'Tablero de pruebas', 'active')"), {"slug": SLUG})
    return ConversationStore(engine), CommerceStore(engine)


def _chat(chats: ConversationStore, contact: str, name: str) -> str:
    return chats.append(SLUG, channel="whatsapp", contact_ref=contact, contact_name=name, message=NewMessage("customer", "Hola")).conversation_id


def test_the_board_counts_moves_and_adds_up_on_postgres(stores):
    chats, commerce = stores
    ana, beto, caro = (_chat(chats, f"57300{index}", name) for index, name in enumerate(("Ana", "Beto", "Caro")))
    lost = commerce.move_customer(SLUG, beto, StageMove.checked(stage="lost", reason="Le pareció caro"))
    assert (lost.stage, lost.lost_reason) == ("lost", "Le pareció caro")
    assert commerce.move_customer(SLUG, caro, StageMove.checked(stage="ready")).stage == "ready"
    with chats._engine.begin() as conn:
        conn.execute(update(conversations).where(conversations.c.id == chats._key(ana)).values(started_at=datetime.now(timezone.utc) - timedelta(days=2)))
    commerce.record_sale(SLUG, NewSale.checked(customer_name="Ana", description="Pedido", amount="40000", currency="COP", conversation_id=ana), created_by="pruebas")

    today = datetime.now(timezone.utc).date()
    board = commerce.pipeline(SLUG, today=today)
    assert {column.stage: column.count for column in board.columns} == {"new": 0, "interested": 0, "ready": 1, "payment": 0, "customer": 1, "lost": 1}
    assert [card.lost_reason for column in board.columns if column.stage == "lost" for card in column.customers] == ["Le pareció caro"]
    stats = board.stats
    assert (stats.open_count, stats.lost_count, stats.won_count, stats.won) == (1, 1, 1, {"COP": Decimal("40000.00")})
    assert stats.close_rate == pytest.approx(1 / 3) and stats.days_to_buy == 2.0
    assert [column.count for column in commerce.pipeline(SLUG, query="an", today=today).columns] == [0, 0, 0, 0, 1, 0]


def test_the_database_refuses_a_stage_that_does_not_exist(stores):
    chats, _commerce = stores
    ana = _chat(chats, "573001", "Ana")
    with pytest.raises(IntegrityError), chats._engine.begin() as conn:
        conn.execute(update(conversations).where(conversations.c.id == chats._key(ana)).values(stage="vip"))
