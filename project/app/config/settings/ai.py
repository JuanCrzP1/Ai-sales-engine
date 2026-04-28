from __future__ import annotations

from typing import Any, Dict


def apply_ai_section(cfg: Dict[str, Any], llm_sec: Dict[str, Any] | None) -> None:
    section = llm_sec if isinstance(llm_sec, dict) else {}
    provider = section.get("provider") or section.get("proveedor")
    if provider:
        cfg["llm_provider"] = provider

    timeout_value = section.get("request_timeout_seconds") or section.get("timeout_seconds")
    if timeout_value is not None:
        cfg["llm_timeout_seconds"] = timeout_value

    provider_fallback = section.get("allow_provider_fallback")
    if provider_fallback is not None:
        cfg["allow_provider_fallback"] = provider_fallback

    openrouter = section.get("openrouter") if isinstance(section.get("openrouter"), dict) else {}
    if openrouter:
        cfg["openrouter_base_url"] = openrouter.get("base_url", cfg.get("openrouter_base_url"))
        cfg["openrouter_model"] = (
            openrouter.get("default_model")
            or openrouter.get("modelo_por_defecto")
            or cfg.get("openrouter_model")
        )
        cfg["openrouter_advanced_model"] = (
            openrouter.get("advanced_model")
            or openrouter.get("modelo_avanzado")
            or cfg.get("openrouter_advanced_model")
        )

    if "embedding_model" in section or "modelo_embeddings" in section:
        cfg["embedding_model"] = section.get("embedding_model") or section.get("modelo_embeddings")
