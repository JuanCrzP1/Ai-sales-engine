## ========================================
## ARCHIVO: test_initial_message_redesign.py
##
## QUÉ VALIDA:
## Motor de saludo por estado y recency, independiente de primer mensaje.
##
## POR QUÉ ES CRÍTICO:
## Evita saludos duplicados en conversación activa y mantiene reactivación por inactividad.
##
## QUÉ PROTEGE:
## Initial_message backend-driven, continuidad conversacional y consistencia multicanal.
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

from app.application.runtime import load_tenant_runtime_yaml
from app.services.ai_service import AIService


def _tenant(slug: str = "asesor_ai_prod") -> SimpleNamespace:
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def _run_turn(
    service: AIService,
    *,
    user_id: str,
    message: str,
    runtime_yaml: dict | None = None,
) -> tuple[str, bool, dict]:
    if runtime_yaml is None:
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
            user_id=user_id,
            include_metadata=True,
        )
    finally:
        orchestrator.generate_business_reply = original_generate

    return str(response or ""), bool(ai_used), dict(metadata or {})


def _run_turn_with_ai_call_count(
    service: AIService,
    *,
    user_id: str,
    message: str,
    runtime_yaml: dict | None = None,
) -> tuple[str, bool, dict, int]:
    if runtime_yaml is None:
        runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod", channel="whatsapp")

    orchestrator = service.pipeline.runtime.ai_orchestrator
    original_generate = orchestrator.generate_business_reply
    call_count = 0

    def _stub_generate(*args, **kwargs):
        nonlocal call_count
        call_count += 1
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
            user_id=user_id,
            include_metadata=True,
        )
    finally:
        orchestrator.generate_business_reply = original_generate

    return str(response or ""), bool(ai_used), dict(metadata or {}), call_count


def _set_last_activity(service: AIService, *, user_id: str, when: datetime) -> None:
    service.pipeline.memory_repository.update_last_user_message_at("asesor_ai_prod", user_id, when)


def _run_conversation(service: AIService, *, user_id: str, messages: list[str], runtime_yaml: dict | None = None) -> list[str]:
    replies: list[str] = []
    for message in messages:
        reply, _ai_used, _metadata = _run_turn(service, user_id=user_id, message=message, runtime_yaml=runtime_yaml)
        replies.append(reply)
    return replies


def test_initial_message_on_first_contact() -> None:
    service = AIService()
    _reply, ai_used, metadata, call_count = _run_turn_with_ai_call_count(
        service,
        user_id="init-redesign-1",
        message="hola",
    )

    assert ai_used is False
    assert str(metadata.get("source") or "") == "initial_message"
    assert call_count == 0


def test_initial_message_blocks_ai_for_valid_greeting_variant() -> None:
    service = AIService()
    _reply, ai_used, metadata, call_count = _run_turn_with_ai_call_count(
        service,
        user_id="init-redesign-1b",
        message="hola amigo",
    )

    assert ai_used is False
    assert str(metadata.get("source") or "") == "initial_message"
    assert call_count == 0


def test_no_repeated_greeting_in_active_conversation() -> None:
    service = AIService()
    _run_turn(service, user_id="init-redesign-2", message="hola")
    _reply, ai_used, metadata = _run_turn(service, user_id="init-redesign-2", message="hola")

    assert ai_used is True
    assert str(metadata.get("source") or "") != "initial_message"


def test_no_greeting_in_active_conversation() -> None:
    service = AIService()
    replies = _run_conversation(
        service,
        user_id="init-redesign-active-no-greeting",
        messages=["Hola", "Dame info", "Y eso funciona?"],
    )

    assert len(replies) == 3
    assert not replies[-1].startswith("Hola")


def test_single_greeting_per_conversation() -> None:
    service = AIService()
    replies = _run_conversation(
        service,
        user_id="init-redesign-single-greeting",
        messages=["Hola", "Quiero info"],
    )

    assert len(replies) == 2
    assert replies[0].startswith("Hola")
    assert not replies[1].startswith("Hola")


def test_initial_message_when_message_starts_with_greeting_prefix() -> None:
    service = AIService()
    reply, ai_used, metadata = _run_turn(service, user_id="init-redesign-3", message="hola precio")

    assert ai_used is True
    assert str(metadata.get("source") or "") != "initial_message"
    assert reply.startswith("Hola")
    assert "Hola, Hola" not in reply


def test_direct_intent_uses_ai_with_micro_greeting_on_new_conversation() -> None:
    service = AIService()
    reply, ai_used, metadata = _run_turn(service, user_id="init-redesign-3c", message="precio")

    assert ai_used is True
    assert str(metadata.get("source") or "") != "initial_message"
    assert reply.startswith("Hola")
    assert "Hola, Hola" not in reply


def test_no_repeated_greeting_across_new_service_instances() -> None:
    service_1 = AIService()
    _run_turn(service_1, user_id="init-redesign-3b", message="hola")

    service_2 = AIService()
    _reply, ai_used, metadata = _run_turn(service_2, user_id="init-redesign-3b", message="hola")

    assert ai_used is True
    assert str(metadata.get("source") or "") != "initial_message"


def test_initial_message_after_inactive_window() -> None:
    # reset_hours=4 garantiza que 20 minutos de inactividad sea estado warm (no cold)
    # warm → IA responde con contexto, sin repetir saludo inicial
    yaml_cfg = load_tenant_runtime_yaml("asesor_ai_prod", channel="whatsapp")
    yaml_cfg["config"]["conversation"]["reset_hours"] = 4

    service = AIService()
    _run_turn(service, user_id="init-redesign-4", message="hola", runtime_yaml=yaml_cfg)
    _set_last_activity(service, user_id="init-redesign-4", when=datetime.now(timezone.utc) - timedelta(minutes=20))

    _reply, ai_used, metadata = _run_turn(service, user_id="init-redesign-4", message="hola", runtime_yaml=yaml_cfg)

    assert ai_used is True
    assert str(metadata.get("source") or "") != "initial_message"


def test_no_initial_message_within_active_window() -> None:
    service = AIService()
    _run_turn(service, user_id="init-redesign-5", message="hola")
    _set_last_activity(service, user_id="init-redesign-5", when=datetime.now(timezone.utc) - timedelta(minutes=5))

    _reply, ai_used, metadata = _run_turn(service, user_id="init-redesign-5", message="hola")

    assert ai_used is True
    assert str(metadata.get("source") or "") != "initial_message"
