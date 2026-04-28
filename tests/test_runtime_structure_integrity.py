## ========================================
## ARCHIVO: test_runtime_structure_integrity.py
##
## QUÉ VALIDA:
## Integridad del runtime y aislamiento de datos en escenarios críticos de ejecución.
##
## POR QUÉ ES CRÍTICO:
## Si falla, se puede romper el flujo comercial o mezclar datos entre tenants.
##
## QUÉ PROTEGE:
## Runtime validation, fuente de YAML y aislamiento multi-tenant.
## ========================================

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.application.pipeline.ai_execution import validate_runtime_yaml as validate_execution_runtime
from app.application.runtime import load_tenant_runtime_yaml
from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService
from app.infrastructure.ai.prompting.builder.prompt_builder import validate_runtime_yaml as validate_prompt_runtime
from app.infrastructure.config.config_service import ConfigService
from app.services.ai_service import AIService


def _tenant(slug: str) -> SimpleNamespace:
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def ask(message_text: str, *, tenant: str, channel: str) -> tuple[str, bool, dict]:
    service = AIService()
    runtime_yaml = load_tenant_runtime_yaml(tenant, channel=channel)
    response, ai_used, metadata = service.generate_business_reply(
        tenant=_tenant(tenant),
        bot_config=None,
        user_message=message_text,
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        user_id=f"phase3-{channel}-{tenant}-{uuid4().hex[:8]}",
        include_metadata=True,
    )
    return str(response or ""), bool(ai_used), dict(metadata or {})


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que las validaciones de prompt y ejecución rechacen runtime incompleto.
##
## POR QUÉ ES IMPORTANTE:
## Previene que se procese una conversación comercial con datos parciales o corruptos.
##
## QUÉ PROTEGE:
## Guardrails de integridad del runtime antes de pasar al motor IA.
## ----------------------------------------
def test_runtime_validation_rejects_incomplete_runtime_payloads() -> None:
    with pytest.raises(RuntimeError):
        validate_prompt_runtime({"sales": {"ok": True}, "business": {"ok": True}, "pricing": {"ok": True}})

    with pytest.raises(RuntimeError):
        validate_execution_runtime({"sales": {"ok": True}, "business": {"ok": True}, "pricing": {"ok": True}, "inventory": {"ok": True}})


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Confirma que la respuesta trae metadata de sales y business ya poblada.
##
## POR QUÉ ES IMPORTANTE:
## Sin estos bloques, la IA pierde contexto de operación y propuesta comercial.
##
## QUÉ PROTEGE:
## Enriquecimiento de metadata contractual en rutas AI-first.
## ----------------------------------------
def test_runtime_builder_populates_sales_and_business_metadata() -> None:
    _reply, _ai_used, metadata = ask("quiero informacion de planes", tenant="asesor_ai_prod", channel="whatsapp")
    assert isinstance(metadata.get("sales"), dict)
    assert isinstance(metadata.get("business"), dict)


def test_runtime_loader_promotes_capabilities_to_root_runtime() -> None:
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod", channel="web")

    capabilities = runtime_yaml.get("capabilities") if isinstance(runtime_yaml.get("capabilities"), dict) else {}
    channels = capabilities.get("channels") if isinstance(capabilities.get("channels"), list) else []
    actions = capabilities.get("actions") if isinstance(capabilities.get("actions"), dict) else {}

    assert isinstance(capabilities, dict)
    assert isinstance(channels, list)
    assert len(channels) > 0
    assert isinstance(actions.get("primary"), list)
    assert len(actions.get("primary") or []) > 0


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que una interacción comercial devuelva intent no vacío.
##
## POR QUÉ ES IMPORTANTE:
## Sin intent, se rompe trazabilidad y coordinación entre etapas de conversación.
##
## QUÉ PROTEGE:
## Contrato de metadata de intención en flujo comercial.
## ----------------------------------------
def test_commercial_turn_returns_non_empty_intent_metadata() -> None:
    _reply, _ai_used, metadata = ask("hola", tenant="asesor_ai_prod", channel="whatsapp")
    assert str(metadata.get("intent") or "").strip()


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Garantiza que PromptBuilder use el yaml ya inyectado y no recargue por ConfigService.
##
## POR QUÉ ES IMPORTANTE:
## Evita sobrescrituras silenciosas que mezclen datos de tenant o canal equivocado.
##
## QUÉ PROTEGE:
## Fuente única de verdad del runtime dentro del armado de prompt.
## ----------------------------------------
def test_prompt_builder_runtime_yaml_is_not_reloaded_from_config_service(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime_yaml = load_tenant_runtime_yaml(
        "asesor_ai_prod",
        extra_yaml={
            "sales": {"closing": {"strategy": "direct_sale", "required_data": []}},
            "pricing": {
                "payment": {
                    "link": "",
                    "transfer": {
                        "enabled": True,
                        "methods": [
                            {
                                "type": "bank",
                                "bank": "Bancolombia",
                                "account_type": "ahorros",
                                "account_number": "1234567890",
                            }
                        ],
                    },
                },
                "business_offers": {"financing": {"available": False, "providers": [], "options": []}},
            },
            "inventory": {"track_stock": False, "items": []},
            "features": {"pricing_enabled": True, "business_model": "saas"},
        },
    )

    def _raise_load(*_args, **_kwargs):
        raise AssertionError("PromptBuilder no debe cargar YAML desde ConfigService")

    monkeypatch.setattr(ConfigService, "load_sales", _raise_load)
    monkeypatch.setattr(ConfigService, "load_business", _raise_load)
    monkeypatch.setattr(ConfigService, "load_pricing", _raise_load)
    monkeypatch.setattr(ConfigService, "load_inventory", _raise_load)

    builder = PromptBuilderService()

    prompt, _metadata, _context = builder.build(
        client_config_id="asesor_ai_prod",
        user_message="hola",
        yaml_config=runtime_yaml,
        faq_results=[],
        sales_decision={"intent": "info"},
        progression_rules=None,
    )

    assert str(prompt or "").strip()


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Comprueba que dos tenants puedan consultar compra sin cruzar datos entre sí.
##
## POR QUÉ ES IMPORTANTE:
## Una fuga entre tenants compromete seguridad y credibilidad de la plataforma.
##
## QUÉ PROTEGE:
## Aislamiento multi-tenant en respuesta, metadata de negocio e inventario.
## ----------------------------------------
def test_multi_tenant_buy_flow_preserves_tenant_isolation() -> None:
    restaurant_reply, _a1, m1 = ask("quiero comprar", tenant="restaurant", channel="whatsapp")
    retail_reply, _a2, m2 = ask("quiero comprar", tenant="tienda_ropa", channel="whatsapp")

    assert len(restaurant_reply.strip()) > 0
    assert len(retail_reply.strip()) > 0
    assert str(m1.get("tenant_slug") or "") == "restaurant"
    assert str(m2.get("tenant_slug") or "") == "tienda_ropa"

    b1 = m1.get("business") if isinstance(m1.get("business"), dict) else {}
    b2 = m2.get("business") if isinstance(m2.get("business"), dict) else {}
    i1 = m1.get("inventory") if isinstance(m1.get("inventory"), dict) else {}
    i2 = m2.get("inventory") if isinstance(m2.get("inventory"), dict) else {}

    assert b1 != b2
    assert bool(i1.get("track_stock", False)) is False
    assert bool(i2.get("track_stock", False)) is True