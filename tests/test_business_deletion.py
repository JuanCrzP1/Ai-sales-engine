"""Eliminar un negocio desde el panel en la nube: todo lo suyo, para siempre, solo su dueño y escribiendo su nombre.

Con la base real (SQLite, con las mismas cascadas que las migraciones) y el panel «en la nube»:
- sin confirmar bien, o si no es su negocio, no se borra nada (uno ajeno responde como inexistente);
- primero se cierra WhatsApp: si el servidor de WhatsApp falla, no se borra nada; si la instancia ya no existía, se sigue;
- después no queda ni una fila del negocio en ninguna tabla, y los demás negocios siguen intactos;
- el motor olvida lo que tenía en memoria de sus clientes; si eso falla, el negocio igual queda borrado.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.admin_api.main import create_app
from app.business_config_application.access import BusinessAccess
from app.business_config_application.business_deletion import BusinessDeletionService
from app.domain.business_config.access import Principal
from app.domain.business_config.channels import ChannelError
from app.domain.business_config.conversations import NewMessage
from app.domain.business_config.errors import NotOwnerError
from app.infrastructure.business_config.api_key_store import ApiKeyStore
from app.infrastructure.business_config.attention_store import AttentionStore
from app.infrastructure.business_config.commerce_store import CommerceStore
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.business_config.example_businesses import import_example, load_example
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.notification_store import NotificationStore
from app.infrastructure.business_config.quick_reply_store import QuickReplyStore
from app.infrastructure.business_config.tables import business_members, metadata, tenants
from app.infrastructure.business_config.usage_store import UsageCounterStore
from app.infrastructure.persistence.memory_repository import MemoryRepository

ANA = Principal(user_id="usuario-ana", email="ana@example.com")
BETO = Principal(user_id="usuario-beto", email="beto@example.com")


class Tokens:
    def verify(self, token: str) -> Principal | None:
        return {"token-de-ana": ANA, "token-de-beto": BETO}.get(token)


class Connection:
    status = "connected"


class View:
    def __init__(self, connected: bool) -> None:
        self.connection = Connection() if connected else None


class WhatsApp:
    """El canal de WhatsApp: qué negocios tienen conexión y qué pasa al cerrarla."""

    available = True

    def __init__(self) -> None:
        self.connected = {"restaurant"}
        self.closed: list[str] = []
        self.fail: ChannelError | None = None

    def get(self, slug):
        return View(slug in self.connected)

    def disconnect(self, slug):
        if self.fail is not None:
            raise self.fail
        self.closed.append(slug)
        self.connected.discard(slug)


class Memory:
    def __init__(self) -> None:
        self.forgotten: list[str] = []
        self.fail = False

    def forget(self, business_slug, contact_ref):
        return None

    def forget_business(self, business_slug):
        if self.fail:
            raise RuntimeError("sin memoria")
        self.forgotten.append(business_slug)


def _as(user: str) -> dict[str, str]:
    return {"Authorization": f"Bearer token-de-{user}"}


@pytest.fixture
def cloud(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'borrar.sqlite3').as_posix()}")
    create_local_schema(engine)
    service = build_business_config_service(engine, secrets_key="x" * 43 + "=")
    for slug in ("restaurant", "clinic", "saas"):
        import_example(service, load_example(slug))
    with engine.begin() as conn:
        ids = {row.slug: row.id for row in conn.execute(select(tenants.c.slug, tenants.c.id))}
        for slug, user in (("restaurant", ANA), ("clinic", ANA), ("saas", BETO)):
            conn.execute(business_members.insert().values(tenant_id=ids[slug], user_id=user.user_id, role="owner", created_at=datetime.now(timezone.utc)))
    store = ConversationStore(engine)
    whatsapp, memory = WhatsApp(), Memory()
    app = create_app(
        service,
        access=BusinessAccess(service, BusinessMembersStore(engine)),
        verifier=Tokens(),
        conversations=store,
        notifications=NotificationStore(engine),
        usage=UsageCounterStore(engine),
        commerce=CommerceStore(engine),
        attention=AttentionStore(engine),
        api_keys=ApiKeyStore(engine),
        quick_replies=QuickReplyStore(engine),
        whatsapp=whatsapp,  # type: ignore[arg-type]
        contact_memory=memory,
    )
    yield TestClient(app), engine, store, whatsapp, memory, ids
    engine.dispose()


def _fill(client: TestClient, store: ConversationStore, slug: str = "restaurant") -> None:
    """Un negocio con un poco de todo: chats con aviso al equipo, una venta, atención humana, respuestas rápidas y claves."""
    chat = store.record(slug, channel="whatsapp", contact_ref="+571", contact_name="Laura", messages=[NewMessage("customer", "Quiero una persona")], handoff=True, handoff_reason="human_request")
    sale = {"customer_name": "Laura", "description": "Cena", "amount": "50000", "currency": "COP", "conversation_id": chat}
    assert client.post(f"/api/businesses/{slug}/sales", headers=_as("ana"), json=sale).status_code == 201
    attention = client.get(f"/api/businesses/{slug}/attention", headers=_as("ana")).json()
    payload = {key: attention[key] for key in ("hours_mode", "team_hours", "timezone", "reply_minutes", "resume_after_minutes", "email_enabled", "email_to")}
    assert client.put(f"/api/businesses/{slug}/attention", headers=_as("ana"), json={**payload, "reply_minutes": 30}).status_code == 200
    quick = {"shortcut": "precios", "category": "Precios", "pieces": [{"kind": "text", "text": "Hola {nombre}, te cuento los precios."}]}
    assert client.post(f"/api/businesses/{slug}/quick-replies", headers=_as("ana"), json=quick).status_code == 201
    for body in (
        {"name": "Leona", "reach": "one", "permissions": {"chat": "write"}},
        {"name": "Claude de algunos", "reach": "some", "businesses": [slug, "clinic"], "permissions": {"assistant": "read"}},
    ):
        assert client.post(f"/api/businesses/{slug}/api-keys", headers=_as("ana"), json=body).status_code == 201


def _rows_of(engine, tenant_id) -> dict[str, int]:
    """Cuántas filas tiene el negocio en cada tabla con `tenant_id`."""
    counts = {}
    with engine.connect() as conn:
        for table in metadata.sorted_tables:
            if "tenant_id" in table.c and table.name != "tenants":
                total = conn.execute(select(func.count()).select_from(table).where(table.c.tenant_id == tenant_id)).scalar_one()
                if total:
                    counts[table.name] = total
        counts["tenants"] = conn.execute(select(func.count()).select_from(tenants).where(tenants.c.id == tenant_id)).scalar_one()
    return counts


def test_the_owner_deletes_everything_of_the_business_and_nothing_else(cloud):
    client, engine, store, whatsapp, memory, ids = cloud
    _fill(client, store)
    _fill(client, store, "clinic")
    before = _rows_of(engine, ids["restaurant"])
    assert {"business_configs", "conversations", "sales", "notifications", "business_attention_settings", "quick_replies", "api_keys", "business_members"} <= set(before)
    clinic_before = _rows_of(engine, ids["clinic"])

    name = next(item["name"] for item in client.get("/api/businesses", headers=_as("ana")).json() if item["slug"] == "restaurant")
    # El nombre, sin importar mayúsculas ni espacios de más.
    deleted = client.delete("/api/businesses/restaurant", params={"confirm": f"  {name.upper()}  "}, headers=_as("ana"))
    assert deleted.status_code == 204, deleted.text

    assert _rows_of(engine, ids["restaurant"]) == {"tenants": 0}
    assert _rows_of(engine, ids["clinic"]) == clinic_before
    assert whatsapp.closed == ["restaurant"] and memory.forgotten == ["restaurant"]
    assert [item["slug"] for item in client.get("/api/businesses", headers=_as("ana")).json()] == ["clinic"]
    assert client.get("/api/businesses/restaurant/config", headers=_as("ana")).status_code == 404
    # La clave de la cuenta que entraba a «algunos» ya solo entra a la clínica.
    keys = {key["name"]: key for key in client.get("/api/businesses/clinic/api-keys", headers=_as("ana")).json()}
    assert keys["Claude de algunos"]["businesses"] == ["clinic"]


def test_without_the_right_name_or_by_someone_else_nothing_is_deleted(cloud):
    client, engine, _store, whatsapp, _memory, ids = cloud
    before = _rows_of(engine, ids["restaurant"])
    for confirm in ("", "otro negocio", "clinic"):
        refused = client.delete("/api/businesses/restaurant", params={"confirm": confirm}, headers=_as("ana"))
        assert refused.status_code == 422 and refused.json()["issues"][0]["path"] == "confirm", confirm
    theirs = client.delete("/api/businesses/restaurant", params={"confirm": "restaurant"}, headers=_as("beto"))
    missing = client.delete("/api/businesses/no_existe", params={"confirm": "no_existe"}, headers=_as("beto"))
    assert theirs.status_code == 404 and theirs.json() == missing.json()
    assert client.delete("/api/businesses/restaurant", params={"confirm": "restaurant"}).status_code == 401
    assert _rows_of(engine, ids["restaurant"]) == before and whatsapp.closed == []


def test_if_whatsapp_cannot_be_closed_nothing_is_deleted(cloud):
    client, engine, _store, whatsapp, memory, ids = cloud
    before = _rows_of(engine, ids["restaurant"])
    whatsapp.fail = ChannelError("El servidor de WhatsApp no responde")
    blocked = client.delete("/api/businesses/restaurant", params={"confirm": "restaurant"}, headers=_as("ana"))
    assert blocked.status_code == 409 and "no se eliminó nada" in blocked.json()["message"]
    assert _rows_of(engine, ids["restaurant"]) == before and memory.forgotten == []
    # Si la instancia ya no existía en el servidor, no hay nada que cerrar: se elimina.
    whatsapp.fail = ChannelError("ya no existe", gone=True)
    assert client.delete("/api/businesses/restaurant", params={"confirm": "restaurant"}, headers=_as("ana")).status_code == 204
    assert _rows_of(engine, ids["restaurant"]) == {"tenants": 0}


def test_a_business_without_whatsapp_and_a_memory_failure_still_get_deleted(cloud):
    client, engine, _store, whatsapp, memory, ids = cloud
    memory.fail = True
    assert client.delete("/api/businesses/clinic", params={"confirm": "clinic"}, headers=_as("ana")).status_code == 204
    assert whatsapp.closed == [] and _rows_of(engine, ids["clinic"]) == {"tenants": 0}


def test_only_the_owner_can_delete():
    class Members:
        def is_member(self, slug, user_id):
            return True

        def is_owner(self, slug, user_id):
            return False

        def slugs_of(self, user_id):
            return {"restaurant"}

    class Configs:
        def get_business(self, slug):
            raise AssertionError("no debe llegar aquí")

    service = BusinessDeletionService(Configs(), BusinessAccess(Configs(), Members()))  # type: ignore[arg-type]
    with pytest.raises(NotOwnerError):
        service.delete(ANA, "restaurant", "restaurant")


def test_agents_cannot_delete_businesses(cloud):
    client, *_ = cloud
    secret = client.post("/api/businesses/restaurant/api-keys", headers=_as("ana"), json={"name": "Agente", "reach": "all", "permissions": {"businesses": "write", "assistant": "write"}}).json()["secret"]
    tools = client.post("/api/mcp", headers={"Authorization": f"Bearer {secret}"}, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).json()["result"]["tools"]
    assert not [tool["name"] for tool in tools if "delete" in tool["name"]]


def test_the_engine_forgets_only_the_clients_of_that_business():
    memory = MemoryRepository()
    memory.save_message(tenant_slug="restaurant", user_id="+571", message_text="Hola")
    memory.save_message(tenant_slug="clinic", user_id="+571", message_text="Hola clínica")
    memory.forget_business(tenant_slug="Restaurant")
    assert memory.get_history(tenant_slug="restaurant", user_id="+571") == []
    assert [item["text"] for item in memory.get_history(tenant_slug="clinic", user_id="+571")] == ["Hola clínica"]
