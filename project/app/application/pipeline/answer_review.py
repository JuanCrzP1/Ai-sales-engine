"""La respuesta del asesor, revisada antes de salir (`ai_execution.py`).

- `ask_and_review` le pide la respuesta a la IA. Si dice algo que no puede salir así, le pide otra y le dice por qué. Eso pasa con algo
  falso sobre los pagos («no recibimos Nequi»), con datos que el cliente no pidió o que ya tiene (`payment_delivery.payment_problem`),
  o si le dice al cliente que lo pasa con el equipo sin haberlo decidido (`handoff_review.py`). La IA decide de nuevo su mensaje, su
  acción y si pasa el chat a una persona: el código no le escribe la respuesta.
- `checked_text` revisa los números. La IA nunca ve los datos de pago, así que un celular o una cuenta que escribe sin haberlo leído es
  inventado. Se cambia por el marcador del dato y el sistema pone el real (`payment_delivery.py`).
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from app.application.pipeline.handoff_review import UNMARKED, handoff_problem
from app.application.pipeline.payment_delivery import payment_problem
from app.application.pipeline.payment_names import payment_terms
from app.application.pipeline.response_postprocessor import without_model_artifacts
from app.application.pipeline.response_router import route_response
from app.application.pipeline.turn_context import TurnContext
from app.domain.business_config.payment_data import mask_invented_numbers, mask_own_markers, redact_payment_values
from app.utils.logger import logger


@dataclass(frozen=True)
class ReviewedAnswer:
    """La respuesta que quedó, cómo la produjo el enrutador (`route_context`, con `ai_metadata`) y lo que sigue mal después de la
    segunda respuesta (`problem`, vacío si nada)."""

    response: str
    ai_used: bool
    route_context: dict
    problem: dict


def ask_and_review(
    runtime,
    *,
    tenant,
    bot_config,
    user_message: str,
    conversation_history: list,
    faq_results: list[dict],
    turn: TurnContext,
) -> ReviewedAnswer:
    def ask(runtime_yaml: dict):
        return route_response(
            runtime=runtime,
            tenant=tenant,
            bot_config=bot_config,
            user_message=user_message,
            conversation_history=conversation_history,
            faq_results=faq_results,
            runtime_yaml=runtime_yaml,
        )

    response, ai_used, route_context = ask(turn.runtime_yaml)
    problem = _problem(response, route_context, turn) if ai_used else {}
    if problem:
        event = "paso_a_persona_segunda_respuesta" if UNMARKED in problem else "pago_segunda_respuesta"
        logger.warning(event, extra={"tenant": turn.tenant_slug, "why": next(iter(problem))})
        second = ask({**turn.runtime_yaml, "answer_again": problem})
        if second[1]:
            response, ai_used, route_context = second
            problem = _problem(response, route_context, turn)
        if UNMARKED in problem:
            # Insistió en decirle que lo pasa sin decidirlo: manda su decisión (no se pasa), y queda a la vista.
            logger.warning("paso_a_persona_sin_marcar", extra={"tenant": turn.tenant_slug})
    return ReviewedAnswer(response=response, ai_used=ai_used, route_context=route_context, problem=problem)


def _problem(answer: str, context, turn: TurnContext) -> dict:
    """Por qué esa respuesta del asesor no puede salir así, o `{}` si está bien."""
    metadata = context.get("ai_metadata") if isinstance(context, dict) and isinstance(context.get("ai_metadata"), dict) else {}
    return payment_problem(
        str(answer or ""),
        turn.runtime_yaml,
        send_payment=str(metadata.get("send_payment") or ""),
        asked=turn.reading.wants_details if turn.reading is not None else None,
        state=turn.op_before,
        remembered=turn.remembered_method,
    ) or handoff_problem(str(answer or ""), metadata)


def checked_text(response: str, turn: TurnContext, user_message: str) -> str:
    """El texto de la respuesta sin restos del modelo y sin números que la IA no leyó en ninguna parte."""
    text = without_model_artifacts(str(response or "")).strip()
    # A veces la IA también escribe su propio marcador («[número de Nequi]»): se cambia por el del sistema.
    checked = mask_invented_numbers(
        mask_own_markers(text),
        _known_to_the_ai(turn.runtime_yaml, str(user_message or "")),
        payment_terms=payment_terms(turn.runtime_yaml),
    )
    if checked != text:
        logger.warning("pago_numero_inventado", extra={"tenant": turn.tenant_slug})
    return checked


def _known_to_the_ai(runtime_yaml: dict, user_message: str) -> str:
    """Todo lo que la IA leyó para responder (el negocio, la memoria y la conversación), en un solo texto: sirve para saber si un
    número que escribió lo leyó en alguna parte o lo inventó. Sin los datos de pago: la IA nunca los ve. (Con ellos, un número
    inventado que coincidía con parte de una cuenta real, «123456789» de «1234567890», pasaba como leído; 13 nov 2026.)"""
    try:
        read = f"{json.dumps(runtime_yaml, ensure_ascii=False, default=str)} {user_message}"
    except (TypeError, ValueError):
        read = user_message
    return redact_payment_values(read, runtime_yaml)
