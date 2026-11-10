"""Migración inicial: lleva los negocios de sus YAML al almacén de BusinessConfig.

Es una operación puntual, no una dependencia: una vez importado, ningún negocio vuelve a leer YAML (ver
`tests/test_business_config_yaml_independence.py`). Es la única parte del nuevo sistema que lee YAML y se
retira con ellos en la Fase 4.

- Antes de escribir nada comprueba la clave de cifrado y que cada negocio, ya preparado, compile a sus YAML.
- Los datos de pago pasan de los YAML al almacén cifrado: la versión guardada solo tiene referencias.
- Nunca toca un negocio que ya tenga versiones: repetir la importación no duplica ni sobrescribe.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.business_config_application.service import BusinessConfigService
from app.domain.business_config.compiler import comparable_with_yaml, compile_business_config
from app.domain.business_config.contract import BusinessConfig, SecretRef
from app.domain.business_config.errors import BusinessConfigError
from app.domain.business_config.payment_data import SECRET_STORE_SOURCE, iter_secret_refs
from app.infrastructure.config.config_service import ConfigService
from app.infrastructure.config.legacy_yaml_importer import LEGACY_SECRET_SOURCE, import_legacy_sections
from app.infrastructure.config.payment_secrets import LegacyYamlSecretResolver

MIGRATION_AUTHOR = "migración inicial desde YAML"


@dataclass(frozen=True)
class PreparedTenant:
    slug: str
    name: str
    document: dict[str, Any]
    payment_values: dict[str, str]
    engine_settings: dict[str, Any]


@dataclass(frozen=True)
class ImportReport:
    created: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    # Ya existían con versiones, pero sin ninguna publicada: no se tocan y requieren revisión.
    unpublished: list[str] = field(default_factory=list)


def read_tenant_sections(config_service: ConfigService, slug: str) -> dict[str, dict]:
    """Las cinco secciones de un negocio, tal como las lee el motor, pero sin cargarlo ni leer `.env`."""

    def _section(payload: Any, key: str) -> dict:
        section = payload.get(key) if isinstance(payload, dict) else {}
        return dict(section) if isinstance(section, dict) else {}

    sections = {name: _section(config_service._load_raw_section(f"{name}.yaml", slug), name) for name in ("sales", "business", "pricing", "inventory")}
    sections["config"] = _section(config_service._load_yaml(config_service.tenants_root / slug / "config.yaml"), "config")
    return sections


def prepare_tenant(config_service: ConfigService, slug: str) -> PreparedTenant:
    """Convierte los YAML de un negocio y comprueba el resultado, sin escribir nada."""
    sections = read_tenant_sections(config_service, slug)
    result = import_legacy_sections(slug, sections)
    document = result.config.model_dump(mode="json", exclude_none=True)
    resolve_from_yaml = LegacyYamlSecretResolver(lambda: sections)
    values: dict[str, str] = {}
    for holder in iter_secret_refs(document):
        ref = holder["secret_ref"]
        stored_ref = f"{SECRET_STORE_SOURCE}:{ref.removeprefix(f'{LEGACY_SECRET_SOURCE}:')}"
        values[stored_ref] = resolve_from_yaml(SecretRef(secret_ref=ref))
        holder["secret_ref"] = stored_ref

    config = BusinessConfig.model_validate(document).with_engine_settings(result.engine_settings)
    if comparable_with_yaml(compile_business_config(config, lambda ref: values[ref.secret_ref])) != sections:
        raise BusinessConfigError(f"{slug}: la configuración preparada no reproduce sus YAML")
    return PreparedTenant(slug, result.config.identity.name, document, values, result.engine_settings.model_dump(mode="json", exclude_none=True))


def import_prepared(service: BusinessConfigService, tenant: PreparedTenant, *, already_registered: bool = False) -> None:
    if not already_registered:
        service.create_business(tenant.slug, tenant.name)
    version = service.save_changes(tenant.slug, tenant.document, payment_values=tenant.payment_values, created_by=MIGRATION_AUTHOR)
    service.save_engine_settings(tenant.slug, tenant.engine_settings)
    service.publish(tenant.slug, version.version)


def import_all(service: BusinessConfigService, config_service: ConfigService) -> ImportReport:
    """Importa los negocios que faltan. Un negocio registrado sin versiones se completa: no hay nada que sobrescribir."""
    service.verify_payment_key()
    existing = {summary.slug: summary for summary in service.list_businesses()}
    slugs = sorted(path.name for path in config_service.tenants_root.iterdir() if path.is_dir() and not path.name.startswith("."))
    pending = [slug for slug in slugs if slug not in existing or existing[slug].latest_version is None]
    # Primero todos, después las escrituras: si uno no se puede preparar, no se escribe ninguno.
    prepared = [prepare_tenant(config_service, slug) for slug in pending]
    for tenant in prepared:
        import_prepared(service, tenant, already_registered=tenant.slug in existing)
    skipped = [slug for slug in slugs if slug not in pending]
    return ImportReport(pending, skipped, [slug for slug in skipped if existing[slug].published_version is None])
