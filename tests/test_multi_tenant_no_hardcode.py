## ========================================
## ARCHIVO: test_multi_tenant_no_hardcode.py
##
## QUÉ VALIDA:
## Que la respuesta no hardcodee planes de otro tenant.
##
## POR QUÉ ES CRÍTICO:
## Hardcodear planes rompe aislamiento multi-tenant y escalabilidad.
##
## QUÉ PROTEGE:
## Consistencia dinámica por tenant y veracidad comercial.
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
from app.infrastructure.config.config_service import ConfigService
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
        user_id=f"no-hardcode-{uuid4().hex[:8]}",
        include_metadata=True,
    )

    return str(response or "")


def test_multi_tenant_no_hardcoded_plan_basico_for_non_plan_tenant() -> None:
    tenant = "restaurant"
    cfg = ConfigService()
    pricing = cfg.load_pricing(client_id=tenant)
    plans = pricing.get("plans") if isinstance(pricing.get("plans"), list) else []

    ## Precondición: este tenant no declara "plan basico" en pricing.plans
    plan_names = [str((p or {}).get("name") or "").strip().lower() for p in plans if isinstance(p, dict)]
    assert "plan basico" not in plan_names

    reply = ask("que planes tienes", tenant=tenant)

    ## No debe inventar el plan de otro tenant
    assert "plan basico" not in reply.lower()
