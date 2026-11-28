"""Las etiquetas de los clientes: el catálogo de cada negocio, las que lleva cada cliente y filtrar por una.

Con la base real (SQLite) y la API del panel «en la nube»:
- el catálogo es de cada negocio: nombre y color, por orden, con cuántos clientes lleva cada etiqueta; no hay dos que se lean igual
  (mayúsculas, acentos, espacios o caracteres invisibles) y hay un máximo;
- quien atiende (también un asesor) crea etiquetas, les cambia el color y se las pone a sus clientes; cambiarles el nombre y
  borrarlas es del dueño o de un administrador; al borrar una, sus clientes solo la pierden;
- las etiquetas de un cliente salen en la lista, en el tablero y en su ficha, y el tablero y la lista se filtran por una;
- nadie alcanza las etiquetas ni los clientes de otro negocio.
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
from app.domain.business_config.customer_labels import LabelChange, LabelError, checked_color, checked_name, checked_selection, label_key
from app.infrastructure.business_config import label_store
from app.infrastructure.business_config.commerce_store import CommerceStore
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.business_config.example_businesses import import_example, load_example
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.notification_store import NotificationStore
from app.infrastructure.business_config.tables import business_members, conversation_labels, tenants
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
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'etiquetas.sqlite3').as_posix()}")
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


def _create(client: TestClient, name: str, color: str | None = None, user: str = "ana", base: str = BASE):
    body = {"name": name} if color is None else {"name": name, "color": color}
    return client.post(f"{base}/labels", json=body, headers=_as(user))


def _catalog(client: TestClient, user: str = "ana") -> list[tuple[str, str, int]]:
    return [(item["name"], item["color"], item["customers"]) for item in client.get(f"{BASE}/labels", headers=_as(user)).json()["labels"]]


def _assign(client: TestClient, conversation_id: str, label_ids: list[str], user: str = "ana"):
    return client.put(f"{BASE}/customers/{conversation_id}/labels", json={"label_ids": label_ids}, headers=_as(user))


# ------------------------------------------------------------------ las reglas


def test_two_labels_that_read_the_same_are_the_same_label():
    assert label_key("VIP") == label_key(" vip ") == label_key("Ví​p") == "vip"
    assert label_key("Niño  mayorista") == "nino mayorista" != label_key("Niña mayorista")
    assert checked_name("  Llamar​   el lunes ") == "Llamar el lunes"
    for name in ("", "  ​ ", "x" * 31):
        with pytest.raises(LabelError) as error:
            checked_name(name)
        assert error.value.field == "name"
    assert checked_color(None) == "slate" and checked_color(" Blue ") == "blue"
    with pytest.raises(LabelError) as error:
        checked_color("#ff0000")
    assert error.value.field == "color"


def test_a_change_and_a_selection_bring_only_what_works():
    assert LabelChange.checked({"color": "green"}) == LabelChange(None, "green")
    assert LabelChange.checked({"name": " Mayorista "}) == LabelChange("Mayorista", None)
    with pytest.raises(LabelError):
        LabelChange.checked({})
    assert checked_selection(["a", " b ", "a", ""]) == ["a", "b"]
    for selection in ("a", [str(n) for n in range(11)]):
        with pytest.raises(LabelError) as error:
            checked_selection(selection)
        assert error.value.field == "label_ids"


# ------------------------------------------------------------------ el catálogo


def test_the_catalog_belongs_to_the_business_and_has_no_repeated_names(platform, monkeypatch):
    _engine, _store, client = platform
    created = _create(client, "  Mayorista ", "green", user="caro")  # una asesora también crea
    assert created.status_code == 201 and (created.json()["name"], created.json()["color"], created.json()["customers"]) == ("Mayorista", "green", 0)
    assert _create(client, "VIP").json()["color"] == "slate"
    for repeated in ("mayorista", " MAYORISTA ", "Mayorísta", "May​orista"):
        refused = _create(client, repeated)
        assert refused.status_code == 422 and refused.json()["issues"] == [{"path": "name", "message": "Ya tienes una etiqueta con ese nombre."}]
    assert _create(client, "", "green").status_code == 422 and _create(client, "Roja", "rojo").json()["issues"][0]["path"] == "color"
    listed = client.get(f"{BASE}/labels", headers=_as("ana")).json()
    assert [item["name"] for item in listed["labels"]] == ["Mayorista", "VIP"] and "green" in listed["colors"]

    # El otro negocio tiene su propio catálogo: puede repetir el nombre y no ve el del restaurante.
    assert _create(client, "Mayorista", user="beto", base="/api/businesses/saas").status_code == 201
    assert client.get(f"{BASE}/labels", headers=_as("beto")).status_code == 404

    monkeypatch.setattr(label_store, "MAX_LABELS", 2)
    full = _create(client, "Otra")
    assert full.status_code == 422 and "borra alguna" in full.json()["message"]


def test_whoever_attends_changes_the_color_but_renaming_and_deleting_is_for_who_configures(platform):
    _engine, store, client = platform
    label = _create(client, "Mayorista").json()["id"]
    _create(client, "VIP")
    recolored = client.patch(f"{BASE}/labels/{label}", json={"color": "amber"}, headers=_as("caro"))
    assert recolored.status_code == 200 and recolored.json()["color"] == "amber"
    assert client.patch(f"{BASE}/labels/{label}", json={"name": "Al por mayor"}, headers=_as("caro")).status_code == 403
    assert client.delete(f"{BASE}/labels/{label}", headers=_as("caro")).status_code == 403

    renamed = client.patch(f"{BASE}/labels/{label}", json={"name": " Al por mayor "}, headers=_as("ana")).json()
    assert (renamed["name"], renamed["color"]) == ("Al por mayor", "amber")
    assert client.patch(f"{BASE}/labels/{label}", json={"name": "al por MAYOR"}, headers=_as("ana")).status_code == 200  # su propio nombre
    taken = client.patch(f"{BASE}/labels/{label}", json={"name": "vip"}, headers=_as("ana"))
    assert taken.status_code == 422 and taken.json()["issues"][0]["path"] == "name"
    assert client.patch(f"{BASE}/labels/{label}", json={}, headers=_as("ana")).status_code == 422

    foreign = _create(client, "Ajena", user="beto", base="/api/businesses/saas").json()["id"]
    for target in (foreign, "no-es-un-id"):
        assert client.patch(f"{BASE}/labels/{target}", json={"color": "red"}, headers=_as("ana")).status_code == 404
        assert client.delete(f"{BASE}/labels/{target}", headers=_as("ana")).status_code == 404


# ------------------------------------------------------------------ las de cada cliente


def test_a_customer_wears_labels_and_they_show_in_the_list_the_board_and_the_card(platform):
    _engine, store, client = platform
    ana, beto = _chat(store, "573001", "Ana"), _chat(store, "573002", "Beto")
    vip, wholesale = _create(client, "VIP", "violet").json()["id"], _create(client, "Mayorista", "green").json()["id"]
    assigned = _assign(client, ana, [vip, wholesale, vip], user="caro")  # una asesora también las pone
    assert assigned.status_code == 200 and [(l["name"], l["color"]) for l in assigned.json()["labels"]] == [("Mayorista", "green"), ("VIP", "violet")]
    _assign(client, beto, [vip])

    listed = {item["name"]: [l["name"] for l in item["labels"]] for item in client.get(f"{BASE}/customers", headers=_as("ana")).json()}
    assert listed == {"Ana": ["Mayorista", "VIP"], "Beto": ["VIP"]}
    card = client.get(f"{BASE}/customers/{ana}", headers=_as("ana")).json()
    assert [l["name"] for l in card["customer"]["labels"]] == ["Mayorista", "VIP"]
    board = client.get(f"{BASE}/pipeline", headers=_as("ana")).json()
    assert {c["name"]: len(c["labels"]) for c in board["columns"][0]["customers"]} == {"Ana": 2, "Beto": 1}
    assert _catalog(client) == [("Mayorista", "green", 1), ("VIP", "violet", 2)]

    # Dejarlo sin ninguna.
    assert _assign(client, ana, []).json()["labels"] == [] and _catalog(client)[0] == ("Mayorista", "green", 0)


def test_the_board_and_the_list_filter_by_a_label_and_the_numbers_still_count_everyone(platform):
    _engine, store, client = platform
    ana, _beto, _caro = _chat(store, "573001", "Ana"), _chat(store, "573002", "Beto"), _chat(store, "573003", "Caro")
    vip = _create(client, "VIP").json()["id"]
    _assign(client, ana, [vip])
    board = client.get(f"{BASE}/pipeline", params={"label": vip}, headers=_as("ana")).json()
    assert board["columns"][0]["count"] == 1 and [c["name"] for c in board["columns"][0]["customers"]] == ["Ana"]
    assert board["stats"]["open_count"] == 3
    assert [c["name"] for c in client.get(f"{BASE}/customers", params={"label": vip}, headers=_as("ana")).json()] == ["Ana"]
    assert client.get(f"{BASE}/customers", params={"label": vip, "q": "beto"}, headers=_as("ana")).json() == []
    # Una etiqueta que no existe no la lleva nadie.
    assert client.get(f"{BASE}/customers", params={"label": "no-existe"}, headers=_as("ana")).json() == []


def test_deleting_a_label_only_takes_it_off_its_customers(platform):
    engine, store, client = platform
    ana = _chat(store, "573001", "Ana")
    vip, wholesale = _create(client, "VIP").json()["id"], _create(client, "Mayorista").json()["id"]
    _assign(client, ana, [vip, wholesale])
    assert client.delete(f"{BASE}/labels/{vip}", headers=_as("ana")).status_code == 204
    assert client.delete(f"{BASE}/labels/{vip}", headers=_as("ana")).status_code == 404
    assert [l["name"] for l in client.get(f"{BASE}/customers", headers=_as("ana")).json()[0]["labels"]] == ["Mayorista"]
    with engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(conversation_labels)).scalar_one() == 1


def test_nobody_labels_a_customer_of_another_business_or_with_a_foreign_label(platform):
    _engine, store, client = platform
    ana = _chat(store, "573001", "Ana")
    foreign_customer = _chat(store, "573009", "De otro negocio", business="saas")
    test_chat = _chat(store, "s1", "Prueba", channel="prueba")
    vip = _create(client, "VIP").json()["id"]
    foreign_label = _create(client, "Ajena", user="beto", base="/api/businesses/saas").json()["id"]
    for conversation in (foreign_customer, test_chat, "no-es-un-id"):
        assert _assign(client, conversation, [vip]).status_code == 404
    assert _assign(client, ana, [vip, foreign_label]).status_code == 404  # una etiqueta de otro negocio no existe aquí
    assert client.get(f"{BASE}/customers", headers=_as("ana")).json()[0]["labels"] == []  # y no quedó a medias
    assert _assign(client, ana, [vip], user="beto").status_code == 404
    too_many = _assign(client, ana, [f"etiqueta-{n}" for n in range(11)])
    assert too_many.status_code == 422 and too_many.json()["issues"][0]["path"] == "label_ids"
