## ========================================
## ARCHIVO: test_memory_context_persistence.py
##
## QUÉ VALIDA:
## Que la memoria conversacional persista entre turnos y conserve datos útiles.
##
## POR QUÉ ES CRÍTICO:
## Si la memoria se vacía, la conversación pierde continuidad comercial.
##
## QUÉ PROTEGE:
## Contexto de memoria y anclajes de venta entre turnos.
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


def _tenant(slug: str = "asesor_ai_prod") -> SimpleNamespace:
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def _ask_with_stub(
    service: AIService,
    *,
    user_id: str,
    message: str,
    ai_text: str,
    memory: dict | None = None,
) -> tuple[str, bool, dict]:
    extra_yaml = {"memory_context": memory} if isinstance(memory, dict) else None
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod", extra_yaml=extra_yaml)
    orchestrator = service.pipeline.runtime.ai_orchestrator
    original_generate = orchestrator.generate_business_reply

    def _stub_generate(*args, **kwargs):
        del args, kwargs
        return ai_text, True, {"intent": "info", "mode": "sales"}

    orchestrator.generate_business_reply = _stub_generate
    try:
        response, ai_used, metadata = service.generate_business_reply(
            tenant=_tenant(),
            bot_config=None,
            user_message=message,
            conversation_history=[],
            faq_results=[],
            yaml_config=runtime_yaml,
            user_id=user_id,
            include_metadata=True,
        )
    finally:
        orchestrator.generate_business_reply = original_generate

    return str(response or ""), bool(ai_used), dict(metadata or {})


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica continuidad de memory_context entre turnos y que guarde señal útil de ventas.
##
## POR QUÉ ES IMPORTANTE:
## Si la memoria llega vacía, el segundo turno pierde contexto comercial y cae en respuestas genéricas.
##
## QUÉ PROTEGE:
## Persistencia conversacional AI-first y anclaje de pricing entre turnos.
## ----------------------------------------
def test_memory_context_persists_and_contains_useful_data() -> None:
    service = AIService()
    user_id = f"mem-persist-{uuid4().hex[:8]}"

    runtime_preview = load_tenant_runtime_yaml("asesor_ai_prod")
    pricing_cfg = runtime_preview.get("pricing") if isinstance(runtime_preview.get("pricing"), dict) else {}
    plans = pricing_cfg.get("plans") if isinstance(pricing_cfg.get("plans"), list) else []
    first_plan = plans[0] if plans and isinstance(plans[0], dict) else {}
    first_plan_pricing = first_plan.get("pricing") if isinstance(first_plan.get("pricing"), dict) else {}
    cop_prices = first_plan_pricing.get("COP") if isinstance(first_plan_pricing.get("COP"), dict) else {}
    price_value = str(cop_prices.get("monthly") or cop_prices.get("implementation") or "180000")

    r1 = _ask_with_stub(
        service,
        user_id=user_id,
        message="cuanto vale",
        ai_text=f"El valor mensual es {price_value} COP.",
    )
    mem = r1[2].get("memory_context")

    ## Debe existir como diccionario
    assert isinstance(mem, dict)

    ## Debe contener información relevante (no vacío inútil)
    assert "price_anchor" in mem or len(mem) > 0

    r2 = _ask_with_stub(
        service,
        user_id=user_id,
        message="esta caro",
        ai_text="Entiendo el punto, revisemos precio y retorno.",
        memory=mem,
    )
    mem2 = r2[2].get("memory_context")

    ## La memoria debe seguir existiendo en el siguiente turno
    assert isinstance(mem2, dict)
    assert mem2 is not None

    ## Debe mantenerse útil tras reinyectarse al segundo turno
    assert "price_anchor" in mem2 or len(mem2) > 0


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que save_message() almacena el role correctamente.
##
## POR QUÉ ES IMPORTANTE:
## El historial estructurado debe diferenciar quién habló.
##
## QUÉ PROTEGE:
## Historial bidireccional con roles usuario/asistente (5C).
## ----------------------------------------
def test_save_message_stores_role() -> None:
    from app.infrastructure.persistence.memory_repository import MemoryRepository

    repo = MemoryRepository()
    repo.save_message(tenant_slug="asesor_ai_prod", user_id="role-test-1", message_text="hola")
    repo.save_message(
        tenant_slug="asesor_ai_prod", user_id="role-test-1",
        message_text="Claro, te ayudo con eso.", role="assistant",
    )
    repo.save_message(
        tenant_slug="asesor_ai_prod", user_id="role-test-1",
        message_text="cuanto vale",
    )

    history = repo.get_history(tenant_slug="asesor_ai_prod", user_id="role-test-1")
    assert len(history) == 3
    assert history[0]["role"] == "user"
    assert history[0]["text"] == "hola"
    assert history[1]["role"] == "assistant"
    assert history[1]["text"] == "Claro, te ayudo con eso."
    assert history[2]["role"] == "user"
    assert history[2]["text"] == "cuanto vale"


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que el role por defecto es "user".
##
## POR QUÉ ES IMPORTANTE:
## Compatibilidad retroactiva con todas las llamadas existentes.
##
## QUÉ PROTEGE:
## Que el cambio de 5C no rompe nada del pipeline actual.
## ----------------------------------------
def test_save_message_default_role_is_user() -> None:
    from app.infrastructure.persistence.memory_repository import MemoryRepository

    repo = MemoryRepository()
    repo.save_message(tenant_slug="asesor_ai_prod", user_id="role-default-1", message_text="mensaje sin rol explícito")

    history = repo.get_history(tenant_slug="asesor_ai_prod", user_id="role-default-1")
    assert len(history) == 1
    assert history[0]["role"] == "user"


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que mensajes legacy (sin campo role) devuelven "user".
##
## POR QUÉ ES IMPORTANTE:
## Compatibilidad con entradas almacenadas antes de 5C.
##
## QUÉ PROTEGE:
## Backward compatibility del historial.
## ----------------------------------------
def test_get_history_backward_compatible_with_legacy_entries() -> None:
    from app.infrastructure.persistence.memory_repository import MemoryRepository

    repo = MemoryRepository()
    # Inyectar directamente una entrada legacy sin rol (como existiría antes de 5C)
    key = ("asesor_ai_prod", "legacy-user-1")
    repo._messages_by_user[key] = [
        {"text": "mensaje antiguo", "timestamp": None},  # sin campo "role"
    ]

    history = repo.get_history(tenant_slug="asesor_ai_prod", user_id="legacy-user-1")
    assert len(history) == 1
    assert history[0]["role"] == "user"
    assert history[0]["text"] == "mensaje antiguo"


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que la respuesta de la IA se persiste con role="assistant" tras un turno real.
##
## POR QUÉ ES IMPORTANTE:
## Es el contrato central de 5C: el historial debe incluir ambos lados de la conversación.
##
## QUÉ PROTEGE:
## Que _persist_final_response() guarda la respuesta IA en get_history().
## ----------------------------------------
def test_ai_response_persisted_as_assistant() -> None:
    service = AIService()
    uid = f"ai-assistant-role-{uuid4().hex[:8]}"
    flow = service.pipeline.conversation_flow

    _ask_with_stub(service, user_id=uid, message="cuanto vale", ai_text="El precio es 180.000 COP mensuales.")

    history = flow.memory.get_history(tenant_slug="asesor_ai_prod", user_id=uid)
    roles = [item.get("role") for item in history]

    # Debe haber al menos una entrada de usuario y una de asistente
    assert "user" in roles, "Historial debe tener mensaje de usuario"
    assert "assistant" in roles, "Historial debe tener respuesta de la IA"

    assistant_entries = [item for item in history if item.get("role") == "assistant"]
    assert len(assistant_entries) >= 1
    assert "precio" in assistant_entries[-1]["text"].lower() or "180" in assistant_entries[-1]["text"]


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que conversation_history entregado a runtime contiene ambos roles.
##
## POR QUÉ ES IMPORTANTE:
## El prompt/pipeline recibirá historial real de ambos lados.
##
## QUÉ PROTEGE:
## Que _inject_conversation_history pasa entries con role al runtime_yaml.
## ----------------------------------------
def test_conversation_history_in_runtime_contains_both_roles() -> None:
    service = AIService()
    uid = f"runtime-history-roles-{uuid4().hex[:8]}"
    flow = service.pipeline.conversation_flow

    # Primer turno: usuario pregunta, IA responde
    _ask_with_stub(service, user_id=uid, message="tengo muchos mensajes", ai_text="Entiendo, eso te hace perder clientes.")

    # Verificar historial en memoria antes del segundo turno
    history = flow.memory.get_history(tenant_slug="asesor_ai_prod", user_id=uid)
    roles = {item.get("role") for item in history}
    assert "user" in roles
    assert "assistant" in roles


## ========================================
## FASE 5D-A: history_summary con roles
## ========================================

def _make_stub_memory_service(history_entries: list[dict]) -> object:
    """Crea un stub mínimo de MemoryDomainService para probar _build_memory_context."""
    from types import SimpleNamespace
    from app.domain.conversation.memory import ConversationState

    return SimpleNamespace(
        get_history=lambda *, tenant_slug, user_id: list(history_entries),
        get_last_response=lambda *, tenant_slug, user_id: None,
        get_conversation_state=lambda *, tenant_slug, user_id: ConversationState(),
        get_last_intent=lambda *, tenant_slug, user_id: None,
        get_detected_intent=lambda *, tenant_slug, user_id: None,
        get_last_pain=lambda *, tenant_slug, user_id: None,
        get_payment_method=lambda *, tenant_slug, user_id: None,
        get_payment_status=lambda *, tenant_slug, user_id: None,
        get_stage=lambda *, tenant_slug, user_id: None,
        get_mode=lambda *, tenant_slug, user_id: None,
        build_sales_memory_usage=lambda *, tenant_slug, user_id: "",
    )


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que history_summary incluye prefijos user: y assistant:.
##
## POR QUÉ ES IMPORTANTE:
## La IA debe poder distinguir quién dijo qué en el historial (Fase 5D-A).
##
## QUÉ PROTEGE:
## Formato estructurado con roles del history_summary.
## ----------------------------------------
def test_history_summary_includes_role_prefixes() -> None:
    from app.application.pipeline.ai_execution import _build_memory_context

    entries = [
        {"role": "user",      "text": "tengo muchos mensajes"},
        {"role": "assistant", "text": "Eso te hace perder clientes"},
        {"role": "user",      "text": "ya tengo secretaria"},
        {"role": "user",      "text": "mensaje actual"},  # último → excluido (prior_history)
    ]
    stub = _make_stub_memory_service(entries)
    result = _build_memory_context(stub, tenant_slug="asesor_ai_prod", user_id="5da-roles-1")

    summary = result["history_summary"]
    assert "user: tengo muchos mensajes" in summary
    assert "assistant: Eso te hace perder clientes" in summary
    assert "user: ya tengo secretaria" in summary
    assert " | " not in summary, "El separador ya no debe ser pipe"


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que el orden cronológico se conserva en el history_summary.
##
## POR QUÉ ES IMPORTANTE:
## El modelo debe leer la conversación en orden para entender el flujo.
##
## QUÉ PROTEGE:
## Orden temporal del historial en el prompt.
## ----------------------------------------
def test_history_summary_preserves_chronological_order() -> None:
    from app.application.pipeline.ai_execution import _build_memory_context

    entries = [
        {"role": "user",      "text": "primer mensaje"},
        {"role": "assistant", "text": "primera respuesta"},
        {"role": "user",      "text": "segundo mensaje"},
        {"role": "assistant", "text": "segunda respuesta"},
        {"role": "user",      "text": "mensaje actual"},  # último → excluido
    ]
    stub = _make_stub_memory_service(entries)
    result = _build_memory_context(stub, tenant_slug="asesor_ai_prod", user_id="5da-order-1")

    summary = result["history_summary"]
    lines = [l for l in summary.splitlines() if l.strip()]
    assert lines[0] == "user: primer mensaje"
    assert lines[1] == "assistant: primera respuesta"
    assert lines[2] == "user: segundo mensaje"
    assert lines[3] == "assistant: segunda respuesta"


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que history_summary respeta el límite de 10 entradas anteriores.
##
## POR QUÉ ES IMPORTANTE:
## El prompt no debe crecer ilimitadamente con conversaciones largas.
##
## QUÉ PROTEGE:
## Control de tamaño del contexto de historial en el prompt.
## ----------------------------------------
def test_history_summary_respects_ten_entry_limit() -> None:
    from app.application.pipeline.ai_execution import _build_memory_context

    # 12 mensajes del usuario → prior_history = primeros 11 → history[-10:] → 10 líneas
    entries = [{"role": "user", "text": f"mensaje {i}"} for i in range(12)]
    stub = _make_stub_memory_service(entries)
    result = _build_memory_context(stub, tenant_slug="asesor_ai_prod", user_id="5da-limit-1")

    summary = result["history_summary"]
    lines = [l for l in summary.splitlines() if l.strip()]
    assert len(lines) <= 10, f"Esperado máximo 10 líneas, got {len(lines)}"


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica compatibilidad con entradas legacy sin campo role.
##
## POR QUÉ ES IMPORTANTE:
## Entradas guardadas antes de Fase 5C no tienen role. No deben romperse.
##
## QUÉ PROTEGE:
## Backward compatibility del historial plano pre-5C.
## ----------------------------------------
def test_history_summary_legacy_entries_default_to_user_role() -> None:
    from app.application.pipeline.ai_execution import _build_memory_context

    entries = [
        {"text": "mensaje sin rol"},          # legacy: sin campo role
        {"role": "user", "text": "siguiente"},
        {"role": "user", "text": "actual"},   # último → excluido
    ]
    stub = _make_stub_memory_service(entries)
    result = _build_memory_context(stub, tenant_slug="asesor_ai_prod", user_id="5da-legacy-1")

    summary = result["history_summary"]
    assert "user: mensaje sin rol" in summary
    assert "user: siguiente" in summary


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que last_user_message sigue apuntando al último mensaje del usuario.
##
## POR QUÉ ES IMPORTANTE:
## El cambio de format en history_summary no debe afectar last_user_message.
##
## QUÉ PROTEGE:
## Integridad de last_user_message tras Fase 5D-A.
## ----------------------------------------
def test_last_user_message_unaffected_by_5da_change() -> None:
    from app.application.pipeline.ai_execution import _build_memory_context

    entries = [
        {"role": "user",      "text": "primer dolor"},
        {"role": "assistant", "text": "entiendo, dime más"},
        {"role": "user",      "text": "segundo mensaje"},   # ← debe ser last_user_message
        {"role": "user",      "text": "mensaje actual"},    # último → excluido de prior_history
    ]
    stub = _make_stub_memory_service(entries)
    result = _build_memory_context(stub, tenant_slug="asesor_ai_prod", user_id="5da-last-msg-1")

    assert result["last_user_message"] == "segundo mensaje"
    assert result["last_message"] == "segundo mensaje"


## ========================================
## FASE 5D-B: consolidación de señales comerciales
## ========================================


def _build_prompt_with_memory(memory_ctx: dict, conversation_state: str = "active") -> str:
    from app.application.runtime import load_tenant_runtime_yaml
    from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService

    runtime_yaml = load_tenant_runtime_yaml(
        "asesor_ai_prod",
        extra_yaml={"memory_context": memory_ctx, "conversation_state": conversation_state},
    )
    builder = PromptBuilderService()
    prompt, _, _ = builder.build(
        client_config_id="asesor_ai_prod",
        user_message="siguiente paso",
        yaml_config=runtime_yaml,
        faq_results=[],
        progression_rules=None,
    )
    return str(prompt or "")


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que last_intent aparece una sola vez en el prompt.
##
## POR QUÉ ES IMPORTANTE:
## Antes de 5D-B aparecía en build_conversation_state Y en build_recent_customer_context.
##
## QUÉ PROTEGE:
## Eliminación de redundancia de intent en el prompt (5D-B).
## ----------------------------------------
def test_intent_appears_only_once_in_prompt() -> None:
    prompt = _build_prompt_with_memory({"last_intent": "price", "last_ai_response": "ok"})
    count = prompt.count("Última intención detectada: price")
    assert count == 1, f"Se esperaba 1 ocurrencia de last_intent, encontradas: {count}"


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que last_pain aparece una sola vez en el prompt.
##
## POR QUÉ ES IMPORTANTE:
## Antes de 5D-B aparecía en build_conversation_state Y ahora centralizado en build_recent_customer_context.
##
## QUÉ PROTEGE:
## Eliminación de redundancia de dolor en el prompt (5D-B).
## ----------------------------------------
def test_pain_appears_only_once_in_prompt() -> None:
    prompt = _build_prompt_with_memory(
        {"last_intent": "pain", "last_pain": "mensajes perdidos", "last_ai_response": "ok"}
    )
    count = prompt.count("Dolor detectado: mensajes perdidos")
    assert count == 1, f"Se esperaba 1 ocurrencia de last_pain, encontradas: {count}"


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que payment_status aparece una sola vez cuando existe.
##
## POR QUÉ ES IMPORTANTE:
## Antes de 5D-B aparecía en build_recent_customer_context Y en build_memory_behavior_context.
##
## QUÉ PROTEGE:
## Eliminación de redundancia de estado de pago (5D-B).
## ----------------------------------------
def test_payment_status_appears_only_once_in_prompt() -> None:
    prompt = _build_prompt_with_memory(
        {
            "last_intent": "price",
            "metodo_pago_elegido": "nequi",
            "estado_pago": "pendiente",
            "last_ai_response": "ok",
        }
    )
    count = prompt.count("Estado de pago recordado: pendiente")
    assert count == 1, f"Se esperaba 1 ocurrencia de estado_pago, encontradas: {count}"
    # El bloque MEMORIA también debe tener el dato de pago (no de intent)
    assert "ESTADO_PAGO_PREVIO: pendiente" in prompt
    # intent NO debe aparecer en MEMORIA
    assert "INTENT_DETECTADO_PREVIO" not in prompt


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que el bloque COMPORTAMIENTO CON MEMORIA no se renderiza sin datos de pago.
##
## POR QUÉ ES IMPORTANTE:
## Antes de 5D-B se renderizaba cuando solo había intent (ruido puro).
##
## QUÉ PROTEGE:
## Supresión del bloque de memoria cuando no hay pago activo (5D-B).
## ----------------------------------------
def test_memory_behavior_block_absent_without_payment_data() -> None:
    prompt = _build_prompt_with_memory(
        {"last_intent": "pain", "last_pain": "mensajes", "last_ai_response": "ok"}
    )
    assert "COMPORTAMIENTO CON MEMORIA:" not in prompt


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que el comportamiento comercial sigue intacto tras la consolidación.
##
## POR QUÉ ES IMPORTANTE:
## 5D-B no debe eliminar instrucciones de comportamiento, solo datos duplicados.
##
## QUÉ PROTEGE:
## Continuidad comercial y behavioral del prompt (5D-B).
## ----------------------------------------
def test_commercial_behavior_intact_after_5db() -> None:
    prompt = _build_prompt_with_memory({"last_intent": "price", "last_ai_response": "ok"})
    assert "COMPORTAMIENTO COMERCIAL" in prompt
    assert "Contexto reciente del cliente:" in prompt
    assert "Estado de la conversaci\u00f3n:" in prompt


## ========================================
## FASE 5D-C: bloques permanentes optimizados
## ========================================


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que en estado active sin pago el prompt es significativamente más corto.
##
## POR QUÉ ES IMPORTANTE:
## El caso más frecuente (active, sin pago) ahora elimina capabilities completo y post_payment.
##
## QUÉ PROTEGE:
## Reducción real de tokens en turnos activos (5D-C).
## ----------------------------------------
def test_active_prompt_shorter_without_payment() -> None:
    from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService
    from app.application.runtime import load_tenant_runtime_yaml

    b = PromptBuilderService()
    rt = load_tenant_runtime_yaml("asesor_ai_prod", extra_yaml={
        "conversation_state": "active",
        "memory_context": {"last_intent": "price", "last_pain": "mensajes", "last_ai_response": "ok"},
    })
    prompt, _, _ = b.build(client_config_id="asesor_ai_prod", user_message="siguiente", yaml_config=rt, faq_results=[], progression_rules=None)
    # El prompt activo sin pago debe ser claramente menor que la referencia pre-5D (3253 chars)
    # Umbral actualizado a 2800: fase 1.1 agrega señales comerciales de pricing (~50 chars extra intencionales)
    assert len(prompt) < 2800, f"Prompt activo sin pago demasiado largo: {len(prompt)} chars"


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que capabilities muestra versión compacta en estado active.
##
## POR QUÉ ES IMPORTANTE:
## En turnos activos el agente ya conoce los canales; solo necesita métodos de cierre y acciones.
##
## QUÉ PROTEGE:
## Compactación de capabilities en estados active/warm (5D-C).
## ----------------------------------------
def test_capabilities_compact_in_active_state() -> None:
    from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService

    rt_active = {
        "conversation_state": "active",
        "config": {
            "capabilities": {
                "business_channels": ["whatsapp"],
                "system_channels": ["web"],
                "closing_methods": {"link_payment": {"enabled": True}},
                "actions": {"primary": ["cerrar_venta"]},
            }
        },
    }
    result = PromptBuilderService.build_capabilities_context(rt_active)
    assert "TIPOS DE CANALES:" not in result
    assert "CANALES DE ATENCION" not in result
    assert "Métodos de cierre: link_payment" in result
    assert "Acciones: cerrar_venta" in result


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que capabilities muestra versión completa en estado new.
##
## POR QUÉ ES IMPORTANTE:
## En el primer turno el agente necesita conocer los canales disponibles.
##
## QUÉ PROTEGE:
## Que la compactación no afecte el primer turno (5D-C).
## ----------------------------------------
def test_capabilities_full_in_new_state() -> None:
    from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService

    rt_new = {
        "conversation_state": "new",
        "config": {
            "capabilities": {
                "business_channels": ["whatsapp"],
                "system_channels": ["web"],
                "closing_methods": {"link_payment": {"enabled": True}},
                "actions": {"primary": ["cerrar_venta"]},
            }
        },
    }
    result = PromptBuilderService.build_capabilities_context(rt_new)
    assert "TIPOS DE CANALES:" in result
    assert "CANALES DE ATENCION (business_channels):" in result


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que post_payment NO se renderiza sin datos de pago activos.
##
## POR QUÉ ES IMPORTANTE:
## El bloque POST-PAGO es 300 chars que no aportan valor en la mayoría de turnos.
##
## QUÉ PROTEGE:
## Supresión de post_payment en turnos sin pago activo (5D-C).
## ----------------------------------------
def test_post_payment_absent_without_active_payment() -> None:
    from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService
    from app.application.runtime import load_tenant_runtime_yaml

    rt = load_tenant_runtime_yaml("asesor_ai_prod", extra_yaml={
        "conversation_state": "active",
        "memory_context": {"last_intent": "pain", "last_ai_response": "ok"},
    })
    result = PromptBuilderService.build_post_payment_context(rt)
    assert result == ""


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que post_payment SÍ se renderiza cuando hay pago activo.
##
## POR QUÉ ES IMPORTANTE:
## Cuando el usuario está en flujo de pago, los mensajes exactos son críticos.
##
## QUÉ PROTEGE:
## Que la supresión no afecte el flujo de pago activo (5D-C).
## ----------------------------------------
def test_post_payment_present_with_active_payment() -> None:
    from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService
    from app.application.runtime import load_tenant_runtime_yaml

    rt = load_tenant_runtime_yaml("asesor_ai_prod", extra_yaml={
        "conversation_state": "active",
        "memory_context": {"metodo_pago_elegido": "nequi", "estado_pago": "pendiente"},
    })
    result = PromptBuilderService.build_post_payment_context(rt)
    assert "POST-PAGO:" in result
    assert "ON_USER_REPORT_MESSAGE:" in result


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que pricing sigue presente en estado active.
##
## POR QUÉ ES IMPORTANTE:
## El pricing no debe desaparecer en turnos activos; la IA lo necesita para vender.
##
## QUÉ PROTEGE:
## Preservación de pricing en turnos activos (5D-C).
## ----------------------------------------
def test_pricing_present_in_active_state() -> None:
    prompt = _build_prompt_with_memory({"last_intent": "price", "last_ai_response": "ok"})
    assert "PRICING:" in prompt
    assert "LINK_AVAILABLE:" in prompt
    assert "TRANSFER_METHODS:" in prompt


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que restricciones operativas siguen presentes.
##
## POR QUÉ ES IMPORTANTE:
## Las reglas de grounding son el núcleo de seguridad del prompt.
##
## QUÉ PROTEGE:
## Que la optimización no elimine restricciones críticas (5D-C).
## ----------------------------------------
def test_operational_restrictions_always_present() -> None:
    prompt = _build_prompt_with_memory({"last_intent": "price", "last_ai_response": "ok"})
    assert "REGLA CR\u00cdTICA:" in prompt
    assert "Responde SOLO con informaci\u00f3n que est\u00e9 en el contexto proporcionado." in prompt
