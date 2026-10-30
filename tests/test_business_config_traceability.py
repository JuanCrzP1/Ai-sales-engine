"""
Trazabilidad de la configuración antigua (cinco YAML por negocio) al contrato BusinessConfig v1.

- Cada campo de los YAML de los nueve negocios está catalogado (significado, clase A-E, destino) y su
  valor está de verdad en el destino declarado del documento del negocio.
- Cada campo del contrato tiene origen en los YAML o figura como campo nuevo o derivado documentado.
- Las reglas comerciales existentes quedan tipadas en el contrato, no escondidas en `compatibility`.
- La matriz publicada (`docs/business-config-traceability.md`) está sincronizada con el catálogo.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from app.application.runtime.tenant_runtime_loader import _load_legacy_sections
from app.infrastructure.config.business_config_store import BusinessConfigStore
from app.infrastructure.config.config_service import ConfigService
from app.infrastructure.config.legacy_field_catalog import (
    CATALOG,
    CONSERVED,
    DERIVED_CONTRACT_FIELDS,
    NEW_CONTRACT_FIELDS,
    check_leaf,
    contract_fields,
    contract_leaf_paths,
    covering_leaf,
    destination_path,
    find_entry,
    legacy_leaves,
    resolve_path,
)
from pipeline_harness import TENANTS

ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT_DIR / "project" / "config" / "contracts" / "v1" / "business-config.schema.json"


def _sections(slug: str) -> dict:
    return _load_legacy_sections(ConfigService(), slug)


def _document(slug: str) -> dict:
    return json.loads(BusinessConfigStore(ConfigService().tenants_root).path_for(slug).read_text(encoding="utf-8"))


@pytest.mark.parametrize("slug", TENANTS)
def test_every_legacy_field_reaches_its_declared_destination(slug):
    leaves = list(legacy_leaves(_sections(slug)))
    document = _document(slug)
    assert len(leaves) > 50
    assert [problem for leaf in leaves if (problem := check_leaf(document, leaf))] == []


def test_catalog_entries_are_used_and_coherent():
    used = {find_entry(leaf.pattern).pattern for slug in TENANTS for leaf in legacy_leaves(_sections(slug))}
    patterns = [entry.pattern for entry in CATALOG]
    assert sorted(set(patterns) - used) == [], "entradas del catálogo que ningún negocio usa"
    assert len(patterns) == len(set(patterns))
    for entry in CATALOG:
        assert entry.meaning and entry.category in "ABCDE", entry.pattern
        # Los datos sensibles nunca se tipan como valores, y solo ellos van como referencia.
        assert (entry.kind == "secret") == (entry.category == "D"), entry.pattern
        if entry.kind == "compatibility":
            assert entry.note, f"{entry.pattern}: falta la justificación de dejarlo en compatibilidad"
            assert entry.category != "A", f"{entry.pattern}: la configuración del cliente no puede quedar en compatibilidad"
        if entry.engine.startswith("sí"):
            assert entry.evidence or entry.note, f"{entry.pattern}: uso en el motor sin evidencia"


def test_catalog_engine_column_matches_the_contract_status():
    """`sí` en la columna Motor del catálogo ⇔ el campo de destino está marcado `conectado` en el contrato."""
    fields = contract_fields(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    mismatches = set()
    for slug in TENANTS:
        for leaf in legacy_leaves(_sections(slug)):
            entry = find_entry(leaf.pattern)
            if entry.kind == "compatibility":
                continue
            covering = covering_leaf(destination_path(entry, leaf), set(fields))
            if covering in fields and entry.engine.startswith("sí") != (fields[covering].engine == "conectado"):
                mismatches.add(f"{entry.pattern} ({entry.engine}) → {covering} ({fields[covering].engine})")
    assert sorted(mismatches) == []


def test_evidence_names_exist():
    test_sources = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT_DIR / "tests").glob("test_*.py"))
    names = {name.split("::")[-1] for entry in CATALOG for name in entry.evidence} | {CONSERVED.split("::")[-1]}
    assert sorted(name for name in names if f"def {name}(" not in test_sources) == []


def test_every_contract_field_has_an_origin_or_is_documented_as_new():
    leaves = contract_leaf_paths(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    reached: set[str] = set()
    for slug in TENANTS:
        for leaf in legacy_leaves(_sections(slug)):
            entry = find_entry(leaf.pattern)
            if entry.kind != "compatibility":
                covering = covering_leaf(destination_path(entry, leaf), leaves)
                assert covering, f"{entry.pattern}: el destino no existe en el contrato"
                reached.add(covering)
    assert set(DERIVED_CONTRACT_FIELDS) <= leaves and set(NEW_CONTRACT_FIELDS) <= leaves
    assert leaves - reached - set(DERIVED_CONTRACT_FIELDS) == set(NEW_CONTRACT_FIELDS)


# Estructuras comerciales de los YAML → su lugar tipado en el contrato.
COMMERCIAL_STRUCTURES = {
    "business.value_drivers": "sales.motivation_drivers",
    "business.use_cases": "sales.use_cases",
    "business.customer_profile": "identity.target_customer",
    "business.logistics": "fulfillment",
    "sales.pain.clusters": "sales.customer_problems",
    "sales.discovery": "sales.discovery",
    "sales.qualification": "sales.qualification",
    "sales.support": "sales.support",
    "sales.angles": "sales.angles",
    "sales.conversation_flow": "sales.conversation_flow",
    "sales.solution.mapping": "sales.solution.mapping",
    "sales.solution.process_steps": "sales.solution.process_steps",
    "sales.offer.strategy": "sales.offer_presentation",
    "sales.objection": "sales.objections",
    "sales.closing.strategy": "sales.closing.strategy",
    "sales.closing.triggers": "sales.closing.purchase_signals",
    "sales.closing.next_steps": "sales.closing.next_steps",
    "sales.closing.hard_rules": "sales.closing.rules",
    "pricing.business_offers.financing": "terms.financing",
    "pricing.business_offers.upsell": "sales.offer_mix.upsell",
    "config.capabilities.constraints": "capabilities.restrictions",
}


@pytest.mark.parametrize("slug", TENANTS)
def test_commercial_rules_are_typed_not_hidden_in_compatibility(slug):
    sections, document = _sections(slug), _document(slug)
    present = [legacy for legacy in COMMERCIAL_STRUCTURES if resolve_path(sections, legacy) is not None]
    assert present, "cada negocio tiene reglas comerciales"
    for legacy in present:
        assert resolve_path(document, COMMERCIAL_STRUCTURES[legacy]) is not None, f"{legacy} no quedó tipado"
        assert resolve_path(document.get("compatibility", {}), legacy) is None, f"{legacy} sigue en compatibilidad"


def test_traceability_matrix_is_up_to_date():
    spec = importlib.util.spec_from_file_location("traceability_matrix", ROOT_DIR / "scripts" / "generate_traceability_matrix.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.OUTPUT_PATH.read_text(encoding="utf-8") == module.render_matrix()
