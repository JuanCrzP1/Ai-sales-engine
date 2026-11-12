"""
Trazabilidad de la configuración antigua (cinco YAML por negocio) al contrato BusinessConfig v1.

Los YAML se retiraron el 11 de noviembre de 2026: lo que el motor recibía de ellos quedó congelado en `tests/golden/`, y los
negocios de ejemplo viven en `project/config/tenants/<negocio>/business-config.json`.

- Cada campo de los YAML de los nueve negocios está catalogado (significado, clase A-E, destino) y su
  valor está de verdad en el destino declarado del documento del negocio.
- Cada campo del contrato tiene origen en los YAML o figura como campo nuevo o derivado documentado.
- Las funcionalidades comerciales existentes quedan tipadas en el documento comercial, con sus valores;
  lo técnico queda fuera de él, en `engine-settings.json`.
- La matriz publicada (`docs/business-config-traceability.md`) está sincronizada con el catálogo.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import re
from pathlib import Path

import pytest

from app.infrastructure.business_config.example_businesses import load_example
from app.infrastructure.config.legacy_field_catalog import (
    CATALOG,
    COMMERCIAL_CONTROLS,
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
from pipeline_harness import TENANTS, engine_sections

ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT_DIR / "project" / "config" / "contracts" / "v1" / "business-config.schema.json"


def _sections(slug: str) -> dict:
    return engine_sections(slug)


def _document(slug: str) -> dict:
    return copy.deepcopy(load_example(slug).document)


def _engine_settings(slug: str) -> dict:
    return copy.deepcopy(load_example(slug).engine_settings)


@pytest.mark.parametrize("slug", TENANTS)
def test_every_legacy_field_reaches_its_declared_destination(slug):
    leaves = list(legacy_leaves(_sections(slug)))
    document = {**_document(slug), "engine_settings": _engine_settings(slug)}
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
        if entry.kind == "technical":
            assert entry.note, f"{entry.pattern}: falta la justificación de tratarlo como técnico"
            assert entry.category in "CE", f"{entry.pattern}: lo comercial no puede quedar fuera del documento comercial"
        if entry.kind == "policy":
            assert entry.note and entry.category in "CE", f"{entry.pattern}: una definición común exige justificarla y que no sea decisión del negocio"
        if entry.engine.startswith("sí"):
            assert entry.evidence or entry.note, f"{entry.pattern}: uso en el motor sin evidencia"


def test_catalog_engine_column_matches_the_contract_status():
    """`sí` en la columna Motor del catálogo ⇔ el campo de destino está marcado `conectado` en el contrato."""
    fields = contract_fields(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    mismatches = set()
    for slug in TENANTS:
        for leaf in legacy_leaves(_sections(slug)):
            entry = find_entry(leaf.pattern)
            if entry.kind in ("technical", "policy", "derived"):
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
            if entry.kind in ("typed", "secret"):
                covering = covering_leaf(destination_path(entry, leaf), leaves)
                assert covering, f"{entry.pattern}: el destino no existe en el contrato"
                reached.add(covering)
    assert set(DERIVED_CONTRACT_FIELDS) <= leaves and set(NEW_CONTRACT_FIELDS) <= leaves
    assert leaves - reached - set(DERIVED_CONTRACT_FIELDS) == set(NEW_CONTRACT_FIELDS)


# Estructuras comerciales de los YAML → su lugar tipado en el contrato.
COMMERCIAL_STRUCTURES = {
    "business.value_drivers": "sales.motivations",
    "business.brand_name": "identity.brand_name",
    "business.use_cases": "sales.use_cases",
    "business.customer_profile": "identity.target_customer",
    "business.logistics": "fulfillment",
    "sales.pain.clusters": "sales.customer_problems",
    "sales.discovery": "sales.discovery",
    "sales.qualification": "sales.qualification",
    "sales.support": "sales.support",
    "sales.angles": "sales.motivations",
    "sales.conversation_flow": "sales.conversation_flow",
    "sales.progression_rules": "sales.conversation_flow",
    "sales.solution.mapping": "sales.customer_problems",
    "sales.offer.recommendation_rules": "sales.recommendation_rules",
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
    "config.capabilities.closing_methods": "capabilities.closing_methods",
    "config.features": "features",
    "config.initial_message.enabled": "messages.welcome.enabled",
    "config.response.length": "response_style.length",
    "config.response.max_words": "response_style.max_words",
}


@pytest.mark.parametrize("slug", TENANTS)
def test_commercial_rules_are_typed_in_the_commercial_document(slug):
    sections, document, settings = _sections(slug), _document(slug), _engine_settings(slug)
    present = [legacy for legacy in COMMERCIAL_STRUCTURES if resolve_path(sections, legacy) is not None]
    assert present, "cada negocio tiene reglas comerciales"
    for legacy in present:
        assert resolve_path(document, COMMERCIAL_STRUCTURES[legacy]) is not None, f"{legacy} no quedó tipado"
        assert resolve_path(settings["legacy"], legacy) is None, f"{legacy} quedó fuera del documento comercial"


@pytest.mark.parametrize("slug", TENANTS)
def test_commercial_document_has_no_technical_settings(slug):
    document, settings = _document(slug), _engine_settings(slug)
    assert not {"engine", "compatibility", "conversation", "flags", "legacy"} & set(document)
    assert set(settings) <= {"schema_version", "tenant_slug", "conversation", "flags", "legacy"}
    # Lo heredado solo conserva campos que el catálogo clasifica como técnicos.
    for leaf in legacy_leaves(settings["legacy"]):
        assert find_entry(leaf.pattern).kind == "technical", leaf.pattern


def test_commercial_controls_keep_their_values_in_the_contract():
    """Cada funcionalidad comercial tiene su campo en el contrato, y cada negocio conserva su valor en él."""
    fields = contract_fields(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    controls = {control.pattern for control in COMMERCIAL_CONTROLS}
    seen: set[str] = set()
    for slug in TENANTS:
        document = {**_document(slug), "engine_settings": _engine_settings(slug)}
        for leaf in legacy_leaves(_sections(slug)):
            if leaf.pattern in controls:
                entry = find_entry(leaf.pattern)
                assert entry.kind == "typed" and entry.category in "AB", leaf.pattern
                assert covering_leaf(destination_path(entry, leaf), set(fields)), leaf.pattern
                assert check_leaf(document, leaf) is None
                seen.add(leaf.pattern)
    assert sorted(controls - seen) == [], "funcionalidades que ningún negocio usa"


@pytest.mark.parametrize(
    "path, options",
    [
        ("response_style.length", "short \\| medium \\| long"),
        ("features.business_model", "catalog \\| saas \\| services \\| service_booking"),
        ("features.pricing_enabled", "interruptor true/false"),
        ("messages.welcome.enabled", "interruptor true/false"),
        ("sales.support.explain_first", "interruptor true/false"),
        ("sales.closing.strategy", "direct_sale \\| lead_capture \\| booking \\| checkout"),
        ("terms.price_framing", "directo \\| comparativo"),
    ],
)
def test_commercial_options_are_closed_in_the_schema(path, options):
    fields = contract_fields(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    assert fields[path].value_type == options


def _all_leaves():
    return [leaf for slug in TENANTS for leaf in legacy_leaves(_sections(slug))]


def test_every_yaml_switch_is_typed_in_the_commercial_contract():
    """Todo interruptor de los YAML queda tipado; los únicos técnicos son las banderas internas."""
    switches = {leaf.pattern for leaf in _all_leaves() if isinstance(leaf.value, bool)}
    assert len(switches) >= 20
    for pattern in switches:
        entry = find_entry(pattern)
        if pattern.startswith("config.flags."):
            assert entry.kind == "technical", pattern
        elif entry.kind == "derived":
            assert entry.category == "E" and entry.note, pattern
        else:
            assert entry.kind == "typed" and entry.category in "AB", pattern


def test_values_used_by_the_businesses_are_preserved_for_every_kind_of_option():
    """El tipo de cierre conserva también `lead_capture`, que los YAML solo mencionan en su definición común."""
    fields = contract_fields(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    strategies = set(fields["sales.closing.strategy"].value_type.split(" \\| "))
    assert strategies == {"direct_sale", "lead_capture", "booking", "checkout"}
    templates = {leaf.path.split(".")[3] for leaf in _all_leaves() if leaf.pattern == "sales.closing.behavior.<estrategia>.goal"}
    assert templates == strategies
    description = fields["sales.closing.strategy"].description
    goals = {leaf.value for leaf in _all_leaves() if leaf.pattern == "sales.closing.behavior.<estrategia>.goal"}
    assert goals == {"confirmar_compra", "capturar_datos", "agendar", "enviar_pago"}
    assert all(word in description for word in ("confirmar la compra", "capturar datos", "agendar", "enviar el pago"))


def test_exceptions_to_the_commercial_contract_are_exactly_the_documented_ones():
    """Lo que no está en el documento comercial es una excepción explícita, justificada y sin crecer en silencio."""
    technical = {entry.pattern for entry in CATALOG if entry.kind == "technical"}
    common = {entry.pattern for entry in CATALOG if entry.kind == "policy"}
    assert technical == {
        "business.type",
        "config.capabilities.channels",
        "config.conversation.**",
        "config.flags.**",
        "config.initial_message.recency.**",
    }
    assert common == {"sales.closing.behavior.<estrategia>.goal", "sales.closing.next_step.action"}
    assert {entry.pattern for entry in CATALOG if entry.kind == "derived"} == {"config.features.catalog_mode"}
    for entry in CATALOG:
        if entry.kind in ("technical", "policy", "derived"):
            assert entry.note and entry.category in "CE", entry.pattern


def test_common_definition_is_the_same_in_every_business():
    for pattern in ("sales.closing.behavior.<estrategia>.goal", "sales.closing.next_step.action"):
        by_slug = {slug: sorted((leaf.path, leaf.value) for leaf in legacy_leaves(_sections(slug)) if leaf.pattern == pattern) for slug in TENANTS}
        assert all(by_slug.values()) and len({tuple(values) for values in by_slug.values()}) == 1, pattern


def test_contract_only_fields_are_commercial_and_have_a_clear_responsibility():
    fields = contract_fields(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    sections = {"identity", "offer", "terms", "payments[]", "sales", "messages", "response_style", "knowledge", "inventory"}
    for path in NEW_CONTRACT_FIELDS:
        field = fields[path]
        assert field.audience in {"cliente", "avanzado"}, f"{path}: no lo configura el negocio"
        assert field.description, f"{path}: sin descripción de su responsabilidad"
        assert path.split(".")[0] in sections, f"{path}: fuera de los módulos comerciales"
    descriptions = [fields[path].description for path in NEW_CONTRACT_FIELDS if not path.endswith((".currency", ".amount"))]
    assert len(descriptions) == len(set(descriptions)), "campos con la misma responsabilidad"


def test_traceability_matrix_is_up_to_date():
    spec = importlib.util.spec_from_file_location("traceability_matrix", ROOT_DIR / "scripts" / "generate_traceability_matrix.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.OUTPUT_PATH.read_text(encoding="utf-8") == module.render_matrix()
