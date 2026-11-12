"""El servidor MCP: un agente de IA trabaja en los negocios de una cuenta con una clave de API y sus permisos por área.

Cubre lo que importa de punta a punta, con la base real (SQLite) y el panel «en la nube» (cada usuario solo llega a lo suyo):
- sin clave válida (o vencida o revocada) no entra; el ritmo tiene límite;
- cada clave ve y usa solo lo que se le permitió, y solo en sus negocios: un negocio ajeno responde como inexistente;
- un agente monta un negocio completo: lo crea, lo configura (con datos de pago que nunca vuelve a ver), lo revisa, lo prueba y lo
  publica;
- lo que no cumple el contrato vuelve como error que el agente puede corregir, sin guardar nada.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.admin_api.main import create_app
from app.business_config_application import usage_limits as usage_module
from app.business_config_application.access import BusinessAccess
from app.business_config_application.assistant_lab import PlaygroundReply
from app.business_config_application.mcp.protocol import SUPPORTED_PROTOCOL_VERSIONS
from app.business_config_application.mcp.tool import invalid_arguments, obj, text
from app.domain.business_config.access import Principal
from app.domain.business_config.agent_edits import business_slug_for, merged, with_new_payment_values
from app.domain.business_config.ai_settings import AssistantTurn
from app.domain.business_config.config_changes import config_changes
from app.domain.business_config.errors import InvalidFieldsError
from app.domain.business_config.key_permissions import (
    SCOPE_ASSISTANT_CHAT,
    SCOPE_BUSINESSES_CREATE,
    SCOPE_CONFIG_WRITE,
    expiry_from,
    permissions_of,
    validated_permissions,
)
from app.domain.business_config.usage_limits import UsageLimit
from app.infrastructure.business_config.api_key_store import ApiKeyStore
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.business_config.example_businesses import import_example, load_example
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.tables import api_keys, business_members, tenants
from app.infrastructure.business_config.usage_store import UsageCounterStore

ANA = Principal(user_id="usuario-ana", email="ana@example.com")
BETO = Principal(user_id="usuario-beto", email="beto@example.com")
NEQUI = "3157778899"
LINK = "https://pagos.example.com/panaderia"
FULL = {"businesses": "write", "assistant": "write", "payments": "write"}


class Tokens:
    def verify(self, token: str) -> Principal | None:
        return {"token-de-ana": ANA, "token-de-beto": BETO}.get(token)


class FakeLab:
    asked: list[tuple[str, str, str]] = []

    def talk(self, tenant_slug, *, message, source="draft", session_id=None):
        FakeLab.asked.append((tenant_slug, message, source))
        return PlaygroundReply(session_id or "c" * 32, source, 1, AssistantTurn(reply="¡Hola! El pan cuesta $2.000.", intent="info"))


def _as(user: str) -> dict[str, str]:
    return {"Authorization": f"Bearer token-de-{user}"}


@pytest.fixture
def store(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'mcp.sqlite3').as_posix()}")
    create_local_schema(engine)
    service = build_business_config_service(engine, secrets_key="x" * 43 + "=")
    for slug in ("restaurant", "saas"):
        import_example(service, load_example(slug))
    with engine.begin() as conn:
        ids = {row.slug: row.id for row in conn.execute(select(tenants.c.slug, tenants.c.id))}
        for slug, user in (("restaurant", ANA), ("saas", BETO)):
            conn.execute(business_members.insert().values(tenant_id=ids[slug], user_id=user.user_id, role="owner", created_at=datetime.now(timezone.utc)))
    yield engine, service
    engine.dispose()


@pytest.fixture
def cloud(store):
    engine, service = store
    FakeLab.asked = []
    app = create_app(
        service,
        FakeLab(),
        access=BusinessAccess(service, BusinessMembersStore(engine)),
        verifier=Tokens(),
        usage=UsageCounterStore(engine),
        api_keys=ApiKeyStore(engine),
        mcp_url=lambda: "https://panel.example.com/api/mcp",
    )
    return TestClient(app), engine


def _key(client: TestClient, user: str = "ana", business: str = "restaurant", **body) -> str:
    payload = {"name": "Claude de prueba", "reach": "all", "permissions": FULL, **body}
    response = client.post(f"/api/businesses/{business}/api-keys", headers=_as(user), json=payload)
    assert response.status_code == 201, response.text
    return response.json()["secret"]


def _rpc(client: TestClient, secret: str, method: str, params: dict | None = None, message_id: int = 1):
    response = client.post("/api/mcp", headers={"Authorization": f"Bearer {secret}"}, json={"jsonrpc": "2.0", "id": message_id, "method": method, "params": params or {}})
    return response


def _call(client: TestClient, secret: str, tool: str, **arguments) -> dict:
    response = _rpc(client, secret, "tools/call", {"name": tool, "arguments": arguments})
    assert response.status_code == 200, response.text
    return response.json()["result"]


# ---------------------------------------------------------------------------
# Entrar
# ---------------------------------------------------------------------------

def test_without_a_valid_key_it_answers_401_and_only_accepts_post(cloud):
    client, _engine = cloud
    missing = client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
    assert missing.status_code == 401 and missing.headers["www-authenticate"].startswith("Bearer")
    wrong = client.post("/api/mcp", headers={"Authorization": "Bearer ase_live_" + "x" * 40}, json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
    assert wrong.status_code == 401 and 'error="invalid_token"' in wrong.headers["www-authenticate"]
    assert client.get("/api/mcp").status_code == 405


def test_initialize_negotiates_the_version_and_explains_the_rules(cloud):
    client, _engine = cloud
    secret = _key(client)
    result = _rpc(client, secret, "initialize", {"protocolVersion": "2025-03-26"}).json()["result"]
    assert result["protocolVersion"] == "2025-03-26" and result["serverInfo"]["name"] == "ai-sales-engine"
    assert "BORRADOR" in result["instructions"] and "Nunca inventes" in result["instructions"]
    unknown = _rpc(client, secret, "initialize", {"protocolVersion": "1999-01-01"}).json()["result"]
    assert unknown["protocolVersion"] == SUPPORTED_PROTOCOL_VERSIONS[0]
    assert _rpc(client, secret, "ping").json()["result"] == {}
    assert _rpc(client, secret, "resources/list").json()["error"]["code"] == -32601


def test_each_key_sees_only_the_tools_it_was_allowed(cloud):
    client, _engine = cloud
    reader = _key(client, reach="some", businesses=["restaurant"], permissions={"assistant": "read"})
    names = {tool["name"] for tool in _rpc(client, reader, "tools/list").json()["result"]["tools"]}
    assert names == {"read_platform_guide", "get_config_guide", "get_business_config", "review_business_config", "list_versions", "get_ai_settings", "list_ai_models"}
    full = {tool["name"]: tool for tool in _rpc(client, _key(client), "tools/list").json()["result"]["tools"]}
    assert {"create_business", "update_business_config", "publish_business_config", "test_assistant"} <= set(full)
    assert full["publish_business_config"]["annotations"]["destructiveHint"] is True
    assert full["get_business_config"]["annotations"]["readOnlyHint"] is True
    # Pedir una herramienta sin permiso es un error del protocolo, aunque no aparezca en la lista.
    denied = _rpc(client, reader, "tools/call", {"name": "update_business_config", "arguments": {"business": "restaurant", "changes": {}}}).json()
    assert denied["error"]["code"] == -32602 and "permiso" in denied["error"]["message"]


def test_an_expired_or_revoked_key_stops_working(cloud):
    client, engine = cloud
    secret = _key(client)
    assert _rpc(client, secret, "ping").status_code == 200
    with engine.begin() as conn:
        conn.execute(update(api_keys).values(expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)))
    assert _rpc(client, secret, "ping").status_code == 401
    other = _key(client, name="Otra")
    key_id = next(key["id"] for key in client.get("/api/businesses/restaurant/api-keys", headers=_as("ana")).json() if key["name"] == "Otra")
    assert client.post(f"/api/businesses/restaurant/api-keys/{key_id}/revoke", headers=_as("ana")).status_code == 200
    assert _rpc(client, other, "ping").status_code == 401


def test_a_key_has_a_rhythm_limit_and_messages_can_come_in_batches(cloud, monkeypatch):
    client, _engine = cloud
    secret = _key(client)
    headers = {"Authorization": f"Bearer {secret}"}
    batch = client.post("/api/mcp", headers=headers, json=[{"jsonrpc": "2.0", "id": 1, "method": "ping"}, {"jsonrpc": "2.0", "method": "notifications/initialized"}, {"jsonrpc": "2.0", "id": 2, "method": "ping"}])
    assert [reply["id"] for reply in batch.json()] == [1, 2]
    assert client.post("/api/mcp", headers=headers, json={"jsonrpc": "2.0", "method": "notifications/initialized"}).status_code == 202
    broken = client.post("/api/mcp", headers={**headers, "Content-Type": "application/json"}, content=b"{no es json")
    assert broken.status_code == 400 and broken.json()["error"]["code"] == -32700
    monkeypatch.setattr(usage_module, "MCP_PER_KEY", UsageLimit("mcp_key", limit=1, window_seconds=60))
    limited = _key(client, name="Con límite")
    assert _rpc(client, limited, "ping").status_code == 200
    second = _rpc(client, limited, "ping")
    assert second.status_code == 429 and int(second.headers["retry-after"]) >= 1


# ---------------------------------------------------------------------------
# Cada cliente, lo suyo
# ---------------------------------------------------------------------------

def test_a_key_never_reaches_another_clients_business(cloud):
    client, _engine = cloud
    ana = _key(client)
    names = [item["business"] for item in _call(client, ana, "list_businesses")["structuredContent"]["businesses"]]
    assert names == ["restaurant"]
    foreign = _call(client, ana, "get_business_config", business="saas")
    assert foreign["isError"] is True and foreign["structuredContent"]["error"] == "Ese negocio no existe o esta clave no entra a él. Usa list_businesses."
    # Beto no puede crear claves que entren a los negocios de Ana.
    stolen = client.post("/api/businesses/saas/api-keys", headers=_as("beto"), json={"name": "Robo", "reach": "some", "businesses": ["restaurant"], "permissions": FULL})
    assert stolen.status_code == 404
    # Una clave de algunos negocios no llega a los demás ni crea negocios.
    some = _key(client, reach="some", businesses=["restaurant"], permissions={"assistant": "write"})
    assert _call(client, some, "get_business_config", business="restaurant").get("isError") is None


def test_the_rules_of_a_key_are_checked_when_it_is_created(cloud):
    client, _engine = cloud
    base = "/api/businesses/restaurant/api-keys"
    chat_for_all = client.post(base, headers=_as("ana"), json={"name": "x", "reach": "all", "permissions": {"chat": "write"}})
    assert chat_for_all.status_code == 422 and chat_for_all.json()["issues"][0]["path"] == "permissions.chat"
    create_with_one = client.post(base, headers=_as("ana"), json={"name": "x", "reach": "one", "permissions": {"businesses": "write"}})
    assert create_with_one.status_code == 422 and create_with_one.json()["issues"][0]["path"] == "permissions.businesses"
    bad_expiry = client.post(base, headers=_as("ana"), json={"name": "x", "reach": "all", "permissions": FULL, "expires_in_days": 7})
    assert bad_expiry.status_code == 422 and bad_expiry.json()["issues"][0]["path"] == "expires_in_days"
    listed = client.get(base, headers=_as("ana")).json()
    assert listed == []
    _key(client, expires_in_days=30)
    key = client.get(base, headers=_as("ana")).json()[0]
    assert key["reach"] == "all" and key["permissions"] == FULL and key["expires_at"] and key["active"] is True
    # La clave de la cuenta de Ana no aparece en los negocios de Beto.
    assert client.get("/api/businesses/saas/api-keys", headers=_as("beto")).json() == []


# ---------------------------------------------------------------------------
# Montar un negocio completo
# ---------------------------------------------------------------------------

def test_an_agent_builds_a_complete_business_and_publishes_it_when_asked(cloud):
    client, _engine = cloud
    secret = _key(client)
    responses: list[str] = []

    def call(tool: str, **arguments) -> dict:
        result = _call(client, secret, tool, **arguments)
        responses.append(json.dumps(result, ensure_ascii=False))
        assert result.get("isError") is None, result
        return result["structuredContent"]

    guide = call("read_platform_guide")["guide"]
    assert "Montar un negocio completo" in guide and "Nunca inventes" in guide
    templates = [item["template"] for item in call("list_business_templates")["templates"]]
    assert "restaurante" in templates
    created = call("create_business", name="Panadería La Esquina", template="restaurante")
    business = created["business"]
    assert business == "panaderia_la_esquina" and created["status"] == "sin publicar"
    payments_guide = call("get_config_guide", section="pagos")
    assert "payments" in payments_guide["schema"]["properties"] and "TransferMethod" in payments_guide["schema"]["$defs"]

    current = call("get_business_config", business=business)
    assert current["publication"] == "never" and current["document"]["identity"]["name"] == "Panadería La Esquina"
    saved = call(
        "update_business_config",
        business=business,
        base_version=current["latest_version"],
        changes={
            "identity": {"description": "Pan artesanal recién horneado en el barrio.", "brand_name": "La Esquina"},
            "payments": [{"id": "principal", "transfer_enabled": True, "link_enabled": True, "link": {"value": LINK}, "transfer_methods": [{"type": "nequi", "number": {"value": NEQUI}}]}],
        },
    )
    assert saved["status"] == "borrador" and saved["payment_values_saved"] == 2

    after = call("get_business_config", business=business, section="pagos")
    profile = after["document"]["payments"][0]
    assert profile["transfer_methods"][0]["number"]["secret_ref"].startswith("secret_store:")
    states = {state["masked"] for state in after["payment_fields"].values()}
    assert "••••8899" in states
    review = call("review_business_config", business=business)
    assert review["first_publication"] is True and review["can_publish"] is True and review["changes"] == []
    # El agente ve los mismos avisos que el panel, con su campo: la plantilla tiene local físico pero no dirección.
    assert {"field": "identity.location.address", "message": "Sin dirección, el asistente no podrá decir dónde queda tu local."} in review["warnings"]

    reply = call("test_assistant", business=business, message="¿Cuánto cuesta el pan?")
    assert reply["reply"].startswith("¡Hola!") and FakeLab.asked[-1] == (business, "¿Cuánto cuesta el pan?", "draft")

    published = call("publish_business_config", business=business)
    assert published["published_version"] == saved["saved_version"]
    assert call("get_business_config", business=business)["publication"] == "published"

    # Un cambio después de publicar se ve en la revisión, con cómo estaba y cómo queda.
    call("update_business_config", business=business, changes={"identity": {"brand_name": "Panadería La Esquina 2"}})
    changes = call("review_business_config", business=business)["changes"]
    assert {"path": "identity.brand_name", "kind": "changed", "before": "La Esquina", "after": "Panadería La Esquina 2", "protected": False} in changes

    # El negocio es de Ana: lo ve en su panel, y Beto no.
    assert business in [item["slug"] for item in client.get("/api/businesses", headers=_as("ana")).json()]
    assert business not in [item["slug"] for item in client.get("/api/businesses", headers=_as("beto")).json()]
    versions = call("list_versions", business=business)["versions"]
    # Todas, también la primera (la de la plantilla al crear el negocio), quedan a nombre del agente y de su dueño.
    assert all(item["created_by"] == "Agente «Claude de prueba» (ana@example.com)" for item in versions)
    # Ningún dato de pago salió jamás hacia el agente.
    assert not any(NEQUI in text_ or LINK in text_ for text_ in responses)


def test_what_breaks_the_contract_comes_back_to_be_fixed_and_nothing_is_saved(cloud):
    client, _engine = cloud
    secret = _key(client)
    before = _call(client, secret, "list_versions", business="restaurant")["structuredContent"]["versions"]
    broken = _call(client, secret, "update_business_config", business="restaurant", changes={"offer": {"model": "suscripcion"}, "identity": {"name": None}})
    assert broken["isError"] is True
    issues = {issue["path"]: issue for issue in broken["structuredContent"]["issues"]}
    assert "identity.name" in issues and "offer.model" in issues and "options" in issues["offer.model"]
    assert _call(client, secret, "list_versions", business="restaurant")["structuredContent"]["versions"] == before
    current = _call(client, secret, "get_business_config", business="restaurant")["structuredContent"]["document"]
    items = current["offer"]["catalog"]["items"]
    items[0]["id"] = "pan_aliñado"
    accent = _call(client, secret, "update_business_config", business="restaurant", changes={"offer": {"catalog": {"items": items}}})
    assert accent["isError"] is True and "sin tildes ni ñ" in accent["structuredContent"]["issues"][0]["message"]
    stray = _call(client, secret, "update_business_config", business="restaurant", changes={"identity": {"description": {"value": NEQUI}}})
    assert stray["isError"] is True and NEQUI not in json.dumps(stray)
    latest = _call(client, secret, "get_business_config", business="restaurant")["structuredContent"]["latest_version"]
    conflict = _call(client, secret, "update_business_config", business="restaurant", base_version=latest - 1, changes={"identity": {"brand_name": "X"}})
    assert conflict["isError"] is True and "cambió" in conflict["structuredContent"]["error"]


def test_payment_data_needs_its_own_permission(cloud):
    client, _engine = cloud
    secret = _key(client, permissions={"assistant": "write"}, reach="some", businesses=["restaurant"])
    result = _call(client, secret, "update_business_config", business="restaurant", changes={"payments": [{"id": "principal", "transfer_enabled": True, "transfer_methods": [{"type": "nequi", "number": {"value": NEQUI}}]}]})
    assert result["isError"] is True and "datos de pago" in result["structuredContent"]["error"]
    create = _rpc(client, secret, "tools/call", {"name": "create_business", "arguments": {"name": "Otro"}}).json()
    assert create["error"]["code"] == -32602


def test_arguments_are_checked_before_running_anything(cloud):
    client, _engine = cloud
    secret = _key(client)
    unknown = _rpc(client, secret, "tools/call", {"name": "get_business_config", "arguments": {"business": "restaurant", "seccion": "x"}}).json()
    assert unknown["error"]["code"] == -32602 and "seccion" in unknown["error"]["message"]
    wrong = _rpc(client, secret, "tools/call", {"name": "get_config_guide", "arguments": {"section": "todo"}}).json()
    assert "negocio" in wrong["error"]["message"]
    missing = _rpc(client, secret, "tools/call", {"name": "test_assistant", "arguments": {"business": "restaurant"}}).json()
    assert missing["error"]["message"] == "Falta «message»."


# ---------------------------------------------------------------------------
# Las piezas puras
# ---------------------------------------------------------------------------

def test_a_partial_change_merges_objects_replaces_lists_and_removes_with_null():
    document = {"identity": {"name": "A", "brand_name": "B", "differentiators": ["x", "y"]}, "messages": {"welcome": "Hola"}}
    result = merged(document, {"identity": {"brand_name": None, "differentiators": ["z"]}, "messages": {"fallback": "Ya vuelvo"}})
    assert result == {"identity": {"name": "A", "differentiators": ["z"]}, "messages": {"welcome": "Hola", "fallback": "Ya vuelvo"}}
    assert document["identity"]["brand_name"] == "B"


def test_payment_values_become_references_and_only_where_they_belong():
    document, values = with_new_payment_values(
        {"payments": [{"id": "principal", "link": {"value": LINK}, "transfer_methods": [{"type": "nequi", "number": {"value": NEQUI}}]}]},
        new_id=lambda: "abc",
    )
    assert document["payments"][0]["link"] == {"secret_ref": "secret_store:principal.link.agente_abc"}
    assert values == {"secret_store:principal.link.agente_abc": LINK, "secret_store:principal.nequi.number.agente_abc": NEQUI}
    with pytest.raises(InvalidFieldsError) as error:
        with_new_payment_values({"identity": {"description": {"value": NEQUI}}})
    assert [issue.path for issue in error.value.issues] == ["identity.description"]


def test_a_business_identifier_comes_from_its_name_and_never_repeats():
    assert business_slug_for("Panadería La Esquina!", []) == "panaderia_la_esquina"
    assert business_slug_for("Panadería La Esquina", ["panaderia_la_esquina"]) == "panaderia_la_esquina_2"
    assert business_slug_for("¡¡!!", []) == "negocio"


def test_what_changes_pairs_list_items_and_hides_payment_data():
    before = {"knowledge": {"faqs": [{"question": "¿Hay envío?", "answer": "No"}]}, "payments": [{"id": "p", "link": {"secret_ref": "secret_store:a~1"}}]}
    after = {"knowledge": {"faqs": [{"question": "¿Hay envío?", "answer": "Sí"}, {"question": "¿Abren domingo?", "answer": "Sí"}]}, "payments": [{"id": "p", "link": {"secret_ref": "secret_store:a~2"}}]}
    changes = {change.path: change for change in config_changes(before, after)}
    assert changes["knowledge.faqs[¿Hay envío?].answer"].after == "Sí"
    assert changes["knowledge.faqs[¿Abren domingo?]"].kind == "added"
    secret = changes["payments[p].link"]
    assert secret.protected and secret.before is None and secret.after is None
    assert config_changes(None, after) == [] and config_changes(after, after) == []


def test_permissions_by_area_and_their_rules():
    scopes = validated_permissions({"businesses": "write", "assistant": "read"}, "all")
    assert SCOPE_BUSINESSES_CREATE in scopes and SCOPE_CONFIG_WRITE not in scopes
    assert permissions_of(scopes) == {"businesses": "write", "assistant": "read"}
    assert validated_permissions({"chat": "write"}, "one") == (SCOPE_ASSISTANT_CHAT,)
    for permissions, reach in (({}, "all"), ({"chat": "write"}, "some"), ({"payments": "read"}, "all"), ({"desconocida": "write"}, "all")):
        if permissions == {"desconocida": "write"}:
            with pytest.raises(InvalidFieldsError):
                validated_permissions(permissions, reach)
            continue
        with pytest.raises(InvalidFieldsError):
            validated_permissions(permissions, reach)
    now = datetime(2026, 11, 12, tzinfo=timezone.utc)
    assert expiry_from(90, now) == now + timedelta(days=90) and expiry_from(None, now) is None


def test_the_argument_check_reads_nested_schemas():
    schema = obj({"name": text("Nombre."), "items": {"type": "array", "items": {"type": "integer"}}}, ("name",))
    assert invalid_arguments(schema, {"name": "x", "items": [1, 2]}) is None
    assert invalid_arguments(schema, {"name": "x", "items": [1, "dos"]}) == "«items[1]» debe ser de tipo integer."
    assert invalid_arguments(schema, {}) == "Falta «name»."


def test_an_old_local_database_upgrades_its_keys_without_losing_them(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'vieja.sqlite3').as_posix()}")
    create_local_schema(engine)
    service = build_business_config_service(engine, secrets_key="x" * 43 + "=")
    import_example(service, load_example("restaurant"))
    with engine.begin() as conn:
        tenant = conn.execute(select(tenants.c.id)).scalar_one()
        conn.exec_driver_sql("DROP TABLE api_key_businesses")
        conn.exec_driver_sql("DROP TABLE api_keys")
        conn.exec_driver_sql(
            "CREATE TABLE api_keys (id CHAR(32) PRIMARY KEY, tenant_id CHAR(32) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, name TEXT NOT NULL, "
            "prefix TEXT NOT NULL, key_hash TEXT NOT NULL, scopes JSON NOT NULL, created_by TEXT, created_at DATETIME NOT NULL, last_used_at DATETIME, revoked_at DATETIME)"
        )
        conn.exec_driver_sql(
            "INSERT INTO api_keys (id, tenant_id, name, prefix, key_hash, scopes, created_at) VALUES (?, ?, 'Leona', 'ase_live_Ab12Cd', ?, ?, ?)",
            ("a" * 32, tenant.hex, "f" * 64, json.dumps([SCOPE_ASSISTANT_CHAT]), datetime.now(timezone.utc).isoformat(" ")),
        )
    create_local_schema(engine)
    keys = ApiKeyStore(engine).list_keys("restaurant", local=True)
    assert [(key.name, key.reach.kind, key.business_slug) for key in keys] == [("Leona", "one", "restaurant")]
    engine.dispose()
