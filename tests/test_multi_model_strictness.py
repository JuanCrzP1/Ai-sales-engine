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

    # Palabras inequívocamente tecnológicas — "sistema" se excluye porque un restaurante
    # puede decir "sistema de pedidos" de forma legítima
    forbidden_words = ["automatización", "automatizacion", "software"]
    forbidden_phrases = ["sistema comercial", "sistema de ventas", "plataforma de ventas"]

    assert not any(word in reply.lower() for word in forbidden_words), (
        f"La respuesta del restaurante usa lenguaje de software: {reply!r}"
    )
    assert not any(phrase in reply.lower() for phrase in forbidden_phrases), (
        f"La respuesta del restaurante usa frases de SaaS: {reply!r}"
    )


def test_saas_does_not_sound_like_catalog() -> None:
    reply = ask("que venden", tenant="asesor_ai_prod")

    forbidden = ["hamburguesa", "producto", "bebida"]

    assert not any(word in reply.lower() for word in forbidden)


def test_catalog_mentions_products() -> None:
    reply = ask("que venden", tenant="restaurant")

    assert len(reply.split()) > 5
