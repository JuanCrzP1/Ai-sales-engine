"""Seguridad de `POST /api/v1/simulate`: acceso, respuesta y aislamiento de la memoria real.

Usa la ruta y sus dependencias reales (`get_current_user`, `get_current_tenant`) sobre una base SQLite temporal con el
esquema del ORM. Solo se simula la verificación del token, porque la autenticación definitiva está aplazada a la fase de
nube y hoy no hay ninguna librería JWT instalada. El modelo también está simulado, los datos son ficticios y nada sale a
la red. Las aserciones comparan conteos y nombres: si una falla, el informe no debe mostrar datos de pago.
"""
from __future__ import annotations

import inspect
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pipeline_harness import TENANTS, reply
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import dependencies
from app.api.controllers import simulation
from app.api.dependencies import get_current_tenant, get_current_user
from app.application.ai_pipeline import AIPipeline
from app.application.runtime import load_tenant_runtime_yaml
from app.config import settings
from app.database.connection import get_db
from app.domain.business_config.payment_data import REDACTED_PAYMENT_VALUE, payment_values, redact_payment_values
from app.infrastructure.persistence.memory_repository import SQLMemoryRepository
from app.models import AdminUser, Base, Tenant
from app.services.ai_service import GLOBAL_MEMORY_SERVICE, AIService
from app.services.auth_service import AuthService

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
PROBE = Path(__file__).resolve().with_name("simulation_app_probe.py")

URL = f"{settings.api_prefix}/simulate"
MESSAGE = {"user_message": "tengo muchos mensajes"}
FAKE_REPLY = "Respuesta simulada."
JWT_SECRET = "secreto-ficticio-de-las-pruebas-0123456789"
TEST_TOKEN_PREFIX = "token-de-prueba-"
PAYMENT_METHODS = ("link", "nequi", "daviplata", "bank", "breb")
METADATA_FIELDS = {"source", "intent", "conversation_state", "tenant_slug"}
REAL_TOKEN_VERIFICATION = AuthService.get_user_from_token


@pytest.fixture
def llm(monkeypatch):
    """Sustituye al modelo: registra todo lo que recibiría (instrucciones y conversación) y responde lo indicado, sin red."""
    state = SimpleNamespace(prompts=[], reply=reply(FAKE_REPLY))
    original = AIPipeline.__init__

    def _init(self, *args, **kwargs):
        original(self, *args, **kwargs)

        def _generate(prompt, *, user_message, bot_config=None, history=None, **_kwargs):
            state.prompts.append("\n".join([str(prompt), *(str(item.get("content") or "") for item in history or [])]))
            return state.reply

        self.runtime.generate = _generate

    monkeypatch.setattr(AIPipeline, "__init__", _init)
    return state


def _verify_test_token(self, token: str):
    """Sustituye solo la verificación del token: identifica a un administrador sin usar ninguna librería JWT."""
    admin_id = token.removeprefix(TEST_TOKEN_PREFIX)
    if not token.startswith(TEST_TOKEN_PREFIX) or not admin_id.isdigit():
        return None
    return self.db.query(AdminUser).filter(AdminUser.id == int(admin_id)).first()


@pytest.fixture
def api(monkeypatch, llm):
    monkeypatch.setattr(AuthService, "get_user_from_token", _verify_test_token)
    monkeypatch.setattr(simulation, "_sessions", OrderedDict())
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def _db():
        db = sessions()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(simulation.router, prefix=settings.api_prefix)
    app.dependency_overrides[get_db] = _db
    yield SimpleNamespace(client=TestClient(app), sessions=sessions)
    engine.dispose()


def _admin(api, slug: str = "saas") -> dict[str, str]:
    """Crea un administrador del negocio, y el negocio si hace falta; devuelve las cabeceras con su token de prueba."""
    with api.sessions() as db:
        tenant = db.query(Tenant).filter(Tenant.slug == slug).first()
        if tenant is None:
            tenant = Tenant(name=slug, slug=slug)
            db.add(tenant)
            db.commit()
        admin = AdminUser(
            tenant_id=tenant.id,
            email=f"admin-{uuid4().hex}@negocio-ficticio.com",
            full_name="Admin ficticio",
            password_hash="no-usada",
        )
        db.add(admin)
        db.commit()
        return {"Authorization": f"Bearer {TEST_TOKEN_PREFIX}{admin.id}"}


def _texts(node):
    if isinstance(node, dict):
        for value in node.values():
            yield from _texts(value)
    elif isinstance(node, list):
        for value in node:
            yield from _texts(value)
    elif isinstance(node, str):
        yield node


def _numbers(node):
    if isinstance(node, dict):
        for value in node.values():
            yield from _numbers(value)
    elif isinstance(node, list):
        for value in node:
            yield from _numbers(value)
    elif isinstance(node, (int, float)) and not isinstance(node, bool):
        yield node


def _keys(node):
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from _keys(value)
    elif isinstance(node, list):
        for value in node:
            yield from _keys(value)


def _leaked(values: list[str], text: str) -> int:
    return sum(1 for value in values if value in text)


def _real_flow(slug: str, message: str, *, user_id: str | None = None):
    """El flujo que usan los canales reales: `AIService` con su memoria global."""
    return AIService().generate_business_reply(
        tenant=SimpleNamespace(slug=slug),
        bot_config=None,
        user_message=message,
        conversation_history=[],
        faq_results=[],
        yaml_config=load_tenant_runtime_yaml(slug),
        user_id=user_id or f"cliente-{uuid4().hex}",
        include_metadata=True,
    )


# 1. Sin autenticación: 401 o 403, y el motor no llega a ejecutarse.


@pytest.mark.parametrize("slug", TENANTS)
def test_only_the_tenant_header_is_not_enough(api, llm, slug):
    response = api.client.post(URL, headers={"X-Tenant-Slug": slug}, json=MESSAGE)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert llm.prompts == []


def test_a_request_without_credentials_is_rejected(api, llm):
    assert api.client.post(URL, json=MESSAGE).status_code == 401
    assert api.client.post(URL, json={"no_es_valido": True}).status_code == 401
    assert llm.prompts == []


def test_a_malformed_body_does_not_reach_the_engine(api, llm):
    # FastAPI interpreta el JSON antes que las dependencias: puede responder 422, pero sin datos ni motor.
    response = api.client.post(URL, headers={"Content-Type": "application/json"}, content=b"{mal")
    assert response.status_code in {401, 422}
    assert llm.prompts == []


@pytest.mark.parametrize(
    "token",
    ["basura", f"{TEST_TOKEN_PREFIX}no-es-un-numero", f"{TEST_TOKEN_PREFIX}999"],
    ids=["no_es_un_token", "usuario_invalido", "usuario_inexistente"],
)
def test_tokens_that_do_not_identify_an_admin_are_rejected(api, llm, token):
    _admin(api)
    response = api.client.post(URL, headers={"Authorization": f"Bearer {token}"}, json=MESSAGE)
    assert response.status_code == 401
    assert llm.prompts == []


def test_with_the_real_token_verification_nothing_reaches_the_engine(api, llm, monkeypatch):
    # Estado actual, sin simular nada: sin librería JWT la verificación falla con 500. Con una instalada a mano
    # sería 401, porque este texto no es un token firmado. En ningún caso da acceso.
    monkeypatch.setattr(AuthService, "get_user_from_token", REAL_TOKEN_VERIFICATION)
    client = TestClient(api.client.app, raise_server_exceptions=False)
    response = client.post(URL, headers=_admin(api), json=MESSAGE)
    assert response.status_code in {401, 500}
    assert "reply" not in response.text
    assert llm.prompts == []


def test_an_inactive_admin_is_rejected(api, llm):
    headers = _admin(api)
    with api.sessions() as db:
        db.query(AdminUser).update({"is_active": False})
        db.commit()
    assert api.client.post(URL, headers=headers, json=MESSAGE).status_code == 401
    assert llm.prompts == []


def test_an_admin_cannot_simulate_another_business(api, llm):
    headers = _admin(api, "saas")
    response = api.client.post(URL, headers={**headers, "X-Tenant-Slug": "clinic"}, json=MESSAGE)
    assert response.status_code == 403
    assert llm.prompts == []


def test_an_inactive_business_is_not_served(api, llm):
    headers = _admin(api)
    with api.sessions() as db:
        db.query(Tenant).update({"is_active": False})
        db.commit()
    assert api.client.post(URL, headers=headers, json=MESSAGE).status_code == 404
    assert llm.prompts == []


def test_a_business_without_configuration_does_not_fall_back_to_another(api, llm):
    headers = _admin(api, "negocio-sin-configuracion")
    assert api.client.post(URL, headers=headers, json=MESSAGE).status_code == 404
    assert llm.prompts == []


@pytest.mark.parametrize(
    "slug",
    [
        "../tenants/restaurant",
        "..\\tenants\\restaurant",
        "negocio/../restaurant",
        "..",
        ".",
        "../system",
        "RESTAURANT",
        "restaurant.",
    ],
)
def test_a_stored_identifier_cannot_open_the_folder_of_another_business(api, llm, slug):
    # El identificador guardado puede ser cualquier texto: el negocio ajeno ya tiene dueño y aun así no debe alcanzarse.
    _admin(api, "restaurant")
    assert api.client.post(URL, headers=_admin(api, slug), json=MESSAGE).status_code == 404
    assert llm.prompts == []


@pytest.mark.parametrize("slug", TENANTS)
def test_the_identifiers_of_the_nine_businesses_are_accepted(slug):
    assert simulation._BUSINESS_SLUG.fullmatch(slug)


def test_the_route_reuses_the_existing_authentication():
    route = next(item for item in simulation.router.routes if item.path == "/simulate")
    assert {dependency.call for dependency in route.dependant.dependencies} == {get_current_user, get_current_tenant}
    assert not hasattr(dependencies, "get_tenant_by_slug_public")


def test_only_the_neon_auth_verifier_uses_a_jwt_library():
    # Las cuentas de la plataforma son de Neon Auth: el panel en la nube comprueba sus tokens con PyJWT, solo en su verificador.
    # La librería del sistema de cuentas anterior (`python-jose`) sigue sin declararse.
    declared = "".join((PROJECT_DIR / name).read_text(encoding="utf-8").lower() for name in ("requirements.txt", "requirements-dev.txt"))
    assert not re.search(r"^(python-jose|jose|authlib)\b", declared, re.MULTILINE)
    assert re.search(r"^pyjwt==", declared, re.MULTILINE)
    uses = {
        path.relative_to(PROJECT_DIR).as_posix()
        for path in (PROJECT_DIR / "app").rglob("*.py")
        if re.search(r"^\s*(import jwt|from jwt)\b", path.read_text(encoding="utf-8"), re.MULTILINE)
    }
    assert uses == {"app/infrastructure/auth/neon_auth.py"}


# 2. Con autenticación válida (verificación del token simulada): acceso permitido cuando la ruta está habilitada.


def test_an_identified_admin_is_allowed(api, llm):
    response = api.client.post(URL, headers=_admin(api), json=MESSAGE)
    assert response.status_code == 200
    assert response.json()["reply"] == FAKE_REPLY
    assert response.json()["ai_used"] is True
    assert len(llm.prompts) == 1


def test_the_token_decides_the_business(api):
    headers = _admin(api, "saas")
    without_header = api.client.post(URL, headers=headers, json=MESSAGE)
    with_header = api.client.post(URL, headers={**headers, "X-Tenant-Slug": "saas"}, json=MESSAGE)
    assert without_header.json()["metadata"]["tenant_slug"] == "saas"
    assert with_header.json()["metadata"]["tenant_slug"] == "saas"


# 3. Deshabilitada: 404. Se comprueba con la aplicación real y la configuración resuelta de verdad.


def _run_real_app(tmp_path: Path, **values: str) -> dict:
    env = {key: value for key, value in os.environ.items() if key not in {"ENABLE_SIMULATION_ENDPOINT", "JWT_SECRET", "PYTEST_CURRENT_TEST"}}
    env.update(
        MODE="test",
        ENABLE_FILE_LOGS="0",
        DATABASE_URL=f"sqlite:///{(tmp_path / 'aplicacion.db').as_posix()}",
        **values,
    )
    output = tmp_path / "resultado.json"
    completed = subprocess.run(
        [sys.executable, str(PROBE), str(output)],
        cwd=PROJECT_DIR,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    return json.loads(output.read_text(encoding="utf-8"))


def test_nothing_in_the_repository_enables_the_route():
    field = type(settings).model_fields["enable_simulation_endpoint"]
    assert field.default is False
    for name in ("settings.yaml", "bot_config.yaml"):
        path = PROJECT_DIR / "config" / "system" / name
        assert yaml.safe_load(path.read_text(encoding="utf-8"))["features"]["enable_simulation_endpoint"] is False


@pytest.mark.parametrize(
    "values",
    [
        pytest.param({}, id="sin_configurar"),
        pytest.param({"JWT_SECRET": JWT_SECRET}, id="solo_con_secreto_propio"),
        pytest.param({"ENABLE_SIMULATION_ENDPOINT": "false", "JWT_SECRET": JWT_SECRET}, id="bandera_en_false"),
        pytest.param({"ENABLE_SIMULATION_ENDPOINT": "true"}, id="bandera_con_el_secreto_publico"),
        pytest.param({"ENABLE_SIMULATION_ENDPOINT": "true", "JWT_SECRET": ""}, id="bandera_con_el_secreto_vacio"),
        pytest.param({"ENABLE_SIMULATION_ENDPOINT": "true", "JWT_SECRET": "  "}, id="bandera_con_el_secreto_en_blanco"),
    ],
)
def test_the_route_does_not_exist_unless_explicitly_enabled(tmp_path, values):
    result = _run_real_app(tmp_path, **values)
    assert result["flag"] is (values.get("ENABLE_SIMULATION_ENDPOINT") == "true")
    assert result["anonymous"] == 404
    assert result["bad_token"] == 404
    assert result["malformed"] == 404
    assert result["get"] == 404
    assert result["in_openapi"] is False
    # Ni un administrador identificado la alcanza.
    assert result["authenticated"] == 404


def test_the_old_register_route_no_longer_exists(tmp_path):
    # La API de administración vieja se retiró: `/auth/register` ya no existe y nadie puede pedir un token por ahí.
    result = _run_real_app(tmp_path)
    assert result["register"] == 404
    assert result["register_issued_token"] is False


def test_the_real_application_serves_the_route_only_with_explicit_configuration(tmp_path):
    result = _run_real_app(tmp_path, ENABLE_SIMULATION_ENDPOINT="true", JWT_SECRET=JWT_SECRET)
    assert result["flag"] is True
    assert result["in_openapi"] is True
    assert result["anonymous"] == 401
    # Con un token cualquiera responde 500 mientras no haya librería JWT, y el modelo no llega a ejecutarse.
    assert result["bad_token"] in {401, 500}
    assert result["model_calls_without_identity"] == 0
    assert result["authenticated"] == 200
    assert result["reply"] == FAKE_REPLY
    assert result["fields"] == ["ai_used", "metadata", "reply"]
    assert set(result["metadata_fields"]) == METADATA_FIELDS


# 4. La respuesta contiene únicamente los campos autorizados.


@pytest.mark.parametrize("slug", TENANTS)
def test_the_response_only_has_the_authorized_fields(api, slug):
    response = api.client.post(URL, headers=_admin(api, slug), json=MESSAGE)
    body = response.json()
    assert response.status_code == 200
    assert set(body) == {"reply", "ai_used", "metadata"}
    assert set(body["metadata"]) == METADATA_FIELDS
    assert all(value is None or isinstance(value, str) for value in body["metadata"].values())
    assert body["metadata"]["tenant_slug"] == slug


def test_unexpected_metadata_of_the_engine_never_leaves(api, monkeypatch):
    hostile = {
        "source": {"sales": "interno"},
        "intent": "texto libre con datos internos",
        "conversation_state": ["lista"],
        "tenant_slug": "saas",
        "sales": {"hard_rules": ["regla interna"]},
        "business": {"description": "interno"},
        "pricing": {"payment": {"link": "interno"}},
        "features": {"interno": True},
        "inventory": {"interno": True},
        "ai_metadata": {"response": "interno"},
        "memory_context": {"history": "interno"},
        "memory_state": {"history": "interno"},
        "prompt": "interno",
        "api_key": "interno",
    }
    monkeypatch.setattr(AIService, "generate_business_reply", lambda self, **kwargs: ("Hola", True, hostile))
    assert api.client.post(URL, headers=_admin(api), json=MESSAGE).json() == {
        "reply": "Hola",
        "ai_used": True,
        "metadata": {"source": None, "intent": None, "conversation_state": None, "tenant_slug": "saas"},
    }


@pytest.mark.parametrize(
    "field",
    [
        pytest.param({"yaml_config": {"post_payment": {"on_user_report": {"message": "inyectado"}}}}, id="configuracion"),
        pytest.param({"tenant_slug": "clinic"}, id="otro_negocio"),
        pytest.param({"memory_context": {"history": "inyectado"}}, id="memoria"),
    ],
)
def test_the_request_cannot_inject_configuration(api, llm, field):
    response = api.client.post(URL, headers=_admin(api), json={**MESSAGE, **field})
    assert response.status_code == 422
    assert llm.prompts == []


# 5. No se exponen datos de pago.


@pytest.mark.parametrize("slug", TENANTS)
def test_payment_data_reaches_neither_the_response_nor_the_model(api, llm, slug):
    values = payment_values(load_tenant_runtime_yaml(slug))
    assert values
    headers = _admin(api, slug)
    placeholders = 0
    for method in PAYMENT_METHODS:
        llm.prompts.clear()
        llm.reply = reply("Perfecto, seguimos.", intent="buy", send_payment=method, payment_status="pending")
        response = api.client.post(URL, headers=headers, json={"user_message": "quiero pagar", "user_id": method})
        assert response.status_code == 200
        assert _leaked(values, response.text) == 0
        assert _leaked(values, " ".join(llm.prompts)) == 0
        placeholders += REDACTED_PAYMENT_VALUE in response.json()["reply"]
    # El motor sí intentó entregar los datos: la prueba no pasa solo porque el flujo no los pidiera.
    assert placeholders > 0


@pytest.mark.parametrize("slug", TENANTS)
def test_the_response_is_filtered_even_if_the_model_returns_a_payment_value(api, llm, slug):
    values = payment_values(load_tenant_runtime_yaml(slug))
    llm.reply = reply(f"Consigna a {values[0]} y me avisas.")
    response = api.client.post(URL, headers=_admin(api, slug), json=MESSAGE)
    assert response.status_code == 200
    assert _leaked(values, response.text) == 0
    assert REDACTED_PAYMENT_VALUE in response.json()["reply"]


def test_a_payment_number_without_quotes_is_also_removed():
    # Valores ficticios: un YAML puede traer el número sin comillas, y un precio distinto no debe alterarse.
    runtime = {
        "pricing": {"payment": {"link": "", "transfer": {"methods": [{"type": "nequi", "number": 3001234567}]}}, "monthly": 45000, "enabled": True},
        "sales": {"closing": {"actions": ["Pide consignar al 3001234567 y confirmar."]}},
    }
    clean = simulation._without_payment_values(runtime, runtime)
    assert clean["pricing"]["payment"]["transfer"]["methods"][0]["number"] == REDACTED_PAYMENT_VALUE
    assert clean["pricing"]["monthly"] == 45000
    assert clean["pricing"]["enabled"] is True
    # Tampoco queda dentro de un texto libre de otra sección, y la configuración original no cambia.
    assert clean["sales"]["closing"]["actions"] == [f"Pide consignar al {REDACTED_PAYMENT_VALUE} y confirmar."]
    assert runtime["pricing"]["payment"]["transfer"]["methods"][0]["number"] == 3001234567
    assert "3001234567" in runtime["sales"]["closing"]["actions"][0]


def test_the_simulation_does_not_alter_the_real_configuration(api):
    before = json.dumps(load_tenant_runtime_yaml("saas"), ensure_ascii=False, sort_keys=True, default=str)
    assert api.client.post(URL, headers=_admin(api), json=MESSAGE).status_code == 200
    assert json.dumps(load_tenant_runtime_yaml("saas"), ensure_ascii=False, sort_keys=True, default=str) == before


# 6. No se exponen reglas comerciales, configuración interna, prompts ni credenciales.


@pytest.mark.parametrize("slug", TENANTS)
def test_commercial_rules_and_internal_configuration_are_not_exposed(api, llm, slug):
    runtime = load_tenant_runtime_yaml(slug)
    internal = {
        text
        for section in ("sales", "business", "pricing", "features", "inventory")
        for text in _texts(runtime.get(section))
        if len(text.strip()) >= 12
    }
    assert internal
    response = api.client.post(URL, headers=_admin(api, slug), json={"user_message": "quiero saber el precio y cómo pagar"})
    assert response.status_code == 200
    assert sum(1 for text in internal if text in response.text) == 0
    forbidden = {"sales", "business", "pricing", "features", "inventory", "ai_metadata", "memory_context", "memory_state"}
    assert not forbidden & set(_keys(response.json()))
    assert llm.prompts and llm.prompts[0][:200] not in response.text
    prices = {str(value) for value in _numbers(runtime.get("pricing")) if value >= 100}
    assert sum(1 for price in prices if price in response.text) == 0


def test_the_reply_is_free_text_and_is_the_only_field_that_can_mention_a_price(api, llm):
    # Límite conocido: `reply` es el texto de la conversación y puede contener lo que diga el modelo, como en un canal
    # real. Ningún campo estructurado lleva precios. Hoy nadie recibe `reply`: la ruta exige la autenticación aplazada.
    prices = sorted(str(value) for value in _numbers(load_tenant_runtime_yaml("saas").get("pricing")) if value >= 100)
    assert prices
    llm.reply = reply(f"El plan cuesta {prices[0]} al mes.")
    body = api.client.post(URL, headers=_admin(api), json={"user_message": "cuanto cuesta"}).json()
    assert prices[0] in body["reply"]
    assert prices[0] not in json.dumps(body["metadata"])


def test_credentials_are_not_exposed(api, monkeypatch):
    markers = {
        "jwt_secret": "MARCA_SECRETO_JWT",
        "meta_access_token": "MARCA_TOKEN_META",
        "meta_app_secret": "MARCA_SECRETO_META",
        "meta_verify_token": "MARCA_VERIFICACION_META",
        "twilio_auth_token": "MARCA_TOKEN_TWILIO",
        "connector_secrets_key": "MARCA_CLAVE_CONECTORES",
    }
    for name, marker in markers.items():
        monkeypatch.setattr(settings, name, marker)
    response = api.client.post(URL, headers=_admin(api), json=MESSAGE)
    assert response.status_code == 200
    assert [marker for marker in markers.values() if marker in response.text] == []


# 7. No se expone la memoria de la conversación, aunque la simulación la use para continuar.


def test_the_response_does_not_contain_the_conversation(api, llm):
    headers = _admin(api)
    marker = "MARCA_DATO_PERSONAL_DEL_TURNO_ANTERIOR"
    first = api.client.post(URL, headers=headers, json={"user_message": f"Mi documento es {marker}", "user_id": "demo"})
    llm.prompts.clear()
    second = api.client.post(URL, headers=headers, json={"user_message": "como funciona", "user_id": "demo"})
    assert marker not in first.text
    assert marker not in second.text
    # La simulación conserva el contexto dentro de su sesión: por eso sirve para probar una secuencia.
    assert marker in " ".join(llm.prompts)


@pytest.mark.parametrize("slug", TENANTS)
def test_the_same_label_continues_a_simulated_conversation(api, slug):
    headers = _admin(api, slug)
    first = api.client.post(URL, headers=headers, json={"user_message": "hola", "user_id": "secuencia"})
    second = api.client.post(URL, headers=headers, json={"user_message": "hola", "user_id": "secuencia"})
    new_label = api.client.post(URL, headers=headers, json={"user_message": "hola", "user_id": "otra"})
    assert first.json()["metadata"]["source"] == "initial_message"
    assert second.json()["metadata"]["source"] != "initial_message"
    assert new_label.json()["metadata"]["source"] == "initial_message"


# 8. Un `user_id` arbitrario no recupera la memoria de otro cliente.


@pytest.mark.parametrize(
    ("customer", "sent_id"),
    [
        pytest.param(f"cliente-real-{uuid4().hex}", "igual_al_cliente", id="identificador_del_cliente"),
        # Sin identificador, el motor usa "anonymous": antes, todas las llamadas sin `user_id` compartían esa memoria.
        pytest.param("anonymous", None, id="sin_identificador"),
    ],
)
def test_an_arbitrary_user_id_does_not_recover_a_real_conversation(api, llm, customer, sent_id):
    marker = "MARCA_CONVERSACION_REAL_DEL_CLIENTE"
    GLOBAL_MEMORY_SERVICE.save_message(tenant_slug="saas", user_id=customer, message_text=f"Mi cuenta es {marker}")
    GLOBAL_MEMORY_SERVICE.set_last_pain(tenant_slug="saas", user_id=customer, pain=marker)
    before = GLOBAL_MEMORY_SERVICE.get_history(tenant_slug="saas", user_id=customer)
    assert marker in json.dumps(before)
    body = {"user_message": "que te dije antes"}
    if sent_id:
        body["user_id"] = customer

    response = api.client.post(URL, headers=_admin(api), json=body)

    assert response.status_code == 200
    assert marker not in response.text
    assert marker not in " ".join(llm.prompts)
    assert llm.prompts
    # Y tampoco escribe en esa conversación.
    assert GLOBAL_MEMORY_SERVICE.get_history(tenant_slug="saas", user_id=customer) == before


@pytest.mark.parametrize("label", ["cliente-real", None], ids=["con_etiqueta", "sin_etiqueta"])
def test_the_simulation_never_touches_the_real_memory_repository(api, monkeypatch, label):
    headers = _admin(api)
    calls: list[str] = []

    def _recording(name, member):
        def _wrapper(*args, **kwargs):
            calls.append(name)
            return member(*args, **kwargs)

        return _wrapper

    for name, member in list(vars(SQLMemoryRepository).items()):
        if inspect.isfunction(member):
            monkeypatch.setattr(SQLMemoryRepository, name, _recording(name, member))

    for message in ("hola", "tengo muchos mensajes", "quiero empezar"):
        body = {"user_message": message, **({"user_id": label} if label else {})}
        assert api.client.post(URL, headers=headers, json=body).status_code == 200
    assert calls == []


def test_the_engine_never_receives_the_identifier_sent_by_the_caller(api, monkeypatch):
    received: list[str | None] = []
    original = AIPipeline.run

    def _run(self, **kwargs):
        received.append(kwargs["user_id"])
        return original(self, **kwargs)

    monkeypatch.setattr(AIPipeline, "run", _run)
    response = api.client.post(URL, headers=_admin(api), json={"user_message": "hola", "user_id": "573001112233"})
    assert response.status_code == 200
    assert len(received) == 1
    assert "573001112233" not in str(received[0])
    assert str(received[0]).startswith("simulacion-")


def test_admins_of_different_businesses_do_not_share_a_simulated_conversation(api, llm):
    marker = "MARCA_DE_OTRO_NEGOCIO"
    first_admin = _admin(api, "saas")
    second_admin = _admin(api, "clinic")
    label = {"user_id": "misma-etiqueta"}
    api.client.post(URL, headers=first_admin, json={"user_message": f"Mi dato es {marker}", **label})
    llm.prompts.clear()
    response = api.client.post(URL, headers=second_admin, json={"user_message": "que te dije antes", **label})
    assert response.status_code == 200
    assert llm.prompts
    assert marker not in " ".join(llm.prompts)


def test_admins_of_the_same_business_do_not_share_a_simulated_conversation(api, llm):
    # Es el caso difícil: mismo negocio y misma etiqueta, así que solo los separa quién llama.
    marker = "MARCA_DE_OTRO_ADMINISTRADOR"
    first_admin = _admin(api, "saas")
    second_admin = _admin(api, "saas")
    label = {"user_id": "misma-etiqueta"}
    api.client.post(URL, headers=first_admin, json={"user_message": f"Mi dato es {marker}", **label})
    llm.prompts.clear()
    response = api.client.post(URL, headers=second_admin, json={"user_message": "que te dije antes", **label})
    assert response.status_code == 200
    assert llm.prompts
    assert marker not in " ".join(llm.prompts)
    assert len(simulation._sessions) == 2


def test_labels_of_one_admin_are_separate_conversations(api, llm):
    marker = "MARCA_DE_OTRA_SESION"
    headers = _admin(api)
    api.client.post(URL, headers=headers, json={"user_message": f"Mi dato es {marker}", "user_id": "a"})
    llm.prompts.clear()
    api.client.post(URL, headers=headers, json={"user_message": "que te dije antes", "user_id": "b"})
    assert llm.prompts
    assert marker not in " ".join(llm.prompts)


def test_the_simulated_sessions_are_bounded(api, monkeypatch):
    monkeypatch.setattr(simulation, "MAX_SIMULATION_SESSIONS", 2)
    headers = _admin(api)
    # "uno" se vuelve a usar antes de que llegue "tres": la que sale es la que lleva más tiempo sin usarse.
    for label in ("uno", "dos", "uno", "tres"):
        assert api.client.post(URL, headers=headers, json={**MESSAGE, "user_id": label}).status_code == 200
    assert [label for _admin_id, label in simulation._sessions] == ["uno", "tres"]


def test_the_label_length_is_limited(api, llm):
    response = api.client.post(URL, headers=_admin(api), json={**MESSAGE, "user_id": "x" * 65})
    assert response.status_code == 422
    assert llm.prompts == []


# 9. El motor comercial sigue igual: esta ruta es lo único que cambia.


def test_the_real_channels_keep_using_the_real_memory():
    service = AIService()
    assert service.pipeline.conversation_flow.memory is GLOBAL_MEMORY_SERVICE


@pytest.mark.parametrize("slug", TENANTS)
def test_the_simulation_only_differs_from_the_real_flow_in_the_payment_values(api, llm, slug):
    headers = _admin(api, slug)
    runtime = load_tenant_runtime_yaml(slug)
    real_reply, real_ai_used, _metadata = _real_flow(slug, "tengo muchos mensajes")
    real_prompts = list(llm.prompts)
    llm.prompts.clear()
    response = api.client.post(URL, headers=headers, json=MESSAGE)
    assert response.json()["reply"] == real_reply
    assert response.json()["ai_used"] is real_ai_used
    assert llm.prompts == [redact_payment_values(prompt, runtime) for prompt in real_prompts]


@pytest.mark.parametrize("slug", TENANTS)
def test_the_real_flow_still_delivers_payment_data_and_its_full_metadata(llm, slug):
    values = payment_values(load_tenant_runtime_yaml(slug))
    delivered = 0
    metadata = {}
    for method in PAYMENT_METHODS:
        llm.reply = reply("Perfecto, seguimos.", intent="buy", send_payment=method, payment_status="pending")
        real_reply, _ai_used, metadata = _real_flow(slug, "quiero pagar")
        delivered += _leaked(values, real_reply)
    assert delivered > 0
    # El cliente recibe el dato al elegir el método; la IA nunca lo ve (ver test_payment_data_protection.py).
    assert _leaked(values, " ".join(llm.prompts)) == 0
    assert {"sales", "business", "pricing", "memory_context"} <= set(metadata)


def test_the_real_flow_keeps_the_conversation_of_each_customer(llm):
    customer = f"cliente-{uuid4().hex}"
    marker = "MARCA_CONTINUIDAD_DEL_CLIENTE"
    _real_flow("saas", f"Mi dato es {marker}", user_id=customer)
    llm.prompts.clear()
    _real_flow("saas", "como funciona", user_id=customer)
    assert marker in " ".join(llm.prompts)
