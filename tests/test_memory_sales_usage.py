## ========================================
## ARCHIVO: test_memory_sales_usage.py
##
## QUÉ VALIDA:
## Que la memoria comercial se use entre turnos para mantener continuidad.
##
## POR QUÉ ES CRÍTICO:
## Sin continuidad, la conversación suena nueva en cada mensaje.
##
## QUÉ PROTEGE:
## Uso activo de contexto previo y avance comercial en conversaciones reales.
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


def _ask_with_stub(
    service: AIService,
    *,
    user_id: str,
    message: str,
    pain: str,
) -> tuple[str, bool, dict]:
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod", channel="whatsapp")
    orchestrator = service.pipeline.runtime.ai_orchestrator
    original_generate = orchestrator.generate_business_reply

    def _stub_generate(*args, **kwargs):
        del args, kwargs
        return "respuesta ia", True, {"intent": "info", "mode": "sales", "pain": pain}

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


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Ejecuta dos turnos con pain real y valida continuidad en el segundo.
##
## POR QUÉ ES IMPORTANTE:
## El segundo turno debe apoyarse en lo anterior y no reiniciar como conversación nueva.
##
## QUÉ PROTEGE:
## Conexión contexto previo -> avance comercial en uso de memoria.
## ----------------------------------------
def test_second_turn_uses_previous_sales_context() -> None:
    service = AIService()
    user_id = f"mem-sales-{uuid4().hex[:8]}"

    _ask_with_stub(
        service,
        user_id=user_id,
        message="tengo muchos mensajes",
        pain="tengo muchos mensajes",
    )

    _reply2, ai_used2, metadata2 = _ask_with_stub(
        service,
        user_id=user_id,
        message="no me da el tiempo",
        pain="no me da el tiempo",
    )

    ## continuidad: no debe comportarse como arranque
    assert ai_used2 is True
    assert str(metadata2.get("source") or "") != "initial_message"

    ## uso de contexto previo: la memoria comercial debe unir pains entre turnos
    sales_hint = service.pipeline.conversation_flow.memory.build_sales_memory_usage(
        tenant_slug="asesor_ai_prod",
        user_id=user_id,
    ).lower()

    assert sales_hint != ""
    assert "mensaj" in sales_hint
    assert "tiempo" in sales_hint

    ## avance comercial: el hint debe ser accionable y conectado
    assert "has mencionado varias cosas" in sales_hint or "eso que me dijiste" in sales_hint
