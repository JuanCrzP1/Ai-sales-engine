"""Eliminar chats: el panel borra la conversación con todo lo suyo, en la base y en la memoria del asistente.

- Un chat: sus mensajes, fotos y audios, sus avisos (con lo leído) y lo que el asistente recuerda de ese cliente. Las ventas
  registradas se conservan sin el enlace al chat: son la contabilidad del negocio.
- Si no se puede borrar la memoria del asistente, no se borra nada (y se puede intentar de nuevo).
- Los chats de «Probar asistente» se borran de una vez; los de clientes reales no se tocan.
- Nadie borra chats de un negocio ajeno: responde como si no existieran.
- En el motor, olvidar a un cliente borra su historial, su memoria comercial y su registro (contra un PostgreSQL de verdad, en
  `test_memory_postgres.py`).
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.pool import StaticPool

from app.admin_api.main import create_app
from app.business_config_application.access import BusinessAccess
from app.domain.business_config.access import Principal
from app.domain.business_config.commerce import NewSale
from app.domain.business_config.conversations import MediaFile, NewMessage
from app.infrastructure.business_config.commerce_store import CommerceStore
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.business_config.example_businesses import import_example, load_example
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.notification_store import NotificationStore
from app.infrastructure.business_config.tables import (
    business_members,
    conversation_entries,
    conversation_media,
    conversations,
    notification_reads,
    notifications,
    sales,
    tenants,
)
from app.infrastructure.business_config.usage_store import UsageCounterStore

ANA = Principal(user_id="usuario-ana", email="ana@example.com")
BETO = Principal(user_id="usuario-beto", email="beto@example.com")
TOKENS = {"token-de-ana": ANA, "token-de-beto": BETO}
PHONE = "573001112233"


class Tokens:
    def verify(self, token: str) -> Principal | None:
        return TOKENS.get(token)


class FakeMemory:
    """La memoria del asistente: registra a quién olvidó, o falla si la base del motor no responde."""

    def __init__(self) -> None:
        self.forgotten: list[tuple[str, str]] = []
        self.fail = False

    def forget(self, business_slug: str, contact_ref: str) -> None:
        from app.domain.business_config.errors import AssistantUnavailableError

        if self.fail:
            raise AssistantUnavailableError("No se pudo borrar lo que el asistente recuerda de este cliente, así que el chat no se eliminó")
        self.forgotten.append((business_slug, contact_ref))

    def forget_playground(self, business_slug: str, session_id: str | None = None) -> None:
        from app.domain.business_config.errors import AssistantUnavailableError

        if self.fail:
            raise AssistantUnavailableError("No se pudo borrar lo que el asistente recuerda de las pruebas, así que no se borraron")
        self.forgotten.append((business_slug, f"prueba:{session_id or '*'}"))


def _as(user: str) -> dict[str, str]:
    return {"Authorization": f"Bearer token-de-{user}"}


@pytest.fixture
def platform(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'plataforma.sqlite3').as_posix()}")
    create_local_schema(engine)
    service = build_business_config_service(engine, secrets_key=Fernet.generate_key().decode())
    for slug in ("restaurant", "saas"):
        import_example(service, load_example(slug))
    with engine.begin() as conn:
        ids = {row.slug: row.id for row in conn.execute(select(tenants.c.slug, tenants.c.id))}
        for slug, user in (("restaurant", ANA), ("saas", BETO)):
            conn.execute(business_members.insert().values(tenant_id=ids[slug], user_id=user.user_id, role="owner", created_at=datetime.now(timezone.utc)))
    store = ConversationStore(engine)
    memory = FakeMemory()
    app = create_app(
        service,
        access=BusinessAccess(service, BusinessMembersStore(engine)),
        verifier=Tokens(),
        conversations=store,
        notifications=NotificationStore(engine),
        usage=UsageCounterStore(engine),
        commerce=CommerceStore(engine),
        contact_memory=memory,
    )
    yield engine, store, memory, TestClient(app)
    engine.dispose()


def _whatsapp_chat(engine, store) -> str:
    """Un chat completo: mensajes, una foto, un paso a una persona con su aviso leído y una venta registrada."""
    conversation = store.record(
        "restaurant", channel="whatsapp", contact_ref=PHONE, contact_name="Laura",
        messages=[NewMessage("customer", "Quiero hablar con una persona")], handoff=True, handoff_reason="human_request",
    )
    store.append(
        "restaurant", channel="whatsapp", contact_ref=PHONE, contact_name="Laura",
        message=NewMessage("customer", "", kind="image", provider_message_id="WA-1"), media=MediaFile("image/jpeg", b"foto-del-comprobante"),
    )
    NotificationStore(engine).mark_read(["restaurant"], ANA.user_id)
    CommerceStore(engine).record_sale(
        "restaurant", NewSale("Laura", "Almuerzo para 4", Decimal("120000"), "COP", conversation_id=conversation), created_by=ANA.user_id
    )
    return conversation


def _count(engine, table, *where) -> int:
    with engine.connect() as conn:
        return conn.execute(select(func.count()).select_from(table).where(*where)).scalar_one()


# ---------------------------------------------------------------------------
# Un chat
# ---------------------------------------------------------------------------

def test_deleting_a_chat_erases_everything_but_keeps_the_sales(platform):
    engine, store, memory, client = platform
    conversation = _whatsapp_chat(engine, store)
    assert _count(engine, conversation_entries) == 2 and _count(engine, conversation_media) == 1
    assert _count(engine, notifications) == 1 and _count(engine, notification_reads) == 1

    response = client.delete(f"/api/conversations/{conversation}", headers=_as("ana"))

    assert response.status_code == 204
    assert memory.forgotten == [("restaurant", PHONE)], "el asistente olvida a ese cliente"
    for table in (conversations, conversation_entries, conversation_media, notifications, notification_reads):
        assert _count(engine, table) == 0, table.name
    with engine.connect() as conn:
        sale = conn.execute(select(sales.c.customer_name, sales.c.amount, sales.c.conversation_id, sales.c.status)).one()
    assert (sale.customer_name, sale.amount, sale.conversation_id, sale.status) == ("Laura", Decimal("120000"), None, "confirmed")
    assert client.get(f"/api/conversations/{conversation}", headers=_as("ana")).status_code == 404
    assert client.get("/api/conversations?business=restaurant", headers=_as("ana")).json() == []


def test_if_the_assistant_memory_cannot_be_erased_nothing_is_deleted(platform):
    engine, store, memory, client = platform
    conversation = _whatsapp_chat(engine, store)
    memory.fail = True

    response = client.delete(f"/api/conversations/{conversation}", headers=_as("ana"))

    assert response.status_code == 503
    assert "no se eliminó" in response.json()["message"]
    assert _count(engine, conversations) == 1 and _count(engine, conversation_entries) == 2 and _count(engine, conversation_media) == 1


def test_nobody_deletes_the_chats_of_another_business(platform):
    engine, store, memory, client = platform
    conversation = _whatsapp_chat(engine, store)

    response = client.delete(f"/api/conversations/{conversation}", headers=_as("beto"))

    assert (response.status_code, response.json()["code"]) == (404, "not_found")
    assert memory.forgotten == [] and _count(engine, conversations) == 1
    assert client.delete("/api/conversations/no-existe", headers=_as("ana")).status_code == 404


def test_a_test_chat_is_deleted_with_the_memory_of_its_session(platform):
    engine, store, memory, client = platform
    test_chat = store.record("restaurant", channel="prueba", contact_ref="sesion-1", contact_name="Prueba en el panel", messages=[NewMessage("customer", "Hola")])

    assert client.delete(f"/api/conversations/{test_chat}", headers=_as("ana")).status_code == 204
    # «Probar» guarda su memoria en la base (para que no se pierda en Vercel): se borra la de esa sesión, nunca la de un cliente.
    assert memory.forgotten == [("restaurant", "prueba:sesion-1")] and _count(engine, conversations) == 0


# ---------------------------------------------------------------------------
# Los chats de «Probar asistente», de una vez
# ---------------------------------------------------------------------------

def test_the_test_chats_are_deleted_at_once_and_real_customers_stay(platform):
    engine, store, memory, client = platform
    real = _whatsapp_chat(engine, store)
    for session in ("sesion-1", "sesion-2", "sesion-3"):
        store.record("restaurant", channel="prueba", contact_ref=session, contact_name="Prueba en el panel", messages=[NewMessage("customer", "Hola")])
    other_business = store.record("saas", channel="prueba", contact_ref="sesion-beto", contact_name="Prueba en el panel", messages=[NewMessage("customer", "Hola")])

    response = client.delete("/api/businesses/restaurant/conversations/tests", headers=_as("ana"))

    assert (response.status_code, response.json()) == (200, {"deleted": 3})
    assert memory.forgotten == [("restaurant", "prueba:*")]
    with engine.connect() as conn:
        left = {str(row.id) for row in conn.execute(select(conversations.c.id))}
    assert left == {real, other_business}
    # Si la memoria de las pruebas no se puede borrar, no se borra nada.
    store.record("restaurant", channel="prueba", contact_ref="sesion-4", contact_name="Prueba en el panel", messages=[NewMessage("customer", "Hola")])
    memory.fail = True
    assert client.delete("/api/businesses/restaurant/conversations/tests", headers=_as("ana")).status_code == 503
    assert _count(engine, conversations) == 3
    memory.fail = False
    # Otro usuario no puede borrar las pruebas de un negocio ajeno.
    assert client.delete("/api/businesses/saas/conversations/tests", headers=_as("ana")).status_code == 404
    assert _count(engine, conversations) == 3
