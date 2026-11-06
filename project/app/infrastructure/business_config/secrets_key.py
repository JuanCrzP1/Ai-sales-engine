"""La clave que cifra los datos de pago: se reutiliza siempre y nunca se reemplaza.

Se toma, en este orden, de `BUSINESS_CONFIG_SECRETS_KEY`, del archivo local de secretos (`secrets.local.env`, ignorado por git, que
permite usar la misma clave en varios equipos) o de un archivo de la carpeta del usuario, que se crea la primera vez solo si la base
no tiene nada cifrado. Conviene guardar una copia: sin esa clave, los datos de pago no se pueden leer.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from cryptography.fernet import Fernet
from sqlalchemy import func, select
from sqlalchemy.engine import Engine

from app.domain.business_config.errors import SecretResolutionError
from app.infrastructure.business_config.payment_secret_store import SECRETS_KEY_ENV
from app.infrastructure.business_config.tables import business_config_secrets

KEY_FILE = Path.home() / ".ai-sales-engine" / "business_config_secrets.key"
SECRETS_FILE_ENV = "AI_SALES_ENGINE_SECRETS_FILE"
DEFAULT_SECRETS_FILE = Path(__file__).resolve().parents[4] / "secrets.local.env"
_SHARED_KEY_LINE = re.compile(rf"^\s*(?:export\s+)?{SECRETS_KEY_ENV}\s*=(.*)$")


def secrets_file() -> Path:
    """El archivo local de secretos: en la raíz del repositorio, o donde indique `AI_SALES_ENGINE_SECRETS_FILE`."""
    return Path(os.getenv(SECRETS_FILE_ENV) or DEFAULT_SECRETS_FILE)


def read_shared_key(path: Path) -> str:
    """La clave del archivo local, exacta; vacía si no está. Admite BOM, finales de línea de Windows y comillas.

    Solo se lee esa línea: la API no toca las variables del motor que viajan en el mismo archivo.
    """
    if not path.is_file():
        return ""
    key = ""
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        match = _SHARED_KEY_LINE.match(line)
        if match:
            key = match[1].split(" #")[0].strip().strip("\"'")
    return key


def ensure_secrets_key(engine: Engine, key_file: Path = KEY_FILE) -> bool:
    """Deja la clave disponible para este proceso y dice si tuvo que crearla.

    Solo la crea si la base no tiene nada cifrado: otra clave dejaría esos datos ilegibles.
    """
    if os.getenv(SECRETS_KEY_ENV):
        return False
    shared_file = secrets_file()
    shared_key = read_shared_key(shared_file)
    if shared_key:
        if key_file.is_file() and key_file.read_text(encoding="ascii").strip() != shared_key:
            raise SecretResolutionError(
                f"hay dos claves distintas, en {shared_file} y en {key_file}: "
                "'python scripts/local_secrets.py check' indica cuál descifra los datos; conserva solo esa"
            )
        os.environ[SECRETS_KEY_ENV] = shared_key
        return False
    created = not key_file.is_file()
    if created:
        with engine.connect() as connection:
            encrypted = connection.execute(select(func.count()).select_from(business_config_secrets)).scalar_one()
        if encrypted:
            raise SecretResolutionError(
                f"la base tiene datos de pago cifrados y falta su clave: coloca {shared_file}, restaura {key_file} o define {SECRETS_KEY_ENV}"
            )
        key_file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor = os.open(key_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="ascii") as handle:
            handle.write(Fernet.generate_key().decode())
    os.environ[SECRETS_KEY_ENV] = key_file.read_text(encoding="ascii").strip()
    return created
