from __future__ import annotations

from app.application.pipeline.fallback import build_fallback_response
from app.application.pipeline.common import tenant_slug as resolve_tenant_slug
from app.utils.logger import logger

def _log_route_event(*, tenant_slug: str, source: str, ai_metadata: dict, intent: str) -> None:
    stage = str((ai_metadata or {}).get("stage") or "").strip().lower()
    next_step = str((ai_metadata or {}).get("next_step") or "").strip()
    logger.info(
        "ai_route_result",
        extra={
            "tenant": tenant_slug,
            "intent": str(intent or "").strip().lower(),
            "stage": stage,
            "next_step": next_step,
            "source": str(source or "").strip().lower(),
        },
    )


def route_response(
    *,
    runtime,
    tenant,
    bot_config,
    user_message: str,
    conversation_history: list,
    faq_results: list[dict],
    runtime_yaml: dict,
) -> tuple[str, bool, dict]:
    tenant_slug = resolve_tenant_slug(tenant)
    safe_runtime_yaml = runtime_yaml if isinstance(runtime_yaml, dict) else {}
    memory_context = safe_runtime_yaml.get("memory_context") if isinstance(safe_runtime_yaml.get("memory_context"), dict) else {}
    memory_state = memory_context if isinstance(memory_context, dict) else {}

    mode = str((safe_runtime_yaml or {}).get("mode") or "").strip().lower()

    base_context = {
        "mode": mode,
        "tenant_slug": tenant_slug,
        "memory_state": memory_state,
    }

    try:
        generated = runtime.ai_orchestrator.generate_business_reply(
            runtime,
            tenant=tenant,
            bot_config=bot_config,
            user_message=user_message,
            conversation_history=conversation_history,
            faq_results=faq_results,
            yaml_config=runtime_yaml,
        )
        ai_response = ""
        ai_used = True
        ai_metadata: dict = {}
        if isinstance(generated, tuple):
            if len(generated) >= 1:
                ai_response = str(generated[0] or "")
            if len(generated) >= 2:
                ai_used = bool(generated[1])
            if len(generated) >= 3 and isinstance(generated[2], dict):
                ai_metadata = dict(generated[2])
        else:
            ai_response = str(generated or "")

        intent_missing = bool(ai_metadata.get("intent_missing"))
        intent = ai_metadata.get("intent")
        raw = str(ai_response or "").strip()

        _log_route_event(tenant_slug=tenant_slug, source="ai_raw", ai_metadata=ai_metadata, intent=intent)
        return raw, bool(ai_used), {
            **base_context,
            "source": "ai_raw",
            "intent": intent,
            "intent_missing": intent_missing,
            "ai_metadata": ai_metadata,
        }
    except Exception:
        fallback = build_fallback_response(
            user_message=user_message,
            tenant_config={"tenant_slug": tenant_slug, "runtime_yaml": safe_runtime_yaml},
        )
        _log_route_event(tenant_slug=tenant_slug, source="fallback_exception", ai_metadata={}, intent="")
        return fallback, False, {**base_context, "source": "fallback_exception", "intent": "", "ai_metadata": {}}
