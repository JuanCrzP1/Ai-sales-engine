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
    """Patch SubscriptionRepository.is_active → True for all tests except
    test_saas_guards.py, which validates the real enforcement logic in isolation.
    This ensures conversational-core tests are never blocked by missing DB subscriptions.
    """
    if request.node.fspath.basename == "test_saas_guards.py":
        yield
        return

    with patch(
        "app.infrastructure.persistence.subscription_repository.SubscriptionRepository.is_active",
        return_value=True,
    ):
        yield
