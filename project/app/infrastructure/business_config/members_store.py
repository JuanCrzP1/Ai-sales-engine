"""Los miembros de cada negocio, en la tabla `business_members` (implementa `BusinessMembers`)."""
from __future__ import annotations

from sqlalchemy import and_, select
from sqlalchemy.engine import Engine

from app.infrastructure.business_config.tables import business_members, tenants


class BusinessMembersStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def slugs_of(self, user_id: str) -> set[str]:
        query = select(tenants.c.slug).join(business_members, business_members.c.tenant_id == tenants.c.id).where(business_members.c.user_id == user_id)
        with self._engine.connect() as conn:
            return {row.slug for row in conn.execute(query)}

    def is_member(self, tenant_slug: str, user_id: str) -> bool:
        query = (
            select(business_members.c.user_id)
            .join(tenants, tenants.c.id == business_members.c.tenant_id)
            .where(and_(tenants.c.slug == tenant_slug, business_members.c.user_id == user_id))
        )
        with self._engine.connect() as conn:
            return conn.execute(query).first() is not None
