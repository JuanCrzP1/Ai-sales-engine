from __future__ import annotations

from app.application.runtime.runtime_yaml_builder import RuntimeYamlBuilder
from app.infrastructure.config.config_service import ConfigService


def _deep_merge(base: dict, incoming: dict) -> dict:
    result = dict(base)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            if not value:
                result[key] = {}
            else:
                result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _extract_section(payload: dict, key: str) -> dict:
    section = payload.get(key) if isinstance(payload, dict) else {}
    return dict(section) if isinstance(section, dict) else {}


def _load_raw_runtime_yaml(service: ConfigService, tenant_slug: str, channel: str | None = None) -> dict:
    sales_payload = service._load_raw_section("sales.yaml", tenant_slug)
    business_payload = service._load_raw_section("business.yaml", tenant_slug)
    pricing_payload = service._load_raw_section("pricing.yaml", tenant_slug)
    inventory_payload = service._load_raw_section("inventory.yaml", tenant_slug)
    config_payload = service._load_yaml(service.tenants_root / tenant_slug / "config.yaml")

    config_section = _extract_section(config_payload, "config")
    runtime_yaml = {
        "sales": _extract_section(sales_payload, "sales"),
        "business": _extract_section(business_payload, "business"),
        "pricing": _extract_section(pricing_payload, "pricing"),
        "inventory": _extract_section(inventory_payload, "inventory"),
        "config": dict(config_section),
        "capabilities": dict(config_section.get("capabilities") or {}),
        "post_payment": dict(config_section.get("post_payment") or {}),
    }

    normalized_channel = str(channel or "").strip().lower()
    if normalized_channel:
        runtime_yaml["channel"] = normalized_channel

    return runtime_yaml


def load_tenant_runtime_yaml(
    tenant_slug: str,
    *,
    channel: str | None = None,
    extra_yaml: dict | None = None,
    config_service: ConfigService | None = None,
) -> dict:
    normalized_slug = str(tenant_slug or "").strip()
    if not normalized_slug:
        raise RuntimeError("tenant slug missing for runtime yaml")

    service = config_service or ConfigService()
    normalized_slug = service._default_client_id(normalized_slug)
    runtime_yaml = _load_raw_runtime_yaml(service, normalized_slug, channel=channel)

    if isinstance(extra_yaml, dict) and extra_yaml:
        runtime_yaml = _deep_merge(runtime_yaml, extra_yaml)

    return RuntimeYamlBuilder().build(tenant_slug=normalized_slug, partial_yaml=runtime_yaml)