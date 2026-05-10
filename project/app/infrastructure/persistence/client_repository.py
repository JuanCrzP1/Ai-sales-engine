from __future__ import annotations

from sqlalchemy import text

from app.infrastructure.db.connection import get_engine
from app.infrastructure.db.repository import DBRepository


class ClientRepository:
    """Resolve an external contact (WhatsApp/Telegram/etc.) to a stable clients.id UUID."""

    def get_or_create(
        self,
        tenant_slug: str,
        external_id: str,
        name: str | None = None,
    ) -> str | None:
        """Return the UUID of the client row for (tenant_id, external_id).

        Creates the row if it does not exist.
        Optionally updates `name` when it differs from the stored value.
        Returns None if tenant_slug or external_id are empty, or if the tenant is not found.
        """
        normalized_slug = str(tenant_slug or "").strip().lower()
        normalized_ext = str(external_id or "").strip()
        if not normalized_slug or not normalized_ext:
            return None

        tenant = DBRepository().get_tenant_by_key(normalized_slug)
        if not tenant:
            return None

        tenant_id = str(tenant.get("id") or "")
        clean_name = str(name or "").strip() or None

        engine = get_engine()
        with engine.begin() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT id, name
                    FROM clients
                    WHERE tenant_id = :tenant_id AND external_id = :external_id
                    LIMIT 1
                    """
                ),
                {"tenant_id": tenant_id, "external_id": normalized_ext},
            ).fetchone()

            if row:
                client_id = str(row._mapping["id"])
                stored_name = row._mapping.get("name")
                if clean_name and clean_name != stored_name:
                    conn.execute(
                        text(
                            """
                            UPDATE clients
                            SET name = :name
                            WHERE id = :client_id
                            """
                        ),
                        {"name": clean_name, "client_id": client_id},
                    )
                return client_id

            # Insert new client row and return the generated UUID.
            result = conn.execute(
                text(
                    """
                    INSERT INTO clients (tenant_id, external_id, name)
                    VALUES (:tenant_id, :external_id, :name)
                    RETURNING id
                    """
                ),
                {
                    "tenant_id": tenant_id,
                    "external_id": normalized_ext,
                    "name": clean_name,
                },
            ).fetchone()

            return str(result._mapping["id"]) if result else None
