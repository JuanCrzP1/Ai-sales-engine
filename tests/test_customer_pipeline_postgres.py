"""El tablero de Clientes y la ficha contra un PostgreSQL de verdad (`TEST_POSTGRES_URL`, como `test_follow_up_postgres.py`).

Las migraciones 0025 a 0029 se aplican como las aplica la nube (se pueden repetir): la etapa admite «no compró», el tablero cuenta,
lista y mueve con las consultas reales de PostgreSQL (agrupar por etapa y sumar por moneda), la ficha guarda el valor, las notas
y el historial, que se borran con la conversación, las etiquetas (0027) no se repiten y filtran el tablero, los recordatorios
(0028) salen por fecha y en la tarjeta, y avisan una sola vez al llegar su hora aunque dos revisiones corran a la vez (0029).
"""
from __future__ import annotations

import os
import threading
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, delete, func, select, text, update
from sqlalchemy.exc import IntegrityError

from app.domain.business_config.commerce import NewSale
from app.domain.business_config.conversations import NewMessage
from app.domain.business_config.customer_card import DealChange
from app.domain.business_config.reminders import NewReminder
from app.domain.business_config.pipeline import StageMove
from app.infrastructure.business_config import reminder_store
from app.infrastructure.business_config.commerce_store import CommerceStore
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.migrations import MIGRATIONS, run_sql_file
from app.infrastructure.business_config.notification_store import NotificationStore
from app.infrastructure.business_config.tables import conversations, customer_events, customer_notes, notifications

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


def test_the_card_keeps_value_notes_and_history_and_they_go_with_the_conversation(stores):
    chats, commerce = stores
    ana, beto = _chat(chats, "573001", "Ana"), _chat(chats, "573002", "Beto")
    commerce.update_customer_deal(SLUG, ana, DealChange.checked({"amount": "210000", "currency": "COP"}), by="pruebas")
    commerce.update_customer_deal(SLUG, beto, DealChange.checked({"amount": "45.5", "currency": "USD"}), by="pruebas")
    commerce.move_customer(SLUG, ana, StageMove.checked(stage="ready"), by="pruebas")
    note = commerce.add_customer_note(SLUG, ana, "Quiere factura.", author="pruebas")

    card = commerce.customer_card(SLUG, ana)
    assert (card.customer.deal_amount, card.customer.deal_currency, card.stage_since is not None) == (Decimal("210000.00"), "COP", True)
    assert [n.body for n in card.notes] == ["Quiere factura."] and note.author == "pruebas"
    assert [(e.kind, e.to_stage, e.detail, e.actor) for e in reversed(card.events)] == [("value", None, "COP 210.000", "pruebas"), ("stage", "ready", None, "pruebas")]

    board = commerce.pipeline(SLUG, today=datetime.now(timezone.utc).date())
    assert {column.stage: column.value for column in board.columns if column.value} == {"new": {"USD": Decimal("45.50")}, "ready": {"COP": Decimal("210000.00")}}
    assert board.stats.open_value == {"COP": Decimal("210000.00"), "USD": Decimal("45.50")}

    with chats._engine.begin() as conn:
        conn.execute(delete(conversations).where(conversations.c.id == chats._key(ana)))
        left = [conn.execute(select(func.count()).select_from(table).where(table.c.conversation_id == chats._key(ana))).scalar_one() for table in (customer_events, customer_notes)]
    assert left == [0, 0]


def test_labels_do_not_repeat_and_filter_the_board_on_postgres(stores):
    chats, commerce = stores
    ana, _beto = _chat(chats, "573001", "Ana"), _chat(chats, "573002", "Beto")
    vip = commerce.create_label(SLUG, "VIP", "violet", created_by="pruebas")
    with pytest.raises(IntegrityError), chats._engine.begin() as conn:  # la base tampoco deja dos que se lean igual
        conn.execute(text(
            "INSERT INTO customer_labels (id, tenant_id, name, name_key, color) "
            "SELECT uuid_generate_v4(), id, 'vip', 'vip', 'slate' FROM tenants WHERE slug = :slug"
        ), {"slug": SLUG})
    tagged = commerce.set_customer_labels(SLUG, ana, [vip.id])
    assert [(label.name, label.color) for label in tagged.labels] == [("VIP", "violet")]
    assert [(label.name, label.customers) for label in commerce.labels(SLUG)] == [("VIP", 1)]
    board = commerce.pipeline(SLUG, label=vip.id, today=datetime.now(timezone.utc).date())
    assert [column.count for column in board.columns] == [1, 0, 0, 0, 0, 0] and board.stats.open_count == 2
    assert [customer.name for customer in commerce.customers(SLUG, label=vip.id)] == ["Ana"]
    commerce.delete_label(SLUG, vip.id)
    assert commerce.customers(SLUG)[0].labels == () and commerce.labels(SLUG) == []


def test_reminders_go_by_date_and_show_on_the_card_on_postgres(stores):
    chats, commerce = stores
    ana = _chat(chats, "573001", "Ana")
    now = datetime.now(timezone.utc)
    later = NewReminder.checked(title="Enviar propuesta", due_at=(now + timedelta(days=2)).isoformat(), now=now)
    soon = NewReminder.checked(title="Llamar para cerrar", due_at=(now + timedelta(hours=2)).isoformat(), now=now)
    commerce.create_reminder(SLUG, ana, later, by_user=None, by="pruebas")
    first = commerce.create_reminder(SLUG, ana, soon, by_user=None, by="pruebas")
    assert [item.title for item in commerce.reminders(SLUG, done=False)] == ["Llamar para cerrar", "Enviar propuesta"]
    assert commerce.customers(SLUG)[0].next_reminder.title == "Llamar para cerrar"
    commerce.set_reminder_done(SLUG, first.id, True, by="pruebas")
    assert [item.title for item in commerce.reminders(SLUG, done=True)] == ["Llamar para cerrar"]
    assert commerce.customer_card(SLUG, ana).customer.next_reminder.title == "Enviar propuesta"


def test_a_due_reminder_alerts_once_even_with_two_checks_at_the_same_time_on_postgres(engine, stores):
    chats, commerce = stores
    ana = _chat(chats, "573001", "Ana")
    now = datetime.now(timezone.utc)
    for title in ("Llamar para cerrar", "Enviar propuesta"):
        commerce.create_reminder(SLUG, ana, NewReminder.checked(title=title, due_at=(now + timedelta(hours=1)).isoformat(), now=now), by_user=None, by="pruebas")
    # Dos revisiones a la vez (dos procesos de Vercel): cada recordatorio avisa una sola vez (0029).
    start, created = threading.Barrier(2), []

    def check() -> None:
        start.wait()
        created.extend(reminder_store.alert_due_reminders(engine, now=now + timedelta(hours=2)))

    workers = [threading.Thread(target=check) for _ in range(2)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    assert len(created) == 2 and reminder_store.alert_due_reminders(engine, now=now + timedelta(hours=3)) == []
    # Sin responsable: el aviso es para todo el equipo, y la campana de cualquiera de sus personas lo trae.
    items, unread = NotificationStore(engine).recent([SLUG], "alguien-del-equipo", limit=10)
    assert unread == 2 and {item.kind for item in items} == {"reminder"}
    with engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(notifications).where(notifications.c.recipient_id.is_not(None))).scalar_one() == 0

