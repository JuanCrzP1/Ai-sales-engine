"""
bootstrap_saas_data.py

Creates the minimum operational structure in PostgreSQL for every tenant
directory found under project/config/tenants/.

For each tenant the script guarantees exactly one row in:
  - tenants         (name=slug, status='active')
  - admin_users     (name=slug, all other fields NULL)
  - subscriptions   (plan_code='starter', status='trialing', +30 days)
  - tenant_settings (settings='{}')

Behavior:
  - Idempotent: safe to run multiple times without side effects.
  - Never overwrites or updates existing rows.
  - Each tenant is processed in its own transaction; one failure does not
    prevent the rest from being bootstrapped.
  - Reports [created], [existing], or [error] per tenant.

Usage:
  python scripts/bootstrap_saas_data.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from uuid import UUID

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "project"
TENANTS_DIR = PROJECT_DIR / "config" / "tenants"
ENV_FILE = REPO_ROOT / ".env"

# Add project to sys.path so we can import app infrastructure.
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# ---------------------------------------------------------------------------
# Load .env before importing anything that reads settings
# ---------------------------------------------------------------------------
if ENV_FILE.exists():
    from dotenv import load_dotenv

    load_dotenv(ENV_FILE, override=False)

# ---------------------------------------------------------------------------
# DB infrastructure (same pattern as sync_tenants_to_db.py)
# ---------------------------------------------------------------------------
from sqlalchemy import text  # noqa: E402


def _get_engine():
    from app.infrastructure.db.connection import get_engine

    return get_engine()


# ---------------------------------------------------------------------------
# Per-table helpers — all checks use SELECT 1 ... LIMIT 1 for safety
# ---------------------------------------------------------------------------

def _get_tenant_id(conn, slug: str) -> UUID | None:
    row = conn.execute(
        text("SELECT id FROM tenants WHERE slug = :slug LIMIT 1"),
        {"slug": slug},
    ).fetchone()
    return row._mapping["id"] if row else None


def _ensure_tenant(conn, slug: str) -> tuple[UUID, bool]:
    """Return (tenant_id, was_created)."""
    existing_id = _get_tenant_id(conn, slug)
    if existing_id is not None:
        return existing_id, False
    conn.execute(
        text(
            """
            INSERT INTO tenants (name, slug, status)
            VALUES (:name, :slug, 'active')
            """
        ),
        {"name": slug, "slug": slug},
    )
    new_id = _get_tenant_id(conn, slug)
    assert new_id is not None, f"Failed to retrieve id after inserting tenant '{slug}'"
    return new_id, True


def _has_admin_user(conn, tenant_id: UUID) -> bool:
    row = conn.execute(
        text(
            "SELECT 1 FROM admin_users WHERE tenant_id = CAST(:tid AS UUID) LIMIT 1"
        ),
        {"tid": str(tenant_id)},
    ).fetchone()
    return row is not None


def _create_admin_user(conn, tenant_id: UUID, slug: str) -> None:
    conn.execute(
        text(
            """
            INSERT INTO admin_users (tenant_id, name)
            VALUES (CAST(:tid AS UUID), :name)
            """
        ),
        {"tid": str(tenant_id), "name": slug},
    )


def _has_subscription(conn, tenant_id: UUID) -> bool:
    row = conn.execute(
        text(
            "SELECT 1 FROM subscriptions WHERE tenant_id = CAST(:tid AS UUID) LIMIT 1"
        ),
        {"tid": str(tenant_id)},
    ).fetchone()
    return row is not None


def _create_subscription(conn, tenant_id: UUID) -> None:
    conn.execute(
        text(
            """
            INSERT INTO subscriptions (tenant_id, plan_code, status, current_period_end)
            VALUES (
                CAST(:tid AS UUID),
                'starter',
                'trialing',
                now() + interval '30 days'
            )
            """
        ),
        {"tid": str(tenant_id)},
    )


def _has_tenant_settings(conn, tenant_id: UUID) -> bool:
    row = conn.execute(
        text(
            "SELECT 1 FROM tenant_settings WHERE tenant_id = CAST(:tid AS UUID) LIMIT 1"
        ),
        {"tid": str(tenant_id)},
    ).fetchone()
    return row is not None


def _create_tenant_settings(conn, tenant_id: UUID) -> None:
    conn.execute(
        text(
            """
            INSERT INTO tenant_settings (tenant_id, settings)
            VALUES (CAST(:tid AS UUID), '{}'::jsonb)
            """
        ),
        {"tid": str(tenant_id)},
    )


# ---------------------------------------------------------------------------
# Slug discovery
# ---------------------------------------------------------------------------

def _discover_slugs() -> list[str]:
    if not TENANTS_DIR.exists():
        raise FileNotFoundError(f"Tenants directory not found: {TENANTS_DIR}")
    return sorted(
        entry.name
        for entry in TENANTS_DIR.iterdir()
        if entry.is_dir() and not entry.name.startswith(".")
    )


# ---------------------------------------------------------------------------
# Main bootstrap logic
# ---------------------------------------------------------------------------

def bootstrap() -> None:
    slugs = _discover_slugs()
    if not slugs:
        print("No tenant directories found.")
        return

    engine = _get_engine()

    total_created = 0
    total_existing = 0
    errors: list[tuple[str, str]] = []

    for slug in slugs:
        try:
            with engine.begin() as conn:
                tenant_id, tenant_was_created = _ensure_tenant(conn, slug)

                created_parts: list[str] = []
                existing_parts: list[str] = []

                if tenant_was_created:
                    created_parts.append("tenant")
                else:
                    existing_parts.append("tenant")

                if _has_admin_user(conn, tenant_id):
                    existing_parts.append("admin_user")
                else:
                    _create_admin_user(conn, tenant_id, slug)
                    created_parts.append("admin_user")

                if _has_subscription(conn, tenant_id):
                    existing_parts.append("subscription")
                else:
                    _create_subscription(conn, tenant_id)
                    created_parts.append("subscription")

                if _has_tenant_settings(conn, tenant_id):
                    existing_parts.append("tenant_settings")
                else:
                    _create_tenant_settings(conn, tenant_id)
                    created_parts.append("tenant_settings")

            if created_parts:
                print(f"[created]  {slug} -> {', '.join(created_parts)}")
                total_created += len(created_parts)
            else:
                print(f"[existing] {slug}")

            total_existing += len(existing_parts)

        except Exception as exc:
            print(f"[error]    {slug}: {exc}")
            errors.append((slug, str(exc)))

    print()
    print("Summary:")
    print(f"  tenants processed: {len(slugs)}")
    print(f"  records created:   {total_created}")
    print(f"  records existing:  {total_existing}")
    print(f"  errors:            {len(errors)}")

    if errors:
        print()
        print("Errors detail:")
        for slug, msg in errors:
            print(f"  {slug}: {msg}")
        sys.exit(1)


if __name__ == "__main__":
    bootstrap()
