## ========================================
## ARCHIVO: test_v1_gate.py
##
## QUÉ VALIDA (cirugía V1 GATE):
##   FASE 1 — Bug de límite SaaS: el cliente recibe el mensaje comercial de
##            límite de plan y NO un fallback genérico.
##   FASE 2 — Medición de uso: increment() ocurre SOLO tras una respuesta válida
##            de IA; nunca ante fallo de IA o excepción de pipeline; una sola vez.
##   FASE 3 — Resiliencia PostgreSQL: una excepción de repositorio NO tumba el
##            pipeline; devuelve respuesta controlada y la registra en log.
##
## POR QUÉ ES CRÍTICO:
##   Protege monetización (mensaje de upsell + conteo justo) y operación continua
##   (no caída total ante DB intermitente).
## ========================================

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.application.ai_pipeline import AIPipeline
from app.application.pipeline.common import blocked_response, service_unavailable_response
from app.application.pipeline.saas_guard import PLAN_LIMITS
from app.application.runtime import load_tenant_runtime_yaml
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.persistence.memory_repository import MemoryRepository


_LIMIT_MESSAGE = "Ya llegaste al límite del plan. Si quieres seguimos de una y no paras las ventas."
_INACTIVE_MESSAGE = "En este momento no tienes el servicio activo, si quieres lo activamos y lo dejas trabajando ya contigo."
_GENERIC_MESSAGE = "No puedo procesar tu solicitud en este momento."


def _tenant(slug: str = "asesor_ai_prod") -> SimpleNamespace:
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def _build_pipeline(*, is_active=True, can_send=True, plan_code="starter"):
    """Construye un AIPipeline con repos SaaS falsos e inyectados.

    Al inyectar instancias propias, los parches de conftest sobre las clases
    de repositorio no afectan estas instancias: controlamos el comportamiento.
    Memoria en RAM (sin DB) para aislar la prueba.
    """
    sub_repo = MagicMock()
    sub_repo.is_active.return_value = is_active
    sub_repo.get_plan_code.return_value = plan_code

    usage_repo = MagicMock()
    usage_repo.can_send.return_value = can_send

    memory = MemoryDomainService(MemoryRepository())

    pipeline = AIPipeline(
        memory_service=memory,
        subscription_repo=sub_repo,
        usage_repo=usage_repo,
    )
    return pipeline, sub_repo, usage_repo


def _stub_ai(pipeline, *, response="respuesta de ia", ai_used=True, metadata=None, raises=False):
    meta = dict(metadata or {"intent": "info"})

    def _gen(*args, **kwargs):
        if raises:
            raise RuntimeError("mock ai/provider failure")
        return response, ai_used, dict(meta)

    pipeline.runtime.ai_orchestrator.generate_business_reply = _gen


def _run(pipeline, *, message="necesito informacion de precios", user_id=None):
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod")
    return pipeline.run(
        tenant=_tenant(),
        user_message=message,
        user_id=user_id or f"v1gate-{uuid4().hex[:8]}",
        bot_config=None,
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        include_metadata=True,
    )


# ===========================================================================
# FASE 1 — Bug de límite SaaS
# ===========================================================================

def test_plan_limit_returns_correct_upgrade_message():
    """blocked_response debe traducir el dict de límite al mensaje comercial."""
    reason = {"source": "saas_guard_limit_reached", "plan_code": "starter", "limit": PLAN_LIMITS["starter"]}
    assert blocked_response(reason) == _LIMIT_MESSAGE


def test_limit_message_not_replaced_by_generic_fallback():
    """El mensaje de límite NUNCA debe degradarse al genérico."""
    reason = {"source": "saas_guard_limit_reached", "plan_code": "pro", "limit": 10000}
    assert blocked_response(reason) != _GENERIC_MESSAGE
    # Flujo integrado: tenant activo pero cuota agotada → mensaje de límite.
    pipeline, _sub, _usage = _build_pipeline(is_active=True, can_send=False)
    _stub_ai(pipeline)  # no debería llegar a ejecutarse
    response, ai_used, metadata = _run(pipeline)
    assert response == _LIMIT_MESSAGE
    assert ai_used is False
    assert str(metadata.get("source") or "") == "saas_guard_blocked"


def test_limit_flow_keeps_current_behavior():
    """Compatibilidad: strings legacy y casos previos siguen igual."""
    assert blocked_response("subscription_inactive") == _INACTIVE_MESSAGE
    assert blocked_response("usage_limit") == _LIMIT_MESSAGE
    assert blocked_response(None) == _GENERIC_MESSAGE
    assert blocked_response("algo_raro") == _GENERIC_MESSAGE
    # Suscripción inactiva sigue bloqueando con su mensaje propio.
    pipeline, _sub, _usage = _build_pipeline(is_active=False)
    response, ai_used, _meta = _run(pipeline)
    assert response == _INACTIVE_MESSAGE
    assert ai_used is False


# ===========================================================================
# FASE 2 — Medición de uso
# ===========================================================================

def test_usage_increment_after_successful_response():
    pipeline, _sub, usage_repo = _build_pipeline()
    _stub_ai(pipeline, response="todo bien", ai_used=True)
    response, ai_used, _meta = _run(pipeline)
    assert ai_used is True
    assert response.strip() != ""
    usage_repo.increment.assert_called_once_with("asesor_ai_prod")


def test_usage_not_incremented_when_ai_fails():
    pipeline, _sub, usage_repo = _build_pipeline()
    _stub_ai(pipeline, raises=True)  # IA/proveedor cae → fallback (ai_used=False)
    response, ai_used, _meta = _run(pipeline)
    assert ai_used is False
    assert response.strip() != ""  # responde con fallback controlado
    usage_repo.increment.assert_not_called()


def test_usage_not_incremented_on_pipeline_exception():
    pipeline, _sub, usage_repo = _build_pipeline()

    def _boom(*args, **kwargs):
        raise RuntimeError("pipeline stage failure")

    pipeline.ai_execution.run = _boom
    with pytest.raises(RuntimeError):
        _run(pipeline)
    usage_repo.increment.assert_not_called()


def test_usage_increment_once_per_successful_request():
    pipeline, _sub, usage_repo = _build_pipeline()
    _stub_ai(pipeline, ai_used=True)
    _run(pipeline)
    assert usage_repo.increment.call_count == 1


# ===========================================================================
# FASE 3 — Resiliencia PostgreSQL
# ===========================================================================

def test_db_failure_does_not_crash_pipeline():
    pipeline, sub_repo, _usage = _build_pipeline()
    sub_repo.is_active.side_effect = RuntimeError("postgres connection refused")
    # No debe lanzar excepción
    response, ai_used, _meta = _run(pipeline)
    assert ai_used is False
    assert response.strip() != ""


def test_db_failure_returns_controlled_response():
    pipeline, sub_repo, _usage = _build_pipeline()
    sub_repo.is_active.side_effect = RuntimeError("postgres down")
    response, ai_used, metadata = _run(pipeline)
    assert response == service_unavailable_response()
    assert ai_used is False
    assert str(metadata.get("source") or "") == "saas_guard_unavailable"


def test_db_failure_is_logged():
    pipeline, sub_repo, _usage = _build_pipeline()
    sub_repo.is_active.side_effect = RuntimeError("postgres unreachable")
    with patch("app.application.ai_pipeline.logger") as mock_logger:
        _run(pipeline)
    mock_logger.error.assert_called_once()
    assert mock_logger.error.call_args[0][0] == "saas_guard_unavailable"


def test_pipeline_survives_repository_exception():
    """Si el incremento de uso falla (DB caída tras responder), la respuesta de
    IA ya generada se entrega igual; el pipeline no se rompe."""
    pipeline, _sub, usage_repo = _build_pipeline()
    usage_repo.increment.side_effect = RuntimeError("usage write failed")
    _stub_ai(pipeline, response="respuesta valida", ai_used=True)
    response, ai_used, _meta = _run(pipeline)
    assert ai_used is True
    assert response == "respuesta valida"
