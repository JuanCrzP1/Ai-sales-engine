"""Una sola llamada al asesor por mensaje, y el consumo de cada negocio a la vista.

Antes el prompt no pedía el formato de respuesta: el modelo contestaba en texto, el motor lo rechazaba y repetía toda la llamada
con el formato al final. Casi cada mensaje costaba dos llamadas a la clave del negocio. Ahora el formato va en la primera, se le
pide JSON al proveedor y, si algo no viene perfecto, se aprovecha lo que escribió el modelo sin volver a llamarlo.

Además del asesor, un negocio con medios de pago hace una llamada corta por mensaje: el lector de pagos, que entiende qué pide el
cliente sobre el pago (`payment_reading.py`; unos 500 tokens frente a los 3.000 del asesor). Y al asesor solo se le pide otra respuesta
si la primera decía algo falso sobre los pagos o iba a enviar datos que el cliente no pidió (`test_payment_data_protection.py`). Todas
se suman al consumo del negocio.
"""
from __future__ import annotations

import re
import threading
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.application.ai_pipeline import AIPipeline
from app.infrastructure.ai.prompting.instructions import PLATFORM
from app.application.runtime import MessageAI
from app.domain.business_config.ai_settings import AICredentials
from app.domain.business_config.ai_usage import AIUsage
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.business_config.ai_usage_store import AIUsageStore
from app.infrastructure.business_config.database import create_business_config_engine, create_local_schema
from app.infrastructure.business_config.tables import ai_usage
from app.infrastructure.persistence.memory_repository import MemoryRepository
from app.services.ai.ai_orchestrator import FAILED_REPLY
from app.services.ai.output_contract import OUTPUT_CONTRACT
from app.services.ai_runtime.runtime_llm import client as client_module
from app.services.ai_runtime.runtime_llm.prompting import RuntimeLLMImplementation
from pipeline_harness import reply

ROOT_DIR = Path(__file__).resolve().parents[1]
KEY = "sk-or-v1-clave-ficticia-del-restaurante-0001"
MESSAGE = "¿Qué venden y a qué precio?"
CREDENTIALS = AICredentials("openrouter", "openai/gpt-4o-mini", KEY)


def _pipeline(outputs: list[str], **options) -> tuple[AIPipeline, list[str]]:
    """El motor real con un modelo simulado que devuelve `outputs` en orden y registra cada llamada."""
    prompts: list[str] = []
    pipeline = AIPipeline(memory_service=MemoryDomainService(MemoryRepository()), ai_loader=lambda _slug: CREDENTIALS, **options)

    def _generate(prompt, *, user_message, bot_config=None, **_kwargs):
        prompts.append(prompt)
        return outputs.pop(0)

    pipeline.runtime.generate = _generate
    return pipeline, prompts


def _say(pipeline: AIPipeline, *, user: str = "cliente-1") -> tuple[str, bool, dict]:
    return pipeline.run(
        tenant=SimpleNamespace(slug="restaurant", name="restaurant", id="restaurant"),
        user_message=MESSAGE,
        user_id=user,
        bot_config=None,
        conversation_history=[],
        faq_results=[],
        yaml_config=None,
        include_metadata=True,
    )


# ---------------------------------------------------------------------------
# Una llamada por mensaje
# ---------------------------------------------------------------------------

def test_a_well_formed_answer_takes_one_call_and_keeps_its_intent():
    pipeline, prompts = _pipeline([reply("Tenemos menú del día a 18.000.", intent="info")])
    answer, ai_used, metadata = _say(pipeline)
    assert len(prompts) == 1
    assert "menú del día" in answer and ai_used is True and metadata["intent"] == "info"


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        ("Tenemos menú del día a 18.000.", "menú del día"),  # el modelo ignoró el formato y escribió el mensaje
        ('{"response": "Tenemos menú del día.", "intent": "pricing"}', "menú del día"),  # intención que no existe
        ('{"response": "Tenemos menú del día.", "intent": "info", "metadata": {', "menú del día"),  # JSON cortado
    ],
)
def test_an_imperfect_answer_is_used_without_calling_again(output, expected):
    pipeline, prompts = _pipeline([output])
    answer, ai_used, metadata = _say(pipeline)
    assert len(prompts) == 1
    assert expected in answer and ai_used is True
    assert metadata["intent"] == "" and "{" not in answer


def test_an_unusable_answer_never_reaches_the_customer_as_json_and_is_not_repeated():
    pipeline, prompts = _pipeline(['{"intent": "info", "response": "Tenemos menú'])
    answer, ai_used, _metadata = _say(pipeline)
    assert len(prompts) == 1
    assert answer == FAILED_REPLY and ai_used is False


def test_the_first_call_already_asks_for_the_format():
    pipeline, prompts = _pipeline([reply("Hola.")])
    _say(pipeline)
    [prompt] = prompts
    # El formato va con las instrucciones fijas, al principio: igual en todos los mensajes (el proveedor lo reutiliza de su caché).
    assert prompt.startswith(f"{PLATFORM}\n\n{OUTPUT_CONTRACT}")
    for intent in ("pain", "info", "objection", "buy"):
        assert f'"{intent}"' in OUTPUT_CONTRACT
    assert "JSON" in OUTPUT_CONTRACT  # requisito de `response_format: json_object`


def test_simultaneous_messages_do_not_mix_their_instructions():
    """Antes se reemplazaba `runtime.generate` en un objeto compartido: dos mensajes a la vez acumulaban las instrucciones."""
    prompts: list[str] = []
    first_inside, release = threading.Event(), threading.Event()
    pipeline = AIPipeline(memory_service=MemoryDomainService(MemoryRepository()), ai_loader=lambda _slug: CREDENTIALS)

    def _generate(prompt, *, user_message, bot_config=None, **_kwargs):
        prompts.append(prompt)
        if len(prompts) == 1:
            first_inside.set()
            release.wait(10)
        return reply("Hola.")

    pipeline.runtime.generate = _generate
    first = threading.Thread(target=_say, args=(pipeline,), kwargs={"user": "cliente-1"})
    first.start()
    assert first_inside.wait(10)
    second = threading.Thread(target=_say, args=(pipeline,), kwargs={"user": "cliente-2"})
    second.start()
    second.join(10)
    release.set()
    first.join(10)
    assert len(prompts) == 2
    assert [prompt.count("CÓMO RESPONDES") for prompt in prompts] == [1, 1]
    assert pipeline.runtime.generate is _generate


# ---------------------------------------------------------------------------
# La llamada al proveedor
# ---------------------------------------------------------------------------

class _Provider:
    """OpenRouter simulado: guarda cada carga y responde con tokens y costo."""

    payloads: list[dict] = []

    def __init__(self, api_key, *_args):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **payload):
        _Provider.payloads.append(payload)
        return {
            "choices": [{"message": {"content": reply("Hola.")}}],
            "usage": {"prompt_tokens": 1200, "completion_tokens": 80, "total_tokens": 1280, "cost": 0.0004},
        }


@pytest.fixture
def provider(monkeypatch):
    _Provider.payloads = []
    monkeypatch.setattr(client_module, "_OpenRouterCompletions", _Provider)
    return _Provider


def test_the_provider_is_asked_for_json_and_the_usage_goes_to_the_business(provider):
    seen: list[tuple] = []
    config = MessageAI(api_key=KEY, model_name="openai/gpt-4o-mini", on_usage=lambda *usage: seen.append(usage))
    RuntimeLLMImplementation().generate("instrucciones", user_message="hola", bot_config=config)
    assert [payload["response_format"] for payload in provider.payloads] == [{"type": "json_object"}]
    assert seen == [("openai/gpt-4o-mini", 1200, 80, 0.0004)]


def test_a_client_that_does_not_take_the_format_still_answers_once():
    calls: list[dict] = []

    def create(*, model, temperature, messages, max_tokens=None, top_p=None):
        calls.append({"model": model})
        return {"choices": [{"message": {"content": reply("Hola.")}}]}

    runtime = RuntimeLLMImplementation()
    runtime.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    assert runtime.generate("instrucciones", user_message="hola", bot_config=MessageAI(api_key=KEY))
    assert len(calls) == 1


def test_every_answer_of_the_engine_adds_to_its_business_usage(provider):
    seen: list[tuple] = []
    pipeline = AIPipeline(
        memory_service=MemoryDomainService(MemoryRepository()),
        ai_loader=lambda _slug: CREDENTIALS,
        usage_recorder=lambda slug: (lambda *usage: seen.append((slug, *usage))),
    )
    _say(pipeline)
    # La lectura corta del pago y la respuesta del asesor: las dos van al consumo del negocio.
    assert seen == [("restaurant", "openai/gpt-4o-mini", 1200, 80, 0.0004)] * 2


def test_the_openrouter_logs_never_carry_what_the_customer_wrote(monkeypatch):
    records: list[tuple] = []

    class Recorder:
        def info(self, *args, **kwargs):
            records.append((args, kwargs))

        error = warning = info

    class Response:
        status_code = 200
        text = '{"choices": []}'

        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": reply("Hola.")}}]}

    monkeypatch.setattr(client_module, "logger", Recorder())
    monkeypatch.setattr(client_module.requests, "post", lambda *_args, **_kwargs: Response())
    completions = client_module._OpenRouterCompletions(KEY, "https://openrouter.ai/api/v1", 10, 0)
    completions.chat.completions.create(model="openai/gpt-4o-mini", messages=[{"role": "user", "content": MESSAGE}])
    assert records and MESSAGE not in repr(records) and KEY not in repr(records)


# ---------------------------------------------------------------------------
# El consumo de cada negocio
# ---------------------------------------------------------------------------

@pytest.fixture
def usage_store(tmp_path):
    from cryptography.fernet import Fernet

    from app.infrastructure.business_config.database import build_business_config_service
    from app.infrastructure.business_config.example_businesses import import_example, load_example

    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'consumo.sqlite3').as_posix()}")
    create_local_schema(engine)
    service = build_business_config_service(engine, secrets_key=Fernet.generate_key().decode())
    for slug in ("restaurant", "clinic"):
        import_example(service, load_example(slug))
    yield AIUsageStore(engine)
    engine.dispose()


def test_the_usage_adds_up_per_business_day_and_model(usage_store):
    today = date(2026, 11, 10)
    usage_store.add("restaurant", today, AIUsage("openai/gpt-4o-mini", 1000, 50, 0.0003))
    usage_store.add("restaurant", today, AIUsage("openai/gpt-4o-mini", 1100, 70, None))  # sin costo informado
    usage_store.add("restaurant", today, AIUsage("anthropic/claude-haiku", 900, 40, 0.0002))
    usage_store.add("restaurant", today - timedelta(days=40), AIUsage("openai/gpt-4o-mini", 5000, 500, 0.01))
    usage_store.add("clinic", today, AIUsage("openai/gpt-4o-mini", 9999, 999, 1.0))

    summary = usage_store.summary("restaurant", since=today - timedelta(days=29))
    assert (summary.replies, summary.prompt_tokens, summary.completion_tokens) == (3, 3000, 160)
    assert summary.cost_usd == pytest.approx(0.0005)
    assert summary.total_tokens == 3160
    assert [(day.day, day.replies) for day in summary.days] == [(today, 3)]


def test_without_reported_cost_the_cost_is_unknown_not_zero(usage_store):
    today = date(2026, 11, 10)
    usage_store.add("clinic", today, AIUsage("openai/gpt-4o-mini", 100, 10))
    assert usage_store.summary("clinic", since=today).cost_usd is None


def test_the_ai_usage_migration_matches_the_table():
    sql = (ROOT_DIR / "project" / "db" / "migrations" / "0007_ai_usage.sql").read_text(encoding="utf-8")
    body = re.search(r"CREATE TABLE IF NOT EXISTS ai_usage \((.*?)\n\);", sql, re.S).group(1)
    columns = {match.group(1) for match in re.finditer(r"^\s+([a-z_]+)\s+[A-Z]+", body, re.M)} - {"primary"}
    assert columns == {column.name for column in ai_usage.columns}
    assert "PRIMARY KEY (tenant_id, day, model)" in sql and "REFERENCES tenants(id) ON DELETE CASCADE" in sql


def test_the_panel_names_the_same_intents_as_the_engine():
    from app.services.ai.output_contract import INTENTS
    from app.services.ai.structured_output import VALID_INTENTS

    source = (ROOT_DIR / "apps" / "admin-web" / "src" / "domain" / "assistant" / "intents.ts").read_text(encoding="utf-8")
    block = re.search(r"INTENT_LABELS = \{(.*?)\}", source, re.S).group(1)
    assert tuple(re.findall(r"^\s+([a-z]+):", block, re.M)) == INTENTS
    assert set(INTENTS) == VALID_INTENTS
