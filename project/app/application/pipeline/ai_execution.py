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

from app.application.pipeline.fallback import build_fallback_response
from app.application.pipeline.response_postprocessor import enforce_max_words
from app.application.pipeline.response_router import route_response
from app.domain.conversation.demo import DemoDomainService
from app.domain.conversation.memory import ConversationState, MemoryDomainService
from app.domain.memory.observability.audit import emit_memory_audit
from app.domain.memory.salience.selector import select as select_commercial_memory
from app.domain.operations.operational_extractor import extract_op_state
from app.domain.operations.operational_renderer import render_op_anchor, render_op_rule
from app.domain.operations.operational_state import OperationalState
from app.utils.logger import logger


FRAME_BLOCK = """
MODO DE RESPUESTA:

Responde como alguien que vende por chat.

NO respondas como inventario.

Habla en términos de oferta o solución,
no en listas de ítems.

Cuando expliques:
- sé directo
- muéstrale para qué le sirve
- avanza la conversación

Si preguntan por precio, di cuánto es, qué trae, qué no trae, y llevalo a elegir o decidir.

Siempre deja la conversación abierta con una pregunta concreta.

Puedes usar ejemplos concretos.
Habla como si estuvieras explicándole a un cliente real.
Evita frases genéricas de cierre.

Si ya existe contexto de pago en memoria, trátalo como continuidad del mismo proceso.
Si el usuario elige un método de pago, mantén intent=buy e incluye payment_method en la metadata.
Si el usuario reporta que ya pagó, mantén intent=buy e incluye payment_status=reportado en la metadata.
No reinicies el flujo ni vuelvas a ofrecer el método de pago si el usuario ya reportó el pago.
""".strip()

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


def _iter_payment_blocks(pricing: dict) -> list[dict]:
    blocks: list[dict] = []
    plans = pricing.get("plans") if isinstance(pricing.get("plans"), list) else []
    for plan in plans:
        if not isinstance(plan, dict):
            continue
        payment = plan.get("payment") if isinstance(plan.get("payment"), dict) else {}
        if payment:
            blocks.append(payment)

    catalog = pricing.get("catalog") if isinstance(pricing.get("catalog"), dict) else {}
    catalog_payment = catalog.get("payment") if isinstance(catalog.get("payment"), dict) else {}
    if catalog_payment:
        blocks.append(catalog_payment)

    root_payment = pricing.get("payment") if isinstance(pricing.get("payment"), dict) else {}
    if root_payment:
        blocks.append(root_payment)

    return blocks


def _resolve_post_payment_message(runtime_yaml: dict) -> str:
    config = runtime_yaml.get("config") if isinstance(runtime_yaml.get("config"), dict) else {}
    post_payment = config.get("post_payment") if isinstance(config.get("post_payment"), dict) else {}
    on_user_report = post_payment.get("on_user_report") if isinstance(post_payment.get("on_user_report"), dict) else {}
    return str(on_user_report.get("message") or "").strip()


def ejecutar_pago(runtime_yaml: dict, payment_method: str) -> str:
    method = str(payment_method or "").strip().lower()
    if not method:
        return ""

    pricing = runtime_yaml.get("pricing") if isinstance(runtime_yaml.get("pricing"), dict) else {}
    payment_blocks = _iter_payment_blocks(pricing)
    payment_links: list[str] = []
    transfer_methods: dict[str, dict] = {}

    for payment in payment_blocks:
        link = str(payment.get("link") or "").strip()
        if link and link not in payment_links:
            payment_links.append(link)

        transfer = payment.get("transfer") if isinstance(payment.get("transfer"), dict) else {}
        if not bool(transfer.get("enabled", False)):
            continue
        methods = transfer.get("methods") if isinstance(transfer.get("methods"), list) else []
        for item in methods:
            if not isinstance(item, dict):
                continue
            item_type = str(item.get("type") or "").strip().lower()
            if item_type and item_type not in transfer_methods:
                transfer_methods[item_type] = dict(item)

    if method == "link":
        if payment_links:
            return f"Avanzamos con el siguiente paso. Puedes pagar aquí: {payment_links[0]}"
        return ""

    selected = transfer_methods.get(method) if isinstance(transfer_methods.get(method), dict) else {}
    if not selected:
        return ""

    if method in {"nequi", "daviplata"}:
        number = str(selected.get("number") or "").strip()
        if number:
            return f"Avanzamos con el siguiente paso. Puedes hacer la transferencia a {method} usando el número {number}. Cuando lo hagas, avísame para continuar."
        return ""

    if method == "bank":
        bank = str(selected.get("bank") or "").strip()
        account_type = str(selected.get("account_type") or "").strip()
        account_number = str(selected.get("account_number") or "").strip()
        if bank and account_type and account_number:
            return (
                "Avanzamos con el siguiente paso. "
                f"Puedes hacer la transferencia a {bank}, cuenta {account_type} {account_number}. "
                "Cuando lo hagas, avísame para continuar."
            )
        return ""

    if method == "breb":
        reference = str(selected.get("reference") or "").strip()
        if reference:
            return f"Avanzamos con el siguiente paso. Puedes hacer la transferencia Bre-B con la referencia {reference}. Cuando lo hagas, avísame para continuar."
        return ""

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


def _get_configured_payment_methods(runtime_yaml: dict) -> list[str]:
    """Extract the list of payment method types configured for this tenant.

    Reads pricing.plans[*].payment.transfer.methods and
    pricing.catalog.payment.transfer.methods.
    Returns only method type strings (e.g. ["nequi", "bank"]).
    """
    pricing = runtime_yaml.get("pricing") if isinstance(runtime_yaml.get("pricing"), dict) else {}
    seen: set[str] = set()
    result: list[str] = []

    candidate_lists: list[list] = []
    plans = pricing.get("plans") if isinstance(pricing.get("plans"), list) else []
    for plan in plans:
        if not isinstance(plan, dict):
            continue
        try:
            methods = plan["payment"]["transfer"]["methods"]
            if isinstance(methods, list):
                candidate_lists.append(methods)
        except (KeyError, TypeError):
            pass

    catalog = pricing.get("catalog") if isinstance(pricing.get("catalog"), dict) else {}
    try:
        methods = catalog["payment"]["transfer"]["methods"]
        if isinstance(methods, list):
            candidate_lists.append(methods)
    except (KeyError, TypeError):
        pass

    for method_list in candidate_lists:
        for m in method_list:
            if not isinstance(m, dict):
                continue
            t = str(m.get("type") or "").strip().lower()
            if t and t not in seen:
                seen.add(t)
                result.append(t)
    return result


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
        demo_service: DemoDomainService | None = None,
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

        demo_active = bool(runtime_yaml_with_memory.get("demo_input"))
        del demo_service
        runtime_yaml_with_memory["demo_active"] = demo_active

        runtime_yaml_with_memory["response_length"] = _response_length
        runtime_yaml_with_memory["response_max_words"] = _max_words

        validate_runtime_yaml(runtime_yaml_with_memory)

        original_generate = runtime.generate

        def _generate_with_frame(prompt: str, *, user_message: str, bot_config=None):
            framed_prompt = f"{FRAME_BLOCK}\n\n{str(prompt or '').strip()}".strip()
            return original_generate(framed_prompt, user_message=user_message, bot_config=bot_config)

        runtime.generate = _generate_with_frame
        try:
            response, ai_used, route_context = route_response(
                runtime=runtime,
                tenant=tenant,
                bot_config=bot_config,
                user_message=user_message,
                conversation_history=conversation_history,
                faq_results=faq_results,
                runtime_yaml=runtime_yaml_with_memory,
            )
        finally:
            runtime.generate = original_generate

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

            response_text = str(response or "").strip()
            payment_method = str(ai_metadata.get("payment_method") or "").strip().lower()
            payment_status = str(ai_metadata.get("payment_status") or "").strip().lower()
            intent = str(ai_metadata.get("intent") or "").strip().lower()

            if payment_status == "reportado":
                _log_payment_override(
                    tenant_slug=tenant_slug_value,
                    user_id=user_key,
                    payment_method=payment_method,
                    payment_status=payment_status,
                )
                response_text = _resolve_post_payment_message(runtime_yaml_with_memory) or response_text
            elif payment_method and intent == "buy":
                _log_payment_override(
                    tenant_slug=tenant_slug_value,
                    user_id=user_key,
                    payment_method=payment_method,
                    payment_status=payment_status,
                )
                response_text = ejecutar_pago(runtime_yaml_with_memory, payment_method) or response_text

            raw_response = response_text
            persisted_response = raw_response

            # Operational continuity — persist state extracted from response text.
            _route_source = str(route_context.get("source") if isinstance(route_context, dict) else "").strip()
            _configured_methods = _get_configured_payment_methods(runtime_yaml_with_memory)
            _new_op_state = extract_op_state(raw_response, route_source=_route_source, payment_methods=_configured_methods)
            _set_op = getattr(memory_service, "set_op_state", None)
            if callable(_set_op) and _new_op_state.active_process:
                try:
                    _set_op(tenant_slug=tenant_slug_value, user_id=user_key, state_dict=_new_op_state.to_dict())
                except Exception:
                    pass

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
            safe_context = route_meta if isinstance(route_meta, dict) else {}
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
