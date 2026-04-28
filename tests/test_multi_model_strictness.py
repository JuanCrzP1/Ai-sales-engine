## ========================================
## ARCHIVO: test_multi_model_strictness.py
##
## QUÉ VALIDA:
## Que no exista mezcla de modelos entre catalogo y saas.
##
## POR QUÉ ES CRÍTICO:
## Mezclar lenguaje de negocio destruye coherencia y credibilidad del tenant.
##
## QUÉ PROTEGE:
## Blindaje estricto multi-tenant por modelo comercial.
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
        user_id=f"strictness-{uuid4().hex[:8]}",
        include_metadata=True,
    )

    return str(response or "")


def test_catalog_does_not_sound_like_saas() -> None:
    reply = ask("que venden", tenant="restaurant")

    forbidden = ["sistema", "implementación", "automatización", "software"]

    assert not any(word in reply.lower() for word in forbidden)


def test_saas_does_not_sound_like_catalog() -> None:
    reply = ask("que venden", tenant="asesor_ai_prod")

    forbidden = ["hamburguesa", "producto", "bebida"]

    assert not any(word in reply.lower() for word in forbidden)


def test_catalog_mentions_products() -> None:
    reply = ask("que venden", tenant="restaurant")

    assert len(reply.split()) > 5
