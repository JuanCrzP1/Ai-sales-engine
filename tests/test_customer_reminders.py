"""Los recordatorios del equipo: qué hacer con un cliente y cuándo, para quién, y marcarlos hechos.

Con la base real (SQLite) y la API del panel «en la nube»:
- quien atiende (también un asesor) crea un recordatorio para un cliente; sin elegir responsable, queda para quien lo crea; el
  responsable solo puede ser alguien del negocio, o nadie;
- el texto y la fecha se revisan: una fecha que ya pasó o muy lejana no sirve;
- los pendientes salen por fecha (el más próximo primero), del negocio o solo los míos; los hechos aparte, el último primero;
- se marcan hechos (a nombre de quien lo hizo) y se vuelven a abrir; se borran;
- la tarjeta del cliente muestra su pendiente más próximo y su ficha los trae todos;
- nadie alcanza los recordatorios ni los clientes de otro negocio, y una conversación de prueba no tiene recordatorios.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from app.admin_api.main import create_app
from app.business_config_application.access import BusinessAccess
from app.domain.business_config.access import Principal
from app.domain.business_config.conversations import NewMessage
from app.domain.business_config.reminders import FOR_ME, NewReminder, ReminderError
from app.infrastructure.business_config import reminder_store
from app.infrastructure.business_config.commerce_store import CommerceStore
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.business_config.example_businesses import import_example, load_example
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.notification_store import NotificationStore
from app.infrastructure.business_config.tables import business_members, conversations, customer_reminders, tenants
from app.infrastructure.business_config.usage_store import UsageCounterStore

ANA = Principal(user_id="usuario-ana", email="ana@example.com")
BETO = Principal(user_id="usuario-beto", email="beto@example.com")
CARO = Principal(user_id="usuario-caro", email="caro@example.com")
BASE = "/api/businesses/restaurant"
NOW = datetime(2026, 11, 28, 15, 0, tzinfo=timezone.utc)


class Tokens:
    def verify(self, token: str) -> Principal | None:
        return {"token-de-ana": ANA, "token-de-beto": BETO, "token-de-caro": CARO}.get(token)


def _as(user: str) -> dict[str, str]:
    return {"Authorization": f"Bearer token-de-{user}"}


def _soon(hours: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


@pytest.fixture
def platform(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'recordatorios.sqlite3').as_posix()}")
    create_local_schema(engine)
    service = build_business_config_service(engine, secrets_key=Fernet.generate_key().decode())
    for slug in ("restaurant", "saas"):
        import_example(service, load_example(slug))
    with engine.begin() as conn:
        ids = {row.slug: row.id for row in conn.execute(select(tenants.c.slug, tenants.c.id))}
        # Ana es la dueña del restaurante y Caro su asesora; Beto tiene otro negocio.
        for slug, user, role in (("restaurant", ANA, "owner"), ("restaurant", CARO, "agent"), ("saas", BETO, "owner")):
            conn.execute(business_members.insert().values(tenant_id=ids[slug], user_id=user.user_id, role=role, email=user.email, created_at=datetime.now(timezone.utc)))
    store = ConversationStore(engine)
    app = create_app(
        service, None, access=BusinessAccess(service, BusinessMembersStore(engine)), verifier=Tokens(), conversations=store,
        notifications=NotificationStore(engine), usage=UsageCounterStore(engine), commerce=CommerceStore(engine),
    )
    yield engine, store, TestClient(app)
    engine.dispose()


def _chat(store: ConversationStore, contact: str, name: str, *, business: str = "restaurant", channel: str = "whatsapp") -> str:
    return store.append(business, channel=channel, contact_ref=contact, contact_name=name, message=NewMessage("customer", "Hola")).conversation_id


def _create(client: TestClient, conversation_id: str, title: str, due_at: str, user: str = "ana", **extra):
    return client.post(f"{BASE}/customers/{conversation_id}/reminders", json={"title": title, "due_at": due_at, **extra}, headers=_as(user))


def _list(client: TestClient, user: str = "ana", **params) -> list[dict]:
    return client.get(f"{BASE}/reminders", params=params, headers=_as(user)).json()


# ------------------------------------------------------------------ las reglas


def test_a_reminder_needs_what_to_do_and_a_date_that_is_coming():
    made = NewReminder.checked(title="  Llamar   para cerrar ", due_at="2026-11-29T14:00:00Z", now=NOW)
    assert (made.title, made.due_at, made.assignee_id) == ("Llamar para cerrar", datetime(2026, 11, 29, 14, 0, tzinfo=timezone.utc), FOR_ME)
    # La hora llega con su zona y se guarda en UTC.
    assert NewReminder.checked(title="x", due_at="2026-11-29T09:00:00-05:00", now=NOW).due_at == datetime(2026, 11, 29, 14, 0, tzinfo=timezone.utc)
    assert NewReminder.checked(title="x", due_at="2026-11-28T14:55:00+00:00", now=NOW).due_at.minute == 55  # unos minutos atrás, sí
    assert NewReminder.checked(title="x", due_at="2026-11-29T14:00:00Z", now=NOW, assignee_id=" ").assignee_id is None
    for title, due_at, field in (("", "2026-11-29T14:00:00Z", "title"), ("x" * 141, "2026-11-29T14:00:00Z", "title"),
                                 ("x", "mañana", "due_at"), ("x", "2026-11-29T14:00:00", "due_at"), ("x", "2026-11-27T14:00:00Z", "due_at"),
                                 ("x", "2029-01-01T00:00:00Z", "due_at")):
        with pytest.raises(ReminderError) as error:
            NewReminder.checked(title=title, due_at=due_at, now=NOW)
        assert error.value.field == field


# ------------------------------------------------------------------ crear


def test_without_choosing_it_is_for_whoever_creates_it_and_the_owner_is_from_the_team(platform):
    _engine, store, client = platform
    ana = _chat(store, "573001", "Ana")
    mine = _create(client, ana, "Llamar para cerrar", _soon(2), user="caro")  # una asesora también crea
    assert mine.status_code == 201
    body = mine.json()
    assert (body["title"], body["assignee"], body["created_by"], body["done_at"]) == ("Llamar para cerrar", {"user_id": CARO.user_id, "label": "caro@example.com"}, "caro@example.com", None)
    assert (body["customer_name"], body["conversation_id"]) == ("Ana", ana)

    assert _create(client, ana, "Enviar propuesta", _soon(3), assignee_id=ANA.user_id).json()["assignee"]["user_id"] == ANA.user_id
    assert _create(client, ana, "Revisar pago", _soon(4), assignee_id="").json()["assignee"] is None
    refused = _create(client, ana, "x", _soon(1), assignee_id=BETO.user_id)  # Beto es de otro negocio
    assert refused.status_code == 422 and refused.json()["issues"] == [{"path": "assignee_id", "message": "Esa persona no es del equipo de este negocio."}]
    for body, field in (({"title": "", "due_at": _soon(1)}, "title"), ({"title": "x", "due_at": "ayer"}, "due_at"), ({"title": "x", "due_at": _soon(-3)}, "due_at")):
        bad = client.post(f"{BASE}/customers/{ana}/reminders", json=body, headers=_as("ana"))
        assert bad.status_code == 422 and bad.json()["issues"][0]["path"] == field


def test_a_customer_has_a_limit_of_pending_reminders(platform, monkeypatch):
    _engine, store, client = platform
    ana = _chat(store, "573001", "Ana")
    monkeypatch.setattr(reminder_store, "MAX_OPEN_PER_CUSTOMER", 2)
    first = _create(client, ana, "Uno", _soon(1)).json()["id"]
    _create(client, ana, "Dos", _soon(2))
    full = _create(client, ana, "Tres", _soon(3))
    assert full.status_code == 422 and "marca o borra" in full.json()["message"]
    client.patch(f"{BASE}/reminders/{first}", json={"done": True}, headers=_as("ana"))
    assert _create(client, ana, "Tres", _soon(3)).status_code == 201  # uno hecho ya no cuenta


# ------------------------------------------------------------------ listar


def test_pending_ones_go_by_date_mine_or_everyone_and_done_ones_apart(platform):
    _engine, store, client = platform
    ana, beto = _chat(store, "573001", "Ana"), _chat(store, "573002", "Beto")
    later = _create(client, ana, "Enviar propuesta", _soon(30)).json()["id"]
    _create(client, beto, "Llamar a Beto", _soon(1), user="caro")
    soon = _create(client, ana, "Confirmar dirección", _soon(2)).json()["id"]
    test_chat = _chat(store, "s1", "Prueba", channel="prueba")
    assert _create(client, test_chat, "x", _soon(1)).status_code == 404  # una prueba no tiene recordatorios

    assert [item["title"] for item in _list(client)] == ["Llamar a Beto", "Confirmar dirección", "Enviar propuesta"]
    assert [item["title"] for item in _list(client, mine="true")] == ["Confirmar dirección", "Enviar propuesta"]
    assert [item["title"] for item in _list(client, user="caro", mine="true")] == ["Llamar a Beto"]

    done = client.patch(f"{BASE}/reminders/{soon}", json={"done": True}, headers=_as("caro")).json()
    assert done["done_by"] == "caro@example.com" and done["done_at"] is not None
    client.patch(f"{BASE}/reminders/{later}", json={"done": True}, headers=_as("ana"))
    assert [item["title"] for item in _list(client)] == ["Llamar a Beto"]
    assert [item["title"] for item in _list(client, done="true")] == ["Enviar propuesta", "Confirmar dirección"]
    assert client.get(f"{BASE}/reminders", headers=_as("beto")).status_code == 404


# ------------------------------------------------------------------ marcar y borrar


def test_marking_done_twice_keeps_who_and_when_and_it_can_be_reopened(platform):
    _engine, store, client = platform
    ana = _chat(store, "573001", "Ana")
    reminder = _create(client, ana, "Llamar", _soon(1)).json()["id"]
    first = client.patch(f"{BASE}/reminders/{reminder}", json={"done": True}, headers=_as("ana")).json()
    again = client.patch(f"{BASE}/reminders/{reminder}", json={"done": True}, headers=_as("caro")).json()
    assert (again["done_at"], again["done_by"]) == (first["done_at"], "ana@example.com")
    reopened = client.patch(f"{BASE}/reminders/{reminder}", json={"done": False}, headers=_as("caro")).json()
    assert (reopened["done_at"], reopened["done_by"]) == (None, None)
    assert [item["title"] for item in _list(client)] == ["Llamar"]


def test_deleting_and_nobody_reaches_the_reminders_of_another_business(platform):
    engine, store, client = platform
    ana = _chat(store, "573001", "Ana")
    foreign_customer = _chat(store, "573009", "De otro negocio", business="saas")
    reminder = _create(client, ana, "Llamar", _soon(1)).json()["id"]
    foreign = client.post(f"/api/businesses/saas/customers/{foreign_customer}/reminders", json={"title": "Ajeno", "due_at": _soon(1)}, headers=_as("beto")).json()["id"]
    assert _create(client, foreign_customer, "x", _soon(1)).status_code == 404
    for target in (foreign, "no-es-un-id"):
        assert client.patch(f"{BASE}/reminders/{target}", json={"done": True}, headers=_as("ana")).status_code == 404
        assert client.delete(f"{BASE}/reminders/{target}", headers=_as("ana")).status_code == 404
    assert client.patch(f"{BASE}/reminders/{reminder}", json={"done": True}, headers=_as("beto")).status_code == 404

    assert client.delete(f"{BASE}/reminders/{reminder}", headers=_as("caro")).status_code == 204
    assert client.delete(f"{BASE}/reminders/{reminder}", headers=_as("ana")).status_code == 404
    with engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(customer_reminders)).scalar_one() == 1  # el de Beto sigue


# ------------------------------------------------------------------ en la tarjeta y en la ficha


def test_the_card_shows_the_next_pending_one_and_the_customer_file_brings_them_all(platform):
    engine, store, client = platform
    ana = _chat(store, "573001", "Ana")
    _create(client, ana, "Enviar propuesta", _soon(30))
    soon = _create(client, ana, "Llamar para cerrar", _soon(2)).json()["id"]
    board = client.get(f"{BASE}/pipeline", headers=_as("ana")).json()
    assert board["columns"][0]["customers"][0]["next_reminder"]["title"] == "Llamar para cerrar"
    client.patch(f"{BASE}/reminders/{soon}", json={"done": True}, headers=_as("ana"))
    listed = client.get(f"{BASE}/customers", headers=_as("ana")).json()
    assert listed[0]["next_reminder"]["title"] == "Enviar propuesta"

    card = client.get(f"{BASE}/customers/{ana}", headers=_as("caro")).json()
    assert [(item["title"], item["done_at"] is not None) for item in card["reminders"]] == [("Enviar propuesta", False), ("Llamar para cerrar", True)]
    assert card["viewer_id"] == CARO.user_id  # el panel la propone como responsable

    # Si el cliente se borra, sus recordatorios también.
    with engine.begin() as conn:
        conn.execute(delete(conversations).where(conversations.c.id == store._key(ana)))
    assert _list(client) == [] and _list(client, done="true") == []
