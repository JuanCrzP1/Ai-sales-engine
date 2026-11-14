##### 🚨 CONTEXT GENERATION — CRITICAL #####
# Aquí se construye contexto conversacional real.
#
# ⚠️ IMPORTANTE:
# Este contexto DEBE llegar al prompt final.
#
# Si no se usa:
# → se pierde memoria
# → respuestas genéricas
#
# NO eliminar ni ignorar estos datos
########################################

##### 🧠 SYSTEM OVERVIEW #####
# Sistema SaaS multi-tenant AI-first de ventas conversacionales.
#
# Flujo:
# usuario -> prompt_builder -> IA -> structured_output -> respuesta
#
# La IA es responsable de:
# - entender intención
# - generar respuesta
# - ejecutar venta
#
# El código SOLO:
# - pasa contexto
# - orquesta flujo
#
################################

##### 🚨 AI-FIRST RULE #####
# ❌ PROHIBIDO:
# - lógica comercial en código
# - heurísticas por palabras
# - forzar respuestas
# - if/else por intent
#
# ✅ PERMITIDO:
# - pasar datos
# - estructurar contexto
#
################################

##### 🔁 SYSTEM FLOW #####
# 1. recibe mensaje usuario
# 2. construye prompt con contexto (YAML + historial)
# 3. IA genera respuesta
# 4. structured_output interpreta intent
# 5. se devuelve respuesta SIN modificar
#
# ⚠️ IMPORTANTE:
# aquí NO se decide nada comercial
################################

##### 🚫 NO DECISION LAYER #####
# Este módulo NO decide comportamiento comercial.
#
# ❌ NO:
# - modificar respuesta IA
# - forzar cierre
################################

##### ⚠️ ANTI-PATTERNS #####
# NO hacer:
# - if intent == "buy"
# - detectar "quiero"
# - agregar textos manuales de cierre
# - concatenar respuestas
#
# Si haces esto:
# 👉 rompes AI-first
################################
from __future__ import annotations

import json

from app.application.pipeline.fallback import build_fallback_response
from app.application.pipeline.handoff_review import UNMARKED, handoff_problem
from app.application.pipeline.payment_names import named_option, payment_terms
from app.application.pipeline.conversation_summary import refresh_summary
from app.application.pipeline.payment_reading import read_customer_message
from app.application.pipeline.response_postprocessor import enforce_max_words, without_model_artifacts
from app.application.pipeline.response_router import route_response
from app.application.pipeline.payment_delivery import (  # noqa: F401 - las pruebas usan ejecutar_pago y without_payment_placeholder desde aquí
    already_sent,
    compose,
    current_method,
    deliver,
    ejecutar_pago,
    keeps_handoff,
    METHOD_AVAILABLE,
    OFFER_DETAILS,
    payment_problem,
    remembered_message,
    sent_label,
    sent_state,
    without_payment_placeholder,
)
from app.domain.business_config.payment_data import mask_invented_numbers, mask_own_markers, redact_payment_values
from app.domain.conversation.memory import ConversationState, MemoryDomainService
from app.domain.memory.observability.audit import emit_memory_audit
from app.domain.memory.salience.selector import select as select_commercial_memory
from app.domain.operations.operational_renderer import render_op_anchor, render_op_rule
from app.domain.operations.operational_state import OperationalState
from app.utils.logger import logger


def validate_runtime_yaml(runtime_yaml: dict) -> None:
    required = ["sales", "business", "pricing", "inventory", "config"]
    payload = runtime_yaml if isinstance(runtime_yaml, dict) else {}
    for key in required:
        value = payload.get(key)
        if not isinstance(value, dict):
            raise RuntimeError(f"{key} not loaded in runtime")


def _safe_history(memory_service: MemoryDomainService | None, *, tenant_slug: str, user_id: str) -> list[dict]:
    if memory_service is None:
        return []
    try:
        history = memory_service.get_history(tenant_slug=tenant_slug, user_id=user_id)
    except Exception:
        return []
    return history if isinstance(history, list) else []


def _resolve_post_payment_message(runtime_yaml: dict) -> str:
    config = runtime_yaml.get("config") if isinstance(runtime_yaml.get("config"), dict) else {}
    post_payment = config.get("post_payment") if isinstance(config.get("post_payment"), dict) else {}
    on_user_report = post_payment.get("on_user_report") if isinstance(post_payment.get("on_user_report"), dict) else {}
    return str(on_user_report.get("message") or "").strip()


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


def _known_to_the_ai(runtime_yaml: dict, user_message: str) -> str:
    """Todo lo que la IA leyó para responder (el negocio, la memoria y la conversación), en un solo texto: sirve para saber si un
    número que escribió lo leyó en alguna parte o lo inventó. Sin los datos de pago: la IA nunca los ve. (Con ellos, un número
    inventado que coincidía con parte de una cuenta real, «123456789» de «1234567890», pasaba como leído; 13 nov 2026.)"""
    try:
        read = f"{json.dumps(runtime_yaml, ensure_ascii=False, default=str)} {user_message}"
    except (TypeError, ValueError):
        read = user_message
    return redact_payment_values(read, runtime_yaml)


def _remembered_payment_method(memory_service: MemoryDomainService | None, *, tenant_slug: str, user_id: str) -> str:
    """El medio que el cliente ya eligió en esta conversación (lo guarda la memoria), o ""."""
    get_method = getattr(memory_service, "get_payment_method", None)
    if not callable(get_method):
        return ""
    try:
        return str(get_method(tenant_slug=tenant_slug, user_id=user_id) or "").strip()
    except Exception:
        return ""


def _build_memory_context(memory_service: MemoryDomainService | None, *, tenant_slug: str, user_id: str) -> dict:
    if memory_service is None:
        return {}

    history = _safe_history(memory_service, tenant_slug=tenant_slug, user_id=user_id)
    prior_history = history[:-1] if len(history) > 1 else history
    last_message = ""
    if prior_history:
        # Buscar el último mensaje del usuario (no del asistente)
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

    # Conectar sales_memory_usage → sales_memory_hint para que llegue al prompt.
    # build_sales_memory_usage() ya genera el anchor comercial natural ("eso que me dijiste de que...").
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
        # pain_timeline: full list of detected pains across the conversation
        # Required by CommercialMemorySelector for multi-pain scoring
        "pain_timeline": list(getattr(conversation_state, "pain_timeline", None) or []),
    }

    # Operational continuity: read persisted state, render human anchor for next turn.
    _get_op = getattr(memory_service, "get_op_state", None)
    if callable(_get_op):
        try:
            _op_dict = _get_op(tenant_slug=tenant_slug, user_id=user_id)
            _op_state = OperationalState.from_dict(_op_dict) if _op_dict else OperationalState()
            _anchor = render_op_anchor(_op_state)
            _rule = render_op_rule(_op_state)
            if _anchor:
                result["operational_anchor"] = _anchor
                result["operational_rule"] = _rule
        except Exception:
            pass

    return result


def _persist_conversation_state(
    memory_service: MemoryDomainService | None,
    *,
    tenant_slug: str,
    user_id: str,
    intent: str,
) -> None:
    if memory_service is None:
        return

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


def _persist_final_response(
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

    # Guardar respuesta IA en historial estructurado (5C)
    save_msg = getattr(memory_service, "save_message", None)
    if callable(save_msg):
        try:
            save_msg(tenant_slug=tenant_slug, user_id=user_id, message_text=text, role="assistant")
        except Exception:
            pass

    _persist_conversation_state(
        memory_service,
        tenant_slug=tenant_slug,
        user_id=user_id,
        intent=intent,
    )


def _persist_ai_metadata(
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

    detected_intent = str(metadata.get("intent") or "").strip().lower()

    if detected_intent:
        memory_service.set_detected_intent(tenant_slug=tenant_slug, user_id=user_id, intent=detected_intent)

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
        pain_timeline=[str(item).strip() for item in prior_timeline if str(item).strip()][-20:],
        urgency=urgency or str(getattr(previous_state, "urgency", "") or "").strip().lower(),
        last_intent=intent or str(getattr(previous_state, "last_intent", "") or "").strip().lower(),
        stage=stage or str(getattr(previous_state, "stage", "") or "").strip().lower(),
        objections=objection_count if has_objection_count else max(0, int(getattr(previous_state, "objections", 0) or 0)),
        last_cta=last_cta or str(getattr(previous_state, "last_cta", "") or "").strip(),
    )
    memory_service.set_conversation_state(tenant_slug=tenant_slug, user_id=user_id, state=state)


def _log_payment_override(*, tenant_slug: str, user_id: str, payment_method: str, payment_status: str) -> None:
    logger.info(
        {
            "event": "backend_payment_override",
            "tenant": str(tenant_slug or "").strip().lower(),
            "user_id": str(user_id or "").strip().lower(),
            "payment_method": str(payment_method or "").strip().lower(),
            "payment_status": str(payment_status or "").strip().lower(),
        }
    )


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
        tenant_slug_value = str(tenant_slug or "").strip().lower() or str(getattr(tenant, "slug", "") or getattr(tenant, "name", "") or "").strip().lower()
        user_key = str(user_id or "").strip().lower() or "anonymous"
        tenant_config = {
            "tenant_slug": tenant_slug_value,
            "runtime_yaml": runtime_yaml if isinstance(runtime_yaml, dict) else {},
        }
        safe_runtime_yaml = runtime_yaml if isinstance(runtime_yaml, dict) else {}

        _config_section = safe_runtime_yaml.get("config") or {}
        _response_cfg = _config_section.get("response") or {}
        _response_length = str(_response_cfg.get("length") or "short").strip().lower() or "short"
        try:
            _max_words = max(20, int(_response_cfg.get("max_words") or 80))
        except (TypeError, ValueError):
            _max_words = 80
        runtime_yaml_with_memory = dict(safe_runtime_yaml)

        memory_context = _build_memory_context(memory_service, tenant_slug=tenant_slug_value, user_id=user_key)
        if memory_context:
            conv_state = str(safe_runtime_yaml.get("conversation_state") or "new").strip() or "new"
            memory_context["conversation_state"] = conv_state
            runtime_yaml_with_memory["memory_context"] = memory_context

        # Commercial Memory Salience Selection — Phase 2
        # Runs after memory_context is populated. Pure function, no side effects.
        if memory_context:
            _history_for_signal = _safe_history(memory_service, tenant_slug=tenant_slug_value, user_id=user_key)
            _last_ts = None
            try:
                _last_ts = memory_service.get_last_timestamp(tenant_slug=tenant_slug_value, user_id=user_key) if memory_service else None
            except Exception:
                _last_ts = None
            _commercial_signal = select_commercial_memory(
                memory_context=memory_context,
                history=_history_for_signal,
                current_message=user_message,
                last_timestamp=_last_ts,
            )
            runtime_yaml_with_memory["commercial_memory_signal"] = _commercial_signal
            _pricing_mode = "compact" if _commercial_signal.context_weight == "strong" else "normal"
            emit_memory_audit(
                tenant=tenant_slug_value,
                user_id=user_key,
                signal=_commercial_signal,
                pricing_mode=_pricing_mode,
            )

        runtime_yaml_with_memory["response_length"] = _response_length
        runtime_yaml_with_memory["response_max_words"] = _max_words
        # El paso de la conversación y el medio elegido antes de este mensaje (por ejemplo, «ya se le enviaron los datos de Nequi»).
        op_before = _current_op_state(memory_service, tenant_slug=tenant_slug_value, user_id=user_key)
        remembered_method = _remembered_payment_method(memory_service, tenant_slug=tenant_slug_value, user_id=user_key)

        # Lo que pasó antes en una conversación larga, resumido por la IA: el asesor ve los últimos mensajes y, resumido, lo anterior.
        _summary = refresh_summary(
            runtime,
            bot_config=bot_config,
            memory=memory_service,
            runtime_yaml=runtime_yaml_with_memory,
            tenant_slug=tenant_slug_value,
            user_id=user_key,
        ) if memory_service is not None else ""
        if _summary:
            runtime_yaml_with_memory["conversation_summary"] = _summary

        # El lector de pagos: qué pide el cliente sobre el pago en este mensaje, entendido por la IA en una llamada corta. El asesor
        # lo sabe antes de responder.
        reading = read_customer_message(
            runtime,
            bot_config=bot_config,
            runtime_yaml=runtime_yaml_with_memory,
            user_message=str(user_message or ""),
            state=op_before,
            remembered=remembered_method,
            tenant=tenant_slug_value,
        )
        if reading is not None:
            in_course = current_method(op_before, remembered_method, runtime_yaml_with_memory)
            runtime_yaml_with_memory["payment_reading"] = reading.for_prompt(
                runtime_yaml_with_memory, has_details=bool(in_course) and already_sent(op_before, in_course)
            )
        named_method = named_option(str(user_message or ""), runtime_yaml_with_memory)
        if named_method:
            # Un dato del negocio que viene al caso (no se interpreta qué quiere el cliente): ese medio sí lo recibe el negocio.
            runtime_yaml_with_memory["named_payment_method"] = sent_label(runtime_yaml_with_memory, named_method)

        validate_runtime_yaml(runtime_yaml_with_memory)

        def _ask_ai(runtime_yaml: dict):
            return route_response(
                runtime=runtime,
                tenant=tenant,
                bot_config=bot_config,
                user_message=user_message,
                conversation_history=conversation_history,
                faq_results=faq_results,
                runtime_yaml=runtime_yaml,
            )

        def _problem(answer: str, context) -> dict:
            """Por qué esa respuesta del asesor no puede salir así: algo falso sobre los pagos, datos que el cliente no pidió, o que le
            dice al cliente que lo pasa con el equipo sin haberlo decidido."""
            metadata = context.get("ai_metadata") if isinstance(context, dict) and isinstance(context.get("ai_metadata"), dict) else {}
            return payment_problem(
                str(answer or ""),
                runtime_yaml_with_memory,
                send_payment=str(metadata.get("send_payment") or ""),
                asked=reading.wants_details if reading is not None else None,
                state=op_before,
                remembered=remembered_method,
            ) or handoff_problem(str(answer or ""), metadata)

        response, ai_used, route_context = _ask_ai(runtime_yaml_with_memory)
        problem = _problem(response, route_context) if ai_used else {}
        if problem:
            # La respuesta decía algo falso sobre los pagos («no puedo enviarte el número», «no recibimos Nequi»), iba a enviar unos
            # datos que el cliente no pidió, o le decía al cliente que lo pasa con el equipo sin haberlo decidido. Se le pide a la IA
            # que responda otra vez, sabiendo por qué. Lo decide ella de nuevo (su mensaje, su acción, si pasa el chat a una persona);
            # el código no le escribe la respuesta.
            event = "paso_a_persona_segunda_respuesta" if UNMARKED in problem else "pago_segunda_respuesta"
            logger.warning(event, extra={"tenant": tenant_slug_value, "why": next(iter(problem))})
            second = _ask_ai({**runtime_yaml_with_memory, "answer_again": problem})
            if second[1]:
                response, ai_used, route_context = second
                problem = _problem(response, route_context)
            if UNMARKED in problem:
                # Insistió en decirle que lo pasa sin decidirlo: manda su decisión (no se pasa), y queda a la vista.
                logger.warning("paso_a_persona_sin_marcar", extra={"tenant": tenant_slug_value})

        try:
            route_meta = route_context if isinstance(route_context, dict) else {}
            route_meta = {
                **route_meta,
                "sales": runtime_yaml_with_memory.get("sales") if isinstance(runtime_yaml_with_memory.get("sales"), dict) else {},
                "business": runtime_yaml_with_memory.get("business") if isinstance(runtime_yaml_with_memory.get("business"), dict) else {},
                "pricing": runtime_yaml_with_memory.get("pricing") if isinstance(runtime_yaml_with_memory.get("pricing"), dict) else {},
                "features": runtime_yaml_with_memory.get("features") if isinstance(runtime_yaml_with_memory.get("features"), dict) else {},
                "inventory": runtime_yaml_with_memory.get("inventory") if isinstance(runtime_yaml_with_memory.get("inventory"), dict) else {},
                "channel": str(runtime_yaml_with_memory.get("channel") or route_meta.get("channel") or "unknown").strip().lower() or "unknown",
                "conversation_state": str(runtime_yaml_with_memory.get("conversation_state") or "").strip().lower(),
            }
            ai_metadata = route_meta.get("ai_metadata") if isinstance(route_meta.get("ai_metadata"), dict) else {}
            ai_metadata = {
                **ai_metadata,
                "response": str(response or ""),
                "user_message": str(user_message or ""),
            }
            intent = str(ai_metadata.get("intent") or "").strip().lower()
            route_meta = {**route_meta, "intent": intent, "ai_metadata": ai_metadata}
            _persist_ai_metadata(
                memory_service,
                tenant_slug=tenant_slug_value,
                user_id=user_key,
                metadata=ai_metadata,
            )

            response_text = without_model_artifacts(str(response or "")).strip()
            # La IA no ve los datos de pago: un celular o una cuenta que escribe sin haberlo leído es inventado, y a veces escribe su
            # propio marcador («[número de Nequi]»). Se cambian por el marcador del dato y el sistema pone el real.
            checked_text = mask_invented_numbers(
                mask_own_markers(response_text),
                _known_to_the_ai(runtime_yaml_with_memory, str(user_message or "")),
                payment_terms=payment_terms(runtime_yaml_with_memory),
            )
            if checked_text != response_text:
                logger.warning("pago_numero_inventado", extra={"tenant": tenant_slug_value})
                response_text = checked_text
            if problem.get("denied"):
                # Insistió en que el negocio no recibe un medio que sí tiene: esa respuesta falsa no sale; sale la verdad.
                logger.error("pago_medio_negado", extra={"tenant": tenant_slug_value})
                offer = "" if reading is not None and reading.wants_details else OFFER_DETAILS
                response_text = f"{METHOD_AVAILABLE.format(method=problem['denied'])} {offer}".strip()
            payment_method = str(ai_metadata.get("payment_method") or "").strip().lower()
            payment_status = str(ai_metadata.get("payment_status") or "").strip().lower()
            # Si el cliente avisó en este mensaje que ya pagó lo dice el lector de pagos: una pregunta enfocada acierta más que el
            # asesor, que a veces lo marca sin que el cliente lo diga o se le pasa. Un pago avisado siempre lo verifica el equipo.
            # Un pago avisado antes sigue avisado.
            already_reported = str(memory_context.get("estado_pago") or "").strip().lower() == "reportado"
            corrected = None
            if reading is not None and reading.says_paid and payment_status != "reportado":
                corrected = "reportado"
            elif reading is not None and not reading.says_paid and payment_status == "reportado" and not already_reported:
                corrected = ""
            if corrected is not None:
                payment_status = corrected
                set_status = getattr(memory_service, "set_payment_status", None)
                if callable(set_status):
                    set_status(tenant_slug=tenant_slug_value, user_id=user_key, status=payment_status or "none")
            intent = str(ai_metadata.get("intent") or "").strip().lower()
            # Pasa a una persona si el cliente la pidió o reclama; un pago reportado también: solo el equipo puede verificarlo.
            handoff_reason = str(ai_metadata.get("handoff") or "").strip() or ("payment_review" if payment_status == "reportado" else "")

            delivery = None
            if payment_status == "reportado":
                _log_payment_override(
                    tenant_slug=tenant_slug_value,
                    user_id=user_key,
                    payment_method=payment_method,
                    payment_status=payment_status,
                )
                response_text = _resolve_post_payment_message(runtime_yaml_with_memory) or response_text
            else:
                # Los datos de pago: el asesor (la IA) decide con su acción y habla; el sistema pone los datos reales debajo de su
                # mensaje (`payment_delivery.py`).
                delivery = deliver(
                    response_text,
                    runtime_yaml_with_memory,
                    send_payment=str(ai_metadata.get("send_payment") or "").strip().lower(),
                    # Si después de pedirle otra respuesta el asesor insiste en enviar unos datos que el cliente no pidió, no salen: con
                    # varios medios, los datos salen cuando el lector entiende que el cliente debe recibirlos.
                    hold=bool(problem.get("unrequested") or problem.get("repeated")),
                    payment_method=payment_method,
                    asked=reading.wants_details if reading is not None else None,
                    asked_method=reading.method if reading is not None else "",
                    state=op_before,
                    remembered=remembered_method,
                    tenant=tenant_slug_value,
                )
                if delivery.method:
                    # El medio cuyos datos salieron queda anotado: así la IA sabe de cuál habla el cliente más adelante.
                    set_method = getattr(memory_service, "set_payment_method", None)
                    if callable(set_method):
                        set_method(tenant_slug=tenant_slug_value, user_id=user_key, method=delivery.method)
                    _log_payment_override(
                        tenant_slug=tenant_slug_value,
                        user_id=user_key,
                        payment_method=delivery.method,
                        payment_status=payment_status,
                    )
                response_text = delivery.text
                if handoff_reason and not keeps_handoff(delivery):
                    handoff_reason = ""
            payment_details_sent = delivery is not None and bool(delivery.method)

            raw_response = response_text
            persisted_response = raw_response
            if delivery is not None and delivery.details:
                # En su historial la IA ve lo que dijo ella y el marcador de los datos, no el mensaje con los datos.
                persisted_response = remembered_message(delivery, runtime_yaml_with_memory)

            # El paso de la conversación sale de hechos, no de palabras: el sistema entregó los datos de ese medio, así que falta que
            # el cliente pague y envíe el comprobante. Si no, queda el paso que había (vence solo, `PAYMENT_STATE_HOURS`).
            _set_op = getattr(memory_service, "set_op_state", None)
            if payment_details_sent and callable(_set_op):
                try:
                    _set_op(tenant_slug=tenant_slug_value, user_id=user_key, state_dict=sent_state(delivery.method).to_dict())
                except Exception:
                    pass

            if payment_details_sent:
                # El largo máximo es para lo que dice el asesor; los datos de pago van completos debajo.
                lead = enforce_max_words(delivery.lead, _max_words, tenant=tenant_slug_value, user_id=user_key) if delivery.lead.strip() else ""
                final_response = compose(lead, delivery.details, delivery.tail) if delivery.details else raw_response
            else:
                final_response = enforce_max_words(
                    raw_response,
                    _max_words,
                    tenant=tenant_slug_value,
                    user_id=user_key,
                )
            logger.info(
                {
                    "tenant": tenant_slug_value,
                    "channel": str(route_meta.get("channel") or "unknown"),
                    "intent": str(route_meta.get("intent") or "").strip().lower(),
                    "sales_loaded": bool(runtime_yaml_with_memory.get("sales")),
                    "business_loaded": bool(runtime_yaml_with_memory.get("business")),
                    "pricing_loaded": bool(runtime_yaml_with_memory.get("pricing")),
                    "inventory_loaded": bool(runtime_yaml_with_memory.get("inventory")),
                }
            )
            logger.info(
                "ai_mode_execution",
                extra={
                    "tenant": tenant_slug_value,
                    "user_id": user_key,
                    "mode": ai_metadata.get("mode") or route_meta.get("mode"),
                    "intent": ai_metadata.get("intent"),
                },
            )
            _persist_final_response(
                memory_service,
                tenant_slug=tenant_slug_value,
                user_id=user_key,
                response=persisted_response,
                intent=str(route_meta.get("intent") or "").strip().lower(),
            )
            safe_context = dict(route_meta) if isinstance(route_meta, dict) else {}
            # La conversación pasa a una persona: quien la guarda pausa la IA en ese chat y avisa al equipo del negocio.
            if handoff_reason:
                safe_context.update(handoff=True, handoff_reason=handoff_reason)
            return final_response, bool(ai_used), safe_context
        except Exception:
            fallback = build_fallback_response(user_message=user_message, tenant_config=tenant_config)
            fallback_context = route_context if isinstance(route_context, dict) else {}
            fallback_metadata = fallback_context.get("ai_metadata") if isinstance(fallback_context.get("ai_metadata"), dict) else {}
            fallback_intent = str(fallback_metadata.get("intent") or "").strip().lower()
            _persist_final_response(
                memory_service,
                tenant_slug=tenant_slug_value,
                user_id=user_key,
                response=fallback,
                intent=fallback_intent,
            )
            return fallback, False, {
                "source": "fallback_exception_execution",
                "intent": fallback_intent,
                "tenant_slug": tenant_slug_value,
            }
