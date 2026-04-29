import os

from sqlalchemy import text

from app.infrastructure.db.connection import get_engine


class DBRepository:

    @staticmethod
    def _mock_tenant_without_db():
        if os.getenv("DATABASE_URL") is None:
            return {
                "id": "asesor_ai_prod",
                "slug": "asesor_ai_prod",
                "status": "active",
            }
        return None

    def get_tenant_by_id(self, tenant_id: str):
        mock_tenant = self._mock_tenant_without_db()
        if mock_tenant is not None:
            return mock_tenant

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
        mock_tenant = self._mock_tenant_without_db()
        if mock_tenant is not None:
            return mock_tenant

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
        mock_tenant = self._mock_tenant_without_db()
        if mock_tenant is not None:
            return mock_tenant

        normalized = str(tenant_key or "").strip().lower()
        if not normalized:
            return None

        try:
            return self.get_tenant_by_id(normalized)
        except Exception:
            return self.get_tenant_by_slug(normalized)