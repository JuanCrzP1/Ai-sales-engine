"""A qué negocio pertenece una operación. Toda lectura o escritura parte de aquí y se filtra por el id que devuelve."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.engine import Connection, Row

from app.domain.business_config.errors import BusinessNotFoundError
from app.infrastructure.business_config.tables import tenants


def tenant_of(conn: Connection, tenant_slug: str) -> Row:
    tenant = conn.execute(select(tenants).where(tenants.c.slug == tenant_slug)).first()
    if tenant is None:
        raise BusinessNotFoundError(f"{tenant_slug}: el negocio no existe en la base de datos")
    return tenant
