"""El turno del asesor: recibe el mensaje del cliente y devuelve la respuesta que sale. Dirige los pasos, cada uno en su módulo:

1. Lo que el asesor sabe antes de responder: memoria, resumen, lector de pagos y largo de respuesta (`turn_context.py`).
2. La respuesta de la IA, revisada: si dice algo que no puede salir así, se le pide otra (`answer_review.py`).
3. Lo que decidió queda en la memoria del cliente, con los datos que el cliente dio (`turn_persistence.py`).
4. El pago: los datos reales debajo del mensaje, el pago avisado y el largo máximo (`payment_outcome.py`).
5. Si el chat pasa a una persona, la nota para el equipo (`handoff_brief.py`). Quien guarda la conversación pausa la IA y avisa.

AI-first: la IA entiende, decide y escribe. El código le pasa el contexto y revisa que lo que sale sea cierto, sin decidir nunca por
palabras. También pone los datos de pago, que la IA nunca ve. Si algo falla después de que la IA respondió, sale la respuesta de
respaldo (`fallback.py`).
"""
from __future__ import annotations

from app.application.pipeline.answer_review import ReviewedAnswer, ask_and_review, checked_text
from app.application.pipeline.fallback import build_fallback_response
from app.application.pipeline.handoff_brief import brief_for_team
from app.application.pipeline.payment_outcome import settle_payment
from app.application.pipeline.turn_context import TurnContext, prepare_turn
from app.application.pipeline.turn_persistence import save_ai_metadata, save_customer_data, save_final_response
from app.domain.conversation.memory import MemoryDomainService
from app.utils.logger import logger

# Las secciones del negocio que acompañan el resultado del turno (y su registro).
BUSINESS_SECTIONS = ("sales", "business", "pricing", "features", "inventory")


class AIExecution:
    def run(
        self,
        *,
        runtime,
        tenant,
        bot_config,
        user_message: str,
        conversation_history: list,
        faq_results: list[dict],
        runtime_yaml: dict,
        memory_service: MemoryDomainService | None,
        tenant_slug: str,
        user_id: str,
    ) -> tuple[str, bool, dict]:
        turn = prepare_turn(
            runtime,
            tenant=tenant,
            bot_config=bot_config,
            user_message=user_message,
            runtime_yaml=runtime_yaml,
            memory_service=memory_service,
            tenant_slug=tenant_slug,
            user_id=user_id,
        )
        answer = ask_and_review(
            runtime,
            tenant=tenant,
            bot_config=bot_config,
            user_message=user_message,
            conversation_history=conversation_history,
            faq_results=faq_results,
            turn=turn,
        )
        try:
            context = _turn_context(answer, turn, user_message)
            ai_metadata = context["ai_metadata"]
            save_ai_metadata(memory_service, tenant_slug=turn.tenant_slug, user_id=turn.user_id, metadata=ai_metadata)
            save_customer_data(
                memory_service, tenant_slug=turn.tenant_slug, user_id=turn.user_id, metadata=ai_metadata, runtime_yaml=turn.runtime_yaml,
            )
            outcome = settle_payment(
                checked_text(answer.response, turn, user_message),
                ai_metadata=ai_metadata,
                problem=answer.problem,
                turn=turn,
                memory_service=memory_service,
            )
            _log_turn(context, turn)
            save_final_response(
                memory_service,
                tenant_slug=turn.tenant_slug,
                user_id=turn.user_id,
                response=outcome.remembered_response,
                intent=context["intent"],
            )
            if outcome.handoff_reason:
                context.update(handoff=True, handoff_reason=outcome.handoff_reason)
                # Para quien lo atiende: quién es el cliente y qué necesita, en dos o tres frases.
                context["handoff_summary"] = brief_for_team(
                    runtime, bot_config=bot_config, memory=memory_service, runtime_yaml=turn.runtime_yaml,
                    tenant_slug=turn.tenant_slug, user_id=turn.user_id, reason=outcome.handoff_reason,
                )
            return outcome.final_response, bool(answer.ai_used), context
        except Exception:
            return _fallback(answer, turn, user_message=user_message, runtime_yaml=runtime_yaml, memory_service=memory_service)


def _turn_context(answer: ReviewedAnswer, turn: TurnContext, user_message: str) -> dict:
    """El resultado del turno para quien llamó: lo que trajo el enrutador, las secciones del negocio, el canal, la intención y lo que
    decidió la IA (`ai_metadata`, con su respuesta y el mensaje del cliente)."""
    route = answer.route_context if isinstance(answer.route_context, dict) else {}
    yaml = turn.runtime_yaml
    context = {
        **route,
        **{name: yaml.get(name) if isinstance(yaml.get(name), dict) else {} for name in BUSINESS_SECTIONS},
        "channel": str(yaml.get("channel") or route.get("channel") or "unknown").strip().lower() or "unknown",
        "conversation_state": str(yaml.get("conversation_state") or "").strip().lower(),
    }
    ai_metadata = context.get("ai_metadata") if isinstance(context.get("ai_metadata"), dict) else {}
    ai_metadata = {**ai_metadata, "response": str(answer.response or ""), "user_message": str(user_message or "")}
    return {**context, "intent": str(ai_metadata.get("intent") or "").strip().lower(), "ai_metadata": ai_metadata}


def _log_turn(context: dict, turn: TurnContext) -> None:
    yaml = turn.runtime_yaml
    logger.info(
        {
            "tenant": turn.tenant_slug,
            "channel": str(context.get("channel") or "unknown"),
            "intent": str(context.get("intent") or "").strip().lower(),
            "sales_loaded": bool(yaml.get("sales")),
            "business_loaded": bool(yaml.get("business")),
            "pricing_loaded": bool(yaml.get("pricing")),
            "inventory_loaded": bool(yaml.get("inventory")),
        }
    )
    ai_metadata = context["ai_metadata"]
    logger.info(
        "ai_mode_execution",
        extra={
            "tenant": turn.tenant_slug,
            "user_id": turn.user_id,
            "mode": ai_metadata.get("mode") or context.get("mode"),
            "intent": ai_metadata.get("intent"),
        },
    )


def _fallback(
    answer: ReviewedAnswer,
    turn: TurnContext,
    *,
    user_message: str,
    runtime_yaml: dict,
    memory_service: MemoryDomainService | None,
) -> tuple[str, bool, dict]:
    """La respuesta de respaldo cuando algo falló después de que la IA respondió. Queda en el historial como cualquier respuesta."""
    tenant_config = {"tenant_slug": turn.tenant_slug, "runtime_yaml": runtime_yaml if isinstance(runtime_yaml, dict) else {}}
    fallback = build_fallback_response(user_message=user_message, tenant_config=tenant_config)
    route = answer.route_context if isinstance(answer.route_context, dict) else {}
    metadata = route.get("ai_metadata") if isinstance(route.get("ai_metadata"), dict) else {}
    intent = str(metadata.get("intent") or "").strip().lower()
    save_final_response(memory_service, tenant_slug=turn.tenant_slug, user_id=turn.user_id, response=fallback, intent=intent)
    return fallback, False, {"source": "fallback_exception_execution", "intent": intent, "tenant_slug": turn.tenant_slug}
