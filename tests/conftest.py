from __future__ import annotations

import ast
import functools
import os
import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Bootstrap reproducible: declarar modo test ANTES de cualquier import de `app`.
# Garantiza que la suite corra sin .env local, sin DATABASE_URL y sin PostgreSQL
# (la config resuelve sqlite in-memory en contexto de test). setdefault respeta
# un MODE provisto externamente (p. ej. integración real).
os.environ.setdefault("MODE", "test")

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TESTS_DIR.parent / "project"

for _p in (str(PROJECT_DIR), str(TESTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


REDACTED_IN_REPORTS = "[dato de pago]"


@functools.lru_cache(maxsize=1)
def _payment_values() -> tuple[str, ...]:
    """Datos de pago de los YAML de los negocios (links, números, cuentas, referencias), del más largo al más corto."""
    try:
        from app.application.runtime.tenant_runtime_loader import _load_legacy_sections
        from app.domain.business_config.payment_data import payment_values
        from app.infrastructure.config.config_service import ConfigService

        service = ConfigService()
        values: set[str] = set()
        for tenant_dir in service.tenants_root.iterdir():
            if (tenant_dir / "pricing.yaml").is_file():
                values.update(payment_values(_load_legacy_sections(service, tenant_dir.name)))
        return tuple(sorted(values, key=len, reverse=True))
    except Exception:
        return ()


def _redact_payment_values(text: str) -> str:
    for value in _payment_values():
        text = text.replace(value, REDACTED_IN_REPORTS)
    return text


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Los informes de fallo (y la salida capturada) no muestran datos de pago en consola ni en los logs de CI."""
    outcome = yield
    report = outcome.get_result()
    if not report.failed:
        return
    text = str(report.longrepr)
    if any(value in text for value in _payment_values()):
        report.longrepr = _redact_payment_values(text)
    report.sections = [(title, _redact_payment_values(content)) for title, content in report.sections]


def _local_env_names() -> set[str]:
    """Nombres de las variables de los `.env` locales; nunca se leen sus valores."""
    names: set[str] = set()
    for env_file in (TESTS_DIR.parent / ".env", PROJECT_DIR / ".env"):
        if env_file.is_file():
            for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    names.add(line.split("=", 1)[0].removeprefix("export ").strip())
    return names


def _live_model_tests_requested(config) -> bool:
    """Las pruebas contra el modelo real solo corren si se piden expresamente con `-m integration`."""
    expression = config.getoption("markexpr", default="") or ""
    return re.search(r"(?<!not )\bintegration\b", expression) is not None


def _non_text_settings() -> set[str]:
    """Variables que `Settings` valida como booleano o número: no son credenciales y vacías detendrían la suite."""
    source = (PROJECT_DIR / "app" / "config" / "settings" / "base.py").read_text(encoding="utf-8")
    settings_class = next(node for node in ast.parse(source).body if isinstance(node, ast.ClassDef) and node.name == "Settings")
    return {
        field.target.id.upper()
        for field in settings_class.body
        if isinstance(field, ast.AnnAssign) and ast.unparse(field.annotation) in {"bool", "int", "float"}
    }


def pytest_configure(config):
    """Una ejecución normal no gasta API ni toca bases reales, aunque exista un `.env` local.

    Antes de que nada importe `app`, deja vacías las variables del `.env` y la clave del modelo: la
    configuración respeta un valor ya definido, así que ni la clave ni `DATABASE_URL` llegan a usarse. La
    suite corre igual que en el CI, que no tiene `.env`. Tampoco lee `secrets.local.env`, ni aunque exista.
    """
    os.environ["AI_SALES_ENGINE_SECRETS_FILE"] = os.devnull
    if _live_model_tests_requested(config):
        return
    for name in (_local_env_names() | {"OPENROUTER_API_KEY"}) - {"MODE"} - _non_text_settings():
        os.environ[name] = ""


def _llm_key_available() -> bool:
    """True si hay una OPENROUTER_API_KEY usable (no vacía ni placeholder)."""
    key = str(os.getenv("OPENROUTER_API_KEY") or "").strip()
    return bool(key) and key not in {"<<TOKEN>>", "<TOKEN>"}


@pytest.fixture(autouse=True)
def _live_tests_answer_with_their_own_business_key(request, monkeypatch):
    """La plataforma no tiene clave general: cada negocio usa la suya. En las pruebas en vivo, el negocio probado usa la
    `OPENROUTER_API_KEY` de quien las corre, como si la hubiera guardado en el panel."""
    if "integration" not in request.keywords:
        return
    from app.application import ai_pipeline
    from app.domain.business_config.ai_settings import AICredentials

    key = str(os.getenv("OPENROUTER_API_KEY") or "").strip()
    monkeypatch.setattr(ai_pipeline, "load_business_ai", lambda _slug: AICredentials("openrouter", None, key))


def pytest_collection_modifyitems(config, items):
    """Omite los tests marcados como integración cuando no hay OPENROUTER_API_KEY.

    `pytest` a secas nunca los ejecuta (ver `pytest_configure`): se SKIPean, no fallan. Solo corren con
    `pytest -m integration` y una clave disponible (.env local o secreto de CI), porque consumen API.
    """
    if _llm_key_available():
        return
    skip_integration = pytest.mark.skip(
        reason="integración: requiere OPENROUTER_API_KEY (LLM en vivo)"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture(autouse=True)
def _isolate_last_message_timestamps(request):
    """Aísla la marca del último mensaje del usuario en cada prueba.

    - test_sql_memory_repository.py → sin parches (valida la memoria SQL real)
    - resto                         → set/get_last_user_message_at usan un dict por prueba,
      de modo que el estado histórico de la DB no contamina las pruebas conversacionales,
      mientras los cambios dentro de la prueba (ventanas de actividad) siguen funcionando.
    """
    test_file = request.node.fspath.basename

    if test_file == "test_sql_memory_repository.py":
        yield
        return

    # Per-test in-memory store: (tenant_slug, user_id) → datetime | None
    # Captures writes done during this test only; DB state from previous runs is ignored.
    _mem_store: dict = {}

    # Capture the real implementation BEFORE the patch is applied.
    import importlib as _il
    _mem_mod = _il.import_module("app.infrastructure.persistence.memory_repository")
    _orig_set = _mem_mod.SQLMemoryRepository.set_last_user_message_at

    def _fake_set(self, *, tenant_slug: str, user_id: str, sent_at) -> None:
        # Write to DB (keeps get_memory() consistent within the test)
        _orig_set(self, tenant_slug=tenant_slug, user_id=user_id, sent_at=sent_at)
        # Also record in per-test store so _fake_get sees it
        _mem_store[(tenant_slug, user_id)] = sent_at

    def _fake_get(self, *, tenant_slug: str, user_id: str):
        # Read ONLY from per-test store → historical DB state is invisible
        return _mem_store.get((tenant_slug, user_id))

    _mem_base = "app.infrastructure.persistence.memory_repository.SQLMemoryRepository"

    with (
        patch(f"{_mem_base}.set_last_user_message_at", _fake_set),
        patch(f"{_mem_base}.get_last_user_message_at", _fake_get),
    ):
        yield
