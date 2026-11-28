"""Lo que pasa con el pago en un turno, una vez revisada la respuesta del asesor (`ai_execution.py`).

- Si el cliente avisó en este mensaje que ya pagó, lo dice el lector de pagos (`payment_reading.py`), no el asesor: una pregunta
  enfocada acierta más que el asesor, que a veces lo marca sin que el cliente lo diga o se le pasa. Un pago avisado sale con el mensaje
  del negocio para ese momento y pasa al equipo, porque solo el equipo puede verificarlo. Un pago avisado antes sigue avisado.
  Cuando el equipo lo verifica y toca «Confirmar pago» en el panel, queda «confirmado» (`remember_confirmed_payment`).
- Si no, los datos de pago: el asesor (la IA) decide con su acción y habla, y el sistema pone los datos reales debajo de su mensaje
  (`payment_delivery.deliver`). El medio queda anotado, y el paso de la conversación sale de ese hecho, no de palabras.
- El largo máximo del negocio es para lo que dice el asesor. Los datos de pago van completos debajo.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.application.pipeline.payment_delivery import (
    PaymentDelivery,
    compose,
    confirmed_state,
    deliver,
    remembered_message,
    sent_state,
)
from app.application.pipeline.response_postprocessor import enforce_max_words
from app.application.pipeline.turn_context import TurnContext
from app.domain.conversation.memory import MemoryDomainService
from app.utils.logger import logger

REPORTED = "reportado"
# El equipo verificó el pago y se lo confirmó al cliente desde el chat (`remember_confirmed_payment`).
CONFIRMED = "confirmado"


@dataclass(frozen=True)
class PaymentOutcome:
    """Lo que sale al cliente (`final_response`) y lo que queda en el historial de la IA (`remembered_response`). La IA ve lo que
    dijo ella y el marcador de los datos, no el mensaje con los datos. `handoff_reason` dice si el chat pasa a una persona y por qué
    (vacío si no)."""

    final_response: str
    remembered_response: str
    handoff_reason: str


def settle_payment(
    response_text: str,
    *,
    ai_metadata: dict,
    problem: dict,
    turn: TurnContext,
    memory_service: MemoryDomainService | None,
) -> PaymentOutcome:
    reading = turn.reading
    payment_method = str(ai_metadata.get("payment_method") or "").strip().lower()
    payment_status = _payment_status(ai_metadata, turn, memory_service)
    # Pasa a una persona si el asesor lo decidió (el cliente la pidió, reclama…); un pago avisado también.
    handoff_reason = str(ai_metadata.get("handoff") or "").strip() or ("payment_review" if payment_status == REPORTED else "")

    delivery = None
    if payment_status == REPORTED:
        _log_payment_override(turn, payment_method=payment_method, payment_status=payment_status)
        response_text = _post_payment_message(turn.runtime_yaml) or response_text
    else:
        delivery = deliver(
            response_text,
            turn.runtime_yaml,
            send_payment=str(ai_metadata.get("send_payment") or "").strip().lower(),
            # Si después de pedirle otra respuesta el asesor insiste en enviar unos datos que el cliente no pidió, no salen: con
            # varios medios, los datos salen cuando el lector entiende que el cliente debe recibirlos.
            hold=bool(problem.get("unrequested") or problem.get("repeated")),
            payment_method=payment_method,
            asked=reading.wants_details if reading is not None else None,
            asked_method=reading.method if reading is not None else "",
            state=turn.op_before,
            remembered=turn.remembered_method,
            tenant=turn.tenant_slug,
        )
        if delivery.method:
            _remember_sent_method(delivery, turn, memory_service)
            _log_payment_override(turn, payment_method=delivery.method, payment_status=payment_status)
        response_text = delivery.text

    remembered = response_text
    if delivery is not None and delivery.details:
        remembered = remembered_message(delivery, turn.runtime_yaml)
    return PaymentOutcome(
        final_response=_final_text(response_text, delivery, turn),
        remembered_response=remembered,
        handoff_reason=handoff_reason,
    )


def _payment_status(ai_metadata: dict, turn: TurnContext, memory_service: MemoryDomainService | None) -> str:
    """El estado del pago en este turno. Si el lector y el asesor no coinciden en que el cliente avisó un pago, manda el lector y se
    corrige en la memoria."""
    status = str(ai_metadata.get("payment_status") or "").strip().lower()
    reading = turn.reading
    before = str(turn.memory_context.get("estado_pago") or "").strip().lower()
    already_reported = before == REPORTED
    corrected = None
    if reading is not None and reading.says_paid and status != REPORTED:
        corrected = REPORTED
    elif reading is not None and not reading.says_paid and status == REPORTED and not already_reported:
        corrected = ""
    if corrected is None:
        return status
    set_status = getattr(memory_service, "set_payment_status", None)
    if callable(set_status):
        # Si el asesor marcó un pago que el cliente no avisó, el estado vuelve a ser el de antes: un pago ya confirmado sigue confirmado.
        set_status(tenant_slug=turn.tenant_slug, user_id=turn.user_id, status=corrected or (before if before == CONFIRMED else "none"))
    return corrected


def remember_confirmed_payment(memory_service: MemoryDomainService, *, tenant_slug: str, user_id: str) -> None:
    """El equipo confirmó el pago del cliente (desde el chat del panel): la IA lo sabe, ya no le dice que el equipo lo está verificando
    y el paso «falta que pague y envíe el comprobante» termina. Una sola escritura en la memoria. Si la memoria no lo guardó (la base
    no respondió: el motor sigue sin avisar), lanza `RuntimeError`, para que el panel se lo diga al equipo."""
    with memory_service.turn(tenant_slug=tenant_slug, user_id=user_id):
        memory_service.set_payment_status(tenant_slug=tenant_slug, user_id=user_id, status=CONFIRMED)
        method = memory_service.get_payment_method(tenant_slug=tenant_slug, user_id=user_id)
        memory_service.set_op_state(tenant_slug=tenant_slug, user_id=user_id, state_dict=confirmed_state(method).to_dict())
    if memory_service.get_payment_status(tenant_slug=tenant_slug, user_id=user_id) != CONFIRMED:
        raise RuntimeError("la memoria del asistente no guardó el pago confirmado")


def _remember_sent_method(delivery: PaymentDelivery, turn: TurnContext, memory_service: MemoryDomainService | None) -> None:
    """El medio cuyos datos salieron queda anotado, así la IA sabe de cuál habla el cliente más adelante. El paso de la conversación
    pasa a «falta que pague y envíe el comprobante». Si no salieron datos, queda el paso que había, que vence solo
    (`PAYMENT_STATE_HOURS`)."""
    set_method = getattr(memory_service, "set_payment_method", None)
    if callable(set_method):
        set_method(tenant_slug=turn.tenant_slug, user_id=turn.user_id, method=delivery.method)
    set_op = getattr(memory_service, "set_op_state", None)
    if callable(set_op):
        try:
            set_op(tenant_slug=turn.tenant_slug, user_id=turn.user_id, state_dict=sent_state(delivery.method).to_dict())
        except Exception:
            pass


def _final_text(response_text: str, delivery: PaymentDelivery | None, turn: TurnContext) -> str:
    if delivery is not None and delivery.method:
        lead = enforce_max_words(delivery.lead, turn.max_words, tenant=turn.tenant_slug, user_id=turn.user_id) if delivery.lead.strip() else ""
        return compose(lead, delivery.details, delivery.tail) if delivery.details else response_text
    return enforce_max_words(response_text, turn.max_words, tenant=turn.tenant_slug, user_id=turn.user_id)


def _post_payment_message(runtime_yaml: dict) -> str:
    """El mensaje que el negocio eligió para cuando el cliente avisa que ya pagó, o "" si no eligió uno."""
    config = runtime_yaml.get("config") if isinstance(runtime_yaml.get("config"), dict) else {}
    post_payment = config.get("post_payment") if isinstance(config.get("post_payment"), dict) else {}
    on_user_report = post_payment.get("on_user_report") if isinstance(post_payment.get("on_user_report"), dict) else {}
    return str(on_user_report.get("message") or "").strip()


def _log_payment_override(turn: TurnContext, *, payment_method: str, payment_status: str) -> None:
    logger.info(
        {
            "event": "backend_payment_override",
            "tenant": str(turn.tenant_slug or "").strip().lower(),
            "user_id": str(turn.user_id or "").strip().lower(),
            "payment_method": str(payment_method or "").strip().lower(),
            "payment_status": str(payment_status or "").strip().lower(),
        }
    )
