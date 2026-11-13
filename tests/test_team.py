"""El equipo de cada negocio: Dueño, Administrador y Asesor, con invitaciones por enlace (Configuración → Equipo).

Con la base real (SQLite, con las mismas restricciones que la migración 0016) y el panel «en la nube»:
- las reglas: siempre queda un dueño, nadie se toca a sí mismo, solo un dueño nombra o toca dueños;
- la invitación: el enlace se muestra una vez, se ve sin sesión, se acepta solo con la cuenta del correo invitado y una sola vez;
  renovarla invalida el enlace anterior, retirarla o dejarla vencer también;
- cada rol hace lo suyo: el asesor atiende, pero no configura, no ve reportes ni el equipo; el administrador hace todo menos
  eliminar el negocio y tocar a los dueños;
- un agente de IA (MCP) solo trabaja en los negocios que quien lo conectó puede configurar.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.admin_api.main import create_app
from app.business_config_application.access import BusinessAccess
from app.domain.business_config import team as rules
from app.domain.business_config.access import Principal
from app.domain.business_config.errors import InvalidFieldsError
from app.infrastructure.business_config.api_key_store import ApiKeyStore
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.business_config.example_businesses import import_example, load_example
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.tables import business_members, team_invitations, tenants
from app.infrastructure.business_config.team_store import TeamStore
from app.infrastructure.business_config.usage_store import UsageCounterStore

PEOPLE = {
    "ana": Principal(user_id="usuario-ana", email="ana@example.com"),
    "beto": Principal(user_id="usuario-beto", email="beto@example.com"),
    "carla": Principal(user_id="usuario-carla", email="carla@example.com"),
    "dario": Principal(user_id="usuario-dario", email="dario@example.com"),
}


class Tokens:
    def verify(self, token: str) -> Principal | None:
        return PEOPLE.get(token.removeprefix("token-de-"))


def _as(user: str) -> dict[str, str]:
    return {"Authorization": f"Bearer token-de-{user}"}


@pytest.fixture
def cloud(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'equipo.sqlite3').as_posix()}")
    create_local_schema(engine)
    service = build_business_config_service(engine, secrets_key="x" * 43 + "=")
    import_example(service, load_example("restaurant"))
    with engine.begin() as conn:
        tenant = conn.execute(select(tenants.c.id).where(tenants.c.slug == "restaurant")).scalar_one()
        conn.execute(business_members.insert().values(tenant_id=tenant, user_id=PEOPLE["ana"].user_id, role="owner", email="ana@example.com", created_at=datetime.now(timezone.utc)))
    app = create_app(
        service,
        access=BusinessAccess(service, BusinessMembersStore(engine)),
        verifier=Tokens(),
        usage=UsageCounterStore(engine),
        team=TeamStore(engine),
        api_keys=ApiKeyStore(engine),
        mcp_url=lambda: "https://panel.example.com/api/mcp",
    )
    yield TestClient(app), engine
    engine.dispose()


BASE = "/api/businesses/restaurant"


def _invite(client: TestClient, email: str, role: str, by: str = "ana") -> dict:
    response = client.post(f"{BASE}/team/invitations", headers=_as(by), json={"email": email, "role": role})
    assert response.status_code == 201, response.text
    return response.json()


def _join(client: TestClient, user: str, role: str, by: str = "ana") -> None:
    token = _invite(client, PEOPLE[user].email, role, by)["token"]
    assert client.post(f"/api/invitations/{token}/accept", headers=_as(user)).json() == {"business": "restaurant"}


# --------------------------------------------------------------------------------------------------------------- reglas


def test_each_role_can_what_its_table_says():
    assert rules.can("owner", rules.DELETE_BUSINESS) and not rules.can("admin", rules.DELETE_BUSINESS)
    assert rules.can("admin", rules.CONFIGURE) and rules.can("admin", rules.TEAM) and rules.can("admin", rules.REPORTS)
    assert rules.can("agent", rules.ATTEND)
    assert not any(rules.can("agent", need) for need in (rules.REPORTS, rules.CONFIGURE, rules.TEAM, rules.DELETE_BUSINESS))
    assert not rules.can(None, rules.ATTEND)


@pytest.mark.parametrize(
    "actor, target, new_role, owners, reason",
    [
        ("owner", "owner", "admin", 1, "al menos un dueño"),
        ("admin", "owner", "agent", 2, "Solo un dueño"),
        ("admin", "agent", "owner", 1, "Solo un dueño"),
    ],
)
def test_a_role_change_that_breaks_a_rule_is_refused(actor, target, new_role, owners, reason):
    with pytest.raises(rules.TeamRuleError, match=reason):
        rules.check_role_change(actor_id="a", actor_role=actor, target_id="b", target_role=target, new_role=new_role, owners=owners)


def test_nobody_changes_or_removes_themselves():
    with pytest.raises(rules.TeamRuleError, match="tu propio rol"):
        rules.check_role_change(actor_id="a", actor_role="owner", target_id="a", target_role="owner", new_role="admin", owners=2)
    with pytest.raises(rules.TeamRuleError, match="a ti mismo"):
        rules.check_removal(actor_id="a", actor_role="owner", target_id="a", target_role="owner", owners=2)


@pytest.mark.parametrize(
    "email, role, actor, path",
    [("no-es-correo", "agent", "owner", "email"), ("x@y.co", "jefe", "owner", "role"), ("x@y.co", "owner", "admin", "role")],
)
def test_an_invitation_problem_comes_back_on_its_field(email, role, actor, path):
    with pytest.raises(InvalidFieldsError) as error:
        rules.validated_invitation(email=email, role=role, actor_role=actor)
    assert [issue.path for issue in error.value.issues] == [path]


def test_the_invitation_email_is_tidied_and_the_link_is_only_kept_as_a_fingerprint():
    assert rules.validated_invitation(email="  Ana@Example.COM ", role="agent", actor_role="owner") == ("ana@example.com", "agent")
    token = rules.new_invitation_token()
    assert token.startswith("inv_") and len(token) > 40 and rules.token_fingerprint(token) != token and len(rules.token_fingerprint(token)) == 64


# ---------------------------------------------------------------------------------------------------------- invitaciones


def test_an_invitation_is_seen_without_session_and_accepted_once_with_the_invited_account(cloud):
    client, engine = cloud
    issued = _invite(client, " Beto@Example.com ", "agent")
    assert issued["email"] == "beto@example.com" and issued["role"] == "agent" and issued["status"] == "pending"
    with engine.connect() as conn:
        assert conn.execute(select(team_invitations.c.token_hash)).scalar_one() != issued["token"]

    preview = client.get(f"/api/invitations/{issued['token']}")
    assert preview.status_code == 200
    assert preview.json()["business_name"] and preview.json()["invited_by"] == "ana@example.com" and "token" not in preview.json()

    wrong = client.post(f"/api/invitations/{issued['token']}/accept", headers=_as("carla"))
    assert wrong.status_code == 404 and "beto@example.com" in wrong.json()["message"]
    assert client.post(f"/api/invitations/{issued['token']}/accept").status_code == 401

    assert client.post(f"/api/invitations/{issued['token']}/accept", headers=_as("beto")).json() == {"business": "restaurant"}
    again = client.post(f"/api/invitations/{issued['token']}/accept", headers=_as("beto"))
    assert again.status_code == 404 and "ya se usó" in again.json()["message"]

    businesses = client.get("/api/businesses", headers=_as("beto")).json()
    assert [(item["slug"], item["role"]) for item in businesses] == [("restaurant", "agent")]
    team = client.get(f"{BASE}/team", headers=_as("ana")).json()
    assert [(member["email"], member["role"], member["me"]) for member in team["members"]] == [("ana@example.com", "owner", True), ("beto@example.com", "agent", False)]
    assert team["invitations"] == [] and team["my_role"] == "owner"


def test_renewing_revoking_or_expiring_a_link_stops_it(cloud):
    client, engine = cloud
    first = _invite(client, "beto@example.com", "agent")
    renewed = client.post(f"{BASE}/team/invitations/{first['id']}/renew", headers=_as("ana")).json()
    assert renewed["id"] == first["id"] and renewed["token"] != first["token"]
    assert client.get(f"/api/invitations/{first['token']}").status_code == 404
    assert client.get(f"/api/invitations/{renewed['token']}").status_code == 200

    # Una invitación nueva al mismo correo reemplaza la anterior.
    replaced = _invite(client, "beto@example.com", "admin")
    assert client.get(f"/api/invitations/{renewed['token']}").json()["message"].startswith("Esta invitación se retiró")
    assert [item["role"] for item in client.get(f"{BASE}/team", headers=_as("ana")).json()["invitations"]] == ["admin"]

    assert client.delete(f"{BASE}/team/invitations/{replaced['id']}", headers=_as("ana")).status_code == 204
    assert client.get(f"/api/invitations/{replaced['token']}").status_code == 404
    assert client.delete(f"{BASE}/team/invitations/{replaced['id']}", headers=_as("ana")).status_code == 404

    late = _invite(client, "carla@example.com", "agent")
    with engine.begin() as conn:
        conn.execute(update(team_invitations).values(expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)))
    expired = client.post(f"/api/invitations/{late['token']}/accept", headers=_as("carla"))
    assert expired.status_code == 404 and "venció" in expired.json()["message"]
    listed = client.get(f"{BASE}/team", headers=_as("ana")).json()["invitations"]
    assert [(item["email"], item["status"]) for item in listed] == [("carla@example.com", "expired")]
    assert client.get("/api/invitations/inv_no-existe").status_code == 404


def test_someone_already_in_the_team_is_not_invited_again(cloud):
    client, _engine = cloud
    _join(client, "beto", "agent")
    response = client.post(f"{BASE}/team/invitations", headers=_as("ana"), json={"email": "BETO@example.com", "role": "admin"})
    assert response.status_code == 422 and response.json()["issues"] == [{"path": "email", "message": "Esa persona ya está en el equipo."}]


# ------------------------------------------------------------------------------------------------------- lo que hace cada rol


def test_an_agent_attends_but_does_not_configure_report_or_manage_the_team(cloud):
    client, _engine = cloud
    _join(client, "beto", "agent")
    beto = _as("beto")
    # Atiende: ve el negocio, sus chats, sus clientes, registra ventas y usa respuestas rápidas.
    assert client.get(f"{BASE}/config", headers=beto).status_code == 200
    assert client.get("/api/conversations", headers=beto).status_code in (200, 503)
    assert client.get(f"{BASE}/channels/whatsapp", headers=beto).status_code in (200, 503)
    # No configura, no ve reportes, no administra el equipo ni elimina el negocio.
    refused = [
        client.put(f"{BASE}/config", headers=beto, json={"document": {}, "payment_values": {}, "base_version": 1}),
        client.post(f"{BASE}/publish", headers=beto, json={"version": 1}),
        client.get(f"{BASE}/review", headers=beto),
        client.get(f"{BASE}/ai", headers=beto),
        client.post(f"{BASE}/channels/whatsapp/connect", headers=beto),
        client.get(f"{BASE}/api-keys", headers=beto),
        client.get(f"{BASE}/team", headers=beto),
        client.post(f"{BASE}/team/invitations", headers=beto, json={"email": "x@y.co", "role": "agent"}),
        client.delete(f"{BASE}?confirm=x", headers=beto),
    ]
    assert [response.status_code for response in refused] == [403] * len(refused)
    assert refused[0].json()["message"].startswith("Configurar el negocio es del dueño o de un administrador")
    assert refused[-1].json()["message"] == "Solo el dueño del negocio puede hacer esto."


def test_an_admin_runs_the_team_but_does_not_touch_owners_or_delete_the_business(cloud):
    client, _engine = cloud
    _join(client, "carla", "admin")
    _join(client, "beto", "agent", by="carla")
    carla = _as("carla")
    assert client.get(f"{BASE}/review", headers=carla).status_code == 200
    assert client.get(f"{BASE}/team", headers=carla).json()["my_role"] == "admin"
    # Cambia y quita asesores, pero no invita dueños, no toca al dueño ni se toca a sí misma.
    assert client.put(f"{BASE}/team/members/usuario-beto", headers=carla, json={"role": "admin"}).json()["role"] == "admin"
    owner_invite = client.post(f"{BASE}/team/invitations", headers=carla, json={"email": "dario@example.com", "role": "owner"})
    assert owner_invite.status_code == 422 and owner_invite.json()["issues"][0]["path"] == "role"
    to_owner = client.put(f"{BASE}/team/members/usuario-ana", headers=carla, json={"role": "agent"})
    assert to_owner.status_code == 409 and "Solo un dueño" in to_owner.json()["message"]
    assert client.put(f"{BASE}/team/members/usuario-carla", headers=carla, json={"role": "owner"}).status_code == 409
    assert client.delete(f"{BASE}/team/members/usuario-beto", headers=carla).status_code == 204
    assert client.delete(f"{BASE}?confirm=x", headers=carla).status_code == 403
    # Quitado del equipo, el negocio deja de existir para él.
    assert client.get(f"{BASE}/config", headers=_as("beto")).status_code == 404


def test_the_business_always_keeps_an_owner(cloud):
    client, _engine = cloud
    _join(client, "carla", "owner")
    ana = _as("ana")
    # Con dos dueños, uno puede dejar de serlo; el último, no.
    assert client.put(f"{BASE}/team/members/usuario-carla", headers=ana, json={"role": "admin"}).json()["role"] == "admin"
    assert client.put(f"{BASE}/team/members/usuario-ana", headers=_as("carla"), json={"role": "admin"}).status_code == 409
    assert client.delete(f"{BASE}/team/members/usuario-ana", headers=ana).status_code == 409
    assert client.delete(f"{BASE}/team/members/no-existe", headers=ana).status_code == 409


def test_without_accounts_there_is_no_team(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'local.sqlite3').as_posix()}")
    create_local_schema(engine)
    service = build_business_config_service(engine, secrets_key="x" * 43 + "=")
    import_example(service, load_example("restaurant"))
    client = TestClient(create_app(service, team=TeamStore(engine)), base_url="http://127.0.0.1", client=("127.0.0.1", 50000))
    assert client.get(f"{BASE}/team").status_code == 503
    assert client.get("/api/businesses").json()[0]["role"] == "owner"
    engine.dispose()


# -------------------------------------------------------------------------------------------------------------------- MCP


def test_an_agent_connected_by_an_advisor_does_not_reach_the_business(cloud):
    client, engine = cloud
    secret = client.post(f"{BASE}/api-keys", headers=_as("ana"), json={"name": "Claude", "reach": "all", "permissions": {"businesses": "read"}}).json()["secret"]

    def businesses() -> list[str]:
        response = client.post("/api/mcp", headers={"Authorization": f"Bearer {secret}"}, json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "list_businesses", "arguments": {}}})
        return [item["business"] for item in response.json()["result"]["structuredContent"]["businesses"]]

    assert businesses() == ["restaurant"]
    # Si quien conectó la clave pasa a asesor, su agente deja de llegar al negocio.
    _join(client, "carla", "owner")
    assert client.put(f"{BASE}/team/members/usuario-ana", headers=_as("carla"), json={"role": "agent"}).status_code == 200
    assert businesses() == []
    assert client.get(f"{BASE}/api-keys", headers=_as("ana")).status_code == 403
