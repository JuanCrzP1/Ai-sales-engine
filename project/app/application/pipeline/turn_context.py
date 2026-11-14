"""Lo que el asesor sabe antes de responder un mensaje: se arma una vez por turno, antes de llamar a la IA (`ai_execution.py`).

- La memoria del cliente (`build_memory_context`): lo último que dijo y lo que se le respondió, sus intereses, el medio de pago que
  eligió, si avisó un pago y el paso de la conversación (por ejemplo, «ya se le enviaron los datos de Nequi»).
- Lo que conviene recordarle en este mensaje (`select_commercial_memory`) y, en una conversación larga, el resumen de lo anterior
  (`conversation_summary.py`).
- Qué pide el cliente sobre el pago en este mensaje, entendido por la IA en una llamada corta (`payment_reading.py`).
- El largo de respuesta que eligió el negocio.

No decide nada comercial: reúne datos para el prompt. Si al negocio le falta una sección (`validate_runtime_yaml`), el turno no sigue.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.application.pipeline.conversation_summary import refresh_summary
from app.application.pipeline.payment_delivery import already_sent, current_method, sent_label
from app.application.pipeline.payment_names import named_option
from app.application.pipeline.payment_reading import PaymentReading, read_customer_message
from app.domain.conversation.memory import MemoryDomainService
from app.domain.memory.observability.audit import emit_memory_audit
from app.domain.memory.salience.selector import select as select_commercial_memory
from app.domain.operations.operational_renderer import render_op_anchor, render_op_rule
from app.domain.operations.operational_state import OperationalState

# Si el negocio no eligió un largo de respuesta (`engine_policy.py`).
DEFAULT_LENGTH = "short"
DEFAULT_MAX_WORDS = 80
MIN_MAX_WORDS = 20


@dataclass(frozen=True)
class TurnContext:
    """Lo que el asesor sabe en este turno. `runtime_yaml` es el del negocio con la memoria, el resumen y la lectura del pago: es lo
    que lee el prompt."""

    tenant_slug: str
    user_id: str
    runtime_yaml: dict
    memory_context: dict
    max_words: int
    # El paso de la conversación y el medio de pago elegido antes de este mensaje.
    op_before: OperationalState | None
    remembered_method: str
    # Qué pide el cliente sobre el pago en este mensaje, o None si el lector no respondió.
    reading: PaymentReading | None


def validate_runtime_yaml(runtime_yaml: dict) -> None:
    required = ["sales", "business", "pricing", "inventory", "config"]
    payload = runtime_yaml if isinstance(runtime_yaml, dict) else {}
    for key in required:
        value = payload.get(key)
        if not isinstance(value, dict):
            raise RuntimeError(f"{key} not loaded in runtime")


def prepare_turn(
    runtime,
    *,
    tenant,
    bot_config,
    user_message: str,
    runtime_yaml: dict,
    memory_service: MemoryDomainService | None,
    tenant_slug: str,
    user_id: str,
) -> TurnContext:
    slug = str(tenant_slug or "").strip().lower() or str(getattr(tenant, "slug", "") or getattr(tenant, "name", "") or "").strip().lower()
    user_key = str(user_id or "").strip().lower() or "anonymous"
    safe_runtime_yaml = runtime_yaml if isinstance(runtime_yaml, dict) else {}
    length, max_words = _response_length(safe_runtime_yaml)
    with_memory = dict(safe_runtime_yaml)

    memory_context = build_memory_context(memory_service, tenant_slug=slug, user_id=user_key)
    if memory_context:
        memory_context["conversation_state"] = str(safe_runtime_yaml.get("conversation_state") or "new").strip() or "new"
        with_memory["memory_context"] = memory_context
        # Qué de la memoria pesa en este mensaje. Función pura, sin efectos.
        signal = select_commercial_memory(
            memory_context=memory_context,
            history=_safe_history(memory_service, tenant_slug=slug, user_id=user_key),
            current_message=user_message,
            last_timestamp=_last_timestamp(memory_service, tenant_slug=slug, user_id=user_key),
        )
        with_memory["commercial_memory_signal"] = signal
        emit_memory_audit(
            tenant=slug,
            user_id=user_key,
            signal=signal,
            pricing_mode="compact" if signal.context_weight == "strong" else "normal",
        )

    with_memory["response_length"] = length
    with_memory["response_max_words"] = max_words
    op_before = _current_op_state(memory_service, tenant_slug=slug, user_id=user_key)
    remembered_method = _remembered_payment_method(memory_service, tenant_slug=slug, user_id=user_key)

    # Lo que pasó antes en una conversación larga, resumido por la IA: el asesor ve los últimos mensajes y, resumido, lo anterior.
    summary = refresh_summary(
        runtime,
        bot_config=bot_config,
        memory=memory_service,
        runtime_yaml=with_memory,
        tenant_slug=slug,
        user_id=user_key,
    ) if memory_service is not None else ""
    if summary:
        with_memory["conversation_summary"] = summary

    # El lector de pagos: qué pide el cliente sobre el pago en este mensaje, entendido por la IA en una llamada corta. El asesor lo
    # sabe antes de responder.
    reading = read_customer_message(
        runtime,
        bot_config=bot_config,
        runtime_yaml=with_memory,
        user_message=str(user_message or ""),
        state=op_before,
        remembered=remembered_method,
        tenant=slug,
    )
    if reading is not None:
        in_course = current_method(op_before, remembered_method, with_memory)
        with_memory["payment_reading"] = reading.for_prompt(with_memory, has_details=bool(in_course) and already_sent(op_before, in_course))
    named_method = named_option(str(user_message or ""), with_memory)
    if named_method:
        # Un dato del negocio que viene al caso (no se interpreta qué quiere el cliente): ese medio sí lo recibe el negocio.
        with_memory["named_payment_method"] = sent_label(with_memory, named_method)

    validate_runtime_yaml(with_memory)
    return TurnContext(
        tenant_slug=slug,
        user_id=user_key,
        runtime_yaml=with_memory,
        memory_context=memory_context,
        max_words=max_words,
        op_before=op_before,
        remembered_method=remembered_method,
        reading=reading,
    )


def _response_length(runtime_yaml: dict) -> tuple[str, int]:
    """El largo de respuesta del negocio («short», «medium»…) y su máximo de palabras."""
    response = (runtime_yaml.get("config") or {}).get("response") or {}
    length = str(response.get("length") or DEFAULT_LENGTH).strip().lower() or DEFAULT_LENGTH
    try:
        max_words = max(MIN_MAX_WORDS, int(response.get("max_words") or DEFAULT_MAX_WORDS))
    except (TypeError, ValueError):
        max_words = DEFAULT_MAX_WORDS
    return length, max_words


def _safe_history(memory_service: MemoryDomainService | None, *, tenant_slug: str, user_id: str) -> list[dict]:
    if memory_service is None:
        return []
    try:
        history = memory_service.get_history(tenant_slug=tenant_slug, user_id=user_id)
    except Exception:
        return []
    return history if isinstance(history, list) else []


def _last_timestamp(memory_service: MemoryDomainService | None, *, tenant_slug: str, user_id: str):
    try:
        return memory_service.get_last_timestamp(tenant_slug=tenant_slug, user_id=user_id) if memory_service else None
    except Exception:
        return None


def _current_op_state(memory_service: MemoryDomainService | None, *, tenant_slug: str, user_id: str) -> OperationalState | None:
    """El paso de la conversación guardado antes de este turno (por ejemplo, «ya se le enviaron los datos de Nequi»), o None."""
    get_op = getattr(memory_service, "get_op_state", None)
    if not callable(get_op):
        return None
    try:
        stored = get_op(tenant_slug=tenant_slug, user_id=user_id)
        return OperationalState.from_dict(stored) if stored else None
    except Exception:
        return None


def _remembered_payment_method(memory_service: MemoryDomainService | None, *, tenant_slug: str, user_id: str) -> str:
    """El medio que el cliente ya eligió en esta conversación (lo guarda la memoria), o ""."""
    get_method = getattr(memory_service, "get_payment_method", None)
    if not callable(get_method):
        return ""
    try:
        return str(get_method(tenant_slug=tenant_slug, user_id=user_id) or "").strip()
    except Exception:
        return ""


def build_memory_context(memory_service: MemoryDomainService | None, *, tenant_slug: str, user_id: str) -> dict:
    """Lo que la memoria sabe del cliente, como lo lee el prompt (`memory_context`). Vacío sin memoria."""
    if memory_service is None:
        return {}

    history = _safe_history(memory_service, tenant_slug=tenant_slug, user_id=user_id)
    prior_history = history[:-1] if len(history) > 1 else history
    last_message = ""
    if prior_history:
        # El último mensaje del cliente (no del asesor).
        for entry in reversed(prior_history):
            if isinstance(entry, dict):
                if entry.get("role", "user") == "user":
                    last_message = str(entry.get("text") or "").strip()
                    break
            else:
                last_message = str(entry or "").strip()
                break

    history_summary = ""
    if prior_history:
        compact_history = []
        for entry in prior_history[-10:]:
            if isinstance(entry, dict):
                role = str(entry.get("role") or "user").strip().lower() or "user"
                sample = str(entry.get("text") or "").strip()
            else:
                role = "user"
                sample = str(entry or "").strip()
            if sample:
                compact_history.append(f"{role}: {sample}")
        history_summary = "\n".join(compact_history)

    last_response = None
    get_last_response = getattr(memory_service, "get_last_response", None)
    if callable(get_last_response):
        try:
            last_response = get_last_response(tenant_slug=tenant_slug, user_id=user_id)
        except Exception:
            last_response = None

    conversation_state = memory_service.get_conversation_state(tenant_slug=tenant_slug, user_id=user_id)
    memory = {
        "last_intent": memory_service.get_last_intent(tenant_slug=tenant_slug, user_id=user_id),
        "intent_detectado": memory_service.get_detected_intent(tenant_slug=tenant_slug, user_id=user_id),
        "active_pain": memory_service.get_last_pain(tenant_slug=tenant_slug, user_id=user_id),
        "metodo_pago_elegido": memory_service.get_payment_method(tenant_slug=tenant_slug, user_id=user_id),
        "estado_pago": memory_service.get_payment_status(tenant_slug=tenant_slug, user_id=user_id) or "none",
        "stage": memory_service.get_stage(tenant_slug=tenant_slug, user_id=user_id),
        "mode": memory_service.get_mode(tenant_slug=tenant_slug, user_id=user_id),
        "next_step": getattr(conversation_state, "last_cta", None),
    }

    # La frase con la que el asesor retoma lo que el cliente contó («eso que me dijiste de que…»).
    sales_memory_hint = ""
    build_sales_memory_usage = getattr(memory_service, "build_sales_memory_usage", None)
    if callable(build_sales_memory_usage):
        try:
            sales_memory_hint = str(build_sales_memory_usage(tenant_slug=tenant_slug, user_id=user_id) or "").strip()
        except Exception:
            sales_memory_hint = ""

    result = {
        "last_message": last_message,
        "last_user_message": last_message,
        "last_response": last_response,
        "last_ai_response": last_response,
        "history_summary": history_summary,
        "sales_memory_hint": sales_memory_hint,

        "last_intent": memory.get("last_intent"),
        "intent_detectado": memory.get("intent_detectado"),
        "last_pain": memory.get("active_pain"),
        "metodo_pago_elegido": memory.get("metodo_pago_elegido"),
        "estado_pago": memory.get("estado_pago"),

        "stage": memory.get("stage"),
        "mode": memory.get("mode"),

        "last_cta": memory.get("next_step"),
        # Todos los intereses o problemas que contó el cliente: `select_commercial_memory` los pondera.
        "pain_timeline": list(getattr(conversation_state, "pain_timeline", None) or []),
    }

    # El paso de la conversación guardado, dicho para el asesor («ya le enviaste los datos de Nequi…»).
    get_op = getattr(memory_service, "get_op_state", None)
    if callable(get_op):
        try:
            stored = get_op(tenant_slug=tenant_slug, user_id=user_id)
            op_state = OperationalState.from_dict(stored) if stored else OperationalState()
            anchor = render_op_anchor(op_state)
            rule = render_op_rule(op_state)
            if anchor:
                result["operational_anchor"] = anchor
                result["operational_rule"] = rule
        except Exception:
            pass

    return result
