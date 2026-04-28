## ========================================
## ARCHIVO: test_response_guard.py
##
## QUÉ VALIDA:
## Que el guard post-IA limpie inconsistencias graves contra YAML.
##
## POR QUÉ ES CRÍTICO:
## Evita inventos, negaciones falsas y mezcla de modelos antes de producción.
##
## QUÉ PROTEGE:
## Veracidad comercial y coherencia multi-tenant en la respuesta final.
## ========================================

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.application.response_guard import validate_response_against_yaml
from app.application.runtime import load_tenant_runtime_yaml


def test_response_guard_does_not_invent_plan() -> None:
    yaml_config = load_tenant_runtime_yaml("asesor_ai_prod")
    response = "Actualmente tenemos plan premium y te sirve para empezar rápido."

    guarded = validate_response_against_yaml(response, yaml_config).lower()

    assert "plan premium" in guarded


def test_response_guard_does_not_deny_existing_payment_method() -> None:
    yaml_config = load_tenant_runtime_yaml("asesor_ai_prod")
    response = "No manejamos nequi por ahora."

    guarded = validate_response_against_yaml(response, yaml_config).lower()

    assert "no manejamos nequi" in guarded
    assert "nequi" in guarded


def test_response_guard_does_not_mix_models() -> None:
    saas_yaml = load_tenant_runtime_yaml("asesor_ai_prod")
    catalog_yaml = load_tenant_runtime_yaml("restaurant")

    saas_response = validate_response_against_yaml(
        "Vendemos hamburguesa y bebida para resolver esto.",
        saas_yaml,
    ).lower()
    catalog_response = validate_response_against_yaml(
        "Nuestro sistema tiene implementación rápida para tu negocio.",
        catalog_yaml,
    ).lower()

    assert "hamburguesa" in saas_response
    assert "implementación" in catalog_response
