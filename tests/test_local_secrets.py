"""El archivo local de secretos: lleva la misma clave de un equipo a otro sin cambiarla, sin mostrarla y sin subirla a GitHub."""
from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
from pathlib import Path

import httpx
import pytest
from cryptography.fernet import Fernet

from app.domain.business_config.errors import SecretResolutionError
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.business_config.payment_secret_store import SECRETS_KEY_ENV
from app.infrastructure.business_config.secrets_key import DEFAULT_SECRETS_FILE, SECRETS_FILE_ENV, ensure_secrets_key, read_shared_key, secrets_file

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT = ROOT_DIR / "scripts" / "local_secrets.py"
RUN_SCRIPT = ROOT_DIR / "scripts" / "run_admin_api.py"
EXAMPLE = ROOT_DIR / "secrets.local.env.example"
LINK_REF = "secret_store:principal.link"
LINK_VALUE = "https://pagos-ficticios.example/multiplataforma"


def _script():
    spec = importlib.util.spec_from_file_location("local_secrets_script", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_secrets_file(path: Path) -> dict[str, str]:
    return _script().read_secrets_file(path)


def _document(slug: str) -> dict:
    return {
        "schema_version": "1.0",
        "tenant_slug": slug,
        "identity": {"name": "Negocio ficticio", "industry": "pruebas", "description": "Ficticio.", "value_proposition": "Ficticia."},
        "offer": {"model": "plans", "plans": [{"id": "basico", "name": "Básico", "prices": [{"currency": "COP", "monthly": 100000}], "includes": ["Soporte"], "payment_profile": "principal"}]},
        "terms": {},
        "payments": [{"id": "principal", "link": {"secret_ref": LINK_REF}, "transfer_enabled": False}],
        "sales": {},
        "capabilities": {
            "service_channels": ["whatsapp"],
            "actions_support": ["responder_dudas"],
            "closing_methods": {"payment_link": True, "human_handoff": False, "data_collection": True},
            "data_collection": {"enabled": True, "fields": ["nombre"]},
        },
        "messages": {"welcome": {"enabled": False, "text": ""}},
        "response_style": {"length": "short"},
        "knowledge": {"faqs": []},
        "inventory": {"items": []},
    }


@pytest.fixture
def machine(tmp_path, monkeypatch):
    """Un equipo ficticio: sus rutas, su clave en la carpeta del usuario y una base con un dato de pago cifrado con ella."""
    key = Fernet.generate_key().decode()
    home = tmp_path / "perfil"
    key_file = home / ".ai-sales-engine" / "business_config_secrets.key"
    key_file.parent.mkdir(parents=True)
    key_file.write_text(key, encoding="ascii")
    database_url = f"sqlite:///{(tmp_path / 'business_config.sqlite3').as_posix()}"
    engine = create_business_config_engine(database_url)
    create_local_schema(engine)
    build_business_config_service(engine, secrets_key=key).create_business("cafe_aroma", "Café Aroma", document=_document("cafe_aroma"), payment_values={LINK_REF: LINK_VALUE})
    engine.dispose()
    env_file = tmp_path / ".env"
    env_file.write_text("# TOKEN_VIEJO=comentario-que-no-debe-viajar\nOPENROUTER_API_KEY=clave-ficticia-del-modelo\nexport TENANT_SLUG=cafe_aroma\nDATABASE_URL='postgresql://u:p$a@localhost/db'\n", encoding="utf-8")
    monkeypatch.setenv(SECRETS_KEY_ENV, "")
    return type("Machine", (), {"key": key, "key_file": key_file, "database_url": database_url, "env_file": env_file, "target": tmp_path / "secrets.local.env", "root": tmp_path})


def test_export_keeps_the_exact_key_and_every_variable_without_showing_them(machine, capsys):
    assert _script().export_secrets(machine.target, machine.env_file, machine.key_file) == 0

    values = read_secrets_file(machine.target)
    assert values[SECRETS_KEY_ENV] == machine.key
    assert machine.key.endswith("=")
    assert values["OPENROUTER_API_KEY"] == "clave-ficticia-del-modelo"
    assert values["TENANT_SLUG"] == "cafe_aroma"
    assert values["DATABASE_URL"] == "postgresql://u:p$a@localhost/db"
    assert machine.key_file.read_text(encoding="ascii") == machine.key
    assert "comentario-que-no-debe-viajar" not in machine.target.read_text(encoding="utf-8")
    assert b"\r\n" not in machine.target.read_bytes()

    printed = capsys.readouterr().out
    assert "OPENROUTER_API_KEY" in printed
    for secret in (machine.key, "clave-ficticia-del-modelo", "p$a"):
        assert secret not in printed


def test_export_never_generates_a_key(machine, capsys):
    machine.key_file.unlink()
    assert _script().export_secrets(machine.target, machine.env_file, machine.key_file) == 1
    assert not machine.target.exists()
    assert not machine.key_file.exists()
    assert "no genera claves" in capsys.readouterr().out


def test_export_never_changes_a_key_that_is_already_there(machine, capsys):
    other = Fernet.generate_key().decode()
    machine.target.write_text(f"{SECRETS_KEY_ENV}={other}\n", encoding="utf-8")
    assert _script().export_secrets(machine.target, machine.env_file, machine.key_file) == 1
    assert read_secrets_file(machine.target)[SECRETS_KEY_ENV] == other
    assert other not in capsys.readouterr().out


def test_export_updates_the_variables_and_keeps_what_was_added_by_hand(machine):
    script = _script()
    assert script.export_secrets(machine.target, machine.env_file, machine.key_file) == 0
    with machine.target.open("a", encoding="utf-8") as handle:
        handle.write("TOKEN_A_MANO=valor-a-mano\n")
    machine.env_file.write_text("OPENROUTER_API_KEY=clave-nueva\n", encoding="utf-8")

    assert script.export_secrets(machine.target, machine.env_file, machine.key_file) == 0
    values = read_secrets_file(machine.target)
    assert values[SECRETS_KEY_ENV] == machine.key
    assert values["OPENROUTER_API_KEY"] == "clave-nueva"
    assert values["TOKEN_A_MANO"] == "valor-a-mano"


def test_a_value_that_cannot_travel_intact_stops_the_export(machine, capsys):
    machine.env_file.write_text('MULTILINEA="linea uno\nlinea dos"\n', encoding="utf-8")
    assert _script().export_secrets(machine.target, machine.env_file, machine.key_file) == 1
    assert not machine.target.exists()
    assert "linea uno" not in capsys.readouterr().out


def test_install_creates_the_env_of_the_other_machine_without_the_key(machine, capsys):
    script = _script()
    script.export_secrets(machine.target, machine.env_file, machine.key_file)
    capsys.readouterr()
    new_env = machine.root / "otro_equipo.env"

    assert script.install_secrets(machine.target, new_env) == 0

    assert read_secrets_file(new_env) == {"OPENROUTER_API_KEY": "clave-ficticia-del-modelo", "TENANT_SLUG": "cafe_aroma", "DATABASE_URL": "postgresql://u:p$a@localhost/db"}
    printed = capsys.readouterr().out
    assert machine.key not in printed and "clave-ficticia-del-modelo" not in printed


def test_install_never_overwrites_an_existing_env(machine, capsys):
    script = _script()
    script.export_secrets(machine.target, machine.env_file, machine.key_file)
    capsys.readouterr()
    machine.env_file.write_text("OPENROUTER_API_KEY=clave-local-distinta\n", encoding="utf-8")

    assert script.install_secrets(machine.target, machine.env_file) == 0

    assert machine.env_file.read_text(encoding="utf-8") == "OPENROUTER_API_KEY=clave-local-distinta\n"
    printed = capsys.readouterr().out
    assert "no se modificó" in printed and "OPENROUTER_API_KEY" in printed
    assert "clave-local-distinta" not in printed and "clave-ficticia-del-modelo" not in printed


def test_install_requires_the_file_and_its_key(machine, capsys):
    script = _script()
    assert script.install_secrets(machine.target, machine.root / "x.env") == 1
    machine.target.write_text("OPENROUTER_API_KEY=algo\n", encoding="utf-8")
    assert script.install_secrets(machine.target, machine.root / "x.env") == 1
    assert not (machine.root / "x.env").exists()


def test_check_decrypts_every_value_without_showing_anything(machine, capsys):
    script = _script()
    script.export_secrets(machine.target, machine.env_file, machine.key_file)
    capsys.readouterr()

    assert script.check_secrets(machine.target, machine.key_file, machine.database_url) == 0

    printed = capsys.readouterr().out
    assert "1 de 1 datos de pago se descifran" in printed
    assert "1 negocios" in printed
    for secret in (machine.key, LINK_VALUE, "clave-ficticia-del-modelo"):
        assert secret not in printed


def test_check_fails_with_a_key_that_does_not_decrypt_the_data(machine, capsys):
    other = Fernet.generate_key().decode()
    machine.target.write_text(f"{SECRETS_KEY_ENV}={other}\n", encoding="utf-8")
    machine.key_file.unlink()

    assert _script().check_secrets(machine.target, machine.key_file, machine.database_url) == 1

    printed = capsys.readouterr().out
    assert "0 de 1 datos de pago se descifran" in printed
    assert other not in printed


def test_check_says_which_of_two_keys_decrypts_the_data(machine, capsys):
    other = Fernet.generate_key().decode()
    machine.target.write_text(f"{SECRETS_KEY_ENV}={other}\n", encoding="utf-8")

    assert _script().check_secrets(machine.target, machine.key_file, machine.database_url) == 1

    printed = capsys.readouterr().out
    assert "la del archivo: 0 de 1" in printed
    assert "la de la carpeta del usuario: 1 de 1" in printed
    assert other not in printed and machine.key not in printed


def test_check_does_not_create_a_database_that_is_not_there(machine, capsys):
    script = _script()
    script.export_secrets(machine.target, machine.env_file, machine.key_file)
    missing = machine.root / "no_existe.sqlite3"

    assert script.check_secrets(machine.target, machine.key_file, f"sqlite:///{missing.as_posix()}") == 1

    assert not missing.exists()
    assert "cópiala del otro equipo" in capsys.readouterr().out


@pytest.mark.parametrize(
    "text",
    [
        "﻿BUSINESS_CONFIG_SECRETS_KEY={key}\r\n",  # guardado con BOM y finales de línea de Windows
        "# comentario\n\nBUSINESS_CONFIG_SECRETS_KEY={key}\n",
        'BUSINESS_CONFIG_SECRETS_KEY="{key}"\n',
        "export BUSINESS_CONFIG_SECRETS_KEY={key}",
    ],
)
def test_the_key_is_read_exactly_however_the_file_was_saved(tmp_path, text):
    key = Fernet.generate_key().decode()
    path = tmp_path / "secrets.local.env"
    path.write_bytes(text.format(key=key).encode("utf-8"))
    # La API y este programa leen el archivo por caminos distintos y deben ver la misma clave.
    assert read_shared_key(path) == key
    assert read_secrets_file(path)[SECRETS_KEY_ENV] == key


def test_the_api_only_reads_the_line_of_the_key(tmp_path):
    key = Fernet.generate_key().decode()
    path = tmp_path / "secrets.local.env"
    path.write_text(f"OPENROUTER_API_KEY=clave-del-motor\nDATABASE_URL=algo\n{SECRETS_KEY_ENV}={key} # comentario\n", encoding="utf-8")
    assert read_shared_key(path) == key
    assert read_shared_key(tmp_path / "no_existe.env") == ""


def test_the_location_of_the_file_does_not_depend_on_the_user_folder(monkeypatch, tmp_path):
    monkeypatch.delenv(SECRETS_FILE_ENV)
    assert DEFAULT_SECRETS_FILE == ROOT_DIR / "secrets.local.env"
    assert secrets_file() == DEFAULT_SECRETS_FILE
    assert Path.home() not in DEFAULT_SECRETS_FILE.parents or ROOT_DIR in DEFAULT_SECRETS_FILE.parents
    chosen = tmp_path / "otra" / "ubicacion.env"
    monkeypatch.setenv(SECRETS_FILE_ENV, str(chosen))
    assert secrets_file() == chosen


def test_the_key_of_the_shared_file_is_used_and_nothing_is_created(machine, monkeypatch):
    _script().export_secrets(machine.target, machine.env_file, machine.key_file)
    machine.key_file.unlink()
    monkeypatch.setenv(SECRETS_FILE_ENV, str(machine.target))
    engine = create_business_config_engine(machine.database_url)

    assert ensure_secrets_key(engine, machine.key_file) is False

    assert os.environ[SECRETS_KEY_ENV] == machine.key
    assert not machine.key_file.exists()
    # Solo la clave: las variables del motor no llegan a la API.
    assert "clave-ficticia-del-modelo" not in os.environ.values()
    engine.dispose()


def test_two_different_keys_stop_the_start_without_choosing_one(machine, monkeypatch):
    other = Fernet.generate_key().decode()
    machine.target.write_text(f"{SECRETS_KEY_ENV}={other}\n", encoding="utf-8")
    monkeypatch.setenv(SECRETS_FILE_ENV, str(machine.target))
    engine = create_business_config_engine(machine.database_url)

    with pytest.raises(SecretResolutionError, match="dos claves distintas") as error:
        ensure_secrets_key(engine, machine.key_file)

    assert other not in str(error.value) and machine.key not in str(error.value)
    assert os.environ[SECRETS_KEY_ENV] == ""
    engine.dispose()


def test_a_blank_key_in_the_file_does_not_replace_the_one_of_the_user_folder(machine, monkeypatch):
    machine.target.write_text(f"{SECRETS_KEY_ENV}=\n", encoding="utf-8")
    monkeypatch.setenv(SECRETS_FILE_ENV, str(machine.target))
    engine = create_business_config_engine(machine.database_url)
    assert ensure_secrets_key(engine, machine.key_file) is False
    assert os.environ[SECRETS_KEY_ENV] == machine.key
    engine.dispose()


def test_without_any_key_the_message_says_where_to_put_it(machine, monkeypatch):
    machine.key_file.unlink()
    monkeypatch.setenv(SECRETS_FILE_ENV, str(machine.target))
    engine = create_business_config_engine(machine.database_url)
    with pytest.raises(SecretResolutionError, match="falta su clave") as error:
        ensure_secrets_key(engine, machine.key_file)
    assert machine.target.name in str(error.value)
    assert not machine.key_file.exists()
    engine.dispose()


def test_the_real_server_reads_the_data_on_a_new_machine_only_with_the_file(machine, tmp_path):
    """Otro perfil de usuario, sin clave en él: basta el archivo. Ni la crea ni la muestra."""
    _script().export_secrets(machine.target, machine.env_file, machine.key_file)
    new_home = tmp_path / "perfil_del_otro_equipo"
    new_home.mkdir()
    import socket

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    env = {
        **os.environ,
        SECRETS_KEY_ENV: "",
        SECRETS_FILE_ENV: str(machine.target),
        "BUSINESS_CONFIG_DATABASE_URL": machine.database_url,
        "ADMIN_API_PORT": str(port),
        "HOME": str(new_home),
        "USERPROFILE": str(new_home),
    }
    output = tmp_path / "salida.txt"
    with output.open("w", encoding="utf-8") as sink:
        server = subprocess.Popen([sys.executable, str(RUN_SCRIPT)], env=env, stdout=sink, stderr=subprocess.STDOUT)
    try:
        waited = subprocess.run([sys.executable, str(RUN_SCRIPT), "--wait"], env=env, capture_output=True, encoding="utf-8", timeout=60)
        assert waited.returncode == 0
        base = f"http://127.0.0.1:{port}/api/businesses/cafe_aroma"
        assert httpx.get(f"{base}/review").json()["compiles"] is True
        assert [field["status"] for field in httpx.get(f"{base}/config").json()["payment_fields"].values()] == ["configured"]
    finally:
        server.terminate()
        server.wait(timeout=20)
    assert not (new_home / ".ai-sales-engine").exists()
    assert machine.key not in output.read_text(encoding="utf-8")


def test_the_real_server_refuses_to_start_with_two_different_keys(machine, tmp_path):
    other = Fernet.generate_key().decode()
    machine.target.write_text(f"{SECRETS_KEY_ENV}={other}\n", encoding="utf-8")
    env = {
        **os.environ,
        SECRETS_KEY_ENV: "",
        SECRETS_FILE_ENV: str(machine.target),
        "BUSINESS_CONFIG_DATABASE_URL": machine.database_url,
        "HOME": str(machine.key_file.parent.parent),
        "USERPROFILE": str(machine.key_file.parent.parent),
    }
    result = subprocess.run([sys.executable, str(RUN_SCRIPT)], env=env, capture_output=True, encoding="utf-8", timeout=60)
    assert result.returncode == 1
    assert "dos claves distintas" in result.stdout
    assert other not in result.stdout and machine.key not in result.stdout


def test_the_command_line_check_works_and_prints_no_values(machine):
    _script().export_secrets(machine.target, machine.env_file, machine.key_file)
    env = {**os.environ, SECRETS_KEY_ENV: "", SECRETS_FILE_ENV: str(machine.target), "BUSINESS_CONFIG_DATABASE_URL": machine.database_url, "HOME": str(machine.root), "USERPROFILE": str(machine.root), "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run([sys.executable, str(SCRIPT), "check"], env=env, capture_output=True, encoding="utf-8", timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 de 1" in result.stdout
    assert machine.key not in result.stdout + result.stderr


@pytest.mark.skipif(os.name == "nt", reason="los permisos de POSIX no existen en Windows")
def test_on_unix_only_the_owner_can_read_the_files(machine):
    script = _script()
    script.export_secrets(machine.target, machine.env_file, machine.key_file)
    new_env = machine.root / "otro.env"
    script.install_secrets(machine.target, new_env)
    assert stat.S_IMODE(machine.target.stat().st_mode) == 0o600
    assert stat.S_IMODE(new_env.stat().st_mode) == 0o600


@pytest.mark.skipif(os.name != "nt", reason="las listas de acceso de NTFS solo existen en Windows")
def test_on_windows_only_the_owner_can_read_the_files(machine):
    script = _script()
    script.export_secrets(machine.target, machine.env_file, machine.key_file)
    granted = subprocess.run(["icacls", str(machine.target)], capture_output=True, encoding="utf-8", errors="replace").stdout
    rows = [line.strip() for line in granted.splitlines() if ":(" in line]
    assert len(rows) == 1
    assert (os.environ.get("USERNAME") or "").lower() in rows[0].lower()
    assert "(I)" not in rows[0]
    assert read_secrets_file(machine.target)[SECRETS_KEY_ENV] == machine.key


def test_git_ignores_the_real_file_and_not_the_example():
    def ignored(name: str) -> bool:
        return subprocess.run(["git", "check-ignore", "-q", "--no-index", name], cwd=ROOT_DIR).returncode == 0

    assert ignored("secrets.local.env")
    assert ignored("secrets.local.env.tmp")
    assert not ignored("secrets.local.env.example")
    assert "secrets.local.env" in (ROOT_DIR / ".dockerignore").read_text(encoding="utf-8")


def test_the_example_has_no_values_and_names_what_the_project_needs():
    values = dict(_script()._assignments(EXAMPLE))
    assert set(values.values()) == {""}
    assert {SECRETS_KEY_ENV, "OPENROUTER_API_KEY", "DATABASE_URL", "META_VERIFY_TOKEN"} <= set(values)
    # Nada del sistema anterior: el polling de Telegram y su negocio fijo se retiraron.
    assert not {"TELEGRAM_TOKEN", "TELEGRAM_ADMIN_ID", "TENANT_SLUG"} & set(values)


def test_the_guide_explains_both_systems_and_how_to_move_the_file():
    guide = (ROOT_DIR / "docs" / "operations.md").read_text(encoding="utf-8")
    section = guide[guide.index("### Trabajar Desde Windows Y macOS") :]
    for expected in ("local_secrets.py export", "local_secrets.py install", "local_secrets.py check", "scp ", "business_config.sqlite3", "source .venv/bin/activate", ".venv\\Scripts\\Activate.ps1"):
        assert expected in section
