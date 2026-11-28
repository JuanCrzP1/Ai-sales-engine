"""Los campos del cliente: los datos propios que cada negocio guarda de sus clientes.

Con la base real (SQLite) y la API del panel «en la nube»:
- cada valor se guarda en una forma única, sin importar cómo se escribió (números con miles y decimales a la colombiana, fechas,
  sí o no, la opción de una lista sin importar mayúsculas ni acentos), y un valor que no es de su tipo se rechaza;
- el dueño crea, renombra, cambia las opciones y borra campos; una asesora no, pero llena los valores;
- no hay dos campos que se lean igual, una lista necesita al menos dos opciones y hay un máximo de campos;
- los valores cambian todos o ninguno, con quién y cuándo; dejar uno en blanco lo vacía y repetir el mismo valor no cambia quién lo puso;
- quitar una opción deja sin valor a quienes la tenían, y borrar un campo borra sus valores;
- nadie alcanza los campos ni los clientes de otro negocio, y una conversación de prueba no tiene ficha.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.admin_api.main import create_app
from app.business_config_application.access import BusinessAccess
from app.domain.business_config.access import Principal
from app.domain.business_config.conversations import NewMessage
from app.domain.business_config.customer_fields import (
    CHOICE,
    DATE,
    NUMBER,
    TEXT,
    YES_NO,
    CustomerField,
    FieldChange,
    FieldError,
    NewField,
    checked_value,
)
from app.infrastructure.business_config import field_store
from app.infrastructure.business_config.commerce_store import CommerceStore
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.business_config.example_businesses import import_example, load_example
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.notification_store import NotificationStore
from app.infrastructure.business_config.tables import business_members, customer_field_values, tenants
from app.infrastructure.business_config.usage_store import UsageCounterStore

ANA = Principal(user_id="usuario-ana", email="ana@example.com")
BETO = Principal(user_id="usuario-beto", email="beto@example.com")
CARO = Principal(user_id="usuario-caro", email="caro@example.com")
BASE = "/api/businesses/restaurant"


def _field(kind: str, options: tuple[str, ...] = ()) -> CustomerField:
    return CustomerField(id="f1", name="Campo", kind=kind, options=options)


# ------------------------------------------------------------------ las reglas


def test_each_value_is_kept_in_one_form_however_it_was_written():
    number = _field(NUMBER)
    for raw, kept in (
        ("1.200", "1200"), ("1.200.000", "1200000"), ("1,5", "1.5"), ("1.200,50", "1200.5"), ("1,200.50", "1200.5"), ("$ 49.900", "49900"),
        ("25,000", "25000"), ("0.125", "0.125"), (3, "3"), (2.5, "2.5"), ("-4", "-4"), ("  7 ", "7"),
    ):
        assert checked_value(number, raw) == kept, raw
    date = _field(DATE)
    assert [checked_value(date, raw) for raw in ("2026-11-29", "29/11/2026", "1/2/1990")] == ["2026-11-29", "2026-11-29", "1990-02-01"]
    yes_no = _field(YES_NO)
    assert [checked_value(yes_no, raw) for raw in (True, False, "Sí", "no", "1")] == ["true", "false", "true", "false", "true"]
    choice = _field(CHOICE, ("Mayorista", "Al detal"))
    assert checked_value(choice, "  mayorísta ") == "Mayorista"
    assert checked_value(_field(TEXT), "  Calle  10 #4-20 ") == "Calle 10 #4-20"
    # En blanco, el campo queda vacío.
    assert [checked_value(_field(kind), raw) for kind, raw in ((TEXT, "  "), (NUMBER, ""), (DATE, None))] == [None, None, None]


def test_a_value_that_is_not_of_its_type_is_refused():
    for kind, raw, message in (
        (NUMBER, "mil", "Escribe un número."), (NUMBER, "1e9999", "Escribe un número."), (NUMBER, "1234567890123456", "Escribe un número."),
        (NUMBER, True, "Escribe un número."), (DATE, "31/02/2026", "Elige una fecha."), (DATE, "mañana", "Elige una fecha."),
        (DATE, "1800-01-01", "Elige una fecha."), (YES_NO, "tal vez", "Elige sí o no."), (CHOICE, "Otro", "Elige una de las opciones."),
        (TEXT, "x" * 201, "Es muy largo (máximo 200 caracteres)."),
    ):
        with pytest.raises(FieldError) as error:
            checked_value(_field(kind, ("Mayorista", "Al detal")), raw)
        assert (str(error.value), error.value.field) == (message, "values.f1"), (kind, raw)


def test_a_field_needs_a_name_a_type_and_a_list_its_options():
    made = NewField.checked(name="  Tipo   de cliente ", kind=CHOICE, options=["Mayorista", " ", "Al detal"])
    assert (made.name, made.kind, made.options) == ("Tipo de cliente", CHOICE, ("Mayorista", "Al detal"))
    assert NewField.checked(name="Ciudad", kind=TEXT, options=["no", "sirven"]).options == ()  # solo una lista tiene opciones
    for name, kind, options, field in (
        ("", TEXT, None, "name"), ("x" * 41, TEXT, None, "name"), ("Ciudad", "color", None, "kind"), ("Tipo", CHOICE, ["Solo una"], "options"),
        ("Tipo", CHOICE, ["VIP", "vip"], "options"), ("Tipo", CHOICE, ["x" * 41, "y"], "options"), ("Tipo", CHOICE, None, "options"),
    ):
        with pytest.raises(FieldError) as error:
            NewField.checked(name=name, kind=kind, options=options)
        assert error.value.field == field, (name, kind, options)
    with pytest.raises(FieldError):
        FieldChange.checked({})


# ------------------------------------------------------------------ la API


class Tokens:
    def verify(self, token: str) -> Principal | None:
        return {"token-de-ana": ANA, "token-de-beto": BETO, "token-de-caro": CARO}.get(token)


def _as(user: str) -> dict[str, str]:
    return {"Authorization": f"Bearer token-de-{user}"}


@pytest.fixture
def platform(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'campos.sqlite3').as_posix()}")
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


def _create(client: TestClient, name: str, kind: str, options: list[str] | None = None, user: str = "ana"):
    return client.post(f"{BASE}/customer-fields", json={"name": name, "kind": kind, **({"options": options} if options else {})}, headers=_as(user))


def _set(client: TestClient, conversation_id: str, values: dict, user: str = "caro"):
    return client.patch(f"{BASE}/customers/{conversation_id}/fields", json={"values": values}, headers=_as(user))


def _shown(card: dict) -> dict[str, object]:
    return {item["field"]["name"]: item["value"] for item in card["fields"]}


def test_the_owner_creates_the_fields_and_an_advisor_cannot(platform):
    _engine, _store, client = platform
    city = _create(client, " Ciudad ", "text")
    assert city.status_code == 201 and city.json() == {"id": city.json()["id"], "name": "Ciudad", "kind": "text", "options": [], "filled": 0}
    kind = _create(client, "Tipo de cliente", "choice", ["Mayorista", "Al detal"]).json()
    assert kind["options"] == ["Mayorista", "Al detal"]
    assert _create(client, "Cumpleaños", "date").status_code == 201

    assert _create(client, "Zona", "text", user="caro").status_code == 403
    assert client.patch(f"{BASE}/customer-fields/{kind['id']}", json={"name": "Tipo"}, headers=_as("caro")).status_code == 403
    assert client.delete(f"{BASE}/customer-fields/{kind['id']}", headers=_as("caro")).status_code == 403
    repeated = _create(client, "ciudad", "text")
    assert repeated.status_code == 422 and repeated.json()["issues"] == [{"path": "name", "message": "Ya tienes un campo con ese nombre."}]
    assert _create(client, "Tipo", "choice", ["Una"]).json()["issues"][0]["path"] == "options"

    listed = client.get(f"{BASE}/customer-fields", headers=_as("caro")).json()  # la asesora los ve
    assert [item["name"] for item in listed["fields"]] == ["Ciudad", "Tipo de cliente", "Cumpleaños"]  # en el orden en que se crearon
    assert listed["kinds"] == ["text", "number", "date", "yes_no", "choice"] and listed["limits"]["fields"] == 30


def test_a_business_has_a_limit_of_fields(platform, monkeypatch):
    _engine, _store, client = platform
    monkeypatch.setattr(field_store, "MAX_FIELDS", 2)
    _create(client, "Uno", "text")
    _create(client, "Dos", "number")
    full = _create(client, "Tres", "text")
    assert full.status_code == 422 and "borra alguno" in full.json()["message"]


def test_the_team_fills_the_values_all_or_none_with_who_and_when(platform):
    _engine, store, client = platform
    laura = _chat(store, "573001", "Laura")
    city, budget, vip = (_create(client, name, kind).json()["id"] for name, kind in (("Ciudad", "text"), ("Presupuesto", "number"), ("Es VIP", "yes_no")))
    card = client.get(f"{BASE}/customers/{laura}", headers=_as("caro")).json()
    assert _shown(card) == {"Ciudad": None, "Presupuesto": None, "Es VIP": None}  # todos los campos, vacíos

    saved = _set(client, laura, {city: " Medellín ", budget: "1.500.000", vip: True})
    assert saved.status_code == 200
    assert {item["field"]["name"]: (item["value"], item["updated_by"]) for item in saved.json()["fields"]} == {
        "Ciudad": ("Medellín", "caro@example.com"), "Presupuesto": ("1500000", "caro@example.com"), "Es VIP": (True, "caro@example.com"),
    }

    # Un valor que no sirve: no cambia ninguno.
    refused = _set(client, laura, {city: "Bogotá", budget: "mucho"}, user="ana")
    assert refused.status_code == 422 and refused.json()["issues"] == [{"path": f"values.{budget}", "message": "Escribe un número."}]
    assert _shown(client.get(f"{BASE}/customers/{laura}", headers=_as("ana")).json())["Ciudad"] == "Medellín"

    # El mismo valor no cambia quién lo puso; en blanco lo vacía.
    again = _set(client, laura, {city: "Medellín", vip: ""}, user="ana").json()["fields"]
    assert [(item["value"], item["updated_by"]) for item in again if item["field"]["name"] in ("Ciudad", "Es VIP")] == [("Medellín", "caro@example.com"), (None, None)]
    assert client.get(f"{BASE}/customer-fields", headers=_as("ana")).json()["fields"][0]["filled"] == 1

    unknown = _set(client, laura, {"00000000-0000-0000-0000-000000000000": "x"})
    assert unknown.status_code == 422 and "ya no existe" in unknown.json()["message"]
    assert _set(client, laura, {}).status_code == 422


def test_removing_an_option_empties_it_and_deleting_a_field_deletes_its_values(platform):
    engine, store, client = platform
    laura, pedro = _chat(store, "573001", "Laura"), _chat(store, "573002", "Pedro")
    kind = _create(client, "Tipo", "choice", ["Mayorista", "Al detal", "vip"]).json()["id"]
    _set(client, laura, {kind: "Mayorista"})
    _set(client, pedro, {kind: "VIP"})
    assert _shown(client.get(f"{BASE}/customers/{pedro}", headers=_as("ana")).json())["Tipo"] == "vip"

    changed = client.patch(f"{BASE}/customer-fields/{kind}", json={"name": "Tipo de cliente", "options": ["VIP", "Al detal"]}, headers=_as("ana"))
    assert changed.json() == {"id": kind, "name": "Tipo de cliente", "kind": "choice", "options": ["VIP", "Al detal"], "filled": 1}
    assert _shown(client.get(f"{BASE}/customers/{laura}", headers=_as("ana")).json())["Tipo de cliente"] is None  # «Mayorista» se quitó
    assert _shown(client.get(f"{BASE}/customers/{pedro}", headers=_as("ana")).json())["Tipo de cliente"] == "VIP"  # la misma, escrita distinto

    city = _create(client, "Ciudad", "text").json()["id"]
    assert client.patch(f"{BASE}/customer-fields/{city}", json={"options": ["A", "B"]}, headers=_as("ana")).status_code == 422
    assert client.delete(f"{BASE}/customer-fields/{kind}", headers=_as("ana")).status_code == 204
    with engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(customer_field_values)).scalar_one() == 0
    assert list(_shown(client.get(f"{BASE}/customers/{pedro}", headers=_as("ana")).json())) == ["Ciudad"]


def test_nobody_reaches_the_fields_or_customers_of_another_business(platform):
    _engine, store, client = platform
    laura = _chat(store, "573001", "Laura")
    foreign_customer = _chat(store, "573009", "De otro negocio", business="saas")
    test_chat = _chat(store, "s1", "Prueba", channel="prueba")
    city = _create(client, "Ciudad", "text").json()["id"]
    foreign = client.post("/api/businesses/saas/customer-fields", json={"name": "Ciudad", "kind": "text"}, headers=_as("beto")).json()["id"]

    assert _set(client, foreign_customer, {city: "Cali"}).status_code == 404
    assert _set(client, test_chat, {city: "Cali"}).status_code == 404
    assert _set(client, laura, {foreign: "Cali"}).status_code == 422  # un campo de otro negocio no existe aquí
    for target in (foreign, "no-es-un-id"):
        assert client.patch(f"{BASE}/customer-fields/{target}", json={"name": "x"}, headers=_as("ana")).status_code == 404
        assert client.delete(f"{BASE}/customer-fields/{target}", headers=_as("ana")).status_code == 404
    assert client.get(f"{BASE}/customer-fields", headers=_as("beto")).status_code == 404
    assert client.patch(f"{BASE}/customers/{laura}/fields", json={"values": {city: "Cali"}}, headers=_as("beto")).status_code == 404
