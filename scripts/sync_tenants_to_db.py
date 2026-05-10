"""
sync_tenants_to_db.py

Synchronizes all tenants defined as YAML directories under
project/config/tenants/ into the PostgreSQL `tenants` table.

Behavior:
  - existing slug → skip, report as [existing]
  - missing slug  → INSERT with name=slug, status='active'
  - idempotent: safe to run multiple times
  - never creates subscriptions
  - never modifies existing rows

Usage:
  python scripts/sync_tenants_to_db.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "project"
TENANTS_DIR = PROJECT_DIR / "config" / "tenants"
ENV_FILE = REPO_ROOT / ".env"

# Add project to sys.path so we can import app modules
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# ---------------------------------------------------------------------------
# Load .env before importing anything that reads settings
# ---------------------------------------------------------------------------
if ENV_FILE.exists():
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE, override=False)

# ---------------------------------------------------------------------------
# Now import DB infrastructure
# ---------------------------------------------------------------------------
from sqlalchemy import text  # noqa: E402


def _get_engine():
    from app.infrastructure.db.connection import get_engine
    return get_engine()


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def _slug_exists(conn, slug: str) -> bool:
    row = conn.execute(
        text("SELECT 1 FROM tenants WHERE slug = :slug LIMIT 1"),
        {"slug": slug},
    ).fetchone()
    return row is not None


def _insert_tenant(conn, slug: str) -> None:
    conn.execute(
        text(
            """
            INSERT INTO tenants (name, slug, status)
            VALUES (:name, :slug, 'active')
            """
        ),
        {"name": slug, "slug": slug},
    )


def _discover_slugs() -> list[str]:
    if not TENANTS_DIR.exists():
        raise FileNotFoundError(f"Tenants directory not found: {TENANTS_DIR}")
    return sorted(
        entry.name
        for entry in TENANTS_DIR.iterdir()
        if entry.is_dir() and not entry.name.startswith(".")
    )


def sync() -> None:
    slugs = _discover_slugs()
    if not slugs:
        print("No tenant directories found.")
        return

    created: list[str] = []
    existing: list[str] = []
    errors: list[tuple[str, str]] = []

    engine = _get_engine()

    for slug in slugs:
        try:
            with engine.begin() as conn:
                if _slug_exists(conn, slug):
                    print(f"[existing] {slug}")
                    existing.append(slug)
                else:
                    _insert_tenant(conn, slug)
                    print(f"[created]  {slug}")
                    created.append(slug)
        except Exception as exc:
            print(f"[error]    {slug}: {exc}")
            errors.append((slug, str(exc)))

    print()
    print("Summary:")
    print(f"  created:  {len(created)}")
    print(f"  existing: {len(existing)}")
    print(f"  errors:   {len(errors)}")

    if errors:
        print()
        print("Errors detail:")
        for slug, msg in errors:
            print(f"  {slug}: {msg}")
        sys.exit(1)


if __name__ == "__main__":
    sync()
