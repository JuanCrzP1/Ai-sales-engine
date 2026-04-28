from __future__ import annotations

from typing import Any, Dict


CORE_CONNECTOR_KEYS = (
    "database_url",
    "jwt_secret",
    "jwt_algorithm",
    "jwt_expire_minutes",
    "openrouter_api_key",
    "twilio_account_sid",
    "twilio_auth_token",
    "twilio_whatsapp_number",
    "meta_access_token",
    "meta_phone_number_id",
    "meta_verify_token",
    "meta_app_secret",
    "meta_business_account_id",
    "meta_ig_account_id",
    "connector_secrets_key",
    "public_base_url",
)


def apply_connectors_section(cfg: Dict[str, Any], raw_cfg: Dict[str, Any] | None) -> None:
    source = raw_cfg if isinstance(raw_cfg, dict) else {}
    for key in CORE_CONNECTOR_KEYS:
        if key in source:
            cfg[key] = source[key]
