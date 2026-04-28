from sqlalchemy import text

from app.infrastructure.db.connection import get_engine


class DBRepository:

    def get_tenant_by_id(self, tenant_id: str):
        engine = get_engine()

        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT id, slug, status
                    FROM tenants
                    WHERE id = CAST(:tenant_id AS UUID)
                    LIMIT 1
                """
                ),
                {"tenant_id": tenant_id}
            ).fetchone()

            if not result:
                return None

            return dict(result._mapping)

    def get_tenant_by_slug(self, slug: str):
        engine = get_engine()

        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT id, slug, status
                    FROM tenants
                    WHERE slug = :slug
                    LIMIT 1
                """
                ),
                {"slug": slug}
            ).fetchone()

            if not result:
                return None

            return dict(result._mapping)

    def get_tenant_by_key(self, tenant_key: str):
        normalized = str(tenant_key or "").strip().lower()
        if not normalized:
            return None

        try:
            return self.get_tenant_by_id(normalized)
        except Exception:
            return self.get_tenant_by_slug(normalized)