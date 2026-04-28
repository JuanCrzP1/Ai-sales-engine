## ========================================
## ARCHIVO: test_multi_model_behavior.py
##
## QUÉ VALIDA:
## Comportamiento por modelo de negocio sin hardcode cross-tenant.
##
## POR QUÉ ES CRÍTICO:
## Responder con modelo incorrecto rompe conversión y coherencia multi-tenant.
##
## QUÉ PROTEGE:
## Adaptación dinámica por tenant (productos vs servicios/planes).
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


def _tenant(slug: str) -> SimpleNamespace:
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def ask(message: str, *, tenant: str) -> str:
    service = AIService()
    runtime_yaml = load_tenant_runtime_yaml(tenant, channel="whatsapp")

    response, _ai_used, _metadata = service.generate_business_reply(
        tenant=_tenant(tenant),
        bot_config=None,
        user_message=message,
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        user_id=f"multi-model-{uuid4().hex[:8]}",
        include_metadata=True,
    )

    return str(response or "").lower()


def test_restaurant_behaves_as_product_catalog_not_plan_sales() -> None:
    reply = ask("que venden", tenant="restaurant")

    assert len(reply.split()) > 5
    assert "plan basico" not in reply


def test_saas_behaves_as_service_or_plan_model() -> None:
    reply = ask("que venden", tenant="asesor_ai_prod")

    assert len(reply.split()) > 5
    assert "hamburguesa" not in reply
