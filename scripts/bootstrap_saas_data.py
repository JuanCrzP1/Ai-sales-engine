"""
bootstrap_saas_data.py

Garantiza en PostgreSQL la fila de `tenants` de cada negocio de ejemplo (`project/config/tenants/<negocio>/`): de ella cuelgan la
memoria del motor (`clients`, `conversation_messages`, `conversation_memory`) y el almacén del panel. Lo usa
`scripts/setup_cloud_database.py` en la rama `pruebas`.

Hasta el 18 de noviembre de 2026 también creaba una fila en `admin_users` y otra en `tenant_settings`, del sistema anterior; esas
tablas se retiraron (`project/db/migrations/0023_retire_legacy_tables.sql`).

La plataforma no tiene suscripciones, planes ni límites por cuenta: este script no los crea.

- Se puede repetir: nunca sobrescribe ni cambia una fila que ya existe.
- Cada negocio va en su propia transacción: si uno falla, los demás siguen.
- Informa [created], [existing] o [error] por negocio.

Uso:
  python scripts/bootstrap_saas_data.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "project"
TENANTS_DIR = PROJECT_DIR / "config" / "tenants"
ENV_FILE = REPO_ROOT / ".env"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# El `.env` antes de importar nada que lea los ajustes.
if ENV_FILE.exists():
    from dotenv import load_dotenv

    load_dotenv(ENV_FILE, override=False)

from sqlalchemy import text  # noqa: E402


def _get_engine():
    from app.infrastructure.db.connection import get_engine

    return get_engine()


def _get_tenant_id(conn, slug: str) -> UUID | None:
    row = conn.execute(text("SELECT id FROM tenants WHERE slug = :slug LIMIT 1"), {"slug": slug}).fetchone()
    return row._mapping["id"] if row else None


def _ensure_tenant(conn, slug: str) -> bool:
    """La fila del negocio en `tenants`. True si se creó ahora."""
    if _get_tenant_id(conn, slug) is not None:
        return False
    conn.execute(text("INSERT INTO tenants (name, slug, status) VALUES (:name, :slug, 'active')"), {"name": slug, "slug": slug})
    if _get_tenant_id(conn, slug) is None:
        raise RuntimeError(f"no se pudo leer la fila recién creada de '{slug}'")
    return True


def _discover_slugs() -> list[str]:
    if not TENANTS_DIR.exists():
        raise FileNotFoundError(f"No existe la carpeta de negocios: {TENANTS_DIR}")
    return sorted(entry.name for entry in TENANTS_DIR.iterdir() if entry.is_dir() and not entry.name.startswith("."))


def bootstrap() -> None:
    slugs = _discover_slugs()
    if not slugs:
        print("No hay negocios de ejemplo.")
        return

    engine = _get_engine()
    created = 0
    errors: list[tuple[str, str]] = []
    for slug in slugs:
        try:
            with engine.begin() as conn:
                was_created = _ensure_tenant(conn, slug)
            print(f"[created]  {slug}" if was_created else f"[existing] {slug}")
            created += int(was_created)
        except Exception as exc:  # noqa: BLE001 - cada negocio informa su error y los demás siguen
            print(f"[error]    {slug}: {type(exc).__name__}")
            errors.append((slug, type(exc).__name__))

    print()
    print("Resumen:")
    print(f"  negocios revisados: {len(slugs)}")
    print(f"  creados:            {created}")
    print(f"  errores:            {len(errors)}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    bootstrap()
