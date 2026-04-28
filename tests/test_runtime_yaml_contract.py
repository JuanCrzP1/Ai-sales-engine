## ========================================
## ARCHIVO: test_runtime_yaml_contract.py
##
## QUÉ VALIDA:
## Que runtime_yaml tenga estructura completa y falle ante payload inválido.
##
## POR QUÉ ES CRÍTICO:
## Sin contrato de runtime, la IA opera sin contexto real del negocio.
##
## QUÉ PROTEGE:
## Contrato SaaS multi-tenant y consistencia de datos de runtime.
## ========================================

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.application.runtime import load_tenant_runtime_yaml
from app.application.runtime.runtime_yaml_builder import RuntimeYamlBuilder


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que el loader falle cuando pricing llega vacío por override.
##
## POR QUÉ ES IMPORTANTE:
## Sin pricing válido, la IA no puede sostener conversación comercial con datos reales.
##
## QUÉ PROTEGE:
## Contrato runtime_yaml obligatorio para pricing en SaaS multi-tenant.
## ----------------------------------------
def test_fails_if_missing_pricing() -> None:
    with pytest.raises(RuntimeError):
        load_tenant_runtime_yaml("asesor_ai_prod", extra_yaml={"pricing": {}})


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Verifica que RuntimeYamlBuilder rechace un payload totalmente vacío.
##
## POR QUÉ ES IMPORTANTE:
## Evita ejecutar flujo AI-first con contexto inexistente, lo que genera respuestas inválidas.
##
## QUÉ PROTEGE:
## Validación dura de entrada en construcción de runtime por tenant.
## ----------------------------------------
def test_fails_if_yaml_empty() -> None:
    with pytest.raises(RuntimeError):
        RuntimeYamlBuilder().build("test", {})


## ----------------------------------------
## QUÉ HACE ESTE TEST:
## Confirma que el runtime final siempre expone todas las claves críticas.
##
## POR QUÉ ES IMPORTANTE:
## Si falta una clave, el pipeline puede romperse o degradar decisiones en tiempo real.
##
## QUÉ PROTEGE:
## Estabilidad del contrato común sales business pricing inventory config.
## ----------------------------------------
def test_runtime_always_has_required_keys() -> None:
    yaml = load_tenant_runtime_yaml("asesor_ai_prod")
    for key in ["sales", "business", "pricing", "inventory", "config"]:
        assert key in yaml