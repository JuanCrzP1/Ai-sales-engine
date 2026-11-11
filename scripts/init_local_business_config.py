"""
init_local_business_config.py

Prepara la base local de BusinessConfig: un archivo SQLite ignorado por git e independiente de la base del
motor (`BUSINESS_CONFIG_DATABASE_URL` indica otra ubicación). No toca lo que la base ya contenga.

Con `--import-tenants` registra y publica además los negocios de ejemplo de `project/config/tenants/` (sus
`business-config.json`), con sus datos de pago de ejemplo en el almacén cifrado. Los negocios que ya tienen versiones
no se tocan. Exige `BUSINESS_CONFIG_SECRETS_KEY`, que se comprueba antes de escribir nada.

No modifica los ejemplos del repositorio y nunca imprime datos de pago.

Usage:
  python scripts/init_local_business_config.py                   # crea la base y las tablas
  python scripts/init_local_business_config.py --import-tenants  # además importa los negocios

Clave de cifrado (guárdala fuera del repositorio; sin ella los datos de pago no se pueden leer):
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "project"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.domain.business_config.errors import SecretResolutionError  # noqa: E402
from app.infrastructure.business_config.database import (  # noqa: E402
    build_business_config_service,
    create_business_config_engine,
    create_local_schema,
)
from app.infrastructure.business_config.payment_secret_store import check_secrets_key  # noqa: E402


def _import_tenants(engine) -> int:
    from app.infrastructure.business_config.example_businesses import import_examples

    report = import_examples(build_business_config_service(engine))
    print(f"[ok] importados={len(report.created)} ya_existian={len(report.skipped)}")
    if report.unpublished:
        print(f"[aviso] ya existían sin ninguna versión publicada, no se tocaron: {', '.join(report.unpublished)}")
        return 1
    return 0


def main() -> int:
    import_tenants = "--import-tenants" in sys.argv[1:]
    if import_tenants:
        try:
            check_secrets_key()
        except SecretResolutionError as exc:
            print(f"[error] {exc} (ver la ayuda de este script)")
            return 1
    engine = create_business_config_engine()
    try:
        create_local_schema(engine)
        print(f"[ok] base lista: {engine.url.render_as_string(hide_password=True)}")
        if not import_tenants:
            return 0
        try:
            return _import_tenants(engine)
        except (ValueError, SecretResolutionError) as exc:
            # Datos que no se pueden importar tal cual: se informa sin escribir nada y sin traza.
            print(f"[error] {exc}")
            return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
