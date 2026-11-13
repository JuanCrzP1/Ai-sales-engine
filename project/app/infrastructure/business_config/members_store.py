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

    def is_owner(self, tenant_slug: str, user_id: str) -> bool:
        query = (
            select(business_members.c.user_id)
            .join(tenants, tenants.c.id == business_members.c.tenant_id)
            .where(and_(tenants.c.slug == tenant_slug, business_members.c.user_id == user_id, business_members.c.role == "owner"))
        )
        with self._engine.connect() as conn:
            return conn.execute(query).first() is not None

    def role_of(self, tenant_slug: str, user_id: str) -> str | None:
        query = (
            select(business_members.c.role)
            .join(tenants, tenants.c.id == business_members.c.tenant_id)
            .where(and_(tenants.c.slug == tenant_slug, business_members.c.user_id == user_id))
        )
        with self._engine.connect() as conn:
            row = conn.execute(query).first()
        return row.role if row is not None else None

    def roles_of(self, user_id: str) -> dict[str, str]:
        query = select(tenants.c.slug, business_members.c.role).join(business_members, business_members.c.tenant_id == tenants.c.id).where(business_members.c.user_id == user_id)
        with self._engine.connect() as conn:
            return {row.slug: row.role for row in conn.execute(query)}
