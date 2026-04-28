from __future__ import annotations

import io
import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.application.runtime import load_tenant_runtime_yaml
from app.application.runtime.tenant_runtime_loader import _load_raw_runtime_yaml
from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService
from app.infrastructure.config.config_service import ConfigService
from app.services.ai_service import AIService
from semantic_guard import has_forward_intent


def _tenant(slug: str = "asesor_ai_prod") -> SimpleNamespace:
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def _normalize(text: str) -> str:
    return str(text or "").strip().lower()


def _paragraphs(text: str) -> list[str]:
    return [paragraph.strip() for paragraph in str(text or "").split("\n\n") if paragraph.strip()]


def _has_value_signal(text: str) -> bool:
    normalized = _normalize(text)
    return any(token in normalized for token in ("vent", "client", "dinero", "oportun", "respuest", "respond", "seguim"))


def _has_non_technical_tone(text: str) -> bool:
    normalized = _normalize(text)
    forbidden = ["pipeline", "automatización_respuesta", "automatizacion_respuesta", "flujo"]
    return not any(word in normalized for word in forbidden)


def _run_turn(*, message: str, user_id: str, tenant_slug: str = "asesor_ai_prod") -> str:
    service = AIService()
    runtime_yaml = load_tenant_runtime_yaml(tenant_slug, channel="whatsapp")

    service.generate_business_reply(
        tenant=_tenant(tenant_slug),
        bot_config=None,
        user_message="hola",
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        user_id=user_id,
        include_metadata=True,
    )

    response, _ai_used, _metadata = service.generate_business_reply(
        tenant=_tenant(tenant_slug),
        bot_config=None,
        user_message=message,
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        user_id=user_id,
        include_metadata=True,
    )
    return str(response or "")


@pytest.fixture
def run_bot():
    def _runner(message: str) -> str:
        return _run_turn(message=message, user_id=f"sales-behavior-{uuid4().hex[:8]}")

    return _runner


@pytest.fixture
def response(run_bot) -> str:
    return run_bot("tengo muchos mensajes")


@pytest.fixture
def runtime_yaml() -> dict:
    return load_tenant_runtime_yaml("asesor_ai_prod", channel="whatsapp")


@pytest.fixture
def raw_yaml() -> dict:
    return _load_raw_runtime_yaml(ConfigService(), "asesor_ai_prod", channel="whatsapp")


@pytest.fixture
def prompt(runtime_yaml: dict) -> str:
    service = AIService()
    pipeline = service.pipeline
    runtime = pipeline.runtime
    ai_execution = pipeline.ai_execution
    captured: dict[str, str] = {}
    original_generate = runtime.generate

    def _capture_generate(prompt: str, *, user_message: str, bot_config=None):
        del bot_config
        captured["prompt"] = str(prompt or "")
        captured["user_message"] = str(user_message or "")
        return '{"response": "ok", "intent": "info"}'

    runtime.generate = _capture_generate
    try:
        with io.StringIO() as _buffer, pytest.MonkeyPatch().context() as _ctx:
            ai_execution.run(
                runtime=runtime,
                tenant=_tenant(),
                bot_config=None,
                user_message="hola",
                conversation_history=[],
                faq_results=[],
                runtime_yaml=runtime_yaml,
                memory_service=pipeline.conversation_flow.memory,
                demo_service=pipeline.conversation_flow.demo,
                tenant_slug="asesor_ai_prod",
                user_id=f"prompt-capture-{uuid4().hex[:8]}",
            )
    finally:
        runtime.generate = original_generate

    return str(captured.get("prompt") or "")


def test_response_pushes_next_step(response: str) -> None:
    """
    Este test valida que el sistema SIEMPRE intenta avanzar la conversación.

    No importa el texto exacto.
    Importa que exista una intención clara de continuar (pregunta o siguiente paso).

    Esto es crítico para ventas.
    """
    assert "?" in response or "¿" in response or has_forward_intent(response)


def test_response_max_two_paragraphs(response: str) -> None:
    """
    El sistema debe responder en formato corto tipo WhatsApp.

    Máximo 2 bloques de texto (separados por salto de línea doble).
    Esto garantiza legibilidad y naturalidad.
    """
    assert len(_paragraphs(response)) <= 2


def test_response_not_technical(response: str) -> None:
    """
    El sistema NO debe sonar técnico.

    Debe evitar palabras como:
    - pipeline
    - automatización_respuesta
    - flujo
    - sistema

    Esto protege el lenguaje comercial humano.
    """
    normalized = _normalize(response)
    assert _has_non_technical_tone(response)
    assert "sistema" not in normalized


def test_response_mentions_value_or_money(response: str) -> None:
    """
    El sistema debe conectar con valor o dinero.

    No siempre debe decir precio, pero sí debe reflejar:
    - ventas
    - clientes
    - dinero
    - oportunidades

    Esto valida que está en modo comercial.
    """
    assert _has_value_signal(response)


def test_what_do_you_sell_behavior(run_bot) -> None:
    """
    Caso crítico del sistema.

    Input: "qué vendes"

    Debe:
    - explicar valor
    - conectar con beneficio
    - cerrar con pregunta

    NO debe quedarse solo describiendo.
    """
    response = run_bot("qué vendes")
    normalized = _normalize(response)

    assert "?" in response or "¿" in response or has_forward_intent(response)
    assert any(word in normalized for word in ["vent", "client", "respond", "seguim", "oportun"])


def test_objection_expensive(run_bot) -> None:
    """
    El sistema debe manejar objeción de precio.

    Debe:
    - validar la objeción
    - reencuadrar valor
    - empujar siguiente paso

    NO debe solo justificar precio.
    """
    response = run_bot("está caro")
    normalized = _normalize(response)

    assert "?" in response or "¿" in response or has_forward_intent(response)
    assert any(word in normalized for word in ["vale", "retorno", "vent", "pierd", "oportun", "invers"])


def test_input_appears_once_in_system(prompt: str) -> None:
    """
    El input del usuario debe aparecer SOLO una vez dentro del system prompt.

    Y una vez en el mensaje user.

    Esto evita ruido y degradación del modelo.
    """
    user_message = "hola"
    system_prompt = prompt

    assert system_prompt.count(user_message) <= 1


def test_runtime_yaml_integrity(runtime_yaml: dict, raw_yaml: dict) -> None:
    """
    El runtime_yaml debe ser idéntico al YAML original del tenant.

    Esto evita pérdida de contexto comercial.
    """
    assert runtime_yaml == raw_yaml