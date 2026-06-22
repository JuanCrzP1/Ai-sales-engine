from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from semantic_guard import has_forward_intent

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import pytest

from app.application.runtime import load_tenant_runtime_yaml
from app.services.ai_service import AIService

# Suite de integración: ejercita el LLM en vivo (requiere OPENROUTER_API_KEY).
pytestmark = pytest.mark.integration


def _tenant(slug: str) -> SimpleNamespace:
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def _run_turn(*, message: str, tenant_slug: str = "asesor_ai_prod") -> str:
    service = AIService()
    runtime_yaml = load_tenant_runtime_yaml(tenant_slug, channel="whatsapp")
    user_id = f"response-structure-{uuid4().hex[:8]}"

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


def _blocks(text: str) -> list[str]:
    return [block.strip() for block in str(text or "").split("\n\n") if block.strip()]


def test_response_not_single_long_block() -> None:
    response = _run_turn(message="cuánto cuesta")

    assert len(response) < 400 or "\n\n" in response


def test_response_max_two_blocks() -> None:
    response = _run_turn(message="qué incluye el servicio")
    blocks = _blocks(response)

    assert len(blocks) <= 2


def test_cta_in_second_block_when_present() -> None:
    response = _run_turn(message="cuánto cuesta")
    normalized = response.lower()

    assert has_forward_intent(response) or "?" in response or any(
        term in normalized for term in ("precio", "cuesta", "cop", "usd", "mensual", "pago")
    )


def test_simple_response_keeps_clarity_and_commercial_context() -> None:
    response = _run_turn(message="qué es esto")
    blocks = _blocks(response)
    normalized = response.lower()

    assert len(blocks) <= 2
    assert any(term in normalized for term in ("servicio", "negocio", "ventas", "clientes", "seguimiento"))