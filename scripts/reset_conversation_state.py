"""
Reset conversational history stored in PostgreSQL.

What it clears:
  - conversation_messages
  - conversation_memory

Default behavior:
  - clears all tenants and all users

Optional targeted behavior:
  - clears a single tenant_slug + user_id pair

Notes:
  - This script is cross-platform because it is plain Python.
  - If a FastAPI/uvicorn server is still running, restart it after the reset to
    ensure any in-process RAM cache is discarded as well.

Usage:
  python scripts/reset_conversation_state.py
  python scripts/reset_conversation_state.py --tenant-slug demo --user-id 573001234567
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import text


REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "project"
ENV_FILE = REPO_ROOT / ".env"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

if ENV_FILE.exists():
    from dotenv import load_dotenv

    load_dotenv(ENV_FILE, override=False)


def _get_engine():
    from app.infrastructure.db.connection import get_engine

    return get_engine()


def _resolve_ids(conn, tenant_slug: str, user_id: str) -> tuple[str, str] | None:
    row = conn.execute(
        text(
            """
            SELECT t.id AS tenant_id, c.id AS client_id
            FROM tenants t
            JOIN clients c ON c.tenant_id = t.id
            WHERE t.slug = :slug
              AND c.external_id = :external_id
            LIMIT 1
            """
        ),
        {"slug": tenant_slug, "external_id": user_id},
    ).fetchone()
    if not row:
        return None
    return str(row._mapping["tenant_id"]), str(row._mapping["client_id"])


def _reset_all() -> None:
    engine = _get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM conversation_messages"))
        conn.execute(text("DELETE FROM conversation_memory"))
    print("[ok] Se borró todo el historial conversacional de PostgreSQL")


def _reset_one(tenant_slug: str, user_id: str) -> int:
    engine = _get_engine()
    with engine.begin() as conn:
        ids = _resolve_ids(conn, tenant_slug=tenant_slug, user_id=user_id)
        if ids is None:
            print("[warn] No existe conversación almacenada para ese tenant_slug/user_id")
            return 1

        tenant_id, client_id = ids
        conn.execute(
            text("DELETE FROM conversation_messages WHERE tenant_id = :tid AND client_id = :cid"),
            {"tid": tenant_id, "cid": client_id},
        )
        conn.execute(
            text("DELETE FROM conversation_memory WHERE tenant_id = :tid AND client_id = :cid"),
            {"tid": tenant_id, "cid": client_id},
        )

    print(f"[ok] Se borró el historial para tenant={tenant_slug} user_id={user_id}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Limpia la memoria conversacional persistida en PostgreSQL"
    )
    parser.add_argument("--tenant-slug", default="", help="Tenant a limpiar")
    parser.add_argument("--user-id", default="", help="Usuario a limpiar")
    args = parser.parse_args()

    tenant_slug = str(args.tenant_slug or "").strip()
    user_id = str(args.user_id or "").strip()

    if bool(tenant_slug) != bool(user_id):
        print("[error] --tenant-slug y --user-id deben enviarse juntos o ambos vacíos")
        return 2

    try:
        if tenant_slug and user_id:
            code = _reset_one(tenant_slug=tenant_slug, user_id=user_id)
        else:
            _reset_all()
            code = 0
    except Exception as exc:
        print(f"[error] Falló el reset conversacional: {exc}")
        return 1

    print("[info] Si el servidor sigue corriendo, reinícialo para limpiar también la RAM del proceso")
    return code


if __name__ == "__main__":
    raise SystemExit(main())