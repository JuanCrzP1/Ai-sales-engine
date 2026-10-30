from __future__ import annotations

import os

from sqlalchemy.exc import SQLAlchemyError

from app.application.runtime.runtime_yaml_builder import RuntimeYamlBuilder
from app.domain.business_config.compiler import compile_business_config
from app.infrastructure.config.business_config_repository import BusinessConfigRepository
from app.infrastructure.config.business_config_store import BusinessConfigError, BusinessConfigStore
from app.infrastructure.config.config_service import ConfigService
from app.infrastructure.config.legacy_yaml_importer import LEGACY_SECRET_SOURCE
from app.infrastructure.config.payment_secret_store import SECRET_STORE_SOURCE, PaymentSecretStore
from app.infrastructure.config.payment_secrets import LegacyYamlSecretResolver, SecretResolutionError, resolve_by_source
from app.infrastructure.db.connection import get_engine
from app.utils.logger import logger

# Negocios que leen su configuración del contrato global.
# Valores: lista separada por comas de slugs, o "*" para todos. Vacío: todos usan los YAML.
CONTRACT_TENANTS_ENV = "BUSINESS_CONFIG_CONTRACT_TENANTS"

# Dónde está el contrato de esos negocios: "file" (por defecto, `business-config.json` en la carpeta
# del tenant) o "database" (versión publicada en `business_configs`, con datos de pago cifrados).
CONTRACT_STORE_ENV = "BUSINESS_CONFIG_STORE"


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


def _load_legacy_sections(service: ConfigService, tenant_slug: str) -> dict[str, dict]:
    config_payload = service._load_yaml(service.tenants_root / tenant_slug / "config.yaml")
    return {
        "sales": _extract_section(service._load_raw_section("sales.yaml", tenant_slug), "sales"),
        "business": _extract_section(service._load_raw_section("business.yaml", tenant_slug), "business"),
        "pricing": _extract_section(service._load_raw_section("pricing.yaml", tenant_slug), "pricing"),
        "inventory": _extract_section(service._load_raw_section("inventory.yaml", tenant_slug), "inventory"),
        "config": _extract_section(config_payload, "config"),
    }


def _assemble_runtime_yaml(sections: dict[str, dict], channel: str | None = None) -> dict:
    config_section = dict(sections.get("config") or {})
    runtime_yaml = {
        "sales": dict(sections.get("sales") or {}),
        "business": dict(sections.get("business") or {}),
        "pricing": dict(sections.get("pricing") or {}),
        "inventory": dict(sections.get("inventory") or {}),
        "config": config_section,
        "capabilities": dict(config_section.get("capabilities") or {}),
        "post_payment": dict(config_section.get("post_payment") or {}),
    }

    normalized_channel = str(channel or "").strip().lower()
    if normalized_channel:
        runtime_yaml["channel"] = normalized_channel

    return runtime_yaml


def _load_raw_runtime_yaml(service: ConfigService, tenant_slug: str, channel: str | None = None) -> dict:
    return _assemble_runtime_yaml(_load_legacy_sections(service, tenant_slug), channel=channel)


def contract_enabled_for(tenant_slug: str) -> bool:
    enabled = {item.strip() for item in str(os.getenv(CONTRACT_TENANTS_ENV) or "").split(",") if item.strip()}
    return "*" in enabled or tenant_slug in enabled


def contract_store() -> str:
    return "database" if str(os.getenv(CONTRACT_STORE_ENV) or "").strip().lower() == "database" else "file"


def compile_contract_sections(service: ConfigService, tenant_slug: str) -> dict[str, dict]:
    """Contrato del negocio → validación → compilación a las secciones que consume el motor."""
    legacy_secrets = LegacyYamlSecretResolver(lambda: _load_legacy_sections(service, tenant_slug))
    if contract_store() == "database":
        engine = get_engine()
        config = BusinessConfigRepository(engine).published(tenant_slug)
        resolver = resolve_by_source(
            {LEGACY_SECRET_SOURCE: legacy_secrets, SECRET_STORE_SOURCE: PaymentSecretStore(engine).resolver(tenant_slug)}
        )
        return compile_business_config(config, resolver)
    config = BusinessConfigStore(service.tenants_root).load(tenant_slug)
    return compile_business_config(config, legacy_secrets)


def _load_contract_runtime_yaml(service: ConfigService, tenant_slug: str, channel: str | None = None) -> dict | None:
    try:
        sections = compile_contract_sections(service, tenant_slug)
    except (BusinessConfigError, SecretResolutionError, SQLAlchemyError, ValueError) as exc:
        # Una configuración inválida nunca deja al negocio sin servicio: se usan sus YAML.
        # De un error de base de datos solo se registra el tipo: su texto puede incluir datos de conexión.
        error = type(exc).__name__ if isinstance(exc, SQLAlchemyError) else str(exc)
        logger.error("business_config_contract_invalid", extra={"tenant": tenant_slug, "error": error})
        return None
    return _assemble_runtime_yaml(sections, channel=channel)


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

    runtime_yaml = None
    if contract_enabled_for(normalized_slug):
        runtime_yaml = _load_contract_runtime_yaml(service, normalized_slug, channel=channel)
    if runtime_yaml is None:
        runtime_yaml = _load_raw_runtime_yaml(service, normalized_slug, channel=channel)

    if isinstance(extra_yaml, dict) and extra_yaml:
        runtime_yaml = _deep_merge(runtime_yaml, extra_yaml)

    return RuntimeYamlBuilder().build(tenant_slug=normalized_slug, partial_yaml=runtime_yaml)
