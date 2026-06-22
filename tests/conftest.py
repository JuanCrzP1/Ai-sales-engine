from __future__ import annotations

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
def _bypass_saas_for_core_tests(request):
    """Patch SaaS and memory infrastructure for all tests except specific suites:

    - test_saas_guards.py           → no patches (validates real enforcement logic)
    - test_sql_memory_repository.py → SaaS patches only (validates real SQL memory)
    - all others                    → SaaS patches + in-memory last_message_at store

    Memory patch: set/get_last_user_message_at are redirected to a per-test
    in-memory dict, so historical DB state never contaminates conversational tests,
    while intra-test state changes (e.g. simulating activity windows) still work.
    """
    test_file = request.node.fspath.basename

    if test_file == "test_saas_guards.py":
        yield
        return

    _saas_targets = [
        (
            "app.infrastructure.persistence.subscription_repository"
            ".SubscriptionRepository.is_active",
            True,
        ),
        (
            "app.infrastructure.persistence.usage_repository"
            ".UsageRepository.can_send",
            True,
        ),
        (
            "app.infrastructure.persistence.usage_repository"
            ".UsageRepository.increment",
            None,
        ),
        (
            # get_plan_code también consulta la DB dentro de check_access;
            # sin mock dependería de un Postgres sembrado (dependencia oculta del entorno).
            "app.infrastructure.persistence.subscription_repository"
            ".SubscriptionRepository.get_plan_code",
            None,
        ),
    ]

    if test_file == "test_sql_memory_repository.py":
        with (
            patch(_saas_targets[0][0], return_value=_saas_targets[0][1]),
            patch(_saas_targets[1][0], return_value=_saas_targets[1][1]),
            patch(_saas_targets[2][0], return_value=_saas_targets[2][1]),
            patch(_saas_targets[3][0], return_value=_saas_targets[3][1]),
        ):
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
        patch(_saas_targets[0][0], return_value=_saas_targets[0][1]),
        patch(_saas_targets[1][0], return_value=_saas_targets[1][1]),
        patch(_saas_targets[2][0], return_value=_saas_targets[2][1]),
        patch(_saas_targets[3][0], return_value=_saas_targets[3][1]),
        patch(f"{_mem_base}.set_last_user_message_at", _fake_set),
        patch(f"{_mem_base}.get_last_user_message_at", _fake_get),
    ):
        yield
