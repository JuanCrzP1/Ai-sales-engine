from __future__ import annotations

import functools
import os
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


def _llm_key_available() -> bool:
    """True si hay una OPENROUTER_API_KEY usable (no vacía ni placeholder)."""
    key = str(os.getenv("OPENROUTER_API_KEY") or "").strip()
    return bool(key) and key not in {"<<TOKEN>>", "<TOKEN>"}


def pytest_collection_modifyitems(config, items):
    """Omite los tests marcados como integración cuando no hay OPENROUTER_API_KEY.

    Permite `git clone && pytest` en verde sin .env ni secretos: la suite unitaria
    corre y la de integración (LLM en vivo) se SKIPea (no falla). Con la key
    presente (.env local o secreto de CI) la integración se ejecuta normalmente.
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
