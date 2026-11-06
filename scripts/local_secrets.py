"""
local_secrets.py

Archivo local de secretos, para trabajar con los mismos datos desde varios equipos (Windows y macOS). `secrets.local.env`, en la
raíz del repositorio e ignorado por git, reúne la clave que cifra los datos de pago de BusinessConfig y las variables del `.env` del
motor. Este programa nunca imprime valores, nunca genera una clave y nunca cambia la existente.

Usage:
  python scripts/local_secrets.py export   # lo crea o lo actualiza en este equipo, desde su clave y su `.env`
  python scripts/local_secrets.py install  # en el otro equipo: protege el archivo y crea `.env` si falta
  python scripts/local_secrets.py check    # comprueba el archivo y que su clave descifra los datos de pago

Variable opcional: `AI_SALES_ENGINE_SECRETS_FILE` (otra ubicación del archivo). Instrucciones: docs/operations.md.
"""
from __future__ import annotations

import argparse
import getpass
import io
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "project"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from cryptography.fernet import Fernet, InvalidToken  # noqa: E402
from dotenv import dotenv_values  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

from app.domain.business_config.errors import SecretResolutionError  # noqa: E402
from app.infrastructure.business_config.database import create_business_config_engine  # noqa: E402
from app.infrastructure.business_config.payment_secret_store import SECRETS_KEY_ENV, check_secrets_key  # noqa: E402
from app.infrastructure.business_config.secrets_key import KEY_FILE, secrets_file  # noqa: E402
from app.infrastructure.business_config.tables import business_config_secrets, business_configs, tenants  # noqa: E402

ENV_FILE = REPO_ROOT / ".env"
HEADER = """\
# Secretos locales de AI Sales Engine. NO SUBIR A GITHUB: está en .gitignore y contiene valores reales.
# Traslado entre equipos e instalación: docs/operations.md, «Trabajar Desde Windows Y macOS».
# La clave de cifrado debe conservarse exacta, incluido el = final: sin ella, los datos de pago guardados no se pueden leer.

"""
_ASSIGNMENT = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$")


def read_secrets_file(path: Path) -> dict[str, str]:
    """Sus variables con valor, exactas. No expande `$` y admite un archivo guardado con BOM o con finales de línea de Windows."""
    if not path.is_file():
        return {}
    return {name: value for name, value in dotenv_values(path, interpolate=False, encoding="utf-8-sig").items() if value}


def _assignments(path: Path) -> dict[str, str]:
    """Cada `NOMBRE=valor` tal como está escrito. Los comentarios no viajan: podrían contener secretos antiguos."""
    if not path.is_file():
        return {}
    matches = map(_ASSIGNMENT.match, path.read_text(encoding="utf-8-sig").splitlines())
    return {match[1]: match[2].strip() for match in matches if match}


def _parsed(text: str) -> dict[str, str | None]:
    return dict(dotenv_values(stream=io.StringIO(text), interpolate=False))


def _restrict(path: Path) -> bool:
    """Deja el archivo legible solo por el usuario actual."""
    if os.name == "nt":
        user = os.environ.get("USERNAME") or getpass.getuser()
        return subprocess.run(["icacls", str(path), "/inheritance:r", "/grant:r", f"{user}:F"], capture_output=True).returncode == 0
    os.chmod(path, 0o600)
    return True


def _write_private(path: Path, text: str) -> None:
    """Escribe de una sola vez y con los permisos ya puestos: el archivo nunca queda a medias ni abierto a otros usuarios."""
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.unlink(missing_ok=True)
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    if not _restrict(temporary):
        print(f"[aviso] no se pudieron restringir los permisos de {path.name}")
    os.replace(temporary, path)


def _key_of_file(key_file: Path) -> str:
    return key_file.read_text(encoding="ascii").strip() if key_file.is_file() else ""


def _git_ignored(path: Path) -> bool | None:
    """True si git lo ignora, False si no, None si está fuera del repositorio o git no está disponible."""
    try:
        code = subprocess.run(["git", "check-ignore", "-q", str(path)], cwd=REPO_ROOT, capture_output=True).returncode
    except OSError:
        return None
    return {0: True, 1: False}.get(code)


def export_secrets(target: Path, env_file: Path = ENV_FILE, key_file: Path = KEY_FILE) -> int:
    current = read_secrets_file(target)
    personal_key = _key_of_file(key_file)
    key = os.getenv(SECRETS_KEY_ENV) or current.get(SECRETS_KEY_ENV) or personal_key
    if not key:
        print(f"[error] no hay ninguna clave en este equipo ({key_file}). Este programa no genera claves.")
        return 1
    try:
        check_secrets_key(key)
    except SecretResolutionError as exc:
        print(f"[error] {exc}")
        return 1
    for source, other in ((target, current.get(SECRETS_KEY_ENV)), (key_file, personal_key)):
        if other and other != key:
            print(f"[error] {source} tiene otra clave. No se cambió nada: 'check' indica cuál descifra los datos.")
            return 1

    # Lo añadido a mano al archivo se conserva; lo que esté en `.env` se actualiza.
    variables = {**_assignments(target), **_assignments(env_file)}
    variables.pop(SECRETS_KEY_ENV, None)
    lines = [f"{SECRETS_KEY_ENV}={key}"]
    if variables:
        lines += ["", "# Variables del motor. 'install' las copia a .env en el otro equipo."]
        lines += [f"{name}={value}" for name, value in variables.items()]
    text = HEADER + "\n".join(lines) + "\n"

    # Se comprueba antes de escribir: lo que se lea de vuelta debe ser exactamente lo que había.
    parsed = _parsed(text)
    environment = dict(dotenv_values(env_file, interpolate=False, encoding="utf-8-sig")) if env_file.is_file() else {}
    environment.pop(SECRETS_KEY_ENV, None)
    different = sorted(name for name, value in environment.items() if parsed.get(name) != value)
    if parsed.get(SECRETS_KEY_ENV) != key or different:
        print(f"[error] no se pudieron trasladar sin alterarlas: {different or SECRETS_KEY_ENV}. No se escribió nada.")
        return 1

    _write_private(target, text)
    print(f"[ok] {target}: clave de cifrado y {len(variables)} variables más: {', '.join(variables) or 'ninguna'}")
    if not env_file.is_file():
        print(f"[aviso] no hay {env_file}: el archivo solo lleva lo anterior")
    if _git_ignored(target) is False:
        print("[error] git NO ignora este archivo: añádelo a .gitignore antes de hacer commit")
        return 1
    return 0


def install_secrets(target: Path, env_file: Path = ENV_FILE) -> int:
    if not target.is_file():
        print(f"[error] no existe {target}: cópialo primero desde el otro equipo (docs/operations.md)")
        return 1
    if not read_secrets_file(target).get(SECRETS_KEY_ENV):
        print(f"[error] {target} no tiene {SECRETS_KEY_ENV}")
        return 1
    if _restrict(target):
        print(f"[ok] {target}: solo tu usuario puede leerlo")
    else:
        print(f"[aviso] no se pudieron restringir los permisos de {target}")

    written = _assignments(target)
    variables = {name: value for name, value in written.items() if name != SECRETS_KEY_ENV and value}
    if not variables:
        print("[ok] no trae variables del motor: el panel no las necesita")
    elif env_file.is_file():
        incoming, existing = read_secrets_file(target), read_secrets_file(env_file)
        different = sorted(name for name in variables if incoming.get(name) != existing.get(name))
        if different:
            print(f"[aviso] {env_file} ya existe y no se modificó. Variables distintas: {', '.join(different)}")
        else:
            print(f"[ok] {env_file} ya coincide")
    else:
        _write_private(env_file, "\n".join(f"{name}={value}" for name, value in variables.items()) + "\n")
        print(f"[ok] {env_file} creado con {len(variables)} variables: {', '.join(variables)}")
    print("Comprueba con: python scripts/local_secrets.py check")
    return 0


def _decrypted(ciphertexts: list[str], key: str) -> int:
    cipher = Fernet(key.encode("utf-8"))
    count = 0
    for ciphertext in ciphertexts:
        try:
            cipher.decrypt(ciphertext.encode("ascii"))
            count += 1
        except InvalidToken:
            pass
    return count


def check_secrets(target: Path, key_file: Path = KEY_FILE, database_url: str | None = None) -> int:
    if not target.is_file():
        print(f"[error] no existe {target}")
        return 1
    ok = True
    ignored = _git_ignored(target)
    if ignored is False:
        print(f"[error] git NO ignora {target}: añádelo a .gitignore")
        ok = False
    elif ignored:
        print(f"[ok] {target}: git lo ignora")
    else:
        print(f"[ok] {target}: fuera del repositorio")
    if os.name != "nt" and stat.S_IMODE(target.stat().st_mode) & 0o077:
        print("[aviso] otros usuarios pueden leerlo: 'install' lo corrige")

    values = read_secrets_file(target)
    key = values.get(SECRETS_KEY_ENV, "")
    try:
        check_secrets_key(key)
    except SecretResolutionError as exc:
        print(f"[error] {exc}")
        return 1
    print(f"[ok] clave de cifrado con formato válido | otras variables: {len(values) - 1}")

    candidates = {"la del archivo": key}
    personal_key = _key_of_file(key_file)
    if personal_key and personal_key != key:
        print(f"[error] {key_file} tiene otra clave: la API no arrancará hasta que quede solo una")
        candidates["la de la carpeta del usuario"] = personal_key
        ok = False
    active = os.getenv(SECRETS_KEY_ENV)
    if active and active != key:
        print(f"[error] {SECRETS_KEY_ENV} está definida con otra clave y tiene prioridad")
        candidates["la de la variable de entorno"] = active
        ok = False

    engine = create_business_config_engine(database_url)
    try:
        location = engine.url.database
        if engine.dialect.name == "sqlite" and location and not Path(location).is_file():
            print(f"[error] no hay base en {location}: cópiala del otro equipo con el sistema apagado")
            return 1
        with engine.connect() as connection:
            businesses = connection.execute(select(func.count()).select_from(tenants)).scalar_one()
            versions = connection.execute(select(func.count()).select_from(business_configs)).scalar_one()
            ciphertexts = list(connection.execute(select(business_config_secrets.c.ciphertext)).scalars())
    finally:
        engine.dispose()
    print(f"[ok] base {location}: {businesses} negocios, {versions} versiones")
    for label, candidate in candidates.items():
        count = _decrypted(ciphertexts, candidate)
        readable = count == len(ciphertexts)
        print(f"[{'ok' if readable else 'error'}] {label}: {count} de {len(ciphertexts)} datos de pago se descifran")
        ok = ok and readable
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Archivo local de secretos. Nunca imprime valores.")
    parser.add_argument("command", choices=["export", "install", "check"])
    command = parser.parse_args(argv).command
    target = secrets_file()
    if command == "export":
        return export_secrets(target)
    if command == "install":
        return install_secrets(target)
    return check_secrets(target)


if __name__ == "__main__":
    raise SystemExit(main())
