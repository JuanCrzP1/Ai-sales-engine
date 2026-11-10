"""La IA es de cada negocio: el motor responde cada mensaje con la clave de OpenRouter y el modelo del negocio que lo recibe.

La plataforma no tiene clave propia. Un negocio sin clave no responde con IA, aunque haya una clave en el entorno, y un mensaje
nunca sale con la clave de otro negocio, aunque el mismo motor atienda a varios.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet

from app.application.ai_pipeline import AIPipeline
from app.application.runtime import MessageAI, load_business_ai, message_ai
from app.config import settings
from app.domain.business_config.ai_settings import AICredentials
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.business_config import database as business_config_database
from app.infrastructure.business_config import runtime_access
from app.infrastructure.business_config.ai_settings_store import AISettingsStore
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.business_config.payment_secret_store import SECRETS_KEY_ENV
from app.infrastructure.config.config_service import ConfigService
from app.infrastructure.config.legacy_store_migration import import_prepared, prepare_tenant
from app.infrastructure.persistence.memory_repository import MemoryRepository
from app.services.ai_runtime.runtime_llm import client as client_module
from app.services.ai_runtime.runtime_llm.prompting import RuntimeLLMImplementation
from pipeline_harness import reply

KEY_A = "sk-or-v1-clave-ficticia-del-restaurante-0001"
KEY_B = "sk-or-v1-clave-ficticia-de-la-clinica-0002"
ENV_KEY = "sk-or-v1-clave-del-entorno-que-nunca-se-usa-9999"
MESSAGE = "¿Qué venden y a qué precio?"


def _engine(ai_loader=None) -> tuple[AIPipeline, list[MessageAI]]:
    """Un mismo motor para todos los negocios. Registra con qué IA se pidió cada respuesta, sin llamar al proveedor."""
    calls: list[MessageAI] = []
    pipeline = AIPipeline(memory_service=MemoryDomainService(MemoryRepository()), ai_loader=ai_loader)

    def _generate(prompt, *, user_message, bot_config=None, **_kwargs):
        calls.append(bot_config)
        return reply("Respuesta.")

    pipeline.runtime.generate = _generate
    return pipeline, calls


def _say(pipeline: AIPipeline, slug: str) -> tuple[str, bool]:
    return pipeline.run(
        tenant=SimpleNamespace(slug=slug, name=slug, id=slug),
        user_message=MESSAGE,
        user_id=f"cliente-de-{slug}",
        bot_config=None,
        conversation_history=[],
        faq_results=[],
        yaml_config=None,
    )


# ---------------------------------------------------------------------------
# Cada mensaje, con la IA de su negocio
# ---------------------------------------------------------------------------

def test_each_message_uses_the_key_and_model_of_its_business():
    businesses = {
        "restaurant": AICredentials("openrouter", "openai/gpt-4o-mini", KEY_A),
        "clinic": AICredentials("openrouter", None, KEY_B),
    }
    pipeline, calls = _engine(businesses.get)
    for slug in ("restaurant", "clinic", "restaurant"):
        _say(pipeline, slug)
    assert [(call.api_key, call.model_name) for call in calls] == [(KEY_A, "openai/gpt-4o-mini"), (KEY_B, None), (KEY_A, "openai/gpt-4o-mini")]


def test_a_business_without_key_never_answers_with_ai(monkeypatch):
    # Ni siquiera con una clave en el entorno: la plataforma no tiene clave propia.
    monkeypatch.setenv("OPENROUTER_API_KEY", ENV_KEY)
    built: list[str] = []
    monkeypatch.setattr(client_module, "_OpenRouterCompletions", lambda api_key, *_args: built.append(api_key))
    pipeline = AIPipeline(memory_service=MemoryDomainService(MemoryRepository()), ai_loader=lambda _slug: None)
    answer, ai_used = _say(pipeline, "restaurant")
    assert answer and ai_used is False
    assert built == []


def test_the_call_to_the_provider_goes_out_with_the_key_of_that_message(monkeypatch):
    sent: list[str] = []

    class Provider:
        def __init__(self, api_key, *_args):
            sent.append(api_key)
            answer = {"choices": [{"message": {"content": reply("Hola.")}}]}
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **_payload: answer))

    monkeypatch.setattr(client_module, "_OpenRouterCompletions", Provider)
    runtime = RuntimeLLMImplementation()
    for key in (KEY_A, KEY_B):
        assert runtime.generate("prompt", user_message="hola", bot_config=MessageAI(api_key=key))
    assert sent == [KEY_A, KEY_B]
    # El cliente de un mensaje no se guarda: el siguiente no puede heredarlo.
    assert runtime.client is None
    with pytest.raises(RuntimeError, match="business_ai_key_missing"):
        runtime.generate("prompt", user_message="hola", bot_config=MessageAI())


def test_a_message_never_takes_the_key_from_the_caller():
    caller = SimpleNamespace(api_key=KEY_B, openrouter_api_key=KEY_B, model_name="openai/gpt-4o", temperature=0.2)
    assert message_ai(caller, None) == MessageAI(model_name="openai/gpt-4o", temperature=0.2)
    business = AICredentials("openrouter", None, KEY_A)
    assert message_ai(caller, business) == MessageAI(api_key=KEY_A, model_name="openai/gpt-4o", temperature=0.2)
    assert message_ai(None, AICredentials("openrouter", "openai/gpt-4o-mini", KEY_A)).model_name == "openai/gpt-4o-mini"


def test_the_key_never_appears_in_a_log():
    for value in (AICredentials("openrouter", "openai/gpt-4o-mini", KEY_A), MessageAI(api_key=KEY_A, model_name="openai/gpt-4o-mini")):
        assert KEY_A not in repr(value) and KEY_A not in str(value)


def test_the_platform_has_no_general_key_and_starts_without_one(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert not hasattr(settings, "openrouter_api_key")
    from app import main

    main.prepare_application()


# ---------------------------------------------------------------------------
# La clave que el negocio guardó en el panel
# ---------------------------------------------------------------------------

@pytest.fixture
def platform(tmp_path, monkeypatch):
    """El almacén de la plataforma con dos negocios: solo el restaurante guardó su clave."""
    path = tmp_path / "plataforma.sqlite3"
    engine = create_business_config_engine(f"sqlite:///{path.as_posix()}")
    create_local_schema(engine)
    key = Fernet.generate_key().decode()
    configs = build_business_config_service(engine, secrets_key=key)
    for slug in ("restaurant", "clinic"):
        import_prepared(configs, prepare_tenant(ConfigService(), slug))
    AISettingsStore(engine, key).save_ai_settings("restaurant", model="openai/gpt-4o-mini", api_key=KEY_A, clear_key=False)
    monkeypatch.setenv(business_config_database.DATABASE_URL_ENV, f"sqlite:///{path.as_posix()}")
    monkeypatch.setenv(SECRETS_KEY_ENV, key)
    runtime_access.dispose_shared_engines()
    yield engine
    runtime_access.dispose_shared_engines()
    engine.dispose()


def test_the_engine_reads_each_business_key_from_the_platform(platform):
    assert load_business_ai("restaurant") == AICredentials("openrouter", "openai/gpt-4o-mini", KEY_A)
    assert load_business_ai("clinic") is None
    assert load_business_ai("negocio-inexistente") is None


def test_a_real_message_answers_with_the_key_saved_in_the_panel(platform):
    pipeline, calls = _engine()
    _say(pipeline, "restaurant")
    _say(pipeline, "clinic")
    assert [(call.api_key, call.model_name) for call in calls] == [(KEY_A, "openai/gpt-4o-mini"), (None, None)]


def test_each_answer_adds_to_the_usage_of_its_business_and_a_failure_never_blocks_the_reply(platform):
    from datetime import datetime, timezone

    from app.application.runtime import business_usage_recorder
    from app.infrastructure.business_config.ai_usage_store import AIUsageStore

    business_usage_recorder("restaurant")("openai/gpt-4o-mini", 1200, 80, 0.0004)
    business_usage_recorder("negocio_inexistente")("openai/gpt-4o-mini", 1, 1, None)  # se registra el fallo y sigue
    today = datetime.now(timezone.utc).date()
    summary = AIUsageStore(platform).summary("restaurant", since=today)
    assert (summary.replies, summary.prompt_tokens, summary.completion_tokens, summary.cost_usd) == (1, 1200, 80, 0.0004)
