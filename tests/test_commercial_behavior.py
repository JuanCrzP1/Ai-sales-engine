## ========================================
## ARCHIVO: test_commercial_behavior.py
##
## QUÉ VALIDA:
## Que la respuesta comercial no sea pasiva y empuje a un siguiente paso.
##
## POR QUÉ ES CRÍTICO:
## Si este comportamiento cae, el sistema conversa pero deja de vender.
##
## QUÉ PROTEGE:
## Comportamiento comercial activo en conversaciones AI-first.
## ========================================

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import pytest

from app.application.runtime import load_tenant_runtime_yaml
from app.services.ai_service import AIService
from semantic_guard import has_forward_intent

# Suite de integración: ejercita el LLM en vivo (requiere OPENROUTER_API_KEY).
pytestmark = pytest.mark.integration


def _tenant(slug: str):
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def ask(message: str):
    service = AIService()
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod", channel="whatsapp")

    response, ai_used, metadata = service.generate_business_reply(
        tenant=_tenant("asesor_ai_prod"),
        bot_config=None,
        user_message=message,
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        user_id="test-user",
        include_metadata=True,
    )

    return str(response or "").lower()


def test_response_pushes_conversation_forward():
    reply = ask("tengo muchos mensajes")

    ## Señal 1: debe invitar a avanzar (pregunta o siguiente paso)
    assert "?" in reply or has_forward_intent(reply)

    ## Señal 2: debe conectar con impacto comercial o problema real
    assert any(
        word in reply
        for word in [
            "client",
            "vent",
            "oportun",
            "seguim",
            "respond",
        ]
    )


## ─────────────────────────────────────────────────────────────────────────────
## TESTS DE CONTEXTO CONDICIONAL Y NO-REPETICIÓN
## La supresión del pitch ocurre cuando la IA ya respondió antes (last_ai_response
## presente). Sin respuesta previa, siempre se inyecta contexto completo.
## ─────────────────────────────────────────────────────────────────────────────

def _build_prompt_for_state(conversation_state: str, user_message: str, *, last_ai_response: str = "") -> str:
    from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService

    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod", channel="whatsapp")
    runtime_yaml["conversation_state"] = conversation_state
    if last_ai_response:
        runtime_yaml["memory_context"] = {"last_ai_response": last_ai_response}

    prompt, _, _ = PromptBuilderService().build(
        client_config_id="asesor_ai_prod",
        user_message=user_message,
        yaml_config=runtime_yaml,
        faq_results=[],
        progression_rules=None,
    )
    return str(prompt or "")


def test_no_pitch_repetition_when_ai_already_spoke():
    ## Cuando la IA ya respondió (last_ai_response presente) en estado active,
    ## no se inyecta business_context ni sales_context.
    prev_response = "Con gusto te explico cómo funciona el servicio."
    prompt_active = _build_prompt_for_state("active", "como funciona", last_ai_response=prev_response)

    assert "promesa comercial" not in prompt_active.lower()
    assert "industria del negocio" not in prompt_active.lower()

    ## La regla de continuidad sí debe estar
    assert "no lo repitas" in prompt_active.lower() or "no reinicies" in prompt_active.lower()


def test_full_context_on_active_first_real_turn():
    ## Sin last_ai_response, aunque el estado sea active, se inyecta
    ## contexto completo (primer turno real de la IA).
    prompt_active_first = _build_prompt_for_state("active", "tengo muchos mensajes")

    assert "promesa comercial" in prompt_active_first.lower() or "industria del negocio" in prompt_active_first.lower()


def test_full_context_on_new_state():
    ## En estado "new" el contexto completo siempre está disponible.
    prompt_new = _build_prompt_for_state("new", "hola")

    assert "promesa comercial" in prompt_new.lower() or "industria del negocio" in prompt_new.lower()


def test_full_context_on_cold_state():
    ## En estado "cold" también se necesita reenganche con contexto completo.
    prompt_cold = _build_prompt_for_state("cold", "hola de nuevo")

    assert "promesa comercial" in prompt_cold.lower() or "industria del negocio" in prompt_cold.lower()

