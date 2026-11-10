"""Deja lista una rama de la base PostgreSQL de la nube (Neon) desde este equipo.

Cada rama lee su cadena de conexión del entorno o del `.env` de la raíz, tal como la da Neon; nunca se imprime:

| Rama | Variable | Qué recibe |
|---|---|---|
| `production` | `CLOUD_DATABASE_URL_PRODUCTION` | Solo el esquema: los negocios los crean las cuentas reales |
| `pruebas` | `CLOUD_DATABASE_URL_PRUEBAS` | El esquema y los negocios de ejemplo de este equipo |

  python scripts/setup_cloud_database.py --branch pruebas           # informa qué haría, sin escribir nada
  python scripts/setup_cloud_database.py --branch pruebas --apply   # lo hace

Todos los pasos se pueden repetir; lo que ya está no se toca:
1. Esquema del motor (`project/docs/postgresql_schema.sql`), si falta la tabla `tenants`.
2. Almacén de BusinessConfig: las migraciones de `project/db/migrations`, en orden (todas se pueden repetir).
Solo en `pruebas`:
3. Filas operativas de cada negocio (`scripts/bootstrap_saas_data.py`, apuntado a la nube).
4. Copia de lo que guarda el panel en este equipo: versiones, datos de pago, ajustes técnicos y clave de IA de cada negocio. Los
   secretos viajan cifrados: la clave de cifrado no sale de este equipo. Un negocio que ya tiene versiones en la nube no se toca.
5. Comprobación: con la clave de este equipo, lo publicado en la nube compila igual que lo publicado aquí.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import create_engine, inspect, insert, select, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.engine.url import make_url

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
sys.path.insert(0, str(PROJECT_DIR))

from app.config import normalize_database_url  # noqa: E402
from app.domain.business_config.compiler import compile_business_config  # noqa: E402
from app.infrastructure.business_config.database import database_url, sqlite_file  # noqa: E402
from app.infrastructure.business_config.runtime_access import reader_for  # noqa: E402
from app.infrastructure.business_config.secrets_key import find_secrets_key  # noqa: E402
from app.infrastructure.business_config.tables import (  # noqa: E402
    business_ai_settings,
    business_config_secrets,
    business_configs,
    business_engine_settings,
    tenants,
)

# Por rama: la variable con su cadena de conexión y si recibe los negocios de ejemplo.
BRANCHES = {
    "production": ("CLOUD_DATABASE_URL_PRODUCTION", False),
    "pruebas": ("CLOUD_DATABASE_URL_PRUEBAS", True),
}
ENGINE_SCHEMA = PROJECT_DIR / "docs" / "postgresql_schema.sql"
# Las migraciones del almacén, en orden. Todas se pueden aplicar más de una vez.
MIGRATIONS = sorted((PROJECT_DIR / "db" / "migrations").glob("[0-9][0-9][0-9][0-9]_*.sql"))
BOOTSTRAP = ROOT_DIR / "scripts" / "bootstrap_saas_data.py"
STORE_TABLES = (business_configs, business_config_secrets, business_engine_settings, business_ai_settings)


def cloud_url(variable: str) -> str:
    url = os.getenv(variable) or dotenv_values(ROOT_DIR / ".env").get(variable) or ""
    if not url.strip():
        raise SystemExit(f"[error] Falta {variable}: pega la cadena de conexión de esa rama de Neon en el .env de la raíz.")
    return normalize_database_url(url)


def describe(url: str) -> str:
    """Servidor y base, sin usuario ni contraseña."""
    parsed = make_url(url)
    return f"{parsed.host}/{parsed.database}"


def local_store() -> Engine:
    url = database_url()
    path = sqlite_file(url)
    if path is not None and not path.is_file():
        raise SystemExit("[error] No existe el almacén local del panel: no hay nada que copiar.")
    return create_engine(url)


def _run_sql_file(cloud: Engine, path: Path) -> None:
    """El archivo completo en una transacción: si algo falla, no queda nada a medias."""
    sql = path.read_text(encoding="utf-8").replace("BEGIN;", "").replace("COMMIT;", "")
    with cloud.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.exec_driver_sql(f"BEGIN;\n{sql}\nCOMMIT;")


def _migration_tables(path: Path) -> set[str]:
    """Las tablas que crea una migración."""
    return set(re.findall(r"CREATE TABLE IF NOT EXISTS ([a-z_]+)", path.read_text(encoding="utf-8")))


def _cloud_tenant_ids(connection: Connection) -> dict[str, object]:
    return {row.slug: row.id for row in connection.execute(text("SELECT id, slug FROM tenants"))}


def _has_versions(connection: Connection, tenant_id: object) -> bool:
    return connection.execute(select(business_configs.c.id).where(business_configs.c.tenant_id == tenant_id).limit(1)).first() is not None


def plan(cloud: Engine, local: Engine | None) -> list[str]:
    """Lo que falta en la nube, sin escribir nada. Sin `local`, solo el esquema."""
    tables = set(inspect(cloud).get_table_names())
    steps = []
    if "tenants" not in tables:
        steps.append("crear el esquema del motor")
    missing = [path.name for path in MIGRATIONS if _migration_tables(path) - tables]
    steps += [f"aplicar {name}" for name in missing]
    if local is None:
        return steps
    with local.connect() as source:
        slugs = [row.slug for row in source.execute(select(tenants.c.slug).order_by(tenants.c.slug))]
    if "tenants" in tables and "business_configs" in tables:
        with cloud.connect() as target:
            ids = _cloud_tenant_ids(target)
            pending = [slug for slug in slugs if slug not in ids or not _has_versions(target, ids[slug])]
    else:
        pending = slugs
    steps += [f"copiar {slug}" for slug in pending]
    return steps


def bootstrap(url: str) -> None:
    """Las filas operativas de cada negocio, con el script de siempre apuntado a la nube."""
    result = subprocess.run([sys.executable, str(BOOTSTRAP)], env={**os.environ, "DATABASE_URL": url}, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"[error] bootstrap_saas_data.py terminó con código {result.returncode}")


def copy_businesses(cloud: Engine, local: Engine) -> list[tuple[str, str]]:
    report = []
    # Una base local anterior a una migración no tiene sus tablas (el panel las crea al arrancar): no hay nada que copiar de ellas.
    present = set(inspect(local).get_table_names())
    copied_tables = [table for table in STORE_TABLES if table.name in present]
    with local.connect() as source:
        local_tenants = list(source.execute(select(tenants.c.id, tenants.c.slug).order_by(tenants.c.slug)))
        with cloud.begin() as target:
            ids = _cloud_tenant_ids(target)
            for local_id, slug in local_tenants:
                cloud_id = ids.get(slug)
                if cloud_id is None:
                    report.append((slug, "sin fila en tenants: no se copia"))
                    continue
                if _has_versions(target, cloud_id):
                    report.append((slug, "ya estaba"))
                    continue
                for table in copied_tables:
                    rows = [dict(row._mapping) for row in source.execute(select(table).where(table.c.tenant_id == local_id))]
                    if rows:
                        target.execute(insert(table), [{**row, "tenant_id": cloud_id} for row in rows])
                report.append((slug, "copiado"))
    return report


def verify(cloud: Engine, local: Engine) -> list[tuple[str, bool]]:
    key = find_secrets_key()
    if not key:
        raise SystemExit("[error] No encuentro la clave de cifrado de este equipo: no se puede comprobar.")
    here, there = reader_for(local, key), reader_for(cloud, key)
    with local.connect() as source:
        slugs = [row.slug for row in source.execute(select(tenants.c.slug).order_by(tenants.c.slug))]
    results = []
    for slug in slugs:
        try:
            same = compile_business_config(there.published(slug), there.payment_resolver(slug)) == compile_business_config(
                here.published(slug), here.payment_resolver(slug)
            )
        except Exception:  # noqa: BLE001 - se informa el negocio, nunca el detalle (podría llevar datos)
            same = False
        results.append((slug, same))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--branch", choices=sorted(BRANCHES), required=True, help="rama de Neon que se prepara")
    parser.add_argument("--apply", action="store_true", help="hacer los cambios (sin esto solo informa)")
    args = parser.parse_args()

    variable, with_samples = BRANCHES[args.branch]
    url = cloud_url(variable)
    cloud = create_engine(url, pool_pre_ping=True)
    local = local_store() if with_samples else None
    print(f"[info] Rama {args.branch}: {describe(url)}")
    steps = plan(cloud, local)
    if not args.apply:
        print("[info] Pendiente:" if steps else "[ok] No falta nada.")
        for step in steps:
            print(f"  - {step}")
        print(f"[info] Nada se escribió. Para hacerlo: python scripts/setup_cloud_database.py --branch {args.branch} --apply")
        return 0

    tables = set(inspect(cloud).get_table_names())
    if "tenants" not in tables:
        _run_sql_file(cloud, ENGINE_SCHEMA)
        print("[ok] Esquema del motor creado")
    for migration in MIGRATIONS:
        _run_sql_file(cloud, migration)
    print(f"[ok] Almacén de BusinessConfig al día ({', '.join(path.name for path in MIGRATIONS)})")
    if local is None:
        print("[ok] Esquema listo. Sin negocios de ejemplo: los crean las cuentas reales.")
        return 0
    bootstrap(url)
    print("[ok] Filas operativas de cada negocio")
    for slug, outcome in copy_businesses(cloud, local):
        print(f"  {slug:20} {outcome}")
    results = verify(cloud, local)
    for slug, same in results:
        print(f"  {slug:20} {'igual que aquí' if same else 'DIFERENTE'}")
    if all(same for _slug, same in results):
        print(f"[ok] Los {len(results)} negocios compilan en la nube igual que en este equipo.")
        return 0
    print("[error] Hay negocios que no coinciden: revisa antes de usar la nube.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
