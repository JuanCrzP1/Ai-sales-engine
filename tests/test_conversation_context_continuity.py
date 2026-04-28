## ========================================
## ARCHIVO: test_conversation_context_continuity.py
##
## QUÉ VALIDA:
## Que el contexto de conversación viaje correctamente al turno siguiente.
##
## POR QUÉ ES CRÍTICO:
## Si se pierde, la IA responde fuera de contexto y baja la calidad comercial.
##
## QUÉ PROTEGE:
## Continuidad de memoria, historial y mensaje previo en runtime.
## ========================================

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.application.runtime import load_tenant_runtime_yaml
from app.services.ai_service import AIService


def _tenant(slug: str = "asesor_ai_prod") -> SimpleNamespace:
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def _run_with_stub(
    service: AIService,
    *,
    user_id: str,
    user_message: str,
    metadata: dict,
    ai_text: str = "respuesta ia",
) -> tuple[str, bool, dict]:
    orchestrator = service.pipeline.runtime.ai_orchestrator
    original_generate = orchestrator.generate_business_reply

    def _stub_generate(*args, **kwargs):
        del args, kwargs
        return ai_text, True, dict(metadata)

    orchestrator.generate_business_reply = _stub_generate
    try:
        runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod")
        response, ai_used, route_meta = service.generate_business_reply(
            tenant=_tenant(),
            bot_config=None,
            user_message=user_message,
            conversation_history=[],
            faq_results=[],
            yaml_config=runtime_yaml,
            user_id=user_id,
            include_metadata=True,
        )
        return str(response or ""), bool(ai_used), dict(route_meta or {})
    finally:
        orchestrator.generate_business_reply = original_generate


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Valida que el segundo turno reciba memory_context construido en el turno anterior.
##
## POR QUÉ ES IMPORTANTE:
## Evita que la IA olvide dolor detectado y vuelva a abrir discovery desde cero.
##
## QUÉ PROTEGE:
## Continuidad conversacional y transferencia de memoria entre turnos.
## ----------------------------------------
def test_follow_up_turn_includes_memory_context_from_previous_turn() -> None:
    service = AIService()
    user_id = f"context-memory-{uuid4().hex[:8]}"

    _run_with_stub(
        service,
        user_id=user_id,
        user_message="primer turno con contexto",
        metadata={
            "intent": "pain",
            "stage": "discovery",
            "pain_detected": True,
            "pain": "bloqueo previo",
            "next_step": "continuar",
            "mode": "sales",
        },
    )

    captured: dict = {}
    orchestrator = service.pipeline.runtime.ai_orchestrator
    original_generate = orchestrator.generate_business_reply

    def _capture_generate(*args, **kwargs):
        del args
        cfg = kwargs.get("yaml_config") if isinstance(kwargs.get("yaml_config"), dict) else {}
        captured["memory_context"] = cfg.get("memory_context") if isinstance(cfg.get("memory_context"), dict) else {}
        return "respuesta seguimiento", True, {"intent": "info", "stage": "solution", "mode": "sales"}

    orchestrator.generate_business_reply = _capture_generate
    try:
        runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod")
        _response, ai_used, metadata = service.generate_business_reply(
            tenant=_tenant(),
            bot_config=None,
            user_message="segundo turno",
            conversation_history=[],
            faq_results=[],
            yaml_config=runtime_yaml,
            user_id=user_id,
            include_metadata=True,
        )
    finally:
        orchestrator.generate_business_reply = original_generate

    memory_context = captured.get("memory_context") if isinstance(captured.get("memory_context"), dict) else {}
    assert ai_used is True
    assert str(metadata.get("source") or "") == "ai_raw"
    assert str(memory_context.get("last_intent") or "") == "pain"
    assert str(memory_context.get("last_pain") or "") == "bloqueo previo"
    assert str(memory_context.get("history_summary") or "") != ""


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Comprueba que previous_user_message e historial viajen al turno siguiente.
##
## POR QUÉ ES IMPORTANTE:
## Sin estos campos, la IA pierde referencia temporal y responde fuera de contexto.
##
## QUÉ PROTEGE:
## Transporte de contexto de mensajes e historial en runtime_yaml.
## ----------------------------------------
def test_follow_up_turn_includes_previous_message_and_history() -> None:
    service = AIService()
    user_id = f"context-history-{uuid4().hex[:8]}"

    _run_with_stub(
        service,
        user_id=user_id,
        user_message="mensaje inicial",
        metadata={
            "intent": "info",
            "stage": "discovery",
            "next_step": "continuar",
            "mode": "sales",
        },
    )

    captured: dict = {}
    orchestrator = service.pipeline.runtime.ai_orchestrator
    original_generate = orchestrator.generate_business_reply

    def _capture_generate(*args, **kwargs):
        del args
        cfg = kwargs.get("yaml_config") if isinstance(kwargs.get("yaml_config"), dict) else {}
        captured["previous_user_message"] = str(cfg.get("previous_user_message") or "")
        history = cfg.get("conversation_history") if isinstance(cfg.get("conversation_history"), list) else []
        captured["conversation_history"] = history
        return "respuesta seguimiento", True, {"intent": "info", "stage": "solution", "mode": "sales"}

    orchestrator.generate_business_reply = _capture_generate
    try:
        runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod")
        _response, _ai_used, _metadata = service.generate_business_reply(
            tenant=_tenant(),
            bot_config=None,
            user_message="mensaje siguiente",
            conversation_history=[],
            faq_results=[],
            yaml_config=runtime_yaml,
            user_id=user_id,
            include_metadata=True,
        )
    finally:
        orchestrator.generate_business_reply = original_generate

    history = captured.get("conversation_history") if isinstance(captured.get("conversation_history"), list) else []
    assert captured.get("previous_user_message") == "mensaje inicial"
    assert len(history) >= 1