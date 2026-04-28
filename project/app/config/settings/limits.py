from __future__ import annotations

from typing import Any, Dict


FEATURE_KEY_MAP = {
    "seed_default_data": "seed_default_data",
    "enable_multi_tenant": "enable_multi_tenant",
    "enable_ai_responses": "enable_ai_responses",
    "enable_rule_based_fallback": "enable_rule_based_fallback",
    "enable_intent_shortcuts": "enable_intent_shortcuts",
    "enable_faq_search": "enable_faq_search",
    "enable_human_handoff": "enable_human_handoff",
    "enable_audit_logs": "enable_audit_logs",
    "enable_audit_alerts": "enable_audit_alerts",
    "enable_simulation_endpoint": "enable_simulation_endpoint",
    "enable_webhook_processing": "enable_webhook_processing",
}

FAQ_KEY_MAP = {
    "semantic_threshold": "semantic_threshold",
    "default_limit": "faq_default_limit",
    "require_significant_overlap": "faq_require_significant_overlap",
    "merge_yaml_and_db": "faq_merge_yaml_and_db",
    "deduplicate_by_question": "faq_deduplicate_by_question",
    "exact_match_boost": "faq_exact_match_boost",
}

GROUNDING_KEY_MAP = {
    "source_guard_mode": "source_guard_mode",
    "enable_strict_grounding": "enable_strict_grounding",
    "enable_sensitive_validation": "enable_sensitive_validation",
    "enable_retry_on_unsupported_reply": "enable_retry_on_unsupported_reply",
    "block_unverified_prices": "block_unverified_prices",
    "block_unverified_locations": "block_unverified_locations",
    "block_unverified_delivery_times": "block_unverified_delivery_times",
}


def apply_limits_sections(cfg: Dict[str, Any], raw_cfg: Dict[str, Any] | None) -> None:
    source = raw_cfg if isinstance(raw_cfg, dict) else {}

    behavior_sec = source.get("behavior") if isinstance(source.get("behavior"), dict) else {}
    if not behavior_sec:
        behavior_sec = source.get("comportamiento") if isinstance(source.get("comportamiento"), dict) else {}
    for k, v in behavior_sec.items():
        if k == "umbral_similitud":
            cfg["semantic_threshold"] = v
        elif k == "contexto_conversacion":
            cfg["conversation_context_limit"] = v
        elif k == "max_message_length":
            cfg["max_message_length"] = v
        elif k in {"temperatura", "max_tokens"}:
            continue
        else:
            cfg[k] = v

    features_sec = source.get("features") if isinstance(source.get("features"), dict) else {}
    for source_key, target_key in FEATURE_KEY_MAP.items():
        if source_key in features_sec:
            cfg[target_key] = features_sec[source_key]

    conversation_sec = source.get("conversation") if isinstance(source.get("conversation"), dict) else {}
    if conversation_sec.get("history_limit") is not None:
        cfg["conversation_context_limit"] = conversation_sec["history_limit"]
    if conversation_sec.get("max_message_length") is not None:
        cfg["max_message_length"] = conversation_sec["max_message_length"]
    if conversation_sec.get("truncate_long_messages") is not None:
        cfg["truncate_long_messages"] = conversation_sec["truncate_long_messages"]
    if conversation_sec.get("ask_one_question_only") is not None:
        cfg["ask_one_question_only"] = conversation_sec["ask_one_question_only"]

    faq_policy_sec = source.get("faq_policy") if isinstance(source.get("faq_policy"), dict) else {}
    for source_key, target_key in FAQ_KEY_MAP.items():
        if source_key in faq_policy_sec:
            cfg[target_key] = faq_policy_sec[source_key]

    grounding_sec = source.get("grounding") if isinstance(source.get("grounding"), dict) else {}
    for source_key, target_key in GROUNDING_KEY_MAP.items():
        if source_key in grounding_sec:
            cfg[target_key] = grounding_sec[source_key]

    audit_sec = source.get("audit") if isinstance(source.get("audit"), dict) else {}
    if audit_sec.get("enabled") is not None:
        cfg["enable_audit_logs"] = audit_sec["enabled"]
    if audit_sec.get("alert_on_blocked_response") is not None:
        cfg["enable_audit_alerts"] = audit_sec["alert_on_blocked_response"]
    if audit_sec.get("redact_pii_in_logs") is not None:
        cfg["redact_pii_in_logs"] = audit_sec["redact_pii_in_logs"]

