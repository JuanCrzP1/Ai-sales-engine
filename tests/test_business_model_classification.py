from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.application.runtime import load_tenant_runtime_yaml
from app.infrastructure.ai.prompting.builder.prompt_builder import detect_business_model, resolve_business_model


def _business_model_for_runtime(runtime_yaml: dict) -> str:
    direct = resolve_business_model(
        runtime_yaml.get("business"),
        runtime_yaml.get("pricing"),
        runtime_yaml.get("inventory"),
    )
    integrated = detect_business_model(runtime_yaml)
    assert direct == integrated
    return direct


def test_asesor_ai_prod_is_classified_as_saas() -> None:
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod", channel="whatsapp")
    assert _business_model_for_runtime(runtime_yaml) == "saas"


def test_restaurant_is_classified_as_catalog() -> None:
    runtime_yaml = load_tenant_runtime_yaml("restaurant", channel="whatsapp")
    assert _business_model_for_runtime(runtime_yaml) == "catalog"


def test_service_without_plans_or_inventory_is_classified_as_service() -> None:
    runtime_yaml = {
        "business": {},
        "pricing": {"plans": []},
        "inventory": {"items": []},
    }

    assert _business_model_for_runtime(runtime_yaml) == "service"


def test_empty_structural_runtime_is_classified_as_service() -> None:
    runtime_yaml = {
        "business": {},
        "pricing": {"plans": []},
        "inventory": {"items": []},
    }

    assert _business_model_for_runtime(runtime_yaml) == "service"