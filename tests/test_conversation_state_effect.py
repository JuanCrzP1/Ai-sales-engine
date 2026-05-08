## ========================================
## ARCHIVO: test_conversation_state_effect.py
##
## QUÉ VALIDA:
## Efecto real del estado conversacional sobre el comportamiento del pipeline.
##
## POR QUÉ ES CRÍTICO:
## Garantiza que cold/active no producen saludos duplicados ni reinicio.
##
## QUÉ PROTEGE:
## Continuidad conversacional y avance comercial sin amnesia de bot.
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


def _run_turn(service: AIService, *, user_id: str, message: str) -> tuple[str, bool, dict]:
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


def _set_last_user_message_at(service: AIService, *, user_id: str, when: datetime) -> None:
    service.pipeline.memory_repository.update_last_user_message_at("asesor_ai_prod", user_id, when)


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que estado cold reactive el saludo inicial.
##
## POR QUÉ ES IMPORTANTE:
## cold significa chat inactivo: un saludo puro debe poder reabrir la conversación.
##
## QUÉ PROTEGE:
## Reactivación limpia cuando el usuario vuelve después de inactividad real.
## ----------------------------------------
def test_cold_state_reactivates_initial_message() -> None:
    service = AIService()
    uid = "effect-cold-1"

    # Primera vuelta: registra al usuario
    _run_turn(service, user_id=uid, message="hola")

    # Simular 5 horas de inactividad → estado cold
    _set_last_user_message_at(service, user_id=uid, when=datetime.now(timezone.utc) - timedelta(hours=5))

    # El estado debe ser cold
    last_at = service.pipeline.memory_repository.get_memory("asesor_ai_prod", uid).get("last_user_message_at")
    assert get_conversation_state(last_at, {"conversation": {"active_window_minutes": 15, "reset_hours": 4}}) == "cold"

    # Un segundo saludo cold → debe disparar initial_message
    _reply, ai_used, metadata = _run_turn(service, user_id=uid, message="hola")
    assert ai_used is False
    assert str(metadata.get("source") or "") == "initial_message"


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que estado active NO reinicia la conversación.
##
## POR QUÉ ES IMPORTANTE:
## active significa conversación en curso: no debe haber saludo ni reset.
##
## QUÉ PROTEGE:
## Continuidad y avance directo en conversación activa.
## ----------------------------------------
def test_active_state_does_not_restart_conversation() -> None:
    service = AIService()
    uid = "effect-active-1"

    # Primera vuelta: activa al usuario
    _run_turn(service, user_id=uid, message="hola")

    # Simular mensaje reciente → estado active
    _set_last_user_message_at(service, user_id=uid, when=datetime.now(timezone.utc) - timedelta(minutes=3))

    # El estado debe ser active
    last_at = service.pipeline.memory_repository.get_memory("asesor_ai_prod", uid).get("last_user_message_at")
    assert get_conversation_state(last_at, {"conversation": {"active_window_minutes": 15, "reset_hours": 4}}) == "active"

    # Mensaje de objeción en estado active → va a IA, no reinicia
    _reply, ai_used, metadata = _run_turn(service, user_id=uid, message="esta caro")
    assert ai_used is True
    assert str(metadata.get("source") or "") != "initial_message"


def test_cold_state_clears_runtime_history_and_marks_new() -> None:
    service = AIService()
    uid = "effect-cold-reset-1"
    flow = service.pipeline.conversation_flow
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod", channel="whatsapp")

    flow.memory.save_message(tenant_slug="asesor_ai_prod", user_id=uid, message_text="mensaje viejo")
    flow.memory.set_last_intent(tenant_slug="asesor_ai_prod", user_id=uid, intent="buy")
    flow.memory.set_stage(tenant_slug="asesor_ai_prod", user_id=uid, stage="closing")
    flow.memory.set_last_user_message_at(
        tenant_slug="asesor_ai_prod",
        user_id=uid,
        sent_at=datetime.now(timezone.utc) - timedelta(hours=5),
    )

    result = flow.process(
        tenant=_tenant(),
        tenant_slug="asesor_ai_prod",
        user_id=uid,
        user_message="de que hablas",
        conversation_history=[],
        runtime_yaml=runtime_yaml,
    )

    assert result.runtime_yaml.get("conversation_state") == "new"
    assert result.runtime_yaml.get("conversation_history") == []
    assert flow.memory.get_last_intent(tenant_slug="asesor_ai_prod", user_id=uid) == ""
    assert flow.memory.get_stage(tenant_slug="asesor_ai_prod", user_id=uid) == ""


def test_cold_state_direct_intent_uses_ai_with_micro_greeting() -> None:
    service = AIService()
    uid = "effect-cold-reset-greeting-1"

    _run_turn(service, user_id=uid, message="hola")
    _set_last_user_message_at(service, user_id=uid, when=datetime.now(timezone.utc) - timedelta(hours=5))

    reply, ai_used, metadata = _run_turn(service, user_id=uid, message="precio")
    assert ai_used is True
    assert str(metadata.get("source") or "") != "initial_message"
    assert reply

    _reply_second, ai_used_second, metadata_second = _run_turn(service, user_id=uid, message="precio")
    assert ai_used_second is True
    assert str(metadata_second.get("source") or "") != "initial_message"
