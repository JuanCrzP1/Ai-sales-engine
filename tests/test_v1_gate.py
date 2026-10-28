## ========================================
## ARCHIVO: test_v1_gate.py
##
## QUÉ VALIDA:
##   - El flujo conversacional NO depende de suscripciones, planes ni límites de uso
##     internos: eso es responsabilidad de la plataforma externa.
##   - La atención comercial funciona: precios, pagos y sustituciones de pago de cada
##     negocio siguen llegando al prompt y a la respuesta.
##   - Aislamiento entre negocios: cada tenant recibe solo su propia configuración.
##   - Resiliencia: un fallo de IA devuelve un fallback controlado.
## ========================================

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.application.ai_pipeline import AIPipeline
from app.application.runtime import load_tenant_runtime_yaml
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.persistence.memory_repository import MemoryRepository


def _tenant(slug: str = "asesor_ai_prod") -> SimpleNamespace:
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def _build_pipeline() -> AIPipeline:
    """AIPipeline con memoria en RAM (sin DB). No recibe repositorios de suscripción ni de uso."""
    return AIPipeline(memory_service=MemoryDomainService(MemoryRepository()))


def _stub_ai(pipeline, *, response="respuesta de ia", ai_used=True, metadata=None, raises=False):
    meta = dict(metadata or {"intent": "info"})

    def _gen(*args, **kwargs):
        if raises:
            raise RuntimeError("mock ai/provider failure")
        return response, ai_used, dict(meta)

    pipeline.runtime.ai_orchestrator.generate_business_reply = _gen


def _capture_prompts(pipeline, replies: list[dict]) -> list[str]:
    """Sustituye la llamada al LLM: devuelve salidas estructuradas guionizadas y guarda cada prompt."""
    prompts: list[str] = []
    queue = [json.dumps(reply, ensure_ascii=False) for reply in replies]

    def _generate(prompt, *, user_message, bot_config=None):
        prompts.append(str(prompt))
        return queue.pop(0)

    pipeline.runtime.generate = _generate
    return prompts


def _run(pipeline, *, tenant_slug="asesor_ai_prod", message="necesito informacion de precios", user_id=None):
    runtime_yaml = load_tenant_runtime_yaml(tenant_slug)
    return pipeline.run(
        tenant=_tenant(tenant_slug),
        user_message=message,
        user_id=user_id or f"v1gate-{uuid4().hex[:8]}",
        bot_config=None,
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        include_metadata=True,
    )


# ===========================================================================
# Sin suscripciones ni límites internos
# ===========================================================================

def test_pipeline_has_no_subscription_or_usage_dependencies():
    params = inspect.signature(AIPipeline.__init__).parameters
    assert "subscription_repo" not in params
    assert "usage_repo" not in params
    pipeline = _build_pipeline()
    assert not hasattr(pipeline, "saas_guard")
    assert not hasattr(pipeline, "usage_repo")


def test_conversation_is_served_without_any_subscription_data():
    pipeline = _build_pipeline()
    _stub_ai(pipeline, response="todo bien", ai_used=True)
    response, ai_used, metadata = _run(pipeline)
    assert ai_used is True
    assert response == "todo bien"
    assert str(metadata.get("source") or "") == "ai_raw"


def test_no_subscription_or_plan_limit_code_remains_in_engine():
    app_dir = PROJECT_DIR / "app"
    forbidden = ("SaaSGuard", "saas_guard", "SubscriptionRepository", "UsageRepository", "PLAN_LIMITS", "usage_daily", "FROM subscriptions", "blocked_response(")
    offenders = sorted(
        f"{path.relative_to(app_dir)}:{token}"
        for path in app_dir.rglob("*.py")
        for token in forbidden
        if token in path.read_text(encoding="utf-8")
    )
    assert not offenders


# ===========================================================================
# Venta conversacional: precios y pagos de los negocios
# ===========================================================================

def test_business_prices_and_conditions_reach_the_prompt():
    pipeline = _build_pipeline()
    prompts = _capture_prompts(pipeline, [
        {"response": "Claro, te explico.", "intent": "info"},
        {"response": "Te cuento los precios.", "intent": "info"},
    ])
    user_id = f"v1gate-{uuid4().hex[:8]}"
    _run(pipeline, message="Hola, necesito información de lo que venden", user_id=user_id)
    _response, ai_used, _meta = _run(pipeline, message="¿Y qué precio tiene?", user_id=user_id)

    assert ai_used is True
    pricing_block = prompts[-1].split("PRICING:", 1)[1]
    assert "Plan Basico -> COP: implementation=100000, monthly=110000" in pricing_block
    assert "sin permanencia obligatoria" in pricing_block


def test_business_payment_method_is_delivered_by_the_engine():
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod")
    methods = runtime_yaml["pricing"]["plans"][0]["payment"]["transfer"]["methods"]
    nequi_number = next(str(m["number"]) for m in methods if m.get("type") == "nequi")

    pipeline = _build_pipeline()
    _stub_ai(pipeline, response="Listo.", ai_used=True, metadata={"intent": "buy", "payment_method": "nequi"})
    response, ai_used, _meta = _run(pipeline, message="Quiero pagar por Nequi")

    assert ai_used is True
    assert response.startswith("Avanzamos con el siguiente paso.")
    assert nequi_number in response


def test_business_payment_report_returns_configured_message():
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod")
    expected = " ".join(runtime_yaml["config"]["post_payment"]["on_user_report"]["message"].split())

    pipeline = _build_pipeline()
    _stub_ai(pipeline, response="Gracias.", ai_used=True, metadata={"intent": "buy", "payment_status": "reportado"})
    response, _ai_used, _meta = _run(pipeline, message="Ya pagué")

    assert " ".join(response.split()) == expected


# ===========================================================================
# Aislamiento entre negocios
# ===========================================================================

def test_each_tenant_prompt_contains_only_its_own_offer():
    pipeline = _build_pipeline()
    prompts = _capture_prompts(pipeline, [
        {"response": "Hola.", "intent": "info"},
        {"response": "Hola.", "intent": "info"},
    ])
    _run(pipeline, tenant_slug="asesor_ai_prod", message="¿Qué venden?", user_id="same-user")
    _run(pipeline, tenant_slug="restaurant", message="¿Qué venden?", user_id="same-user")

    saas_prompt, restaurant_prompt = prompts
    assert "Plan Basico" in saas_prompt and "Hamburguesas" not in saas_prompt
    assert "Hamburguesas" in restaurant_prompt and "Plan Basico" not in restaurant_prompt


# ===========================================================================
# Resiliencia
# ===========================================================================

def test_ai_failure_returns_controlled_fallback():
    pipeline = _build_pipeline()
    _stub_ai(pipeline, raises=True)
    response, ai_used, _meta = _run(pipeline)
    assert ai_used is False
    assert response.strip() != ""


def test_pipeline_stage_exception_is_not_swallowed():
    pipeline = _build_pipeline()

    def _boom(*args, **kwargs):
        raise RuntimeError("pipeline stage failure")

    pipeline.ai_execution.run = _boom
    with pytest.raises(RuntimeError):
        _run(pipeline)
