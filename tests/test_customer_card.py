"""La ficha de un cliente: su valor, su responsable, sus notas, sus compras y el historial de lo que le ha pasado.

Con la base real (SQLite) y la API del panel «en la nube»:
- la ficha trae al cliente, desde cuándo está en su etapa, su responsable, el equipo que puede serlo, sus compras, notas e historial;
  cada persona solo ve la de sus negocios, y una conversación de prueba no tiene ficha;
- el valor (monto y moneda) lo pone quien atiende; suma en su columna del tablero y en «por cerrar» mientras no compre;
- el responsable solo puede ser alguien del negocio; si esa persona sale del equipo, el cliente queda sin responsable;
- las notas son del equipo: quedan a nombre de quien las escribió y se pueden borrar;
- el historial anota cada cambio de etapa con quién lo hizo (el asistente, alguien del equipo o una venta), y los cambios de valor
  y de responsable; lo que no cambió de verdad no se anota.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from app.admin_api.main import create_app
from app.business_config_application.access import BusinessAccess
from app.domain.business_config.access import Principal
from app.domain.business_config.conversations import NewMessage
from app.domain.business_config.customer_card import UNSET, CustomerCardError, DealChange, checked_note, money_text
from app.infrastructure.business_config.commerce_store import CommerceStore
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.business_config.example_businesses import import_example, load_example
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.notification_store import NotificationStore
from app.infrastructure.business_config.tables import business_members, customer_events, customer_notes, tenants
from app.infrastructure.business_config.usage_store import UsageCounterStore

ANA = Principal(user_id="usuario-ana", email="ana@example.com")
BETO = Principal(user_id="usuario-beto", email="beto@example.com")
CARO = Principal(user_id="usuario-caro", email="caro@example.com")
BASE = "/api/businesses/restaurant"


class Tokens:
    def verify(self, token: str) -> Principal | None:
        return {"token-de-ana": ANA, "token-de-beto": BETO, "token-de-caro": CARO}.get(token)


def _as(user: str) -> dict[str, str]:
    return {"Authorization": f"Bearer token-de-{user}"}


@pytest.fixture
def platform(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'ficha.sqlite3').as_posix()}")
    create_local_schema(engine)
    service = build_business_config_service(engine, secrets_key=Fernet.generate_key().decode())
    for slug in ("restaurant", "saas"):
        import_example(service, load_example(slug))
    with engine.begin() as conn:
        ids = {row.slug: row.id for row in conn.execute(select(tenants.c.slug, tenants.c.id))}
        # Ana es la dueña del restaurante y Caro su asesora; Beto tiene otro negocio.
        for slug, user, role in (("restaurant", ANA, "owner"), ("restaurant", CARO, "agent"), ("saas", BETO, "owner")):
            conn.execute(
                business_members.insert().values(tenant_id=ids[slug], user_id=user.user_id, role=role, email=user.email, created_at=datetime.now(timezone.utc))
            )
    store = ConversationStore(engine)
    app = create_app(
        service, None, access=BusinessAccess(service, BusinessMembersStore(engine)), verifier=Tokens(), conversations=store,
        notifications=NotificationStore(engine), usage=UsageCounterStore(engine), commerce=CommerceStore(engine),
    )
    yield engine, store, TestClient(app)
    engine.dispose()


def _chat(store: ConversationStore, contact: str, name: str, *messages: NewMessage, business: str = "restaurant", channel: str = "whatsapp") -> str:
    result = None
    for message in messages or (NewMessage("customer", "Hola"),):
        result = store.append(business, channel=channel, contact_ref=contact, contact_name=name, message=message)
    return result.conversation_id


def _card(client: TestClient, conversation_id: str, user: str = "ana"):
    return client.get(f"{BASE}/customers/{conversation_id}", headers=_as(user))


def _patch(client: TestClient, conversation_id: str, body: dict, user: str = "ana"):
    return client.patch(f"{BASE}/customers/{conversation_id}", json=body, headers=_as(user))


def _events(card: dict) -> list[tuple]:
    """El historial, del más antiguo al más reciente: (qué, de, a, quién lo hizo, detalle, a nombre de)."""
    return [(e["kind"], e["from_stage"], e["to_stage"], e["source"], e["detail"], e["actor"]) for e in reversed(card["events"])]


# ------------------------------------------------------------------ las reglas


def test_a_change_brings_only_what_changes_and_checks_it():
    assert DealChange.checked({"amount": "210000", "currency": "cop"}) == DealChange((Decimal("210000.00"), "COP"), UNSET)
    assert DealChange.checked({"amount": ""}) == DealChange(None, UNSET)  # quitar el valor
    assert DealChange.checked({"amount": None, "owner_id": " u1 "}) == DealChange(None, "u1")
    assert DealChange.checked({"owner_id": ""}) == DealChange(UNSET, None)  # sin responsable
    for changes, field in (({"amount": "abc", "currency": "COP"}, "amount"), ({"amount": "0", "currency": "COP"}, "amount"),
                           ({"amount": "10"}, "currency"), ({"amount": "10", "currency": "pesos"}, "currency"), ({}, "amount")):
        with pytest.raises(CustomerCardError) as error:
            DealChange.checked(changes)
        assert error.value.field == field


def test_a_note_is_cleaned_and_has_a_limit_and_money_reads_like_in_colombia():
    assert checked_note("  Prefiere la tarde.  \n  Llamar el lunes ") == "Prefiere la tarde.\n  Llamar el lunes"
    for body in ("", "   ", "x" * 2001):
        with pytest.raises(CustomerCardError) as error:
            checked_note(body)
        assert error.value.field == "body"
    assert money_text(Decimal("210000.00"), "COP") == "COP 210.000"
    assert money_text(Decimal("45.50"), "USD") == "USD 45,50"


# ------------------------------------------------------------------ la ficha


def test_the_card_brings_the_customer_the_team_and_starts_empty(platform):
    _engine, store, client = platform
    ana = _chat(store, "573001", "Ana")
    card = _card(client, ana).json()
    assert (card["customer"]["name"], card["customer"]["stage"], card["customer"]["deal"], card["customer"]["owner"]) == ("Ana", "new", None, None)
    assert (card["stage_since"], card["owner"], card["purchases"], card["notes"], card["events"]) == (None, None, [], [], [])
    # El equipo del negocio, el dueño primero: quienes pueden ser responsables.
    assert [(member["email"], member["role"]) for member in card["assignees"]] == [("ana@example.com", "owner"), ("caro@example.com", "agent")]
    assert _card(client, ana, "caro").status_code == 200  # una asesora también la ve


def test_nobody_sees_the_card_of_another_business_or_of_a_test_chat(platform):
    _engine, store, client = platform
    ana = _chat(store, "573001", "Ana")
    foreign = _chat(store, "573009", "De otro negocio", business="saas")
    test_chat = _chat(store, "s1", "Prueba", channel="prueba")
    assert _card(client, ana, "beto").status_code == 404
    for conversation in (foreign, test_chat, "no-es-un-id"):
        assert _card(client, conversation).status_code == 404
        assert _patch(client, conversation, {"amount": "10", "currency": "COP"}).status_code == 404
        assert client.post(f"{BASE}/customers/{conversation}/notes", json={"body": "x"}, headers=_as("ana")).status_code == 404


# ------------------------------------------------------------------ el valor


def test_the_value_adds_up_in_its_column_and_in_what_is_left_to_close(platform):
    _engine, store, client = platform
    ana, beto, caro = (_chat(store, f"57300{index}", name) for index, name in enumerate(("Ana", "Beto", "Caro")))
    saved = _patch(client, ana, {"amount": "210000", "currency": "cop"}, user="caro")  # una asesora también lo pone
    assert saved.status_code == 200 and saved.json()["customer"]["deal"] == {"amount": "210000.00", "currency": "COP"}
    _patch(client, beto, {"amount": "90000", "currency": "COP"})
    _patch(client, caro, {"amount": "45.5", "currency": "USD"})
    client.post(f"{BASE}/customers/{caro}/stage", json={"stage": "lost"}, headers=_as("ana"))

    board = client.get(f"{BASE}/pipeline", headers=_as("ana")).json()
    columns = {column["stage"]: column for column in board["columns"]}
    assert columns["new"]["value"] == {"COP": "300000.00"} and columns["lost"]["value"] == {"USD": "45.50"}
    assert {card["name"]: card["deal"] for card in columns["new"]["customers"]} == {
        "Ana": {"amount": "210000.00", "currency": "COP"}, "Beto": {"amount": "90000.00", "currency": "COP"},
    }
    assert board["stats"]["open_value"] == {"COP": "300000.00"}  # quien no compró ya no está por cerrar
    assert client.get(f"{BASE}/pipeline", params={"q": "ana"}, headers=_as("ana")).json()["stats"]["open_value"] == {"COP": "300000.00"}

    cleared = _patch(client, ana, {"amount": ""}).json()
    assert cleared["customer"]["deal"] is None
    assert [e[4] for e in _events(cleared) if e[0] == "value"] == ["COP 210.000", None]


def test_a_value_that_does_not_work_is_refused_on_its_field_and_the_same_value_is_not_logged_twice(platform):
    _engine, store, client = platform
    ana = _chat(store, "573001", "Ana")
    for body, field in (({"amount": "cero", "currency": "COP"}, "amount"), ({"amount": "-5", "currency": "COP"}, "amount"),
                        ({"amount": "100"}, "currency"), ({}, "amount")):
        refused = _patch(client, ana, body)
        assert refused.status_code == 422 and refused.json()["issues"][0]["path"] == field
    _patch(client, ana, {"amount": "100", "currency": "COP"})
    again = _patch(client, ana, {"amount": "100.00", "currency": "COP"}).json()
    assert len(again["events"]) == 1


# ------------------------------------------------------------------ el responsable


def test_the_owner_is_someone_of_the_business_and_the_change_is_logged(platform):
    engine, store, client = platform
    ana = _chat(store, "573001", "Ana")
    refused = _patch(client, ana, {"owner_id": BETO.user_id})  # Beto es de otro negocio
    assert refused.status_code == 422 and refused.json()["issues"] == [{"path": "owner_id", "message": "Esa persona no es del equipo de este negocio."}]

    card = _patch(client, ana, {"owner_id": CARO.user_id}).json()
    assert card["owner"] == {"user_id": CARO.user_id, "email": "caro@example.com", "role": "agent"}
    assert card["customer"]["owner"] == {"user_id": CARO.user_id, "label": "caro@example.com"}
    board = client.get(f"{BASE}/pipeline", headers=_as("ana")).json()
    assert board["columns"][0]["customers"][0]["owner"]["label"] == "caro@example.com"
    assert _events(card) == [("owner", None, None, "team", "caro@example.com", "ana@example.com")]

    free = _patch(client, ana, {"owner_id": ""}).json()
    assert free["owner"] is None and _events(free)[-1] == ("owner", None, None, "team", None, "ana@example.com")

    # Si la responsable sale del equipo, el cliente queda sin responsable.
    _patch(client, ana, {"owner_id": CARO.user_id})
    with engine.begin() as conn:
        conn.execute(delete(business_members).where(business_members.c.user_id == CARO.user_id))
    gone = _card(client, ana).json()
    assert gone["owner"] is None and gone["customer"]["owner"] is None


# ------------------------------------------------------------------ las notas


def test_notes_belong_to_the_team_stay_under_their_author_and_can_be_deleted(platform):
    engine, store, client = platform
    ana = _chat(store, "573001", "Ana")
    first = client.post(f"{BASE}/customers/{ana}/notes", json={"body": "  Prefiere que la llamen en la tarde. "}, headers=_as("caro"))
    assert first.status_code == 201 and (first.json()["body"], first.json()["author"]) == ("Prefiere que la llamen en la tarde.", "caro@example.com")
    client.post(f"{BASE}/customers/{ana}/notes", json={"body": "Quiere factura."}, headers=_as("ana"))
    assert [(note["body"], note["author"]) for note in _card(client, ana).json()["notes"]] == [
        ("Quiere factura.", "ana@example.com"), ("Prefiere que la llamen en la tarde.", "caro@example.com"),
    ]
    empty = client.post(f"{BASE}/customers/{ana}/notes", json={"body": "   "}, headers=_as("ana"))
    assert empty.status_code == 422 and empty.json()["issues"][0]["path"] == "body"

    other = _chat(store, "573002", "Beto")
    assert client.delete(f"{BASE}/customers/{other}/notes/{first.json()['id']}", headers=_as("ana")).status_code == 404  # no es de ese cliente
    assert client.delete(f"{BASE}/customers/{ana}/notes/{first.json()['id']}", headers=_as("ana")).status_code == 204
    assert client.delete(f"{BASE}/customers/{ana}/notes/{first.json()['id']}", headers=_as("ana")).status_code == 404
    assert [note["body"] for note in _card(client, ana).json()["notes"]] == ["Quiere factura."]
    with engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(customer_notes)).scalar_one() == 1


# ------------------------------------------------------------------ el historial


def test_the_history_says_who_moved_the_customer_each_time(platform):
    _engine, store, client = platform
    ana = _chat(store, "573001", "Ana", NewMessage("customer", "¿Cuánto vale?"), NewMessage("assistant", "Vale $20.000", "info"))
    _chat(store, "573001", "Ana", NewMessage("customer", "gracias"), NewMessage("assistant", "¡Con gusto!"))  # sin interés nuevo: no cambia
    client.post(f"{BASE}/customers/{ana}/stage", json={"stage": "lost", "reason": "Le pareció caro"}, headers=_as("caro"))
    _chat(store, "573001", "Ana", NewMessage("customer", "Ahora sí lo quiero"), NewMessage("assistant", "¡Listo! ¿Cómo pagas?", "buy"))
    store.request_handoff(ana, "payment_review", "Ya pagué")
    sale = {"customer_name": "Ana", "description": "2 hamburguesas", "amount": "40000", "currency": "COP", "conversation_id": ana}
    assert client.post(f"{BASE}/sales", json=sale, headers=_as("ana")).status_code == 201

    card = _card(client, ana).json()
    assert _events(card) == [
        ("stage", "new", "interested", "assistant", None, None),
        ("stage", "interested", "lost", "team", "Le pareció caro", "caro@example.com"),
        ("stage", "lost", "ready", "assistant", None, None),
        ("stage", "ready", "payment", "assistant", "Avisó un pago", None),
        ("stage", "payment", "customer", "sale", "2 hamburguesas · COP 40.000", "ana@example.com"),
    ]
    assert card["stage_since"] == card["events"][0]["created_at"]  # desde la venta
    assert [(p["description"], p["amount"], p["status"]) for p in card["purchases"]] == [("2 hamburguesas", "40000.00", "confirmed")]
    # Una segunda venta no lo «mueve»: ya era cliente.
    client.post(f"{BASE}/sales", json={**sale, "description": "1 gaseosa", "amount": "5000"}, headers=_as("ana"))
    again = _card(client, ana).json()
    assert len(again["events"]) == 5 and [p["description"] for p in again["purchases"]] == ["1 gaseosa", "2 hamburguesas"]


def test_confirming_a_payment_is_logged_under_who_confirmed_it(platform):
    engine, store, client = platform
    ana = _chat(store, "573001", "Ana", NewMessage("customer", "Te pagué"), NewMessage("assistant", "Lo verifico", "buy"))
    store.request_handoff(ana, "payment_review", "Te pagué")
    claim = store.claim_payment(ana)
    store.finish_payment(ana, claim, by="caro@example.com")
    card = _card(client, ana).json()
    assert _events(card)[-1] == ("stage", "payment", "customer", "team", "Pago confirmado", "caro@example.com")
    assert card["customer"]["stage"] == "customer" and card["stage_since"] is not None
    with engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(customer_events)).scalar_one() == 3


def test_moving_to_the_same_stage_changes_nothing_in_the_history(platform):
    _engine, store, client = platform
    ana = _chat(store, "573001", "Ana")
    client.post(f"{BASE}/customers/{ana}/stage", json={"stage": "lost", "reason": "No respondió más"}, headers=_as("ana"))
    client.post(f"{BASE}/customers/{ana}/stage", json={"stage": "lost", "reason": "Compró en otro lado"}, headers=_as("ana"))
    card = _card(client, ana).json()
    assert len(card["events"]) == 1 and card["customer"]["lost_reason"] == "Compró en otro lado"
