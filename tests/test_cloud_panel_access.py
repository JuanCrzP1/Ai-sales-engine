"""La API del panel en la nube: cada persona entra con su cuenta y solo llega a sus negocios.

Sin sesión válida nada responde (401). Un negocio ajeno responde igual que uno inexistente (404), en todas sus rutas: la
configuración, las versiones, la inteligencia artificial y el área de pruebas. Crear un negocio deja a su dueño como miembro
en la misma transacción, y la importación de los YAML no existe en la nube.
"""
from __future__ import annotations

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin_api.main import create_app
from app.business_config_application.access import BusinessAccess
from app.domain.business_config.access import Principal
from app.domain.business_config.ai_settings import AssistantTurn, KeyCheck
from app.infrastructure.business_config.database import (
    build_assistant_lab_service,
    build_business_config_service,
    create_business_config_engine,
    create_local_schema,
)
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.tables import business_members
from app.infrastructure.business_config.usage_store import UsageCounterStore
from app.infrastructure.business_config.example_businesses import import_example, load_example

ANA = Principal(user_id="usuario-ana", email="ana@example.com")
BETO = Principal(user_id="usuario-beto", email="beto@example.com")
TOKENS = {"token-de-ana": ANA, "token-de-beto": BETO}
KEY = "sk-or-v1-clave-ficticia-de-ana-000000001"


class Tokens:
    """Neon Auth de mentira: cada token conocido es un usuario; cualquier otro no es válido."""

    def verify(self, token: str) -> Principal | None:
        return TOKENS.get(token)


class Runner:
    def reply(self, *, tenant_slug, sections, credentials, session_id, message):
        return AssistantTurn(reply=f"Respuesta a: {message}", intent="info")

    def reset(self, *, tenant_slug, session_id):
        return None


class Verifier:
    def verify(self, credentials):
        return KeyCheck(True, "La clave funciona.")


@pytest.fixture
def cloud(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'nube.sqlite3').as_posix()}")
    create_local_schema(engine)
    key = Fernet.generate_key().decode()
    service = build_business_config_service(engine, secrets_key=key)
    lab = build_assistant_lab_service(engine, service, secrets_key=key, verifier=Verifier(), runner=Runner())
    app = create_app(service, lab, access=BusinessAccess(service, BusinessMembersStore(engine)), verifier=Tokens(), usage=UsageCounterStore(engine))
    yield engine, service, TestClient(app)
    engine.dispose()


def _as(user: str) -> dict[str, str]:
    return {"Authorization": f"Bearer token-de-{user}"}


def _give(engine, slug: str, user: Principal) -> None:
    """Un negocio que ya existía queda a nombre de un usuario (como se hará con `asesor_ai_prod` en producción)."""
    from datetime import datetime, timezone

    from app.infrastructure.business_config.tables import tenants

    with engine.begin() as conn:
        tenant_id = conn.execute(select(tenants.c.id).where(tenants.c.slug == slug)).scalar_one()
        conn.execute(business_members.insert().values(tenant_id=tenant_id, user_id=user.user_id, role="owner", created_at=datetime.now(timezone.utc)))


# ---------------------------------------------------------------------------
# Sin sesión, nada
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer token-falso"}, {"Authorization": "Basic token-de-ana"}, {"Authorization": "Bearer"}])
def test_without_a_valid_session_nothing_answers(cloud, headers):
    _engine, _service, client = cloud
    for method, path in (("get", "/api/businesses"), ("post", "/api/businesses"), ("get", "/api/businesses/restaurant/config"), ("get", "/api/businesses/restaurant/ai")):
        response = client.request(method, path, headers=headers, json={"slug": "nuevo", "name": "Nuevo"} if method == "post" else None)
        assert (response.status_code, response.json()["code"]) == (401, "unauthenticated"), path


def test_the_cloud_api_needs_to_know_the_members_and_shared_usage_counters():
    with pytest.raises(ValueError, match="negocios"):
        create_app(object(), verifier=Tokens())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contadores"):
        create_app(object(), verifier=Tokens(), access=object())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Cada uno, lo suyo
# ---------------------------------------------------------------------------

def test_creating_a_business_makes_its_creator_the_owner(cloud):
    engine, _service, client = cloud
    created = client.post("/api/businesses", headers=_as("ana"), json={"slug": "panaderia_ana", "name": "Panadería Ana"})
    assert created.status_code == 201
    with engine.connect() as conn:
        rows = conn.execute(select(business_members.c.user_id, business_members.c.role)).all()
    assert [(row.user_id, row.role) for row in rows] == [("usuario-ana", "owner")]
    assert [item["slug"] for item in client.get("/api/businesses", headers=_as("ana")).json()] == ["panaderia_ana"]
    assert client.get("/api/businesses", headers=_as("beto")).json() == []


def test_a_business_of_someone_else_answers_like_one_that_does_not_exist(cloud):
    _engine, _service, client = cloud
    client.post("/api/businesses", headers=_as("ana"), json={"slug": "panaderia_ana", "name": "Panadería Ana"})
    base = "/api/businesses/panaderia_ana"
    attempts = [
        ("get", f"{base}/config", None),
        ("put", f"{base}/config", {"document": {}, "payment_values": {}, "base_version": None}),
        ("post", f"{base}/validate", {"document": {}}),
        ("get", f"{base}/review", None),
        ("get", f"{base}/versions", None),
        ("post", f"{base}/versions/1/restore", None),
        ("post", f"{base}/publish", {"version": 1}),
        ("post", f"{base}/rollback", None),
        ("delete", f"{base}?confirm=panaderia_ana", None),
        ("get", f"{base}/ai", None),
        ("put", f"{base}/ai", {"model": None, "api_key": KEY}),
        ("post", f"{base}/ai/verify", None),
        ("post", f"{base}/playground", {"message": "Hola", "source": "draft"}),
        ("delete", f"{base}/playground/{'a' * 32}", None),
    ]
    for method, path, body in attempts:
        theirs = client.request(method, path, headers=_as("beto"), json=body)
        missing = client.request(method, path.replace("panaderia_ana", "no-existe"), headers=_as("beto"), json=body)
        assert (theirs.status_code, theirs.json()["code"]) == (404, "not_found"), f"{method} {path}"
        assert theirs.json() == missing.json(), f"{method} {path}"
    # Y lo de Ana sigue intacto: Beto no pudo guardar ni su clave.
    assert client.get(f"{base}/ai", headers=_as("ana")).json()["key"]["configured"] is False


def test_the_owner_works_on_their_business_and_the_history_says_who(cloud):
    engine, service, client = cloud
    import_example(service, load_example("restaurant"))
    _give(engine, "restaurant", ANA)
    editable = client.get("/api/businesses/restaurant/config", headers=_as("ana"))
    assert editable.status_code == 200
    body = editable.json()
    saved = client.put(
        "/api/businesses/restaurant/config",
        headers=_as("ana"),
        json={"document": body["document"], "payment_values": {}, "base_version": body["latest_version"]},
    )
    assert saved.status_code == 200, saved.json()
    assert max(service.history("restaurant"), key=lambda item: item.version).created_by == "ana@example.com"
    assert client.put("/api/businesses/restaurant/ai", headers=_as("ana"), json={"model": None, "api_key": KEY}).status_code == 200
    assert client.get("/api/businesses/restaurant/config", headers=_as("beto")).status_code == 404


def test_a_taken_identifier_does_not_say_whose_it_is(cloud):
    _engine, _service, client = cloud
    client.post("/api/businesses", headers=_as("ana"), json={"slug": "panaderia", "name": "Panadería"})
    taken = client.post("/api/businesses", headers=_as("beto"), json={"slug": "panaderia", "name": "Otra panadería"})
    assert (taken.status_code, taken.json()["code"]) == (409, "duplicate")
    assert "ana" not in taken.text.lower()
    assert client.get("/api/businesses", headers=_as("beto")).json() == []


def test_the_examples_import_does_not_exist_in_the_cloud(cloud):
    """La API de la nube nunca recibe el importador de los negocios de ejemplo: cada cuenta crea los suyos."""
    _engine, _service, client = cloud
    assert getattr(client.app.state, "examples", None) is None
    response = client.post("/api/businesses/import", headers=_as("ana"))
    assert (response.status_code, response.json()["code"]) == (404, "not_found")
    assert client.get("/api/businesses", headers=_as("ana")).json() == []


# ---------------------------------------------------------------------------
# El motor la publica bajo /panel solo con NEON_AUTH_URL
# ---------------------------------------------------------------------------

def test_the_engine_publishes_the_panel_api_only_with_neon_auth(tmp_path, monkeypatch):
    from fastapi import FastAPI

    from app import main
    from app.infrastructure.business_config import database as business_config_database
    from app.infrastructure.business_config.payment_secret_store import SECRETS_KEY_ENV

    monkeypatch.delenv("NEON_AUTH_URL", raising=False)
    without = FastAPI()
    main.mount_cloud_panel(without)
    assert not any(getattr(route, "path", "") == "/panel" for route in without.routes)

    path = tmp_path / "plataforma.sqlite3"
    create_local_schema(create_business_config_engine(f"sqlite:///{path.as_posix()}"))
    monkeypatch.setenv(business_config_database.DATABASE_URL_ENV, f"sqlite:///{path.as_posix()}")
    monkeypatch.setenv(SECRETS_KEY_ENV, Fernet.generate_key().decode())
    monkeypatch.setenv("NEON_AUTH_URL", "https://ep-ejemplo.neonauth.us-east-1.aws.neon.tech/neondb/auth")
    with_auth = FastAPI()
    main.mount_cloud_panel(with_auth)
    client = TestClient(with_auth)
    assert client.get("/panel/api/health").json() == {"status": "ok"}
    assert client.get("/panel/api/businesses").status_code == 401
    assert client.get("/panel/api/businesses", headers={"Authorization": "Bearer no-es-un-jwt"}).status_code == 401


# ---------------------------------------------------------------------------
# Límites de uso
# ---------------------------------------------------------------------------

def test_the_playground_has_a_limit_per_person_that_answers_429_in_spanish(cloud):
    from app.domain.business_config.usage_limits import PLAYGROUND_PER_USER

    engine, service, client = cloud
    import_example(service, load_example("restaurant"))
    _give(engine, "restaurant", ANA)
    _give(engine, "restaurant", BETO)
    client.put("/api/businesses/restaurant/ai", headers=_as("ana"), json={"model": None, "api_key": KEY})
    talk = {"message": "Hola", "source": "published"}
    for _ in range(PLAYGROUND_PER_USER.limit):
        assert client.post("/api/businesses/restaurant/playground", headers=_as("ana"), json=talk).status_code == 200
    stopped = client.post("/api/businesses/restaurant/playground", headers=_as("ana"), json=talk)
    assert (stopped.status_code, stopped.json()["code"]) == (429, "rate_limited")
    assert stopped.json()["message"].startswith("Hiciste muchas solicitudes seguidas. Espera ")
    assert 1 <= int(stopped.headers["Retry-After"]) <= PLAYGROUND_PER_USER.window_seconds
    # El límite es de cada persona: Beto, del mismo equipo, sigue probando.
    assert client.post("/api/businesses/restaurant/playground", headers=_as("beto"), json=talk).status_code == 200


def test_checking_the_ai_key_has_its_own_limit(cloud):
    from app.domain.business_config.usage_limits import AI_KEY_CHECKS_PER_USER

    engine, service, client = cloud
    import_example(service, load_example("restaurant"))
    _give(engine, "restaurant", ANA)
    client.put("/api/businesses/restaurant/ai", headers=_as("ana"), json={"model": None, "api_key": KEY})
    for _ in range(AI_KEY_CHECKS_PER_USER.limit):
        assert client.post("/api/businesses/restaurant/ai/verify", headers=_as("ana")).status_code == 200
    assert client.post("/api/businesses/restaurant/ai/verify", headers=_as("ana")).status_code == 429


def test_each_owner_sees_the_ai_usage_of_their_business_only(cloud):
    from datetime import datetime, timezone

    from app.domain.business_config.ai_usage import AIUsage
    from app.infrastructure.business_config.ai_usage_store import AIUsageStore

    engine, service, client = cloud
    import_example(service, load_example("restaurant"))
    _give(engine, "restaurant", ANA)
    today = datetime.now(timezone.utc).date()
    AIUsageStore(engine).add("restaurant", today, AIUsage("openai/gpt-4o-mini", 1200, 80, 0.0004))
    usage = client.get("/api/businesses/restaurant/ai/usage", headers=_as("ana"))
    assert usage.status_code == 200
    body = usage.json()
    assert (body["replies"], body["prompt_tokens"], body["completion_tokens"], body["cost_usd"]) == (1, 1200, 80, 0.0004)
    assert body["days"] == [{"day": today.isoformat(), "replies": 1, "tokens": 1280}]
    assert client.get("/api/businesses/restaurant/ai/usage", headers=_as("beto")).status_code == 404
