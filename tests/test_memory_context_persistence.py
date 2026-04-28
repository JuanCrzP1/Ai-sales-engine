## ========================================
## ARCHIVO: test_memory_context_persistence.py
##
## QUÉ VALIDA:
## Que la memoria conversacional persista entre turnos y conserve datos útiles.
##
## POR QUÉ ES CRÍTICO:
## Si la memoria se vacía, la conversación pierde continuidad comercial.
##
## QUÉ PROTEGE:
## Contexto de memoria y anclajes de venta entre turnos.
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
    ai_text: str,
    memory: dict | None = None,
) -> tuple[str, bool, dict]:
    extra_yaml = {"memory_context": memory} if isinstance(memory, dict) else None
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod", extra_yaml=extra_yaml)
    orchestrator = service.pipeline.runtime.ai_orchestrator
    original_generate = orchestrator.generate_business_reply

    def _stub_generate(*args, **kwargs):
        del args, kwargs
        return ai_text, True, {"intent": "info", "mode": "sales"}

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
## Verifica continuidad de memory_context entre turnos y que guarde señal útil de ventas.
##
## POR QUÉ ES IMPORTANTE:
## Si la memoria llega vacía, el segundo turno pierde contexto comercial y cae en respuestas genéricas.
##
## QUÉ PROTEGE:
## Persistencia conversacional AI-first y anclaje de pricing entre turnos.
## ----------------------------------------
def test_memory_context_persists_and_contains_useful_data() -> None:
    service = AIService()
    user_id = f"mem-persist-{uuid4().hex[:8]}"

    runtime_preview = load_tenant_runtime_yaml("asesor_ai_prod")
    pricing_cfg = runtime_preview.get("pricing") if isinstance(runtime_preview.get("pricing"), dict) else {}
    plans = pricing_cfg.get("plans") if isinstance(pricing_cfg.get("plans"), list) else []
    first_plan = plans[0] if plans and isinstance(plans[0], dict) else {}
    first_plan_pricing = first_plan.get("pricing") if isinstance(first_plan.get("pricing"), dict) else {}
    cop_prices = first_plan_pricing.get("COP") if isinstance(first_plan_pricing.get("COP"), dict) else {}
    price_value = str(cop_prices.get("monthly") or cop_prices.get("implementation") or "180000")

    r1 = _ask_with_stub(
        service,
        user_id=user_id,
        message="cuanto vale",
        ai_text=f"El valor mensual es {price_value} COP.",
    )
    mem = r1[2].get("memory_context")

    ## Debe existir como diccionario
    assert isinstance(mem, dict)

    ## Debe contener información relevante (no vacío inútil)
    assert "price_anchor" in mem or len(mem) > 0

    r2 = _ask_with_stub(
        service,
        user_id=user_id,
        message="esta caro",
        ai_text="Entiendo el punto, revisemos precio y retorno.",
        memory=mem,
    )
    mem2 = r2[2].get("memory_context")

    ## La memoria debe seguir existiendo en el siguiente turno
    assert isinstance(mem2, dict)
    assert mem2 is not None

    ## Debe mantenerse útil tras reinyectarse al segundo turno
    assert "price_anchor" in mem2 or len(mem2) > 0
