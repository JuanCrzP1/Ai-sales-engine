## ========================================
## ARCHIVO: test_initial_flow_and_tenant_isolation.py
##
## QUÉ VALIDA:
## Flujo de mensaje inicial, reglas de recencia y aislamiento entre tenants.
##
## POR QUÉ ES CRÍTICO:
## Errores aquí generan onboarding inconsistente o fugas entre clientes.
##
## QUÉ PROTEGE:
## Comportamiento de entrada inicial y seguridad multi-tenant.
## ========================================

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.application.pipeline.conversation_flow import ConversationFlow, should_send_initial_message
from app.application.runtime import load_tenant_runtime_yaml
from app.infrastructure.config.config_service import ConfigService
from app.services.ai_service import AIService


class _MemoryStub:
    def __init__(self) -> None:
        self.initial_message_last_sent_at = None
        self.last_user_message_at = None
        self.saved_messages: list[tuple[str, str, str]] = []

    def get_last_user_message_at(self, *, tenant_slug: str, user_id: str):
        del tenant_slug, user_id
        return self.last_user_message_at

    def set_initial_message_last_sent_at(self, *, tenant_slug: str, user_id: str, sent_at) -> None:
        del tenant_slug, user_id
        self.initial_message_last_sent_at = sent_at

    def save_message(self, *, tenant_slug: str, user_id: str, message_text: str) -> None:
        self.saved_messages.append((tenant_slug, user_id, message_text))

    def set_last_user_message_at(self, *, tenant_slug: str, user_id: str, sent_at) -> None:
        del tenant_slug, user_id
        self.last_user_message_at = sent_at


class _ConfigMustNotLoadInitialMessage:
    def load_initial_message(self, client_id: str | None = None) -> dict:
        raise AssertionError(f"No debía cargar initial_message desde ConfigService para {client_id}")


def _tenant(slug: str) -> SimpleNamespace:
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").split())


def ask(
    message_text: str,
    *,
    tenant: str = "asesor_ai_prod",
    user_id: str | None = None,
    llm_mode: str | None = None,
    stub_ai_reply: str | None = None,
) -> tuple[str, bool, dict]:
    previous_mode = os.getenv("LLM_MODE")
    if llm_mode is None:
        os.environ.pop("LLM_MODE", None)
    else:
        os.environ["LLM_MODE"] = str(llm_mode)
    patched_orchestrator = None
    original_generate = None
    try:
        service = AIService()
        runtime_yaml = load_tenant_runtime_yaml(tenant)
        if stub_ai_reply is not None:
            patched_orchestrator = service.pipeline.runtime.ai_orchestrator
            original_generate = patched_orchestrator.generate_business_reply

            def _stub_generate(*args, **kwargs):
                del args, kwargs
                return str(stub_ai_reply), True

            patched_orchestrator.generate_business_reply = _stub_generate

        response, ai_used, metadata = service.generate_business_reply(
            tenant=_tenant(tenant),
            bot_config=None,
            user_message=message_text,
            conversation_history=[],
            faq_results=[],
            yaml_config=runtime_yaml,
            user_id=user_id or f"initial-flow-{uuid4().hex[:8]}",
            include_metadata=True,
        )
        return str(response or ""), bool(ai_used), dict(metadata or {})
    finally:
        if patched_orchestrator is not None and original_generate is not None:
            patched_orchestrator.generate_business_reply = original_generate
        if previous_mode is None:
            os.environ.pop("LLM_MODE", None)
        else:
            os.environ["LLM_MODE"] = previous_mode


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que el primer saludo devuelva source initial_message.
##
## POR QUÉ ES IMPORTANTE:
## Asegura onboarding consistente antes de entrar a lógica comercial.
##
## QUÉ PROTEGE:
## Gate de mensaje inicial y trazabilidad de origen de respuesta.
## ----------------------------------------
def test_initial_message_flow_returns_initial_message_source() -> None:
    uid = "init-source-test"
    _response, ai_used, meta = ask("hola", user_id=uid)

    assert ai_used is False
    assert meta.get("source") == "initial_message"


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Comprueba que después del primer saludo el siguiente turno sí use IA.
##
## POR QUÉ ES IMPORTANTE:
## Evita bucles de mensajes iniciales que frenan avance comercial.
##
## QUÉ PROTEGE:
## Transición correcta entre bienvenida y conversación activa.
## ----------------------------------------
def test_follow_up_turn_uses_ai_after_initial_message() -> None:
    uid = "init-then-ai-test"
    ask("hola", user_id=uid)
    _response, ai_used, meta = ask("necesito ayuda", user_id=uid, stub_ai_reply="respuesta siguiente")

    assert ai_used is True
    assert meta.get("source") != "initial_message"


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que un mensaje que empieza con saludo active initial_message
## incluso si después agrega intención.
##
## POR QUÉ ES IMPORTANTE:
## El gate de onboarding debe reconocer lenguaje real de WhatsApp.
##
## QUÉ PROTEGE:
## Prioridad del saludo cuando el mensaje inicia con saludo,
## aunque el resto del texto agregue contexto adicional.
## ----------------------------------------
def test_greeting_plus_intent_routes_to_ai_with_micro_greeting() -> None:
    response, ai_used, meta = ask("hola precio", stub_ai_reply="respuesta ia")

    assert ai_used is True
    assert meta.get("source") != "initial_message"
    assert response


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Valida política de recencia para no reenviar bienvenida en ventana activa.
##
## POR QUÉ ES IMPORTANTE:
## Evita spam y preserva continuidad natural en chats frecuentes.
##
## QUÉ PROTEGE:
## Control temporal del envío de mensajes iniciales.
## ----------------------------------------
def test_initial_message_recency_policy_blocks_recent_repeats() -> None:
    now = datetime.now(timezone.utc)
    cfg = {
        "initial_message": {
            "enabled": True,
            "mode": "smart",
        },
        "conversation": {
            "active_window_minutes": 15,
            "reset_hours": 4,
        },
    }

    assert should_send_initial_message(message="hola", last_user_message_at=None, config=cfg) is True
    assert should_send_initial_message(
        message="hola",
        last_user_message_at=now - timedelta(minutes=10),
        config=cfg,
    ) is False
    assert should_send_initial_message(
        message="hola",
        last_user_message_at=now - timedelta(minutes=30),
        config=cfg,
    ) is True
    assert should_send_initial_message(
        message="hola",
        last_user_message_at=now - timedelta(hours=5),
        config=cfg,
    ) is True


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Comprueba que cada tenant reciba su texto inicial propio sin cruces.
##
## POR QUÉ ES IMPORTANTE:
## Un cruce de mensajes entre tenants rompe aislamiento y experiencia de marca.
##
## QUÉ PROTEGE:
## Separación multi-tenant en configuración inicial.
## ----------------------------------------
def test_multi_tenant_initial_messages_remain_isolated() -> None:
    cfg = ConfigService()
    tenant_a = "asesor_ai_prod"
    tenant_b = "demo"

    expected_a = str(
        (
            cfg.load_initial_message(client_id=tenant_a).get("initial_message")
            if isinstance(cfg.load_initial_message(client_id=tenant_a).get("initial_message"), dict)
            else {}
        ).get("text")
        or ""
    ).strip()
    expected_b = str(
        (
            cfg.load_initial_message(client_id=tenant_b).get("initial_message")
            if isinstance(cfg.load_initial_message(client_id=tenant_b).get("initial_message"), dict)
            else {}
        ).get("text")
        or ""
    ).strip()

    response_a, ai_used_a, meta_a = ask("hola", tenant=tenant_a, user_id=f"iso-a-{uuid4().hex[:8]}")
    response_b, ai_used_b, meta_b = ask("hola", tenant=tenant_b, user_id=f"iso-b-{uuid4().hex[:8]}")

    assert meta_a.get("source") == "initial_message"
    assert meta_b.get("source") == "initial_message"
    assert ai_used_a is False
    assert ai_used_b is False
    assert _normalize_text(response_a) == _normalize_text(expected_a)
    assert _normalize_text(response_b) == _normalize_text(expected_b)
    assert _normalize_text(response_a) != _normalize_text(response_b)


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que tenant inexistente falle explícitamente sin fallback cruzado.
##
## POR QUÉ ES IMPORTANTE:
## Impide que un error de tenant termine cargando config de otro cliente.
##
## QUÉ PROTEGE:
## Seguridad de aislamiento y manejo estricto de errores de configuración.
## ----------------------------------------
def test_missing_tenant_yaml_raises_without_cross_tenant_fallback() -> None:
    cfg = ConfigService()
    try:
        cfg.load_initial_message(client_id="tenant_inexistente_xyz")
    except ValueError as exc:
        assert "tenant no encontrado" in str(exc).strip().lower()
        return
    raise AssertionError("Se esperaba ValueError para tenant inexistente")


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Valida el detector de saludos cuando el mensaje empieza con saludo.
##
## POR QUÉ ES IMPORTANTE:
## Si este gate falla, se enrutan mal los primeros turnos de conversación.
##
## QUÉ PROTEGE:
## Clasificación de entrada inicial en ConversationFlow.
## ----------------------------------------
def test_greeting_gate_identifies_first_message_only_inputs() -> None:
    assert ConversationFlow.is_greeting_only("hola") is True
    assert ConversationFlow.is_greeting_only("hola amigo") is True
    assert ConversationFlow.is_greeting_only("hola como estas") is True
    assert ConversationFlow.is_greeting_only("buenas tardes") is True
    assert ConversationFlow.is_greeting_only("hola parcero") is True
    assert ConversationFlow.is_greeting_only("qué más") is True
    assert ConversationFlow.is_greeting_only("parce") is True
    assert ConversationFlow.is_greeting_only("q mas") is True
    assert ConversationFlow.is_greeting_only("buenas") is True
    assert ConversationFlow.is_greeting_only("buenos días") is True
    assert ConversationFlow.is_greeting_only("buenos dias") is True
    assert ConversationFlow.is_greeting_only("hey") is True
    assert ConversationFlow.is_greeting_only("👋") is False
    assert ConversationFlow.is_greeting_only("hola precio") is False
    assert ConversationFlow.is_greeting_only("hola necesito info") is False
    assert ConversationFlow.is_greeting_only("hola quiero información") is False
    assert ConversationFlow.is_greeting_only("hola cuánto cuesta") is False
    assert ConversationFlow.is_greeting_only("buenas tardes me interesa") is False
    assert ConversationFlow.is_greeting_only("qué más, cómo funciona") is False
    assert ConversationFlow.is_greeting_only("dame info") is False
    assert ConversationFlow.is_greeting_only("quiero informacion") is False
    assert ConversationFlow.is_greeting_only("precio") is False


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Confirma que el mensaje inicial enviado sea exactamente el definido en YAML.
##
## POR QUÉ ES IMPORTANTE:
## Evita hardcodes y asegura que cada tenant controle su bienvenida en config.
##
## QUÉ PROTEGE:
## Fuente de verdad YAML para contenido inicial.
## ----------------------------------------
def test_initial_message_flow_uses_yaml_defined_content() -> None:
    tenant_slug = "asesor_ai_prod"
    cfg = ConfigService()
    expected_payload = cfg.load_initial_message(client_id=tenant_slug)
    expected_cfg = expected_payload.get("initial_message") if isinstance(expected_payload.get("initial_message"), dict) else {}
    expected_text = str(expected_cfg.get("text") or "").strip()

    response, ai_used, meta = ask("hola", tenant=tenant_slug, user_id=f"yaml-initial-{uuid4().hex[:8]}")

    assert meta.get("source") == "initial_message"
    assert ai_used is False
    assert _normalize_text(response) == _normalize_text(expected_text)


def test_runtime_config_initial_message_has_priority_over_config_service() -> None:
    memory = _MemoryStub()
    flow = ConversationFlow(
        memory_service=memory,
        demo_service=object(),
        config_service=_ConfigMustNotLoadInitialMessage(),
    )
    runtime_yaml = {
        "config": {
            "initial_message": {
                "enabled": True,
                "mode": "smart",
                "text": "Hola, este saludo viene de la config del tenant.",
            },
            "conversation": {
                "active_window_minutes": 15,
            },
        }
    }

    result = flow.handle_initial_message(
        user_id="runtime-config-initial-message",
        tenant_slug="asesor_ai_prod",
        user_message="hola",
        runtime_yaml=runtime_yaml,
    )

    assert result == ("Hola, este saludo viene de la config del tenant.", "initial_message")
    assert runtime_yaml.get("conversation_stage") == "connection"
    assert memory.initial_message_last_sent_at is not None
    assert memory.saved_messages == [
        ("asesor_ai_prod", "runtime-config-initial-message", "hola")
    ]