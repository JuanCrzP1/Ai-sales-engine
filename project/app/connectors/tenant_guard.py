"""A qué negocio atiende un canal: uno que existe en la plataforma y tiene una versión publicada desde el panel."""
from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError

from app.domain.business_config.errors import BusinessConfigError
from app.infrastructure.business_config.runtime_access import open_published_reader


def resolve_connector_tenant(tenant_slug: str | None) -> str:
    slug = str(tenant_slug or "").strip().lower()
    if not slug:
        raise RuntimeError("tenant requerido")
    try:
        open_published_reader().published(slug)
    except (BusinessConfigError, SQLAlchemyError) as exc:
        raise RuntimeError(f"tenant invalido: {slug}") from exc
    return slug
