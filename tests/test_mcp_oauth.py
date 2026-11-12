"""Conectar un agente con inicio de sesión (OAuth 2.1): lo que hacen Claude (web y app) y ChatGPT al pegar la dirección del servidor.

De punta a punta, con la base real (SQLite) y el panel «en la nube»:
- el agente descubre dónde iniciar sesión (401 → metadatos del recurso → metadatos del servidor) y se registra solo;
- la persona, con su sesión, ve qué agente pide acceso y autoriza con los permisos y negocios que elige (o rechaza);
- el agente cambia el código por tokens con PKCE; el código sirve una vez; renovar cambia el token de renovación;
- con el token entra al servidor MCP con exactamente lo autorizado; la conexión aparece en «Claves de API» y revocarla lo corta.
"""
from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin_api.main import create_app
from app.business_config_application.access import BusinessAccess
from app.domain.business_config.access import Principal
from app.domain.business_config.oauth import (
    OAuthClient,
    OAuthError,
    is_allowed_redirect_uri,
    oauth_addresses,
    pkce_matches,
    read_authorization_request,
    read_client_registration,
    redirect_with,
    resource_metadata_url,
)
from app.infrastructure.business_config.api_key_store import ApiKeyStore
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.business_config.example_businesses import import_example, load_example
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.oauth_store import OAuthStore
from app.infrastructure.business_config.tables import business_members, mcp_oauth_tokens, tenants
from app.infrastructure.business_config.usage_store import UsageCounterStore

ANA = Principal(user_id="usuario-ana", email="ana@example.com")
BETO = Principal(user_id="usuario-beto", email="beto@example.com")
MCP_URL = "https://panel.example.com/api/mcp"
CALLBACK = "https://claude.ai/api/mcp/auth_callback"
VERIFIER = "v" * 64
CHALLENGE = base64.urlsafe_b64encode(hashlib.sha256(VERIFIER.encode()).digest()).rstrip(b"=").decode()


class Tokens:
    def verify(self, token: str) -> Principal | None:
        return {"token-de-ana": ANA, "token-de-beto": BETO}.get(token)


def _as(user: str) -> dict[str, str]:
    return {"Authorization": f"Bearer token-de-{user}"}


@pytest.fixture
def cloud(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'oauth.sqlite3').as_posix()}")
    create_local_schema(engine)
    service = build_business_config_service(engine, secrets_key="x" * 43 + "=")
    for slug in ("restaurant", "clinic", "saas"):
        import_example(service, load_example(slug))
    with engine.begin() as conn:
        ids = {row.slug: row.id for row in conn.execute(select(tenants.c.slug, tenants.c.id))}
        for slug, user in (("restaurant", ANA), ("clinic", ANA), ("saas", BETO)):
            conn.execute(business_members.insert().values(tenant_id=ids[slug], user_id=user.user_id, role="owner", created_at=datetime.now(timezone.utc)))
    app = create_app(
        service,
        access=BusinessAccess(service, BusinessMembersStore(engine)),
        verifier=Tokens(),
        usage=UsageCounterStore(engine),
        api_keys=ApiKeyStore(engine),
        mcp_url=lambda: MCP_URL,
        oauth=OAuthStore(engine),
    )
    yield TestClient(app), engine
    engine.dispose()


def _register(client: TestClient, **extra) -> str:
    response = client.post("/api/oauth/register", json={"client_name": "Claude", "redirect_uris": [CALLBACK], "token_endpoint_auth_method": "none", **extra})
    assert response.status_code == 201, response.text
    return response.json()["client_id"]


def _params(client_id: str, **extra) -> dict[str, str]:
    return {
        "client_id": client_id, "redirect_uri": CALLBACK, "response_type": "code", "code_challenge": CHALLENGE,
        "code_challenge_method": "S256", "state": "estado-del-agente", "resource": MCP_URL, **extra,
    }


def _authorize(client: TestClient, client_id: str, user: str = "ana", **decision) -> dict[str, list[str]]:
    body = {"params": _params(client_id), "approve": True, "permissions": {"assistant": "read"}, "reach": "all", **decision}
    response = client.post("/api/oauth/authorize/decision", headers=_as(user), json=body)
    assert response.status_code == 200, response.text
    target = urlsplit(response.json()["redirect_to"])
    assert f"{target.scheme}://{target.netloc}{target.path}" == CALLBACK
    return parse_qs(target.query)


def _exchange(client: TestClient, client_id: str, code: str, verifier: str = VERIFIER):
    return client.post(
        "/api/oauth/token",
        data={"grant_type": "authorization_code", "code": code, "client_id": client_id, "redirect_uri": CALLBACK, "code_verifier": verifier, "resource": MCP_URL},
    )


def _connect(client: TestClient, user: str = "ana", **decision) -> tuple[str, dict]:
    client_id = _register(client)
    code = _authorize(client, client_id, user, **decision)["code"][0]
    tokens = _exchange(client, client_id, code)
    assert tokens.status_code == 200, tokens.text
    return client_id, tokens.json()


def _mcp(client: TestClient, token: str, method: str, params: dict | None = None):
    return client.post("/api/mcp", headers={"Authorization": f"Bearer {token}"}, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}})


# ---------------------------------------------------------------------------
# Descubrir y registrarse
# ---------------------------------------------------------------------------

def test_the_agent_discovers_where_to_sign_in_from_the_401(cloud):
    client, _engine = cloud
    challenge = client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"}).headers["www-authenticate"]
    assert 'resource_metadata="https://panel.example.com/.well-known/oauth-protected-resource/api/mcp"' in challenge
    resource = client.get("/api/.well-known/oauth-protected-resource/api/mcp").json()
    assert resource["resource"] == MCP_URL and resource["authorization_servers"] == ["https://panel.example.com"]
    server = client.get("/api/.well-known/oauth-authorization-server").json()
    assert server["authorization_endpoint"] == "https://panel.example.com/oauth/authorize"
    assert server["token_endpoint"] == "https://panel.example.com/api/oauth/token"
    assert server["registration_endpoint"] == "https://panel.example.com/api/oauth/register"
    assert server["code_challenge_methods_supported"] == ["S256"] and server["token_endpoint_auth_methods_supported"] == ["none"]
    # Como llegan reenviadas por el panel (`vercel.json`): con barra final, sin redirigir.
    for path in ("/api/.well-known/oauth-authorization-server/", "/api/.well-known/oauth-protected-resource/"):
        assert client.get(path, follow_redirects=False).status_code == 200, path


def test_registration_accepts_only_safe_return_addresses(cloud):
    client, _engine = cloud
    registered = client.post("/api/oauth/register", json={"client_name": "Claude", "redirect_uris": [CALLBACK, "http://127.0.0.1:33418/callback"]})
    assert registered.status_code == 201 and registered.headers["cache-control"].startswith("no-store")
    assert registered.json()["token_endpoint_auth_method"] == "none"
    for uris in ([], ["http://evil.example.com/cb"], ["https://claude.ai/cb#frag"], ["javascript:alert(1)"]):
        refused = client.post("/api/oauth/register", json={"redirect_uris": uris})
        assert refused.status_code == 400 and refused.json()["error"] == "invalid_redirect_uri", uris
    secret_client = client.post("/api/oauth/register", json={"redirect_uris": [CALLBACK], "token_endpoint_auth_method": "client_secret_basic"})
    assert secret_client.json()["error"] == "invalid_client_metadata"


# ---------------------------------------------------------------------------
# Autorizar
# ---------------------------------------------------------------------------

def test_the_consent_screen_needs_a_session_and_says_who_asks(cloud):
    client, _engine = cloud
    client_id = _register(client)
    assert client.get("/api/oauth/authorize/request", params=_params(client_id)).status_code == 401
    prompt = client.get("/api/oauth/authorize/request", params=_params(client_id), headers=_as("ana")).json()
    assert prompt["ready"] is True and prompt["client_name"] == "Claude" and prompt["redirect_host"] == "claude.ai"
    assert "chat" not in {area["id"] for area in prompt["areas"]} and {"assistant", "conversations"} <= {area["id"] for area in prompt["areas"]}
    # Una dirección de regreso que no es la registrada no se devuelve al agente: se muestra en el panel.
    foreign = client.get("/api/oauth/authorize/request", params=_params(client_id, redirect_uri="https://evil.example.com/cb"), headers=_as("ana")).json()
    assert foreign["ready"] is False and foreign["redirect_to"] is None
    # Sin PKCE, sí se le avisa al agente por su dirección.
    no_pkce = client.get("/api/oauth/authorize/request", params=_params(client_id, code_challenge_method="plain"), headers=_as("ana")).json()
    assert no_pkce["ready"] is False and no_pkce["redirect_to"].startswith(CALLBACK) and "error=invalid_request" in no_pkce["redirect_to"]


def test_declining_sends_the_agent_back_with_access_denied(cloud):
    client, _engine = cloud
    back = _authorize(client, _register(client), approve=False)
    assert back["error"] == ["access_denied"] and back["state"] == ["estado-del-agente"] and "code" not in back


def test_the_person_can_only_give_access_to_their_own_businesses(cloud):
    client, _engine = cloud
    client_id = _register(client)
    foreign = client.post(
        "/api/oauth/authorize/decision", headers=_as("ana"),
        json={"params": _params(client_id), "approve": True, "permissions": {"assistant": "read"}, "reach": "some", "businesses": ["saas"]},
    )
    assert foreign.status_code == 404
    chat = client.post(
        "/api/oauth/authorize/decision", headers=_as("ana"),
        json={"params": _params(client_id), "approve": True, "permissions": {"chat": "write"}, "reach": "one", "businesses": ["restaurant"]},
    )
    assert chat.status_code == 422


# ---------------------------------------------------------------------------
# Tokens y servidor MCP
# ---------------------------------------------------------------------------

def test_the_agent_gets_tokens_and_works_with_exactly_what_was_authorized(cloud):
    client, _engine = cloud
    _client_id, tokens = _connect(client, permissions={"assistant": "read"}, reach="some", businesses=["restaurant"])
    assert tokens["token_type"] == "Bearer" and tokens["expires_in"] == 3600
    assert tokens["access_token"].startswith("ase_at_") and tokens["refresh_token"].startswith("ase_rt_")
    names = {tool["name"] for tool in _mcp(client, tokens["access_token"], "tools/list").json()["result"]["tools"]}
    assert {"get_business_config", "review_business_config"} <= names and "update_business_config" not in names
    listed = _mcp(client, tokens["access_token"], "tools/call", {"name": "list_businesses", "arguments": {}}).json()
    assert listed["error"]["code"] == -32602  # «Negocios» no se autorizó
    config = _mcp(client, tokens["access_token"], "tools/call", {"name": "get_business_config", "arguments": {"business": "clinic"}}).json()["result"]
    assert config["isError"] is True  # la clínica también es de Ana, pero no la eligió


def test_a_code_works_once_and_only_with_its_verifier(cloud):
    client, _engine = cloud
    client_id = _register(client)
    code = _authorize(client, client_id)["code"][0]
    assert _exchange(client, client_id, code, verifier="w" * 64).json()["error"] == "invalid_grant"
    # El intento fallido gastó el código: ya no sirve ni con el verificador correcto.
    assert _exchange(client, client_id, code).json()["error"] == "invalid_grant"
    fresh = _authorize(client, client_id)["code"][0]
    assert _exchange(client, client_id, fresh).status_code == 200
    assert _exchange(client, client_id, fresh).status_code == 400


def test_refreshing_rotates_the_refresh_token(cloud):
    client, _engine = cloud
    client_id, first = _connect(client)
    renewed = client.post("/api/oauth/token", data={"grant_type": "refresh_token", "refresh_token": first["refresh_token"], "client_id": client_id})
    assert renewed.status_code == 200, renewed.text
    second = renewed.json()
    assert second["refresh_token"] != first["refresh_token"]
    reused = client.post("/api/oauth/token", data={"grant_type": "refresh_token", "refresh_token": first["refresh_token"], "client_id": client_id})
    assert reused.status_code == 400 and reused.json()["error"] == "invalid_grant"
    assert _mcp(client, second["access_token"], "ping").status_code == 200
    assert client.post("/api/oauth/token", data={"grant_type": "password"}).json()["error"] == "unsupported_grant_type"


def test_the_connection_shows_in_api_keys_and_revoking_it_cuts_everything(cloud):
    client, engine = cloud
    client_id, tokens = _connect(client)
    keys = client.get("/api/businesses/restaurant/api-keys", headers=_as("ana")).json()
    connection = next(key for key in keys if key["kind"] == "oauth")
    assert connection["name"] == "Claude" and connection["prefix"] == "" and connection["permissions"] == {"assistant": "read"}
    assert connection["created_by"] == "ana@example.com" and connection["expires_at"] is None
    # Beto no ve la conexión de Ana.
    assert all(key["kind"] != "oauth" for key in client.get("/api/businesses/saas/api-keys", headers=_as("beto")).json())
    assert client.post(f"/api/businesses/restaurant/api-keys/{connection['id']}/revoke", headers=_as("ana")).status_code == 200
    assert _mcp(client, tokens["access_token"], "ping").status_code == 401
    refused = client.post("/api/oauth/token", data={"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"], "client_id": client_id})
    assert refused.json()["error"] == "invalid_grant"
    with engine.connect() as conn:
        assert conn.execute(select(mcp_oauth_tokens)).all() == []


def test_authorizing_again_replaces_the_previous_connection(cloud):
    client, _engine = cloud
    client_id = _register(client)
    first = _exchange(client, client_id, _authorize(client, client_id)["code"][0]).json()
    _exchange(client, client_id, _authorize(client, client_id, permissions={"assistant": "write"})["code"][0])
    active = [key for key in client.get("/api/businesses/restaurant/api-keys", headers=_as("ana")).json() if key["kind"] == "oauth" and key["active"]]
    assert [key["permissions"] for key in active] == [{"assistant": "write"}]
    assert _mcp(client, first["access_token"], "ping").status_code == 401


def test_without_oauth_the_server_keeps_working_with_keys_only(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'sin-oauth.sqlite3').as_posix()}")
    create_local_schema(engine)
    service = build_business_config_service(engine, secrets_key="x" * 43 + "=")
    client = TestClient(create_app(service, api_keys=ApiKeyStore(engine), mcp_url=lambda: "http://127.0.0.1:8010/api/mcp"), base_url="http://127.0.0.1:8010", client=("127.0.0.1", 50000))
    challenge = client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"}).headers["www-authenticate"]
    assert "resource_metadata" not in challenge
    assert client.get("/api/.well-known/oauth-authorization-server").status_code == 404
    assert client.post("/api/oauth/register", json={"redirect_uris": [CALLBACK]}).status_code == 404
    engine.dispose()


# ---------------------------------------------------------------------------
# Reglas puras
# ---------------------------------------------------------------------------

def test_the_pure_rules():
    assert pkce_matches(VERIFIER, CHALLENGE) and not pkce_matches("corto", CHALLENGE) and not pkce_matches("w" * 64, CHALLENGE)
    assert is_allowed_redirect_uri("https://chatgpt.com/connector_platform_oauth_redirect")
    assert is_allowed_redirect_uri("http://localhost:6274/oauth/callback")
    assert not is_allowed_redirect_uri("http://claude.ai/cb") and not is_allowed_redirect_uri("ftp://x/cb")
    assert read_client_registration({"redirect_uris": [CALLBACK]})[0] == "Agente de IA"
    assert redirect_with("https://x.example/cb?keep=1", {"code": "abc", "state": None}) == "https://x.example/cb?keep=1&code=abc"
    assert resource_metadata_url(MCP_URL) == "https://panel.example.com/.well-known/oauth-protected-resource/api/mcp"
    assert oauth_addresses(MCP_URL).issuer == "https://panel.example.com"
    registered = OAuthClient("id", "Claude", (CALLBACK,), datetime.now(timezone.utc))
    with pytest.raises(OAuthError) as wrong:
        read_authorization_request({"client_id": "id", "redirect_uri": CALLBACK, "response_type": "code", "code_challenge": CHALLENGE, "code_challenge_method": "S256", "resource": "https://otro.example.com/mcp"}, registered, MCP_URL)
    assert wrong.value.code == "invalid_target" and wrong.value.redirectable
