from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import pytest

import semantic_guard
from app.application.runtime import load_tenant_runtime_yaml

# Suite de integración: ejercita el LLM en vivo (requiere OPENROUTER_API_KEY).
pytestmark = pytest.mark.integration
from app.services.ai_service import AIService

TEST_TENANTS = [
    "asesor_ai_prod",
    "restaurant",
    "ecommerce",
    "tienda_de_ropa",
]


def _tenant(slug: str):
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def ask(message: str, tenant: str) -> str:
    service = AIService()
    runtime_yaml = load_tenant_runtime_yaml(tenant, channel="whatsapp")

    response, _, _ = service.generate_business_reply(
        tenant=_tenant(tenant),
        bot_config=None,
        user_message=message,
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        user_id=f"e2e-{uuid4().hex[:6]}",
        include_metadata=True,
    )

    return str(response or "").lower()


def _message(message: str, tenant: str, reply: str, problem: str) -> str:
    return (
        f"tenant={tenant}\n"
        f"input={message}\n"
        f"output={reply}\n"
        f"problema={problem}"
    )


def test_what_do_you_sell_multi_tenant() -> None:
    message = "que venden"
    for tenant in TEST_TENANTS:
        reply = ask(message, tenant)

        assert len(reply.split()) > 8, _message(message, tenant, reply, "informativo")


def test_general_info_does_not_stay_flat() -> None:
    message = "dame información"
    for tenant in TEST_TENANTS:
        reply = ask(message, tenant)

        assert len(reply.split()) > 8, _message(message, tenant, reply, "informativo")


def test_interest_does_not_go_passive() -> None:
    message = "me interesa"
    for tenant in TEST_TENANTS:
        reply = ask(message, tenant)

        assert "?" in reply or len(reply.split()) > 8, _message(
            message,
            tenant,
            reply,
            "pasivo",
        )


def test_price_response_keeps_context() -> None:
    message = "cuanto vale"
    for tenant in TEST_TENANTS:
        reply = ask(message, tenant)

        assert semantic_guard.talks_about_price(reply), _message(
            message,
            tenant,
            reply,
            "no aborda el tema de precio o costo",
        )