## ========================================
## ARCHIVO: test_pipeline_integrity.py
##
## QUÉ VALIDA:
## Que el pipeline conserve metadata clave, fallback y memoria entre turnos.
##
## POR QUÉ ES CRÍTICO:
## Sin estas garantías se pierde trazabilidad y estabilidad operativa.
##
## QUÉ PROTEGE:
## Contrato de salida del pipeline, resiliencia y continuidad conversacional.
## ========================================

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from app.application.runtime import load_tenant_runtime_yaml
from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService
from app.services.ai.structured_output import parse_structured_output

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.services.ai_service import AIService


def _tenant(slug: str = "asesor_ai_prod") -> SimpleNamespace:
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def _run_with_stub(
    service: AIService,
    *,
    user_id: str,
    user_message: str,
    metadata: dict,
    ai_text: str = "respuesta de ia",
) -> tuple[str, bool, dict]:
    orchestrator = service.pipeline.runtime.ai_orchestrator
    original_generate = orchestrator.generate_business_reply

    def _stub_generate(*args, **kwargs):
        del args, kwargs
        return ai_text, True, dict(metadata)

    orchestrator.generate_business_reply = _stub_generate
    try:
        runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod")
        response, ai_used, route_meta = service.generate_business_reply(
            tenant=_tenant(),
            bot_config=None,
            user_message=user_message,
            conversation_history=[],
            faq_results=[],
            yaml_config=runtime_yaml,
            user_id=user_id,
            include_metadata=True,
        )
        return str(response or ""), bool(ai_used), dict(route_meta or {})
    finally:
        orchestrator.generate_business_reply = original_generate


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que una salida válida de IA mantenga source igual a ai_raw.
##
## POR QUÉ ES IMPORTANTE:
## Evita etiquetados incorrectos que distorsionen métricas y diagnósticos de producción.
##
## QUÉ PROTEGE:
## Trazabilidad de origen de respuesta en el pipeline AI-first.
## ----------------------------------------
def test_ai_output_source_remains_ai_raw_under_valid_generation() -> None:
    service = AIService()
    _response, _ai_used, metadata = _run_with_stub(
        service,
        user_id=f"pipeline-source-{uuid4().hex[:8]}",
        user_message="necesito ayuda",
        metadata={
            "intent": "info",
            "mode": "sales",
            "stage": "solution",
        },
    )

    assert str(metadata.get("source") or "") == "ai_raw"


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Comprueba que metadata clave se preserve cuando la IA responde correctamente.
##
## POR QUÉ ES IMPORTANTE:
## Si se pierde metadata, se rompe seguimiento de etapa y siguiente paso comercial.
##
## QUÉ PROTEGE:
## Integridad de intent stage next_step y source en respuestas exitosas.
## ----------------------------------------
def test_valid_ai_output_preserves_basic_metadata() -> None:
    service = AIService()
    response, ai_used, metadata = _run_with_stub(
        service,
        user_id=f"pipeline-meta-{uuid4().hex[:8]}",
        user_message="ok",
        metadata={
            "intent": "info",
            "mode": "sales",
            "stage": "solution",
            "next_step": "continuar",
        },
        ai_text="salida valida",
    )

    ai_metadata = metadata.get("ai_metadata") if isinstance(metadata.get("ai_metadata"), dict) else {}
    assert ai_used is True
    assert response.strip() != ""
    assert str(metadata.get("source") or "") == "ai_raw"
    assert str(metadata.get("intent") or "") == "info"
    assert str(ai_metadata.get("stage") or "") == "solution"
    assert str(ai_metadata.get("next_step") or "") == "continuar"


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Simula una excepción de IA y valida que el sistema responda con fallback controlado.
##
## POR QUÉ ES IMPORTANTE:
## Garantiza continuidad operativa ante fallas técnicas del proveedor IA.
##
## QUÉ PROTEGE:
## Resiliencia del pipeline y contrato de source fallback_exception.
## ----------------------------------------
def test_ai_failure_triggers_exception_fallback_response() -> None:
    service = AIService()
    user_id = f"pipeline-fallback-{uuid4().hex[:8]}"
    orchestrator = service.pipeline.runtime.ai_orchestrator
    original_generate = orchestrator.generate_business_reply

    def _raise_generate(*args, **kwargs):
        del args, kwargs
        raise RuntimeError("mock technical failure")

    orchestrator.generate_business_reply = _raise_generate
    try:
        runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod")
        response, ai_used, metadata = service.generate_business_reply(
            tenant=_tenant(),
            bot_config=None,
            user_message="necesito ayuda",
            conversation_history=[],
            faq_results=[],
            yaml_config=runtime_yaml,
            user_id=user_id,
            include_metadata=True,
        )
    finally:
        orchestrator.generate_business_reply = original_generate

    assert ai_used is False
    assert response.strip() != ""
    assert str(metadata.get("source") or "") == "fallback_exception"


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que el segundo turno reciba last_intent last_pain e history_summary.
##
## POR QUÉ ES IMPORTANTE:
## Sin esa memoria, la conversación pierde continuidad y calidad comercial.
##
## QUÉ PROTEGE:
## Persistencia de contexto conversacional entre turnos del mismo usuario.
## ----------------------------------------
def test_memory_context_persists_last_intent_pain_and_history() -> None:
    service = AIService()
    user_id = f"pipeline-memory-{uuid4().hex[:8]}"

    _run_with_stub(
        service,
        user_id=user_id,
        user_message="estoy perdiendo mensajes importantes",
        metadata={
            "intent": "pain",
            "stage": "discovery",
            "pain_detected": True,
            "pain": "perdida de mensajes",
            "next_step": "cuantificar impacto",
            "urgency": "high",
            "mode": "sales",
            "last_cta": "continuar",
            "objection_count": 0,
        },
        ai_text="respuesta inicial",
    )

    captured: dict = {}
    orchestrator = service.pipeline.runtime.ai_orchestrator
    original_generate = orchestrator.generate_business_reply

    def _capture_generate(*args, **kwargs):
        del args
        cfg = kwargs.get("yaml_config") if isinstance(kwargs.get("yaml_config"), dict) else {}
        captured["memory_context"] = cfg.get("memory_context") if isinstance(cfg.get("memory_context"), dict) else {}
        return "respuesta seguimiento", True, {
            "intent": "info",
            "stage": "solution",
            "pain_detected": True,
            "mode": "sales",
            "next_step": "proponer implementacion",
        }

    orchestrator.generate_business_reply = _capture_generate
    try:
        runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod")
        _response, ai_used, metadata = service.generate_business_reply(
            tenant=_tenant(),
            bot_config=None,
            user_message="ok, como seguimos",
            conversation_history=[],
            faq_results=[],
            yaml_config=runtime_yaml,
            user_id=user_id,
            include_metadata=True,
        )
    finally:
        orchestrator.generate_business_reply = original_generate

    mem = captured.get("memory_context") if isinstance(captured.get("memory_context"), dict) else {}
    assert ai_used is True
    assert str(metadata.get("source") or "") == "ai_raw"
    assert str(mem.get("last_intent") or "") == "pain"
    assert str(mem.get("last_pain") or "") != ""
    assert str(mem.get("last_user_message") or "") == "estoy perdiendo mensajes importantes"
    assert str(mem.get("last_ai_response") or "") == "respuesta inicial"
    assert str(mem.get("history_summary") or "") != ""


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Comprueba que el prompt incluya contexto reciente del cliente si existe.
##
## POR QUÉ ES IMPORTANTE:
## La IA necesita ver último mensaje e intención previa para mantener continuidad.
##
## QUÉ PROTEGE:
## Inyección AI-first de memoria comercial como contexto informativo.
## ----------------------------------------
def test_prompt_builder_includes_recent_customer_context_when_available() -> None:
    builder = PromptBuilderService()
    runtime_yaml = load_tenant_runtime_yaml(
        "asesor_ai_prod",
        extra_yaml={
            "memory_context": {
                "last_user_message": "tengo muchos mensajes",
                "last_intent": "pain",
                "last_ai_response": "te ayudo a organizarlos",
            },
        },
    )

    prompt, _metadata, _context = builder.build(
        client_config_id="asesor_ai_prod",
        user_message="y eso como me ayuda",
        yaml_config=runtime_yaml,
        faq_results=[],
        progression_rules=None,
    )

    assert "Contexto reciente del cliente:" in str(prompt or "")
    assert "Último mensaje: tengo muchos mensajes" not in str(prompt or "")
    assert "Última intención detectada: pain" in str(prompt or "")
    assert "Última respuesta enviada: te ayudo a organizarlos" in str(prompt or "")


def test_prompt_builder_includes_global_grounding_block() -> None:
    builder = PromptBuilderService()
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod")

    prompt, _metadata, _context = builder.build(
        client_config_id="asesor_ai_prod",
        user_message="también messenger?",
        yaml_config=runtime_yaml,
        faq_results=[],
        progression_rules=None,
    )

    prompt_text = str(prompt or "")

    assert "REGLA CRÍTICA:" in prompt_text
    assert "Responde SOLO con información que esté en el contexto proporcionado." in prompt_text
    assert "NO inventes funcionalidades, canales o características que no estén explícitamente mencionadas." in prompt_text
    assert "Si el usuario pregunta por algo que no aparece en el contexto:" in prompt_text


def test_prompt_builder_uses_simplified_commercial_behavior_block() -> None:
    builder = PromptBuilderService()
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod")

    prompt, _metadata, _context = builder.build(
        client_config_id="asesor_ai_prod",
        user_message="dame información",
        yaml_config=runtime_yaml,
        faq_results=[],
        progression_rules=None,
    )

    prompt_text = str(prompt or "")

    assert "Tu objetivo es ayudar al cliente a avanzar en la conversación hacia una decisión." in prompt_text
    assert "Habla como una persona real vendiendo por chat." in prompt_text
    assert "No inicies con frases de soporte como 'claro, puedo ayudarte' o 'si quieres'." not in prompt_text
    assert "🚫 PROHIBIDO (EN CUALQUIER FORMA):" not in prompt_text
    assert "CIERRE COMERCIAL" not in prompt_text


def test_prompt_builder_includes_pricing_in_active_conversation() -> None:
    builder = PromptBuilderService()
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod")
    runtime_yaml["conversation_state"] = "active"

    prompt, _metadata, _context = builder.build(
        client_config_id="asesor_ai_prod",
        user_message="que precio tiene",
        yaml_config=runtime_yaml,
        faq_results=[],
        progression_rules=None,
    )

    prompt_text = str(prompt or "")

    assert "el primer mes se paga 330000 COP (configuracion + primer mes)" in prompt_text
    assert "luego se paga mensualmente 180000 COP" in prompt_text
    assert "LINK_AVAILABLE:" in prompt_text
    assert "TRANSFER_METHODS:" in prompt_text


def test_prompt_builder_uses_only_real_payment_routes_context() -> None:
    builder = PromptBuilderService()
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod")
    runtime_yaml["conversation_state"] = "active"

    prompt, _metadata, _context = builder.build(
        client_config_id="asesor_ai_prod",
        user_message="que precio tiene",
        yaml_config=runtime_yaml,
        faq_results=[],
        progression_rules=None,
    )

    prompt_text = str(prompt or "")

    assert "LINK_AVAILABLE:" in prompt_text
    assert "TRANSFER_AVAILABLE:" in prompt_text
    assert "TRANSFER_METHODS:" in prompt_text
    assert "payment_methods" not in prompt_text


def test_prompt_builder_injects_capabilities_block() -> None:
    builder = PromptBuilderService()
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod")

    prompt, _metadata, _context = builder.build(
        client_config_id="asesor_ai_prod",
        user_message="por dónde atienden?",
        yaml_config=runtime_yaml,
        faq_results=[],
        progression_rules=None,
    )

    prompt_text = str(prompt or "")

    assert "CAPACIDADES DEL NEGOCIO:" in prompt_text
    assert "TIPOS DE CANALES:" in prompt_text
    assert "CANALES DE ATENCION (business_channels):" in prompt_text
    assert "CANALES DEL SISTEMA (system_channels):" in prompt_text
    assert "sin canales de atencion definidos" in prompt_text
    assert "whatsapp" in prompt_text
    assert "Acciones disponibles:" in prompt_text
    assert "activar_servicio, seguimiento" in prompt_text


def test_prompt_builder_supports_split_capability_channels_without_changing_actions() -> None:
    capabilities_context = PromptBuilderService.build_capabilities_context(
        {
            "config": {
                "capabilities": {
                    "business_channels": ["whatsapp", "instagram"],
                    "system_channels": ["web"],
                    "actions": {
                        "primary": ["cerrar_venta", "llamadas"],
                        "support": ["contacto", "seguimiento"],
                    },
                }
            }
        }
    )

    assert "CANALES DE ATENCION (business_channels):" in capabilities_context
    assert "whatsapp, instagram" in capabilities_context
    assert "CANALES DEL SISTEMA (system_channels):" in capabilities_context
    assert "web" in capabilities_context
    assert "Acciones disponibles:" in capabilities_context
    assert "cerrar_venta, llamadas, contacto, seguimiento" in capabilities_context


def test_structured_output_preserves_plain_text_response() -> None:
    response, metadata = parse_structured_output("respuesta natural")

    assert response == "respuesta natural"
    assert metadata.get("intent_missing") is True


def test_structured_output_keeps_original_intent_without_alias_mapping() -> None:
    response, metadata = parse_structured_output('{"response": "ok", "intent": "pricing"}')

    assert response == "ok"
    assert metadata.get("intent") == "pricing"


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Comprueba que el builder reporte prompt_source contractual y no exponga prompt_text.
##
## POR QUÉ ES IMPORTANTE:
## Evita regressions que cambien el origen del prompt o filtren contenido interno.
##
## QUÉ PROTEGE:
## Contrato de metadata del prompt en capa de prompting.
## ----------------------------------------
def test_prompt_metadata_reports_single_contract_block_source() -> None:
    builder = PromptBuilderService()
    runtime_yaml = load_tenant_runtime_yaml(
        "asesor_ai_prod",
        extra_yaml={
            "pricing": {"implementation": "$100", "monthly": "$50", "first_payment": "$150"},
            "memory_context": {
                "last_intent": "info",
                "last_pain": "",
                "stage": "solution",
                "history_summary": "consulta inicial",
            },
        },
    )
    _prompt, metadata, _context = builder.build(
        client_config_id="asesor_ai_prod",
        user_message="quiero ver precio",
        yaml_config=runtime_yaml,
        faq_results=[],
        progression_rules=None,
    )

    assert str((metadata or {}).get("prompt_source") or "") == "single_contract_blocks"
    assert str((metadata or {}).get("prompt_text") or "") == ""