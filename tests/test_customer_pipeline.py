"""El tablero de Clientes: una columna por etapa, mover a mano, «no compró» con su motivo y los números del embudo.

Con la base real (SQLite) y la API del panel «en la nube»:
- el tablero trae las seis columnas en orden (las cinco del embudo y «no compró»), con cuántos hay y sus tarjetas más recientes; las
  pruebas del panel no cuentan, y cada persona solo ve sus negocios;
- quien atiende (también un asesor) mueve a un cliente a cualquier etapa; a «cliente» solo se llega registrando la venta;
- «no compró» guarda el motivo; al salir de ahí, se borra; si esa persona vuelve a escribir con interés, el asistente la regresa
  al embudo; mientras siga ahí, no recibe seguimientos (`tests/test_follow_up.py`);
- los números: cuántos siguen abiertos, lo vendido en 30 días por moneda, de cada 100 cuántos compran, cuánto tardan y qué parte
  avanza de una etapa a la siguiente.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.admin_api.main import create_app
from app.business_config_application.access import BusinessAccess
from app.domain.business_config.access import Principal
from app.domain.business_config.conversations import NewMessage
from app.domain.business_config.pipeline import StageMove, StageMoveError, advance_rates, close_rate
from app.infrastructure.business_config import pipeline_store
from app.infrastructure.business_config.commerce_store import CommerceStore
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.business_config.example_businesses import import_example, load_example
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.notification_store import NotificationStore
from app.infrastructure.business_config.tables import business_members, conversations, tenants
from app.infrastructure.business_config.usage_store import UsageCounterStore

ANA = Principal(user_id="usuario-ana", email="ana@example.com")
BETO = Principal(user_id="usuario-beto", email="beto@example.com")
CARO = Principal(user_id="usuario-caro", email="caro@example.com")
BOARD = "/api/businesses/restaurant/pipeline"


class Tokens:
    def verify(self, token: str) -> Principal | None:
        return {"token-de-ana": ANA, "token-de-beto": BETO, "token-de-caro": CARO}.get(token)


def _as(user: str) -> dict[str, str]:
    return {"Authorization": f"Bearer token-de-{user}"}


@pytest.fixture
def platform(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'tablero.sqlite3').as_posix()}")
    create_local_schema(engine)
    service = build_business_config_service(engine, secrets_key=Fernet.generate_key().decode())
    for slug in ("restaurant", "saas"):
        import_example(service, load_example(slug))
    with engine.begin() as conn:
        ids = {row.slug: row.id for row in conn.execute(select(tenants.c.slug, tenants.c.id))}
        # Ana es la dueña del restaurante y Caro su asesora; Beto tiene otro negocio.
        for slug, user, role in (("restaurant", ANA, "owner"), ("restaurant", CARO, "agent"), ("saas", BETO, "owner")):
            conn.execute(business_members.insert().values(tenant_id=ids[slug], user_id=user.user_id, role=role, created_at=datetime.now(timezone.utc)))
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


def _move(client: TestClient, conversation_id: str, stage: str, reason: str | None = None, user: str = "ana"):
    body = {"stage": stage} if reason is None else {"stage": stage, "reason": reason}
    return client.post(f"/api/businesses/restaurant/customers/{conversation_id}/stage", json=body, headers=_as(user))


def _columns(client: TestClient, **params) -> dict[str, dict]:
    return {column["stage"]: column for column in client.get(BOARD, params=params, headers=_as("ana")).json()["columns"]}


# ------------------------------------------------------------------ las reglas


def test_a_move_keeps_the_reason_only_for_a_lost_customer_and_never_goes_to_client_by_hand():
    assert StageMove.checked(stage=" Ready ") == StageMove("ready")
    assert StageMove.checked(stage="lost", reason="  Le pareció   caro ") == StageMove("lost", "Le pareció caro")
    assert StageMove.checked(stage="lost") == StageMove("lost", None)
    assert StageMove.checked(stage="interested", reason="da igual") == StageMove("interested", None)
    for stage, reason, field in (("cliente", None, "stage"), ("", None, "stage"), ("customer", None, "stage"), ("lost", "x" * 201, "reason")):
        with pytest.raises(StageMoveError) as error:
            StageMove.checked(stage=stage, reason=reason)
        assert error.value.field == field


def test_the_funnel_numbers_count_accumulated_and_leave_the_lost_out_of_the_steps():
    counts = {"new": 4, "interested": 3, "ready": 1, "payment": 0, "customer": 2, "lost": 10}
    # Llegaron: 10 a nuevo, 6 a interesado, 3 a listo, 2 a pagó y 2 a cliente.
    assert advance_rates(counts) == {"new": 0.6, "interested": 0.5, "ready": pytest.approx(2 / 3), "payment": 1.0}
    assert close_rate(counts) == 0.1  # 2 de 20, contando a los que no compraron
    assert close_rate({}) is None and advance_rates({}) == {"new": None, "interested": None, "ready": None, "payment": None}


# ------------------------------------------------------------------ el tablero


def test_the_board_has_a_column_per_stage_with_its_count_and_latest_cards(platform, monkeypatch):
    _engine, store, client = platform
    _chat(store, "573001", "Ana", NewMessage("customer", "Hola"), NewMessage("assistant", "¡Hola! ¿Qué buscas?", "info"))
    _chat(store, "573002", "Beto", NewMessage("customer", "Quiero pedir"), NewMessage("assistant", "¡Listo! ¿Cómo pagas?", "buy"))
    for number in range(3):
        _chat(store, f"57310{number}", f"Nuevo {number}")
    _chat(store, "s1", "Prueba", channel="prueba")
    _chat(store, "573009", "De otro negocio", business="saas")
    monkeypatch.setattr(pipeline_store, "CARDS_PER_STAGE", 2)

    board = client.get(BOARD, headers=_as("ana")).json()
    assert [column["stage"] for column in board["columns"]] == ["new", "interested", "ready", "payment", "customer", "lost"]
    columns = {column["stage"]: column for column in board["columns"]}
    assert {stage: column["count"] for stage, column in columns.items()} == {"new": 3, "interested": 1, "ready": 1, "payment": 0, "customer": 0, "lost": 0}
    # Lo más reciente primero, y solo las tarjetas que caben: la cuenta dice cuántos hay.
    assert [card["name"] for card in columns["new"]["customers"]] == ["Nuevo 2", "Nuevo 1"]
    assert columns["ready"]["customers"][0]["name"] == "Beto" and columns["ready"]["customers"][0]["lost_reason"] is None
    assert board["stats"]["open_count"] == 5 and board["stats"]["lost_count"] == 0
    assert client.get(BOARD, headers=_as("beto")).status_code == 404  # no es su negocio


def test_searching_filters_the_columns_but_the_numbers_still_count_everyone(platform):
    _engine, store, client = platform
    _chat(store, "573001", "Ana")
    _chat(store, "573002", "Beto")
    board = client.get(BOARD, params={"q": "an"}, headers=_as("ana")).json()
    columns = {column["stage"]: column for column in board["columns"]}
    assert columns["new"]["count"] == 1 and [card["name"] for card in columns["new"]["customers"]] == ["Ana"]
    assert board["stats"]["open_count"] == 2
    assert _columns(client, q="573002")["new"]["customers"][0]["name"] == "Beto"  # también por número


# ------------------------------------------------------------------ mover


def test_whoever_attends_moves_a_customer_to_any_stage_but_to_client_only_with_a_sale(platform):
    _engine, store, client = platform
    ana = _chat(store, "573001", "Ana")
    moved = _move(client, ana, "ready", user="caro")  # una asesora también mueve
    assert moved.status_code == 200 and (moved.json()["stage"], moved.json()["name"]) == ("ready", "Ana")
    assert _move(client, ana, "interested").json()["stage"] == "interested"  # a mano sí retrocede
    refused = _move(client, ana, "customer")
    assert refused.status_code == 422 and refused.json()["issues"] == [{"path": "stage", "message": "Para pasarlo a «Cliente», registra su venta."}]
    assert _move(client, ana, "vip").status_code == 422
    assert _columns(client)["interested"]["count"] == 1

    sale = {"customer_name": "Ana", "description": "2 hamburguesas", "amount": "40000", "currency": "COP", "conversation_id": ana}
    assert client.post("/api/businesses/restaurant/sales", json=sale, headers=_as("ana")).status_code == 201
    assert _columns(client)["customer"]["customers"][0]["spent"] == {"COP": "40000.00"}


def test_a_customer_of_another_business_or_a_test_chat_cannot_be_moved(platform):
    _engine, store, client = platform
    foreign = _chat(store, "573009", "De otro negocio", business="saas")
    test_chat = _chat(store, "s1", "Prueba", channel="prueba")
    assert _move(client, foreign, "ready").status_code == 404
    assert _move(client, test_chat, "ready").status_code == 404
    assert _move(client, "no-es-un-id", "ready").status_code == 404
    assert _move(client, _chat(store, "573001", "Ana"), "ready", user="beto").status_code == 404
    assert store.stage_of(foreign) == "new"


def test_a_lost_customer_keeps_the_reason_until_they_leave_that_column(platform):
    _engine, store, client = platform
    ana = _chat(store, "573001", "Ana", NewMessage("customer", "¿Cuánto vale?"), NewMessage("assistant", "Vale $20.000", "info"))
    lost = _move(client, ana, "lost", "  Le pareció caro ").json()
    assert (lost["stage"], lost["lost_reason"]) == ("lost", "Le pareció caro")
    column = _columns(client)["lost"]
    assert column["count"] == 1 and column["customers"][0]["lost_reason"] == "Le pareció caro"
    listed = client.get("/api/businesses/restaurant/customers", params={"stage": "lost"}, headers=_as("ana")).json()
    assert [(item["name"], item["lost_reason"]) for item in listed] == [("Ana", "Le pareció caro")]
    assert _move(client, ana, "lost").json()["lost_reason"] is None  # sin motivo también se puede
    back = _move(client, ana, "interested").json()
    assert (back["stage"], back["lost_reason"]) == ("interested", None)
    with _engine.connect() as conn:
        row = conn.execute(select(conversations.c.lost_reason, conversations.c.lost_at).where(conversations.c.id == store._key(ana))).one()
    assert (row.lost_reason, row.lost_at) == (None, None)


def test_if_a_lost_customer_writes_again_with_interest_the_assistant_brings_them_back(platform):
    _engine, store, client = platform
    ana = _chat(store, "573001", "Ana")
    _move(client, ana, "lost", "No respondió")
    _chat(store, "573001", "Ana", NewMessage("customer", "gracias"), NewMessage("assistant", "¡Con gusto!"))
    assert _columns(client)["lost"]["count"] == 1  # sin interés nuevo, sigue donde lo dejó el equipo
    _chat(store, "573001", "Ana", NewMessage("customer", "Ahora sí lo quiero"), NewMessage("assistant", "¡Listo! ¿Cómo pagas?", "buy"))
    columns = _columns(client)
    assert columns["lost"]["count"] == 0 and columns["ready"]["customers"][0]["lost_reason"] is None


# ------------------------------------------------------------------ los números


def test_the_numbers_say_what_is_open_what_was_sold_how_many_buy_and_how_long_they_take(platform):
    engine, store, client = platform
    now = datetime.now(timezone.utc)
    ana, beto, caro, dani = (_chat(store, f"57300{index}", name) for index, name in enumerate(("Ana", "Beto", "Caro", "Dani")))
    _move(client, beto, "ready")
    _move(client, dani, "lost", "Compró en otro lado")
    with engine.begin() as conn:  # Ana escribió por primera vez hace 4 días; Caro, hace 2
        conn.execute(update(conversations).where(conversations.c.id == store._key(ana)).values(started_at=now - timedelta(days=4)))
        conn.execute(update(conversations).where(conversations.c.id == store._key(caro)).values(started_at=now - timedelta(days=2)))
    for conversation, amount, currency in ((ana, "40000", "COP"), (ana, "10000", "COP"), (caro, "20", "USD")):
        body = {"customer_name": "x", "description": "Pedido", "amount": amount, "currency": currency, "conversation_id": conversation}
        assert client.post("/api/businesses/restaurant/sales", json=body, headers=_as("ana")).status_code == 201

    stats = client.get(BOARD, headers=_as("ana")).json()["stats"]
    assert (stats["open_count"], stats["lost_count"]) == (1, 1)
    assert (stats["won_count"], stats["won"]) == (3, {"COP": "50000.00", "USD": "20.00"})
    assert stats["close_rate"] == 0.5  # 2 de 4 compraron
    assert stats["days_to_buy"] == 3.0  # (4 + 2) / 2: cuenta la primera compra de cada uno
    # Llegaron 3 a nuevo (sin contar a quien no compró), 3 a interesado y a listo (Beto y los dos clientes) y 2 a pagó y a cliente.
    assert stats["advance"] == {"new": 1.0, "interested": 1.0, "ready": pytest.approx(2 / 3), "payment": 1.0}


def test_an_empty_board_has_its_columns_and_no_numbers(platform):
    _engine, _store, client = platform
    board = client.get(BOARD, headers=_as("ana")).json()
    assert [column["count"] for column in board["columns"]] == [0] * 6 and all(column["customers"] == [] for column in board["columns"])
    assert board["stats"] == {
        "open_count": 0, "lost_count": 0, "won_count": 0, "won": {}, "close_rate": None, "days_to_buy": None,
        "advance": {"new": None, "interested": None, "ready": None, "payment": None},
    }
