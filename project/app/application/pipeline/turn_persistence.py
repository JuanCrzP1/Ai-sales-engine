"""Lo que queda en la memoria del cliente después de un turno (`ai_execution.py`).

- `save_ai_metadata`: lo que decidió el asesor en su respuesta (intención, etapa, interés o problema del cliente, medio y estado del
  pago). Así lo sabe en el siguiente mensaje (`turn_context.build_memory_context`).
- `save_customer_data`: los datos que el cliente dio en este mensaje (su nombre, su negocio, que dio el teléfono), junto a los que ya
  había dado. El asesor los ve en cada mensaje y no se los vuelve a pedir (`domain/conversation/customer_data.py`).
- `save_final_response`: lo que respondió, como lo ve la IA en su historial (con el marcador de los datos de pago, nunca los datos).
"""
from __future__ import annotations

from app.domain.business_config.payment_data import redact_payment_values
from app.domain.conversation import customer_data
from app.domain.conversation.memory import ConversationState, MemoryDomainService
from app.utils.logger import logger

# Cuántos intereses o problemas del cliente se recuerdan.
PAIN_TIMELINE_LIMIT = 20


def save_ai_metadata(
    memory_service: MemoryDomainService | None,
    *,
    tenant_slug: str,
    user_id: str,
    metadata: dict,
) -> None:
    if memory_service is None or not isinstance(metadata, dict):
        return

    intent = str(metadata.get("intent") or "").strip().lower()
    stage = str(metadata.get("stage") or "").strip().lower()
    urgency = str(metadata.get("urgency") or "").strip().lower()
    last_cta = str(metadata.get("last_cta") or "").strip()
    pain_text = str(metadata.get("pain") or "").strip()

    pain_detected = bool(metadata.get("pain_detected", False) or pain_text)
    has_objection_count = metadata.get("objection_count") is not None
    try:
        objection_count = max(0, int(metadata.get("objection_count") or 0))
    except (TypeError, ValueError):
        objection_count = 0

    if intent:
        memory_service.set_last_intent(tenant_slug=tenant_slug, user_id=user_id, intent=intent)
    if stage:
        memory_service.set_stage(tenant_slug=tenant_slug, user_id=user_id, stage=stage)
    memory_service.set_last_pain(tenant_slug=tenant_slug, user_id=user_id, pain=pain_text)

    mode = str(metadata.get("mode") or "").strip().lower()
    if mode:
        memory_service.set_mode(tenant_slug=tenant_slug, user_id=user_id, mode=mode)
    if intent:
        memory_service.set_detected_intent(tenant_slug=tenant_slug, user_id=user_id, intent=intent)

    payment_method = str(metadata.get("payment_method") or "").strip().lower()
    if payment_method:
        memory_service.set_payment_method(tenant_slug=tenant_slug, user_id=user_id, method=payment_method)

    payment_status = str(metadata.get("payment_status") or "").strip().lower()
    if payment_status:
        memory_service.set_payment_status(tenant_slug=tenant_slug, user_id=user_id, status=payment_status)
    elif not memory_service.get_payment_status(tenant_slug=tenant_slug, user_id=user_id):
        memory_service.set_payment_status(tenant_slug=tenant_slug, user_id=user_id, status="none")

    previous_state = memory_service.get_conversation_state(tenant_slug=tenant_slug, user_id=user_id)
    prior_timeline = list(getattr(previous_state, "pain_timeline", None) or [])
    if pain_text:
        prior_timeline.append(pain_text)

    state = ConversationState(
        pain_detected=bool(pain_detected or getattr(previous_state, "pain_detected", False)),
        pain_timeline=[str(item).strip() for item in prior_timeline if str(item).strip()][-PAIN_TIMELINE_LIMIT:],
        urgency=urgency or str(getattr(previous_state, "urgency", "") or "").strip().lower(),
        last_intent=intent or str(getattr(previous_state, "last_intent", "") or "").strip().lower(),
        stage=stage or str(getattr(previous_state, "stage", "") or "").strip().lower(),
        objections=objection_count if has_objection_count else max(0, int(getattr(previous_state, "objections", 0) or 0)),
        last_cta=last_cta or str(getattr(previous_state, "last_cta", "") or "").strip(),
    )
    memory_service.set_conversation_state(tenant_slug=tenant_slug, user_id=user_id, state=state)


def save_customer_data(
    memory_service: MemoryDomainService | None,
    *,
    tenant_slug: str,
    user_id: str,
    metadata: dict,
    runtime_yaml: dict,
) -> None:
    """Suma a la memoria los datos que el asesor anotó en este mensaje (`metadata.customer_data`). Nunca guarda datos de pago del
    negocio ni el valor de un dato de contacto; el registro solo dice qué datos dio, nunca cuáles son."""
    raw = metadata.get("customer_data") if isinstance(metadata, dict) else None
    if memory_service is None or not isinstance(raw, dict) or not raw:
        return
    get_data = getattr(memory_service, "get_customer_data", None)
    set_data = getattr(memory_service, "set_customer_data", None)
    if not callable(get_data) or not callable(set_data):
        return
    # Primero, los datos de contacto quedan como «dado»; después, un valor que lleva un dato de pago del negocio no se guarda.
    given = {name: value for name, value in customer_data.tidy(raw).items() if redact_payment_values(value, runtime_yaml) == value}
    if not given:
        return
    known = get_data(tenant_slug=tenant_slug, user_id=user_id)
    merged = customer_data.merge(known, given)
    if merged != known:
        set_data(tenant_slug=tenant_slug, user_id=user_id, data=merged)
        logger.info("datos_del_cliente", extra={"tenant": tenant_slug, "datos": sorted(merged)})


def save_final_response(
    memory_service: MemoryDomainService | None,
    *,
    tenant_slug: str,
    user_id: str,
    response: str,
    intent: str,
) -> None:
    text = str(response or "").strip()
    if memory_service is None or not text:
        return

    set_last_response = getattr(memory_service, "set_last_response", None)
    if callable(set_last_response):
        try:
            set_last_response(tenant_slug=tenant_slug, user_id=user_id, response=text)
        except Exception:
            return

    save_message = getattr(memory_service, "save_message", None)
    if callable(save_message):
        try:
            save_message(tenant_slug=tenant_slug, user_id=user_id, message_text=text, role="assistant")
        except Exception:
            pass

    _save_last_intent(memory_service, tenant_slug=tenant_slug, user_id=user_id, intent=intent)


def _save_last_intent(memory_service: MemoryDomainService, *, tenant_slug: str, user_id: str, intent: str) -> None:
    """La intención de esta respuesta en el estado de la conversación; lo demás del estado queda como estaba."""
    get_state = getattr(memory_service, "get_conversation_state", None)
    set_state = getattr(memory_service, "set_conversation_state", None)
    if not callable(get_state) or not callable(set_state):
        return

    try:
        previous_state = get_state(tenant_slug=tenant_slug, user_id=user_id)
    except Exception:
        previous_state = ConversationState()

    state = ConversationState(
        pain_detected=bool(getattr(previous_state, "pain_detected", False)),
        pain_timeline=list(getattr(previous_state, "pain_timeline", None) or []),
        urgency=str(getattr(previous_state, "urgency", "") or "medium").strip().lower() or "medium",
        last_intent=str(intent or "").strip().lower(),
        stage=str(getattr(previous_state, "stage", "") or "").strip().lower(),
        objections=max(0, int(getattr(previous_state, "objections", 0) or 0)),
        last_cta=str(getattr(previous_state, "last_cta", "") or "").strip(),
    )
    try:
        set_state(tenant_slug=tenant_slug, user_id=user_id, state=state)
    except Exception:
        return
