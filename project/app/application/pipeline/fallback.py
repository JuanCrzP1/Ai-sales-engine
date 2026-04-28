from __future__ import annotations

from app.infrastructure.config.config_service import ConfigService


FALLBACK_COMMERCIAL_MINIMO = (
    "Perfecto, sigamos por aqui. "
    "Con lo que me compartiste, avancemos con el siguiente paso para resolverlo contigo."
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _resolve_yaml_fallback(*, tenant_slug: str, runtime_yaml: dict) -> str:
    runtime_cfg = runtime_yaml.get("config") if isinstance(runtime_yaml.get("config"), dict) else {}
    runtime_settings = runtime_yaml.get("settings") if isinstance(runtime_yaml.get("settings"), dict) else {}

    direct_runtime = _text(runtime_cfg.get("fallback_message")) or _text(runtime_settings.get("fallback_message"))
    if direct_runtime:
        return direct_runtime

    nested_runtime = runtime_cfg.get("fallback") if isinstance(runtime_cfg.get("fallback"), dict) else {}
    nested_runtime_text = _text(nested_runtime.get("message"))
    if nested_runtime_text:
        return nested_runtime_text

    config = ConfigService()
    tenant_settings = config.load_settings(client_id=tenant_slug) if tenant_slug else {}
    tenant_fallback = _text(tenant_settings.get("fallback_message"))
    if tenant_fallback:
        return tenant_fallback

    raw_bot_cfg = config._load_raw_section("bot_config.yaml", client_id=tenant_slug)
    bot_defaults = raw_bot_cfg.get("bot_defaults") if isinstance(raw_bot_cfg.get("bot_defaults"), dict) else {}
    prompts = raw_bot_cfg.get("prompts") if isinstance(raw_bot_cfg.get("prompts"), dict) else {}
    prompts_defaults = prompts.get("defaults") if isinstance(prompts.get("defaults"), dict) else {}

    return _text(bot_defaults.get("fallback_message")) or _text(prompts_defaults.get("fallback_message"))


def _context_anchor(*, user_message: str, runtime_yaml: dict) -> str:
    memory_context = runtime_yaml.get("memory_context") if isinstance(runtime_yaml.get("memory_context"), dict) else {}
    last_pain = _text(memory_context.get("last_pain"))
    if last_pain:
        return last_pain[:120]

    user_text = _text(user_message)
    if user_text:
        return user_text[:120]
    return ""


def build_fallback_response(user_message: str, tenant_config: dict) -> str:
    safe_tenant = tenant_config if isinstance(tenant_config, dict) else {}
    tenant_slug = _text(safe_tenant.get("tenant_slug")).lower()
    runtime_yaml = safe_tenant.get("runtime_yaml") if isinstance(safe_tenant.get("runtime_yaml"), dict) else {}

    yaml_fallback = _resolve_yaml_fallback(tenant_slug=tenant_slug, runtime_yaml=runtime_yaml)
    if yaml_fallback:
        return yaml_fallback

    anchor = _context_anchor(user_message=user_message, runtime_yaml=runtime_yaml)
    if not anchor:
        return FALLBACK_COMMERCIAL_MINIMO

    return (
        f"Perfecto, con lo que me compartiste sobre {anchor}, "
        "sigamos con el siguiente paso para resolverlo contigo."
    )
