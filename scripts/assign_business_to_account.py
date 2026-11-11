#!/usr/bin/env python3
"""Crea en una rama de Neon un negocio de este equipo, a nombre de una cuenta que ya existe en el panel de la nube.

La cuenta la crea su dueño en el panel («Crear cuenta»): este script nunca crea cuentas ni toca contraseñas. Busca la cuenta
por su correo en `neon_auth.user` de esa rama, crea el negocio con su configuración de ejemplo (su `business-config.json`,
como la importación del panel) y deja a esa cuenta como dueña, en la misma transacción. Los datos de pago se cifran
con la clave de esa rama: producción tiene la suya (`secrets.production.env`) y pruebas usa la de este equipo. La clave de IA
no se copia: la pone el dueño en el panel.

    python scripts/assign_business_to_account.py --branch production --slug asesor_ai_prod --email persona@correo.com          # informa
    python scripts/assign_business_to_account.py --branch production --slug asesor_ai_prod --email persona@correo.com --apply  # lo hace

Si el negocio ya existe en esa rama, solo agrega a la cuenta como dueña (si no lo era). Nunca imprime claves ni datos de pago.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import select, text

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
sys.path.insert(0, str(PROJECT_DIR))

from app.config import normalize_database_url  # noqa: E402
from app.domain.business_config.access import OWNER  # noqa: E402
from app.domain.business_config.compiler import compile_business_config  # noqa: E402
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine  # noqa: E402
from app.infrastructure.business_config.members_store import BusinessMembersStore  # noqa: E402
from app.infrastructure.business_config.payment_secret_store import SECRETS_KEY_ENV, PaymentSecretStore  # noqa: E402
from app.infrastructure.business_config.tables import business_members, tenants  # noqa: E402
from app.infrastructure.business_config.example_businesses import import_example, load_example  # noqa: E402

# Rama → (variable del .env con su cadena de conexión, archivo con su clave de cifrado).
BRANCHES = {
    "production": ("CLOUD_DATABASE_URL_PRODUCTION", ROOT_DIR / "secrets.production.env"),
    "pruebas": ("CLOUD_DATABASE_URL_PRUEBAS", ROOT_DIR / "secrets.local.env"),
}


def _value(path: Path, name: str) -> str:
    value = str(dotenv_values(path).get(name) or "").strip() if path.is_file() else ""
    if not value:
        raise SystemExit(f"[error] Falta {name} en {path.name}.")
    return value


def _account(conn, email: str) -> str | None:
    """El identificador de la cuenta con ese correo en Neon Auth de esta rama, o None si todavía no existe."""
    row = conn.execute(text('SELECT id FROM neon_auth."user" WHERE lower(email) = lower(:email)'), {"email": email.strip()}).first()
    return str(row.id) if row else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--branch", choices=sorted(BRANCHES), required=True)
    parser.add_argument("--slug", required=True, help="el negocio de este equipo que se crea en la nube")
    parser.add_argument("--email", required=True, help="el correo de la cuenta que queda como dueña")
    parser.add_argument("--apply", action="store_true", help="hacer los cambios (sin esto solo informa)")
    args = parser.parse_args()

    variable, key_file = BRANCHES[args.branch]
    url = normalize_database_url(_value(ROOT_DIR / ".env", variable))
    key = _value(key_file, SECRETS_KEY_ENV)
    engine = create_business_config_engine(url)
    service = build_business_config_service(engine, secrets_key=key)

    with engine.connect() as conn:
        user_id = _account(conn, args.email)
        exists = conn.execute(select(tenants.c.id).where(tenants.c.slug == args.slug)).first() is not None
    if user_id is None:
        print(f"[error] Todavía no hay una cuenta con ese correo en la rama {args.branch}: créala en el panel («Crear cuenta»).")
        return 1
    owner = BusinessMembersStore(engine).is_member(args.slug, user_id) if exists else False
    print(f"[info] Rama {args.branch}: la cuenta existe. El negocio {args.slug} {'ya existe' if exists else 'no existe todavía'}.")
    if owner:
        print("[ok] Esa cuenta ya es dueña de ese negocio. No falta nada.")
        return 0

    prepared = None if exists else load_example(args.slug)
    if not args.apply:
        step = "agregar la cuenta como dueña" if exists else "crear el negocio con la configuración de este equipo y la cuenta como dueña"
        print(f"[info] Pendiente: {step}. Nada se escribió; para hacerlo, repite con --apply.")
        return 0

    if exists:
        with engine.begin() as conn:
            tenant_id = conn.execute(select(tenants.c.id).where(tenants.c.slug == args.slug)).scalar_one()
            conn.execute(business_members.insert().values(tenant_id=tenant_id, user_id=user_id, role=OWNER, created_at=datetime.now(timezone.utc)))
    else:
        service.create_business(prepared.slug, prepared.name, owner_id=user_id)
        import_example(service, prepared, already_registered=True)

    # Comprobación: lo publicado compila con la clave de esta rama y la cuenta es la dueña.
    published = service.get_published(args.slug)
    compile_business_config(published, PaymentSecretStore(engine, key).resolver(args.slug))
    assert BusinessMembersStore(engine).is_member(args.slug, user_id)
    print(f"[ok] {args.slug} quedó a nombre de esa cuenta en {args.branch}, publicado y con sus datos de pago cifrados con la clave de la rama.")
    print("[info] La clave de IA la pone el dueño en el panel: Inteligencia artificial.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
