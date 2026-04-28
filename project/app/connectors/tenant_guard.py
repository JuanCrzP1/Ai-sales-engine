from __future__ import annotations

from app.infrastructure.config.config_service import ConfigService

_DEMO_ALIAS = {"demo": "asesor_ai_prod"}


def allowed_tenants(config_service: ConfigService | None = None) -> set[str]:
    service = config_service or ConfigService()
    tenants = {
        str(path.name).strip().lower()
        for path in service.tenants_root.iterdir()
        if path.is_dir() and str(path.name).strip()
    }
    return tenants


def resolve_connector_tenant(tenant_slug: str | None, *, config_service: ConfigService | None = None) -> str:
    slug = str(tenant_slug or "").strip().lower()
    if not slug:
        raise RuntimeError("tenant requerido")

    slug = _DEMO_ALIAS.get(slug, slug)
    tenants = allowed_tenants(config_service=config_service)
    if slug not in tenants:
        raise RuntimeError(f"tenant invalido: {slug}")
    return slug
