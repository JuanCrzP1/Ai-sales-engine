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


def _run_turn(*, message: str, tenant_slug: str) -> str:
    service = AIService()
    runtime_yaml = load_tenant_runtime_yaml(tenant_slug, channel="whatsapp")
    uid = f"catalog-behavior-{uuid4().hex[:8]}"

    service.generate_business_reply(
        tenant=_tenant(tenant_slug),
        bot_config=None,
        user_message="hola",
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        user_id=uid,
        include_metadata=True,
    )

    response, _ai_used, _metadata = service.generate_business_reply(
        tenant=_tenant(tenant_slug),
        bot_config=None,
        user_message=message,
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        user_id=uid,
        include_metadata=True,
    )
    return str(response or "")


def _has_forward_intent(text: str) -> bool:
    t = text.lower()
    return "?" in t or any(
        s in t for s in ("pedir", "elegir", "quieres", "te interesa", "cuál", "cual", "qué te", "que te", "avanz", "empez")
    )


# ── TEST 1: catálogo menciona productos ───────────────────────────────────────

def test_restaurant_mentions_catalog_products() -> None:
    response = _run_turn(message="qué vendes", tenant_slug="restaurant")
    catalog_terms = (
        "hamburguesa", "hamburguesas", "bebida", "bebidas",
        "menu", "menú", "producto", "gaseosa", "jugo",
    )
    assert any(term in response.lower() for term in catalog_terms), (
        f"restaurant debería mencionar productos del catálogo. Respuesta: {response!r}"
    )


# ── TEST 2: catálogo no suena SaaS ────────────────────────────────────────────

def test_restaurant_does_not_sound_like_saas() -> None:
    response = _run_turn(message="qué vendes", tenant_slug="restaurant")
    normalized = response.lower()
    for forbidden in ("nuestro sistema", "este sistema", "automatiz", "software"):
        assert forbidden not in normalized, (
            f"No debe sonar como SaaS (término '{forbidden}' detectado). Respuesta: {response!r}"
        )


# ── TEST 3: empuje comercial ──────────────────────────────────────────────────

def test_restaurant_pushes_conversation_forward() -> None:
    response = _run_turn(message="qué vendes", tenant_slug="restaurant")
    assert _has_forward_intent(response), (
        f"restaurant debería empujar la conversación hacia un siguiente paso. Respuesta: {response!r}"
    )


# ── TEST 4: SaaS no se contamina con catálogo ────────────────────────────────

def test_saas_does_not_mention_catalog_products() -> None:
    response = _run_turn(message="qué vendes", tenant_slug="asesor_ai_prod")
    catalog_terms = ("hamburguesa", "bebida", "camiseta", "jean")
    assert not any(term in response.lower() for term in catalog_terms), (
        f"SaaS no debería mencionar productos de catálogo. Respuesta: {response!r}"
    )


# ── TEST 5: tienda_ropa no se rompe ───────────────────────────────────────────

def test_tienda_ropa_still_mentions_products() -> None:
    response = _run_turn(message="qué vendes", tenant_slug="tienda_ropa")
    catalog_terms = ("camiseta", "camisetas", "jean", "jeans", "ropa", "producto", "tienda")
    assert any(term in response.lower() for term in catalog_terms), (
        f"tienda_ropa debería mencionar sus productos. Respuesta: {response!r}"
    )
