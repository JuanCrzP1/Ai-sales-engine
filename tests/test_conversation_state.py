## ========================================
## ARCHIVO: test_conversation_state.py
##
## QUÉ VALIDA:
## Cálculo temporal de estado conversacional new active warm cold.
##
## POR QUÉ ES CRÍTICO:
## Permite contexto consistente por tenant sin alterar decisiones existentes.
##
## QUÉ PROTEGE:
## Capa de estado conversacional SaaS y contrato de metadata del pipeline.
## ========================================

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.application.pipeline.conversation_flow import get_conversation_state
from app.application.runtime import load_tenant_runtime_yaml
from app.services.ai_service import AIService


def _tenant(slug: str = "asesor_ai_prod") -> SimpleNamespace:
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def _run_with_stub(message: str) -> tuple[str, bool, dict]:
    service = AIService()
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod", channel="whatsapp")

    orchestrator = service.pipeline.runtime.ai_orchestrator
    original_generate = orchestrator.generate_business_reply

    def _stub_generate(*args, **kwargs):
        del args, kwargs
        return "respuesta ia", True, {"intent": "info", "mode": "sales"}

    orchestrator.generate_business_reply = _stub_generate
    try:
        response, ai_used, metadata = service.generate_business_reply(
            tenant=_tenant(),
            bot_config=None,
            user_message=message,
            conversation_history=[],
            faq_results=[],
            yaml_config=runtime_yaml,
            user_id="state-check-user",
            include_metadata=True,
        )
    finally:
        orchestrator.generate_business_reply = original_generate

    return str(response or ""), bool(ai_used), dict(metadata or {})


def test_conversation_state_new() -> None:
    assert get_conversation_state(None, {}) == "new"


def test_conversation_state_active() -> None:
    config = {"conversation": {"active_window_minutes": 15, "reset_hours": 4}}
    last_message_at = datetime.now(timezone.utc) - timedelta(minutes=5)

    assert get_conversation_state(last_message_at, config) == "active"


def test_conversation_state_warm() -> None:
    config = {"conversation": {"active_window_minutes": 15, "reset_hours": 4}}
    last_message_at = datetime.now(timezone.utc) - timedelta(minutes=45)

    assert get_conversation_state(last_message_at, config) == "warm"


def test_conversation_state_cold() -> None:
    config = {"conversation": {"active_window_minutes": 15, "reset_hours": 4}}
    last_message_at = datetime.now(timezone.utc) - timedelta(hours=5)

    assert get_conversation_state(last_message_at, config) == "cold"

    _reply, _ai_used, metadata = _run_with_stub("hola que venden")
    assert isinstance(metadata, dict)
    assert "source" in metadata
    assert "intent" in metadata
