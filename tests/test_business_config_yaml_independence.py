"""
El almacén de BusinessConfig funciona solo: sin YAML, sin el motor, sin `.env` y sin las carpetas de los negocios.

Las comprobaciones corren en procesos aparte sobre una copia mínima del código, con solo los paquetes del almacén: en ese
árbol no existen los YAML, ni el motor, ni `.env`, ni las carpetas de los negocios. Además, un gancho de auditoría registra
cualquier intento de abrir esos archivos y se comprueba qué módulos se cargaron.

Sembrar los negocios de ejemplo (`init_local_business_config.py --import-tenants`) lee solo sus tres JSON y nada más.
Los YAML se retiraron el 11 de noviembre de 2026; la referencia de lo que compilaban está en `tests/golden/`.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from app.domain.business_config.payment_data import payment_values
from app.infrastructure.business_config.database import DATABASE_URL_ENV, DEFAULT_LOCAL_DATABASE
from app.infrastructure.business_config.payment_secret_store import SECRETS_KEY_ENV
from pipeline_harness import TENANTS, engine_sections

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
SCRIPT = ROOT_DIR / "scripts" / "init_local_business_config.py"
EXAMPLE_PATH = PROJECT_DIR / "config" / "contracts" / "v1" / "business-config.example.json"
LINK_REF = "secret_store:principal.link"
PHONE_REF = "secret_store:principal.transfer.0.number"
SYSTEM_ENV = ("PATH", "SYSTEMROOT", "TEMP", "TMP", "HOME", "USERPROFILE", "LOCALAPPDATA", "APPDATA")


def _digest(value) -> str:
    canonical = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _base_env(url: str | None = None, key: str | None = None) -> dict[str, str]:
    env = {name: os.environ[name] for name in SYSTEM_ENV if name in os.environ}
    env.update(PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1", ENABLE_FILE_LOGS="0")
    if url:
        env[DATABASE_URL_ENV] = url
    if key:
        env[SECRETS_KEY_ENV] = key
    return env


@pytest.fixture(scope="module")
def isolated_tree(tmp_path_factory) -> Path:
    """Solo los paquetes del nuevo sistema: ni motor, ni YAML, ni `.env`, ni carpetas de negocio."""
    tree = tmp_path_factory.mktemp("arbol_sin_yaml")
    ignore = shutil.ignore_patterns("__pycache__")
    for package in ("app/domain/business_config", "app/business_config_application", "app/infrastructure/business_config"):
        shutil.copytree(PROJECT_DIR / package, tree / package, ignore=ignore)
    for init in ("app/__init__.py", "app/domain/__init__.py", "app/infrastructure/__init__.py"):
        shutil.copy(PROJECT_DIR / init, tree / init)
    shutil.copy(Path(__file__).parent / "business_config_isolated_driver.py", tree / "driver.py")
    assert not [path for path in tree.rglob("*") if path.suffix in (".yaml", ".yml") or path.name.startswith(".env")]
    return tree


def _run_isolated(tree: Path, spec: dict, url: str, key: str) -> dict:
    env = _base_env(url, key)
    # Si algo intentara usar la base del motor, esta URL fallaría: el almacén es independiente de ella.
    env.update(DATABASE_URL="postgresql://base-del-motor-no-disponible/invalida", PYTHONPATH=str(tree), BC_FORBIDDEN_ROOT=str(PROJECT_DIR))
    result = subprocess.run(
        [sys.executable, str(tree / "driver.py")], input=json.dumps(spec), capture_output=True, encoding="utf-8", cwd=tree, env=env, timeout=180
    )
    assert result.returncode == 0, result.stderr[-3000:]
    output = json.loads(result.stdout)
    assert output["opened"] == [], "el nuevo sistema abrió YAML, .env o archivos del proyecto original"
    assert output["forbidden_modules"] == [], "el nuevo sistema cargó módulos del motor o de los YAML"
    assert Path(output["app_location"]).is_relative_to(tree)
    return output["facts"]


def _new_business_document(slug: str) -> dict:
    document = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    document["tenant_slug"] = slug
    document["payments"] = [
        {
            "id": "principal",
            "link": {"secret_ref": LINK_REF},
            "transfer_enabled": True,
            "transfer_methods": [{"type": "nequi", "number": {"secret_ref": PHONE_REF}}],
        }
    ]
    document["offer"]["catalog"]["payment_profile"] = "principal"
    return document


def test_full_cycle_of_a_new_business_without_yaml_and_survives_a_restart(isolated_tree, tmp_path):
    """Crear, guardar, recuperar, publicar, editar, consultar el historial, revertir y recuperar, sin carpetas ni YAML."""
    database = tmp_path / "datos" / "business_config.sqlite3"
    url, key = f"sqlite:///{database.as_posix()}", Fernet.generate_key().decode()
    slug = "floristeria_nueva"
    facts = _run_isolated(
        isolated_tree,
        {
            "scenario": "cycle",
            "slug": slug,
            "document": _new_business_document(slug),
            "values": {LINK_REF: "https://pagos.ejemplo/primero", PHONE_REF: "3005556677"},
            "new_link": "https://pagos.ejemplo/segundo",
        },
        url,
        key,
    )
    assert database.is_file(), "la base se crea sola en la ruta indicada"
    assert not (PROJECT_DIR / "config" / "tenants" / slug).exists(), "crear un negocio no crea carpetas"
    assert facts["created_draft"] == facts["recovered_draft"] == 1 and facts["draft_after_publish"] is True
    assert facts["edited_draft_name"] == "Nombre editado" and facts["published_name_before"] != "Nombre editado"
    assert facts["published_name_after"] == "Nombre editado" and facts["new_link_compiled"] is True
    assert facts["history"] == [[1, "archived"], [2, "published"]]
    assert facts["rollback_to"] == 1 and facts["digest_after_rollback"] == facts["published_digest_1"], "revertir recupera también los pagos"
    assert facts["restored"] == 3 and facts["restored_name"] == "Nombre editado"

    restarted = _run_isolated(isolated_tree, {"scenario": "reopen", "slug": slug}, url, key)
    assert restarted["businesses"] == [slug] and restarted["draft"] == 3
    assert restarted["digest"] == facts["published_digest_1"]
    assert restarted["history"] == [[1, "published"], [2, "archived"], [3, "draft"]]

    raw = database.read_bytes()
    assert b"pagos.ejemplo" not in raw and b"3005556677" not in raw


# ---------------------------------------------------------------------------
# Procedimiento documentado
# ---------------------------------------------------------------------------

AUDITED_SCRIPT = """
import json, os, runpy, sys
opened = []
def audit(event, args):
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        path = os.fsdecode(args[0]).replace(os.sep, "/")
        name = os.path.basename(path).lower()
        if name.endswith((".yaml", ".yml")) or name.startswith(".env") or "/config/tenants/" in path:
            opened.append(name)
sys.addaudithook(audit)
sys.argv = sys.argv[1:]
code = 0
try:
    runpy.run_path(sys.argv[0], run_name="__main__")
except SystemExit as exc:
    code = exc.code or 0
loaded = [name for name in ("yaml", "app.application", "app.config", "app.infrastructure.config") if name in sys.modules]
print("AUDITORIA " + json.dumps({"opened": opened, "loaded": loaded}))
sys.exit(code)
"""


def _run_script(*args: str, url: str, key: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", AUDITED_SCRIPT, str(SCRIPT), *args], capture_output=True, encoding="utf-8", cwd=ROOT_DIR, env=_base_env(url, key), timeout=240
    )


def _audit_of(result: subprocess.CompletedProcess) -> dict:
    return json.loads(next(line for line in result.stdout.splitlines() if line.startswith("AUDITORIA ")).removeprefix("AUDITORIA "))


def test_documented_procedure_creates_the_database_without_yaml_or_key(tmp_path):
    database = tmp_path / "nueva" / "carpeta" / "business_config.sqlite3"
    result = _run_script(url=f"sqlite:///{database.as_posix()}")
    assert result.returncode == 0, result.stderr[-2000:]
    assert database.is_file()
    audit = _audit_of(result)
    assert audit == {"opened": [], "loaded": []}, "crear la base no lee YAML ni carga el motor"
    size = database.stat().st_size
    assert _run_script(url=f"sqlite:///{database.as_posix()}").returncode == 0
    assert database.stat().st_size == size


@pytest.mark.parametrize("key", [None, "no-es-una-clave-fernet"], ids=["sin_clave", "clave_invalida"])
def test_import_writes_nothing_without_a_valid_key(tmp_path, key):
    database = tmp_path / "business_config.sqlite3"
    result = _run_script("--import-tenants", url=f"sqlite:///{database.as_posix()}", key=key)
    assert result.returncode == 1
    assert SECRETS_KEY_ENV in result.stdout
    assert not database.exists(), "sin una clave válida no se crea ni se escribe nada"
    assert _audit_of(result) == {"opened": [], "loaded": []}
    if key:
        assert key not in result.stdout + result.stderr


@pytest.fixture(scope="module")
def imported_nine(tmp_path_factory) -> tuple[Path, str, str, str]:
    """Migración inicial con el procedimiento documentado, dos veces, sobre una base temporal."""
    database = tmp_path_factory.mktemp("nueve_por_script") / "business_config.sqlite3"
    url, key = f"sqlite:///{database.as_posix()}", Fernet.generate_key().decode()
    first = _run_script("--import-tenants", url=url, key=key)
    assert first.returncode == 0, first.stderr[-3000:]
    second = _run_script("--import-tenants", url=url, key=key)
    assert second.returncode == 0, second.stderr[-3000:]
    return database, url, key, first.stdout + first.stderr + second.stdout + second.stderr


def test_documented_import_is_repeatable_and_prints_no_payment_data(imported_nine):
    _database, _url, _key, output = imported_nine
    assert f"importados={len(TENANTS)} ya_existian=0" in output
    assert f"importados=0 ya_existian={len(TENANTS)}" in output
    values = {value for slug in TENANTS for value in payment_values(engine_sections(slug))}
    assert values and [value for value in values if value in output] == []


def test_seeding_the_examples_reads_only_their_json_and_never_loads_the_engine(imported_nine):
    _database, _url, _key, output = imported_nine
    audits = [json.loads(line.removeprefix("AUDITORIA ")) for line in output.splitlines() if line.startswith("AUDITORIA ")]
    assert len(audits) == 2
    example_files = {"business-config.json", "engine-settings.json", "payment-values.json"}
    assert set(audits[0]["opened"]) == example_files, "solo lee los tres JSON de cada negocio de ejemplo"
    assert len(audits[0]["opened"]) == 3 * len(TENANTS)
    assert audits[1]["opened"] == [], "repetirla no vuelve a leer los ejemplos"
    for audit in audits:
        assert audit["loaded"] == [], "ni YAML, ni el motor, ni sus ajustes"


def test_imported_businesses_work_without_yaml_and_compile_to_their_reference(isolated_tree, imported_nine):
    """Los nueve negocios, ya en la base, compilan a su referencia original en un árbol donde no existen los YAML."""
    _database, url, key, _output = imported_nine
    expected = {slug: _digest(engine_sections(slug)) for slug in TENANTS}

    facts = _run_isolated(isolated_tree, {"scenario": "nine", "slugs": TENANTS}, url, key)
    assert facts["businesses"] == sorted(TENANTS)
    for slug in TENANTS:
        item = facts["by_slug"][slug]
        assert item["digest"] == expected[slug], f"{slug}: compilado sin YAML no coincide con su referencia"
        assert item["edited_changes_compilation"] is True and item["draft_recovered"] is True
        assert item["rollback_to"] == 1 and item["digest_after_rollback"] == expected[slug]
        assert item["history"] == [[1, "published"], [2, "archived"]]


def test_local_database_is_out_of_version_control_and_of_the_image():
    assert DEFAULT_LOCAL_DATABASE == PROJECT_DIR / "data" / "business_config.sqlite3"
    for ignore_file in (".gitignore", ".dockerignore"):
        assert "project/data/*.sqlite3*" in (ROOT_DIR / ignore_file).read_text(encoding="utf-8").splitlines(), ignore_file
    if shutil.which("git") and (ROOT_DIR / ".git").exists():
        for name in ("business_config.sqlite3", "business_config.sqlite3-journal", "business_config.sqlite3-wal"):
            ignored = subprocess.run(["git", "check-ignore", "-q", f"project/data/{name}"], cwd=ROOT_DIR)
            assert ignored.returncode == 0, name
