from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .ai import apply_ai_section
from .connectors import apply_connectors_section
from .limits import apply_limits_sections


BASE_DIR = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_DIR = BASE_DIR / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
TENANTS_CONFIG_DIR = CONFIG_DIR / "tenants"
CHANNELS_CONFIG_DIR = CONFIG_DIR / "channels"
ASSETS_CONFIG_DIR = CONFIG_DIR / "assets"
SYSTEM_CONFIG_DIR = CONFIG_DIR / "system"
ACTIVE_TENANT_SLUG = (os.getenv("ACTIVE_TENANT_SLUG") or "asesor_ai_prod").strip() or "asesor_ai_prod"
DEFAULT_TENANT_SLUG = (os.getenv("TENANT_SLUG") or ACTIVE_TENANT_SLUG).strip() or ACTIVE_TENANT_SLUG
AI_FIRST_STRICT = True
AI_FIRST_HARD_MODE = True


def _resolve_env_file_path() -> Path | None:
    candidates = (
        WORKSPACE_ROOT / ".env",
        BASE_DIR / ".env",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


ACTIVE_ENV_FILE = _resolve_env_file_path()
if ACTIVE_ENV_FILE is not None:
    load_dotenv(dotenv_path=ACTIVE_ENV_FILE, override=False)


def _yaml_module():
    return importlib.import_module("yaml")


def _read_yaml_file(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        yaml = _yaml_module()
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _deep_merge_dicts(base: Dict, override: Dict) -> Dict:
    merged = dict(base or {})
    for key, value in (override or {}).items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = _deep_merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def _read_env_file_values(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    values: Dict[str, str] = {}
    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if not key:
                continue
            values[key] = value.strip().strip('"').strip("'")
    except Exception:
        return {}
    return values


def _tenant_slug(tenant_id: str | None = None) -> str:
    return str(tenant_id or DEFAULT_TENANT_SLUG).strip() or DEFAULT_TENANT_SLUG


def _resolve_config_path(name: str, tenant_id: str | None = None) -> Path:
    tenant_slug = _tenant_slug(tenant_id)
    tenant_bot_config = TENANTS_CONFIG_DIR / tenant_slug / "bot_config.yaml"
    if name == "bot_config.yaml" and tenant_bot_config.exists():
        return tenant_bot_config
    mapped_paths = {
        "media.yaml": ASSETS_CONFIG_DIR / "media.yaml",
        "channels.yaml": CHANNELS_CONFIG_DIR / "channels.yaml",
        "bot_config.yaml": SYSTEM_CONFIG_DIR / "bot_config.yaml",
        "settings.yaml": SYSTEM_CONFIG_DIR / "settings.yaml",
        "secrets.yaml": SYSTEM_CONFIG_DIR / "secrets.yaml",
        "conversation_stage.yaml": SYSTEM_CONFIG_DIR / "conversation_stage.yaml",
        "business.yaml": TENANTS_CONFIG_DIR / tenant_slug / "business.yaml",
        "offer.yaml": TENANTS_CONFIG_DIR / tenant_slug / "offer.yaml",
        "pricing.yaml": TENANTS_CONFIG_DIR / tenant_slug / "pricing.yaml",
        "responses.yaml": TENANTS_CONFIG_DIR / tenant_slug / "responses.yaml",
        "objections.yaml": TENANTS_CONFIG_DIR / tenant_slug / "objections.yaml",
        "personality.yaml": TENANTS_CONFIG_DIR / tenant_slug / "personality.yaml",
    }
    return mapped_paths.get(name, CONFIG_DIR / name)


def _load_unified_tenant_section(name: str, tenant_id: str | None = None) -> Dict[str, Any]:
    tenant_slug = _tenant_slug(tenant_id)
    tenant_root = TENANTS_CONFIG_DIR / tenant_slug

    if name in {"settings.yaml", "personality.yaml"}:
        config_yaml_path = tenant_root / "config.yaml"
        if config_yaml_path.exists():
            payload = _read_yaml_file(config_yaml_path)
            section_name = "settings" if name == "settings.yaml" else "personality"
            section_value = payload.get(section_name)
            if isinstance(section_value, dict):
                if name == "personality.yaml":
                    return section_value
                return {section_name: section_value}

    sales_sections = {
        "responses.yaml": "responses",
        "objections.yaml": "objections",
        "offer.yaml": "offer",
        "closing.yaml": "closing",
    }
    section_name = sales_sections.get(name)
    if section_name:
        sales_yaml_path = tenant_root / "sales.yaml"
        if sales_yaml_path.exists():
            payload = _read_yaml_file(sales_yaml_path)
            section_value = payload.get(section_name)
            if isinstance(section_value, dict) and section_name in section_value:
                return section_value
            if section_value is not None:
                return {section_name: section_value}

    return {}


def _load_layer_file(name: str, tenant_id: str | None = None) -> Dict[str, Any]:
    if name in {"settings.yaml", "personality.yaml"}:
        unified_payload = _load_unified_tenant_section(name, tenant_id=tenant_id)
        if unified_payload:
            return unified_payload
    path = _resolve_config_path(name, tenant_id=tenant_id)
    if path.exists():
        return _read_yaml_file(path)
    return _load_unified_tenant_section(name, tenant_id=tenant_id)


_SETTINGS_RAW: Dict[str, Any] = {}


def _apply_app_section(cfg: Dict[str, Any], app_sec: dict) -> None:
    for k, v in app_sec.items():
        if k in ("name", "nombre"):
            cfg["app_name"] = v
        elif k == "version":
            cfg["app_version"] = v
        elif k == "mode":
            cfg["mode"] = v
        elif k == "api_prefix":
            cfg["api_prefix"] = v
        elif k == "debug":
            cfg["debug"] = v
        elif k in ("environment", "entorno"):
            cfg["environment"] = v
        elif k in ("public_base_url", "url_publica"):
            cfg["public_base_url"] = v
        else:
            cfg[k] = v


def _apply_public_section(cfg: Dict[str, Any], public_sec: dict) -> None:
    for k, v in public_sec.items():
        if k in ("base_url", "public_base_url"):
            cfg["public_base_url"] = v
        else:
            cfg[k] = v


def _passthrough_keys() -> tuple[str, ...]:
    return (
        "debug",
        "environment",
        "llm_provider",
        "openrouter_base_url",
        "openrouter_model",
        "openrouter_advanced_model",
        "embedding_model",
        "llm_timeout_seconds",
        "allow_provider_fallback",
        "seed_default_data",
        "enable_multi_tenant",
        "enable_ai_responses",
        "enable_rule_based_fallback",
        "enable_intent_shortcuts",
        "enable_faq_search",
        "enable_human_handoff",
        "enable_audit_logs",
        "enable_audit_alerts",
        "enable_simulation_endpoint",
        "enable_webhook_processing",
        "semantic_threshold",
        "conversation_context_limit",
        "max_message_length",
        "truncate_long_messages",
        "ask_one_question_only",
        "faq_default_limit",
        "faq_require_significant_overlap",
        "faq_merge_yaml_and_db",
        "faq_deduplicate_by_question",
        "faq_exact_match_boost",
        "enable_strict_grounding",
        "enable_sensitive_validation",
        "source_guard_mode",
        "enable_retry_on_unsupported_reply",
        "block_unverified_prices",
        "block_unverified_locations",
        "block_unverified_delivery_times",
        "redact_pii_in_logs",
        "mode",
    )


def _apply_passthrough(cfg: Dict[str, Any], raw_cfg: Dict[str, Any]) -> None:
    for key in _passthrough_keys():
        if key in raw_cfg:
            cfg[key] = raw_cfg[key]


def _enforce_mode_defaults(cfg: Dict[str, Any]) -> None:
    resolved_mode = str(cfg.get("mode") or cfg.get("environment") or "").strip().lower()
    if resolved_mode:
        cfg["mode"] = resolved_mode
    if resolved_mode == "production":
        cfg["debug"] = False
        cfg["source_guard_mode"] = "strict"
        if not str(cfg.get("environment") or "").strip():
            cfg["environment"] = "production"


def _load_yaml_config() -> Dict:
    cfg: Dict = {}
    settings_path = _resolve_config_path("settings.yaml")
    bot_config_path = _resolve_config_path("bot_config.yaml")

    raw_cfg = _read_yaml_file(settings_path)
    raw_cfg = _deep_merge_dicts(raw_cfg, _read_yaml_file(bot_config_path))
    raw_cfg = _deep_merge_dicts(raw_cfg, _load_layer_file("personality.yaml"))
    raw_cfg = _deep_merge_dicts(raw_cfg, _load_layer_file("conversation_stage.yaml"))
    raw_cfg = _deep_merge_dicts(raw_cfg, _read_yaml_file(_resolve_config_path("secrets.yaml")))

    _apply_app_section(cfg, raw_cfg.get("app", {}))
    _apply_public_section(cfg, raw_cfg.get("public", {}))

    apply_ai_section(cfg, raw_cfg.get("llm") if isinstance(raw_cfg.get("llm"), dict) else {})
    apply_limits_sections(cfg, raw_cfg)
    apply_connectors_section(cfg, raw_cfg)
    _apply_passthrough(cfg, raw_cfg)
    _enforce_mode_defaults(cfg)

    global _SETTINGS_RAW
    _SETTINGS_RAW = raw_cfg
    return cfg


def load_config_file(name: str, tenant_id: str | None = None) -> Dict:
    if name in {"settings.yaml", "personality.yaml"}:
        unified_payload = _load_unified_tenant_section(name, tenant_id=tenant_id)
        if unified_payload:
            return unified_payload

    p = _resolve_config_path(name, tenant_id=tenant_id)
    if p.exists():
        return _read_yaml_file(p)

    unified_payload = _load_unified_tenant_section(name, tenant_id=tenant_id)
    if unified_payload:
        return unified_payload

    raw = _SETTINGS_RAW or {}
    if name == "bot_prompts.yaml":
        return raw.get("prompts", {})
    if name == "bot_configs.yaml":
        return {"defaults": raw.get("bot_defaults", {})}
    if name == "intent_keywords.yaml":
        return raw.get("intents", {})
    if name == "defaults.yaml":
        return raw
    return {}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ACTIVE_ENV_FILE) if ACTIVE_ENV_FILE is not None else None, env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Asistente Virtual AI para WhatsApp y CRM"
    app_version: str = "1.0.0"
    mode: str = "development"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    debug: bool = False

    database_url: str = Field(default="")
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 8

    llm_provider: str = "openrouter"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_advanced_model: str = "openai/gpt-4.1-mini"
    llm_timeout_seconds: int = 15
    allow_provider_fallback: bool = False
    embedding_model: str = "text-embedding-3-small"

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = ""
    meta_access_token: str = ""
    meta_phone_number_id: str = ""
    meta_verify_token: str = os.getenv("META_VERIFY_TOKEN", "")
    meta_app_secret: str = ""
    meta_business_account_id: str = ""
    meta_ig_account_id: str = ""
    connector_secrets_key: str = ""
    public_base_url: str = "http://localhost:8000"

    seed_default_data: bool = True
    enable_multi_tenant: bool = True
    enable_ai_responses: bool = True
    enable_rule_based_fallback: bool = True
    enable_intent_shortcuts: bool = True
    enable_faq_search: bool = True
    enable_human_handoff: bool = True
    enable_audit_logs: bool = True
    enable_audit_alerts: bool = True
    enable_simulation_endpoint: bool = True
    enable_webhook_processing: bool = True
    semantic_threshold: float = 0.22
    conversation_context_limit: int = 8
    max_message_length: int = 2000
    truncate_long_messages: bool = True
    ask_one_question_only: bool = True
    faq_default_limit: int = 3
    faq_require_significant_overlap: bool = True
    faq_merge_yaml_and_db: bool = True
    faq_deduplicate_by_question: bool = True
    faq_exact_match_boost: float = 0.15
    source_guard_mode: str = "permissive"
    enable_strict_grounding: bool = True
    enable_sensitive_validation: bool = True
    enable_retry_on_unsupported_reply: bool = True
    block_unverified_prices: bool = True
    block_unverified_locations: bool = True
    block_unverified_delivery_times: bool = True
    redact_pii_in_logs: bool = False


_yaml_cfg = _load_yaml_config()
_env_file_cfg = _read_env_file_values(ACTIVE_ENV_FILE) if ACTIVE_ENV_FILE is not None else {}
for key in list(_yaml_cfg.keys()):
    env_key = key.upper()
    if os.getenv(env_key) is not None:
        _yaml_cfg[key] = os.getenv(env_key)
    elif env_key in _env_file_cfg:
        _yaml_cfg[key] = _env_file_cfg[env_key]

for name in Settings.model_fields.keys():
    env_key = name.upper()
    if os.getenv(env_key) is not None:
        _yaml_cfg[name] = os.getenv(env_key)
    elif env_key in _env_file_cfg:
        _yaml_cfg[name] = _env_file_cfg[env_key]

settings = Settings(**_yaml_cfg)

_database_url = str(settings.database_url or "").strip()
_resolved_mode = str(settings.mode or settings.environment or "").strip().lower()
if not _database_url:
    _database_url = "sqlite:///:memory:"
if not _database_url.lower().startswith(("postgresql+psycopg", "sqlite")):
    raise RuntimeError("DATABASE_URL debe apuntar a PostgreSQL con psycopg")
settings.database_url = _database_url


def get_environment_status() -> Dict[str, Any]:
    root_env = WORKSPACE_ROOT / ".env"
    project_env = BASE_DIR / ".env"
    return {
        "workspace_root": str(WORKSPACE_ROOT),
        "project_root": str(BASE_DIR),
        "selected_env_file": str(ACTIVE_ENV_FILE) if ACTIVE_ENV_FILE is not None and ACTIVE_ENV_FILE.exists() else None,
        "root_env_exists": root_env.exists(),
        "project_env_exists": project_env.exists(),
        "openrouter_api_key_present": bool(str(settings.openrouter_api_key or "").strip()),
        "openai_api_key_present": bool(str(os.getenv("OPENAI_API_KEY") or "").strip()),
        "provider": str(settings.llm_provider or "").strip(),
        "ai_enabled": bool(settings.enable_ai_responses),
    }


def ensure_ai_runtime_ready() -> Dict[str, Any]:
    status = get_environment_status()
    provider = str(settings.llm_provider or "").strip().lower()
    if bool(settings.enable_ai_responses) and provider == "openrouter" and not bool(status["openrouter_api_key_present"]):
        raise RuntimeError("API KEY NOT LOADED")
    return status
