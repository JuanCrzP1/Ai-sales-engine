"""Inteligencia artificial de cada negocio y área de pruebas del panel.

- La clave de OpenRouter de cada negocio se guarda cifrada, nunca sale completa por la API y un negocio no alcanza la de otro.
- El área de pruebas responde con la versión que se está probando (borrador o publicada) y con la clave de ese negocio, en
  conversaciones aisladas: ni de los clientes reales ni de otros negocios.
- El motor real se prueba con el modelo simulado: nada sale a la red.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin_api.main import create_app
from app.application.ai_pipeline import AIPipeline
from app.application.assistant_lab.engine_runner import EngineAssistantRunner
from app.business_config_application.assistant_lab import AssistantLabService
from app.domain.business_config.ai_settings import AICredentials, AssistantTurn, KeyCheck, clean_api_key, clean_model, key_hint
from app.domain.business_config.errors import (
    AIKeyMissingError,
    AssistantUnavailableError,
    BusinessNotFoundError,
    InvalidFieldsError,
    SecretResolutionError,
)
from app.infrastructure.business_config.ai_settings_store import AISettingsStore
from app.infrastructure.business_config.database import (
    build_assistant_lab_service,
    build_business_config_service,
    create_business_config_engine,
    create_local_schema,
)
from app.infrastructure.business_config.tables import business_ai_settings
from app.infrastructure.config.config_service import ConfigService
from app.infrastructure.config.legacy_store_migration import import_prepared, prepare_tenant
from pipeline_harness import reply

KEY_A = "sk-or-v1-clave-ficticia-del-restaurante-0001"
KEY_B = "sk-or-v1-clave-ficticia-de-la-clinica-0002"
# Como el panel: desde este equipo. La API rechaza cualquier otro origen.
LOCAL = {"base_url": "http://127.0.0.1:8010", "client": ("127.0.0.1", 50000)}


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.resets: list[tuple[str, str]] = []

    def reply(self, *, tenant_slug, sections, credentials, session_id, message):
        self.calls.append({"tenant": tenant_slug, "sections": sections, "credentials": credentials, "session": session_id, "message": message})
        return AssistantTurn(reply=f"Respuesta a: {message}", intent="info")

    def reset(self, *, tenant_slug, session_id):
        self.resets.append((tenant_slug, session_id))


class FakeVerifier:
    def __init__(self) -> None:
        self.checked: list[AICredentials] = []

    def verify(self, credentials):
        self.checked.append(credentials)
        return KeyCheck(True, "La clave funciona.")


@pytest.fixture
def store(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'panel.sqlite3').as_posix()}")
    create_local_schema(engine)
    key = Fernet.generate_key().decode()
    configs = build_business_config_service(engine, secrets_key=key)
    for slug in ("restaurant", "clinic"):
        import_prepared(configs, prepare_tenant(ConfigService(), slug))
    runner, verifier = FakeRunner(), FakeVerifier()
    lab = build_assistant_lab_service(engine, configs, secrets_key=key, verifier=verifier, runner=runner)
    yield SimpleNamespace(engine=engine, key=key, configs=configs, lab=lab, runner=runner, verifier=verifier, path=tmp_path / "panel.sqlite3")
    engine.dispose()


# ---------------------------------------------------------------------------
# Dominio
# ---------------------------------------------------------------------------

def test_the_key_is_checked_without_repeating_it():
    assert clean_api_key(f"  {KEY_A}  ") == KEY_A
    for bad in ("corta", f"{KEY_A} con espacio", "x" * 301):
        with pytest.raises(InvalidFieldsError) as error:
            clean_api_key(bad)
        assert bad not in str(error.value) and all(bad not in issue.message for issue in error.value.issues)
    assert key_hint(KEY_A) == "••••0001"


def test_the_model_uses_the_openrouter_names_or_the_engine_default():
    assert clean_model(" openai/gpt-4o-mini ") == "openai/gpt-4o-mini"
    assert clean_model("meta-llama/llama-3.3-70b-instruct:free") == "meta-llama/llama-3.3-70b-instruct:free"
    assert clean_model("") is None and clean_model(None) is None
    for bad in ("gpt-4o", "openai/ gpt", "openai/gpt 4"):
        with pytest.raises(InvalidFieldsError):
            clean_model(bad)


# ---------------------------------------------------------------------------
# Almacén: cifrada, sin salir completa y por negocio
# ---------------------------------------------------------------------------

def test_the_key_is_encrypted_and_only_its_end_is_shown(store):
    saved = store.lab.save_ai_settings("restaurant", model="openai/gpt-4o-mini", api_key=KEY_A)
    assert (saved.key_configured, saved.key_hint, saved.model) == (True, "••••0001", "openai/gpt-4o-mini")
    with store.engine.connect() as conn:
        stored = conn.execute(select(business_ai_settings.c.key_ciphertext)).scalar_one()
    assert KEY_A not in stored
    assert KEY_A.encode() not in store.path.read_bytes()
    assert store.lab._storage.ai_credentials("restaurant") == AICredentials("openrouter", "openai/gpt-4o-mini", KEY_A)


def test_saving_without_a_new_key_keeps_it_and_clearing_removes_it(store):
    store.lab.save_ai_settings("restaurant", model=None, api_key=KEY_A)
    kept = store.lab.save_ai_settings("restaurant", model="anthropic/claude-3.5-haiku")
    assert kept.key_configured and kept.model == "anthropic/claude-3.5-haiku"
    cleared = store.lab.save_ai_settings("restaurant", model=None, clear_key=True)
    assert (cleared.key_configured, cleared.key_hint, cleared.model) == (False, None, None)
    with pytest.raises(InvalidFieldsError):
        store.lab.save_ai_settings("restaurant", model=None, api_key=KEY_A, clear_key=True)


def test_each_business_only_reaches_its_own_key(store):
    store.lab.save_ai_settings("restaurant", model=None, api_key=KEY_A)
    assert store.lab.ai_settings("clinic").key_configured is False
    assert store.lab._storage.ai_credentials("clinic") is None
    store.lab.save_ai_settings("clinic", model=None, api_key=KEY_B)
    assert store.lab._storage.ai_credentials("restaurant").api_key == KEY_A
    assert store.lab._storage.ai_credentials("clinic").api_key == KEY_B
    with pytest.raises(BusinessNotFoundError):
        store.lab.ai_settings("no_existe")


def test_without_the_right_encryption_key_the_ai_key_is_not_readable(store):
    store.lab.save_ai_settings("restaurant", model=None, api_key=KEY_A)
    with pytest.raises(SecretResolutionError):
        AISettingsStore(store.engine, Fernet.generate_key().decode()).ai_credentials("restaurant")


def test_deleting_a_business_deletes_its_ai_key(store):
    store.lab.save_ai_settings("restaurant", model=None, api_key=KEY_A)
    store.configs.delete_business("restaurant")
    with store.engine.connect() as conn:
        assert conn.execute(select(business_ai_settings)).all() == []


# ---------------------------------------------------------------------------
# Servicio del área de pruebas
# ---------------------------------------------------------------------------

def test_without_a_key_the_assistant_cannot_be_tested(store):
    with pytest.raises(AIKeyMissingError):
        store.lab.talk("restaurant", message="Hola")
    assert store.runner.calls == []


def test_the_draft_is_tested_before_publishing(store):
    store.lab.save_ai_settings("restaurant", model=None, api_key=KEY_A)
    document = store.configs.get_editable("restaurant").stored.config.model_dump(mode="json", exclude_none=True)
    document["messages"]["welcome"]["text"] = "Bienvenida del borrador"
    draft = store.configs.save_changes("restaurant", document).version

    from_draft = store.lab.talk("restaurant", message="Hola")
    from_published = store.lab.talk("restaurant", message="Hola", source="published", session_id=from_draft.session_id)
    assert (from_draft.version, from_published.version) == (draft, 1)
    assert store.runner.calls[0]["sections"]["config"]["initial_message"]["text"] == "Bienvenida del borrador"
    assert store.runner.calls[1]["sections"]["config"]["initial_message"]["text"] != "Bienvenida del borrador"
    assert store.runner.calls[0]["credentials"].api_key == KEY_A
    assert from_draft.turn.reply == "Respuesta a: Hola"


def test_the_conversation_continues_and_can_be_restarted(store):
    store.lab.save_ai_settings("restaurant", model=None, api_key=KEY_A)
    first = store.lab.talk("restaurant", message="Hola")
    second = store.lab.talk("restaurant", message="¿Precio?", session_id=first.session_id)
    assert len(first.session_id) == 32 and second.session_id == first.session_id
    store.lab.reset("restaurant", first.session_id)
    assert store.runner.resets == [("restaurant", first.session_id)]
    for bad_session in ("../otro", "ABC", "x" * 32):
        with pytest.raises(InvalidFieldsError):
            store.lab.talk("restaurant", message="Hola", session_id=bad_session)
    for bad_message in ("", "   ", "a" * 1001):
        with pytest.raises(InvalidFieldsError):
            store.lab.talk("restaurant", message=bad_message)


def test_without_the_engine_the_area_says_it_is_unavailable(store):
    lab = AssistantLabService(store.configs, store.lab._storage)
    lab.save_ai_settings("restaurant", model=None, api_key=KEY_A)
    with pytest.raises(AssistantUnavailableError):
        lab.talk("restaurant", message="Hola")
    with pytest.raises(AssistantUnavailableError):
        lab.verify_ai_key("restaurant")


# ---------------------------------------------------------------------------
# API del panel
# ---------------------------------------------------------------------------

@pytest.fixture
def client(store):
    return TestClient(create_app(store.configs, store.lab), **LOCAL)


def test_the_api_never_returns_the_key(client):
    saved = client.put("/api/businesses/restaurant/ai", json={"model": "openai/gpt-4o-mini", "api_key": KEY_A})
    assert saved.status_code == 200
    assert saved.json() == {"provider": "openrouter", "model": "openai/gpt-4o-mini", "key": {"configured": True, "hint": "••••0001"}}
    read = client.get("/api/businesses/restaurant/ai")
    assert KEY_A not in read.text and KEY_A not in saved.text
    rejected = client.put("/api/businesses/restaurant/ai", json={"api_key": "corta"})
    assert rejected.status_code == 422 and "corta" not in rejected.text


def test_the_api_verifies_the_key_and_talks(client, store):
    assert client.post("/api/businesses/restaurant/playground", json={"message": "Hola"}).json()["code"] == "ai_key_missing"
    client.put("/api/businesses/restaurant/ai", json={"api_key": KEY_A})
    assert client.post("/api/businesses/restaurant/ai/verify").json() == {"valid": True, "message": "La clave funciona."}
    answer = client.post("/api/businesses/restaurant/playground", json={"message": "Hola", "source": "published"})
    assert answer.status_code == 200
    body = answer.json()
    assert (body["reply"], body["source"], body["version"], body["ai_answered"]) == ("Respuesta a: Hola", "published", 1, True)
    reset = client.delete(f"/api/businesses/restaurant/playground/{body['session_id']}")
    assert reset.status_code == 204
    assert client.post("/api/businesses/no_existe/playground", json={"message": "Hola"}).status_code == 404


def test_without_the_lab_the_routes_answer_unavailable(store):
    response = TestClient(create_app(store.configs), **LOCAL).get("/api/businesses/restaurant/ai")
    assert (response.status_code, response.json()["code"]) == (503, "unavailable")


# ---------------------------------------------------------------------------
# El motor real en el área de pruebas
# ---------------------------------------------------------------------------

class _Recorder:
    """Construye el motor real y sustituye solo la llamada al modelo: registra lo que recibe y responde lo indicado."""

    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.keys: list[str] = []
        self.models: list[str | None] = []

    def __call__(self, **kwargs) -> AIPipeline:
        pipeline = AIPipeline(**kwargs)

        def _generate(prompt, *, user_message, bot_config=None):
            self.prompts.append(str(prompt))
            self.keys.append(getattr(bot_config, "api_key", None))
            self.models.append(getattr(bot_config, "model_name", None))
            return reply(f"Respuesta {len(self.prompts)}.")

        pipeline.runtime.generate = _generate
        return pipeline


def _sections(store, slug="restaurant"):
    return store.configs.compile_sections(slug)


def test_the_engine_answers_with_the_tested_configuration_and_the_business_key(store):
    recorder = _Recorder()
    runner = EngineAssistantRunner(pipeline_factory=recorder)
    sections = _sections(store)
    sections["config"]["profile"]["name"] = "Nombre Solo En Esta Versión"
    turn = runner.reply(
        tenant_slug="restaurant", sections=sections, credentials=AICredentials("openrouter", "openai/gpt-4o-mini", KEY_A),
        session_id="a" * 32, message="Hola, ¿qué venden?",
    )
    assert turn.reply == "Respuesta 1." and turn.ai_answered
    assert "Negocio: Nombre Solo En Esta Versión" in recorder.prompts[0]
    assert recorder.keys == [KEY_A] and recorder.models == ["openai/gpt-4o-mini"]


def test_each_conversation_has_its_own_memory(store):
    recorder = _Recorder()
    runner = EngineAssistantRunner(pipeline_factory=recorder)
    credentials = AICredentials("openrouter", None, KEY_A)

    def say(session, slug="restaurant"):
        runner.reply(tenant_slug=slug, sections=_sections(store, slug), credentials=credentials, session_id=session, message="¿Qué venden y a qué precio?")
        return recorder.prompts[-1]

    assert "Negocio: " in say("a" * 32)
    assert "Negocio: " not in say("a" * 32), "la misma conversación continúa"
    assert "Negocio: " in say("b" * 32), "otra conversación empieza de cero"
    assert "Negocio: " in say("a" * 32, slug="clinic"), "la misma sesión en otro negocio es otra conversación"
    runner.reset(tenant_slug="restaurant", session_id="a" * 32)
    assert "Negocio: " in say("a" * 32), "reiniciada, empieza de cero"


def test_idle_and_excess_conversations_are_forgotten():
    now = [0.0]
    runner = EngineAssistantRunner(max_sessions=2, idle_seconds=10, clock=lambda: now[0])
    first = runner._memory("restaurant", "a" * 32)
    runner._memory("restaurant", "b" * 32)
    runner._memory("restaurant", "c" * 32)
    assert ("restaurant", "a" * 32) not in runner._sessions, "se descarta la usada hace más tiempo"
    now[0] = 30.0
    runner._memory("restaurant", "d" * 32)
    assert list(runner._sessions) == [("restaurant", "d" * 32)]
    assert runner._memory("restaurant", "a" * 32) is not first
    json.dumps([list(key) for key in runner._sessions])
