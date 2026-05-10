from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TESTS_DIR.parent / "project"

for _p in (str(PROJECT_DIR), str(TESTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


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
    ]

    if test_file == "test_sql_memory_repository.py":
        with (
            patch(_saas_targets[0][0], return_value=_saas_targets[0][1]),
            patch(_saas_targets[1][0], return_value=_saas_targets[1][1]),
            patch(_saas_targets[2][0], return_value=_saas_targets[2][1]),
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
        patch(f"{_mem_base}.set_last_user_message_at", _fake_set),
        patch(f"{_mem_base}.get_last_user_message_at", _fake_get),
    ):
        yield
