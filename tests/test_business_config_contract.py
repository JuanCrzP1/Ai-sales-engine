"""
Contrato global de configuración (BusinessConfig v1): pruebas unitarias, sin ejecutar el motor.

Valida: esquema y tipos generados desde el modelo canónico, marcas de audiencia y estado en el motor,
migración sin pérdida de los nueve negocios (compilado = YAML de origen), ausencia de datos de pago en
los documentos, que los campos solo del contrato no alteran lo que recibe el motor, validaciones,
diagnóstico de los nueve negocios y correspondencia con el documento que produce el panel.
La integración con el motor está en `test_business_config_engine_integration.py` (motor actual) y
`test_business_config_engine_pending.py` (cambios futuros del motor).
"""
from __future__ import annotations

import copy
import importlib.util
import json
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.application.runtime.tenant_runtime_loader import _load_legacy_sections
from app.domain.business_config.compiler import compile_business_config
from app.domain.business_config.contract import BusinessConfig
from app.domain.business_config.diagnostics import review
from app.domain.business_config.engine_policy import (
    DEFAULT_MAX_WORDS,
    DEFAULT_RESPONSE_LENGTH,
    MAX_FAQS,
    MAX_POLICY_CHARS,
    MAX_PROFILE_ITEM_CHARS,
    MAX_PROFILE_ITEMS,
    MIN_MAX_WORDS,
    RESPONSE_LENGTH_MAX_WORDS,
    RESPONSE_LENGTH_WORD_RANGES,
)
from app.domain.business_config.payment_data import payment_values
from app.infrastructure.config.business_config_store import BusinessConfigError, BusinessConfigStore
from app.infrastructure.config.config_service import ConfigService
from app.infrastructure.config.legacy_field_catalog import contract_fields
from app.infrastructure.config.payment_secrets import LegacyYamlSecretResolver
from pipeline_harness import TENANTS, copy_tenant

ROOT_DIR = Path(__file__).resolve().parents[1]
CONTRACTS_DIR = ROOT_DIR / "project" / "config" / "contracts" / "v1"
EXAMPLE_PATH = CONTRACTS_DIR / "business-config.example.json"
PANEL_DOCUMENT = ROOT_DIR / "apps" / "admin-web" / "src" / "test" / "fixtures" / "sampleContractDocument.json"
TODAY = date(2026, 10, 28)


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT_DIR / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sections(slug: str) -> dict:
    return _load_legacy_sections(ConfigService(), slug)


def _document(slug: str) -> dict:
    return json.loads(BusinessConfigStore(ConfigService().tenants_root).path_for(slug).read_text(encoding="utf-8"))


def _example() -> dict:
    return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))


def _schema() -> dict:
    return json.loads((CONTRACTS_DIR / "business-config.schema.json").read_text(encoding="utf-8"))


def _compile(document: dict, slug: str | None = None) -> dict:
    config = BusinessConfig.model_validate(document)
    if slug is None:
        return compile_business_config(config, lambda ref: f"valor:{ref.secret_ref}")
    return compile_business_config(config, LegacyYamlSecretResolver(lambda: _sections(slug)))


# ---------------------------------------------------------------------------
# Modelo canónico y artefactos generados
# ---------------------------------------------------------------------------

def test_published_schema_is_generated_from_the_contract_models():
    module = _load_script("export_business_config_schema")
    assert (CONTRACTS_DIR / "business-config.schema.json").read_text(encoding="utf-8") == module.render_schema()


def test_frontend_types_are_generated_from_the_published_schema():
    module = _load_script("generate_business_config_types")
    assert module.OUTPUT_PATH.read_text(encoding="utf-8") == module.render_types()


def test_schema_marks_who_configures_each_section():
    properties = _schema()["properties"]
    for section in ("identity", "offer", "terms", "payments", "sales", "capabilities", "messages", "response_style", "knowledge", "fulfillment", "inventory"):
        assert properties[section]["x-audience"] == "cliente", section
    assert properties["engine"]["x-audience"] == "operador"
    assert properties["compatibility"]["x-audience"] == "sistema" and properties["compatibility"]["x-engine"] == "conservado"


def test_every_contract_field_has_an_audience_and_an_engine_status():
    fields = contract_fields(_schema())
    assert len(fields) > 150
    for path, field in fields.items():
        assert field.audience in {"cliente", "avanzado", "operador", "sistema"}, path
        assert field.engine in {"conectado", "pendiente", "conservado"}, path
        assert (field.engine == "conservado") == (path == "compatibility"), path
    # Los ajustes internos del motor y los identificadores de etapas no los configura el negocio.
    assert all(fields[path].audience == "operador" for path in fields if path.startswith(("engine.", "sales.conversation_flow.")))
    # Las descripciones no repiten el estado en el motor: sale de `x-engine`.
    assert not any("El motor lo usa" in field.description or "sin uso en el motor" in field.description for field in fields.values())


def test_example_document_is_valid_coherent_and_has_no_payment_values():
    raw = EXAMPLE_PATH.read_text(encoding="utf-8")
    config = BusinessConfig.model_validate_json(raw)
    assert review(config, today=TODAY) == []
    assert "http" not in raw
    assert not any(len(token.strip('",')) >= 9 and token.strip('",').isdigit() for token in raw.split())


# ---------------------------------------------------------------------------
# Los nueve negocios: conservación sin pérdida
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("slug", TENANTS)
def test_tenant_document_is_valid_and_belongs_to_its_folder(slug):
    assert BusinessConfigStore(ConfigService().tenants_root).load(slug).tenant_slug == slug


@pytest.mark.parametrize("slug", TENANTS)
def test_compiled_document_reproduces_the_original_yaml_exactly(slug):
    """Sin pérdida: lo que el motor recibe desde el contrato es idéntico a sus YAML de origen."""
    assert _compile(_document(slug), slug) == _sections(slug)


def test_committed_documents_and_migration_report_are_up_to_date():
    documents, report, errors = _load_script("migrate_tenants_to_contract").build()
    assert errors == []
    assert len(documents) == len(TENANTS)
    for path, text in documents.items():
        assert path.read_text(encoding="utf-8") == text, f"{path.parent.name}: documento desactualizado"
    assert (CONTRACTS_DIR / "migration-report.md").read_text(encoding="utf-8") == report


def test_documents_contain_no_payment_secrets_of_any_tenant():
    secrets = set().union(*(payment_values(_sections(slug)) for slug in TENANTS))
    assert secrets, "los YAML de origen deberían tener datos de pago"
    for slug in TENANTS:
        document = BusinessConfigStore(ConfigService().tenants_root).path_for(slug).read_text(encoding="utf-8")
        leaked = [value for value in secrets if value in document]
        assert not leaked, f"{slug}: {len(leaked)} datos de pago en el documento"


@pytest.mark.parametrize("slug", TENANTS)
def test_offer_prices_and_payment_methods_are_preserved(slug):
    pricing = _sections(slug)["pricing"]
    config = BusinessConfigStore(ConfigService().tenants_root).load(slug)
    if config.offer.model == "plans":
        assert [plan.id for plan in config.offer.plans] == [plan["id"] for plan in pricing["plans"]]
        for plan, original in zip(config.offer.plans, pricing["plans"]):
            assert {price.currency: price.model_dump(exclude={"currency"}, exclude_none=True) for price in plan.prices} == original["pricing"]
    else:
        items = {item.id: {p.currency: p.amount for p in item.prices} for item in config.offer.catalog.items}
        assert items == {item["id"]: item["price"] for item in pricing["catalog"]["items"]}
    method_types = [method.type for profile in config.payments for method in profile.transfer_methods]
    assert method_types == [
        method["type"]
        for block in [plan.get("payment") for plan in pricing.get("plans", [])] + [pricing.get("catalog", {}).get("payment")]
        if block
        for method in block["transfer"]["methods"]
    ]


# ---------------------------------------------------------------------------
# Compilación: lo que solo existe en el contrato no altera lo que recibe el motor
# ---------------------------------------------------------------------------

def _with_every_contract_only_field(document: dict) -> dict:
    document = copy.deepcopy(document)
    first_item = document["offer"]["catalog"]["items"][0]
    first_item["features"] = ["pan artesanal"]
    document["identity"].update(
        brand_name="Marca", opening_hours=[{"days": ["lunes"], "opens": "08:00", "closes": "18:00"}],
    )
    document["terms"].update(
        prices_include_taxes=True,
        promotions=[{"name": "Promo", "details": "2x1", "valid_until": "2999-12-31"}],
        policies={"warranty": "30 días", "returns": "Cambios en 5 días", "cancellation": "Hasta 1 día antes"},
    )
    document["payments"][0]["instructions"] = "Envía el comprobante por este chat."
    document["sales"].update(recommendation_rules=[{"when": "tiene hambre", "recommend": first_item["id"]}], instructions=["Confirma la dirección."])
    document["sales"].setdefault("qualification", {})["criteria"] = ["vive en la ciudad"]
    document["capabilities"].update(human_handoff_when=["pide hablar con una persona"])
    document["capabilities"]["closing_methods"]["human_handoff"] = True
    document["capabilities"]["data_collection"]["consent_notice"] = "Usamos tus datos solo para tu pedido."
    document["capabilities"].setdefault("restrictions", {})["forbidden_claims"] = ["sin gluten"]
    document["messages"].update(after_sale="Gracias", data_request="Tus datos", follow_up="¿Seguimos?", human_handoff="Te paso con alguien")
    document["response_style"].update(formality="formal", emojis=False, instructions=["sin tecnicismos"])
    document["knowledge"] = {"faqs": [{"question": "¿Abren domingos?", "answer": "Sí."}]}
    return document


def test_contract_only_fields_do_not_change_what_the_engine_receives():
    base = _document("restaurant")
    enriched = _with_every_contract_only_field(base)
    if base["capabilities"]["closing_methods"]["human_handoff"]:
        assert _compile(enriched, "restaurant") == _compile(base, "restaurant")
    else:
        handoff_only = copy.deepcopy(base)
        handoff_only["capabilities"]["closing_methods"]["human_handoff"] = True
        assert _compile(enriched, "restaurant") == _compile(handoff_only, "restaurant")


def test_example_document_compiles_to_the_engine_shape():
    compiled = _compile(_example())
    assert set(compiled) == {"business", "sales", "pricing", "inventory", "config"}
    assert compiled["config"]["response"] == {"length": "medium", "max_words": 75}
    assert compiled["pricing"]["catalog"]["items"][0] == {
        "id": "pan_masa_madre", "name": "Pan de masa madre", "category": "panes", "description": "Hogaza de 800 g", "price": {"COP": 18000},
    }
    # Lo que solo existe en el contrato no se compila: perfil, preguntas frecuentes, precio por variante.
    assert "profile" not in compiled["config"] and "knowledge" not in compiled["config"]
    assert compiled["inventory"]["items"][0]["variants"][1] == {"sku": "torta_chocolate_24", "attributes": {"porciones": 24}, "stock": 1}


def test_unavailable_offers_are_not_compiled():
    plans = _document("demo")
    plans["offer"]["plans"][1]["available"] = False
    assert [plan["id"] for plan in _compile(plans, "demo")["pricing"]["plans"]] == [plans["offer"]["plans"][0]["id"]]

    catalog = _document("restaurant")
    category = catalog["offer"]["catalog"]["categories"][0]["id"]
    for item in catalog["offer"]["catalog"]["items"]:
        item["available"] = item["category"] != category
    compiled = _compile(catalog, "restaurant")["pricing"]["catalog"]
    assert category not in {entry["id"] for entry in compiled["categories"]}
    assert all(entry["category"] != category for entry in compiled["items"])


@pytest.mark.parametrize("slug", ["saas", "restaurant"])
def test_engine_section_is_derived_when_missing(slug):
    # Documento como lo crearía un negocio nuevo: sin ajustes internos ni compatibilidad heredada.
    document = _document(slug)
    document.pop("engine")
    document.pop("compatibility")
    features = _compile(document, slug)["config"]["features"]
    if document["offer"]["model"] == "catalog":
        assert features == {"pricing_enabled": True, "catalog_mode": True, "business_model": "catalog"}
    else:
        assert features == {"pricing_enabled": True, "catalog_mode": False}


# ---------------------------------------------------------------------------
# Longitud de respuesta
# ---------------------------------------------------------------------------

def test_response_length_options_and_limits():
    # Límites del motor sin cambios: valor por defecto en runtime 80 palabras, mínimo 20.
    assert (DEFAULT_RESPONSE_LENGTH, DEFAULT_MAX_WORDS, MIN_MAX_WORDS) == ("short", 80, 20)
    assert RESPONSE_LENGTH_MAX_WORDS == {"short": 60, "medium": 75, "long": 100}
    config = _document("asesor_ai_prod")
    del config["response_style"]
    assert BusinessConfig.model_validate(config).response_style.effective_max_words() == 60
    for length, words in RESPONSE_LENGTH_MAX_WORDS.items():
        assert BusinessConfig.model_validate({**config, "response_style": {"length": length}}).response_style.effective_max_words() == words
    # El ajuste avanzado solo es válido dentro del rango de su opción: 20-60, 61-75 y 76 o más
    # (las respuestas detalladas no tienen tope).
    assert RESPONSE_LENGTH_WORD_RANGES == {"short": (20, 60), "medium": (61, 75), "long": (76, None)}
    for length, (low, high) in RESPONSE_LENGTH_WORD_RANGES.items():
        for words in (low, high or 400):
            custom = BusinessConfig.model_validate({**config, "response_style": {"length": length, "max_words": words}})
            assert custom.response_style.effective_max_words() == words
    incoherent = (
        {"max_words": MIN_MAX_WORDS - 1},
        {"length": "short", "max_words": 61},
        {"length": "medium", "max_words": 60},
        {"length": "medium", "max_words": 76},
        {"length": "long", "max_words": 30},
        {"length": "long", "max_words": 75},
        {"length": "huge"},
        {"length": "short", "max_words": "muchas"},
    )
    for invalid in incoherent:
        with pytest.raises(ValidationError):
            BusinessConfig.model_validate({**config, "response_style": invalid})


# ---------------------------------------------------------------------------
# Validaciones: datos incoherentes, referencias inválidas y configuraciones incompletas
# ---------------------------------------------------------------------------

def _first_variant(document: dict) -> dict:
    return document["inventory"]["items"][0]["variants"][0]


INVALID_PLAN_DOCUMENTS = {
    "plan_sin_precios": lambda d: d["offer"]["plans"][0].update(prices=[]),
    "precio_sin_importes": lambda d: d["offer"]["plans"][0].update(prices=[{"currency": "COP"}]),
    "perfil_de_pago_inexistente": lambda d: d["offer"]["plans"][0].update(payment_profile="inexistente"),
    "modelo_sin_catalogo": lambda d: d["offer"].update(model="catalog"),
    "nequi_sin_numero": lambda d: d["payments"][0]["transfer_methods"][0].pop("number"),
    "bienvenida_vacia": lambda d: d["messages"]["welcome"].update(enabled=True, text="  "),
    "sin_metodo_de_cierre": lambda d: d["capabilities"]["closing_methods"].update(payment_link=False, human_handoff=False, data_collection=False),
    "dato_desconocido": lambda d: d["capabilities"]["data_collection"].update(fields=["correo"]),
    "cierre_por_datos_sin_pedirlos": lambda d: d["capabilities"]["data_collection"].update(enabled=False, fields=[]),
    "persona_sin_cierre_con_persona": lambda d: (
        d["capabilities"]["closing_methods"].update(human_handoff=False, payment_link=True),
        d["capabilities"].update(human_handoff_when=["pide hablar con alguien"]),
    ),
    "descripcion_vacia": lambda d: d["identity"].update(description=" "),
    "campo_desconocido": lambda d: d.update(campo_desconocido=True),
    "compatibilidad_desconocida": lambda d: d["compatibility"].update(otra_seccion={}),
    "version_desconocida": lambda d: d.update(schema_version="2.0"),
    "ventana_cero": lambda d: d["engine"].update(conversation={"active_window_minutes": 0, "reset_hours": 4}),
    "motivo_sin_explicacion": lambda d: d["sales"].update(buying_motivation={"primary": "inexistente"}),
    "angulo_sin_motivo": lambda d: d["sales"]["angles"].append({"motivation": "inexistente", "signals": [], "messages": []}),
    "politica_demasiado_larga": lambda d: d["terms"].update(policies={"returns": "x" * (MAX_POLICY_CHARS + 1)}),
}


@pytest.mark.parametrize("case", INVALID_PLAN_DOCUMENTS)
def test_invalid_documents_are_rejected(case):
    document = _document("asesor_ai_prod")
    assert document["sales"].get("motivation_drivers") and document["sales"].get("angles")
    INVALID_PLAN_DOCUMENTS[case](document)
    with pytest.raises(ValidationError):
        BusinessConfig.model_validate(document)


INVALID_CATALOG_DOCUMENTS = {
    "envio_gratis_con_costo": lambda d: d["fulfillment"]["delivery"].update(cost={"type": "gratis", "value": 5000}),
    "sku_repetido": lambda d: d["inventory"]["items"][0]["variants"].append(dict(_first_variant(d))),
    "variante_con_moneda_ajena": lambda d: _first_variant(d).update(prices=[{"currency": "USD", "amount": 10}]),
    "variante_con_moneda_repetida": lambda d: _first_variant(d).update(prices=[{"currency": "COP", "amount": 1}, {"currency": "COP", "amount": 2}]),
    "inventario_de_producto_inexistente": lambda d: d["inventory"]["items"].append({"product_id": "inexistente", "variants": []}),
    "categoria_inexistente": lambda d: d["offer"]["catalog"]["items"][0].update(category="inexistente"),
    "nada_disponible": lambda d: [item.update(available=False) for item in d["offer"]["catalog"]["items"]],
    "horario_invertido": lambda d: d["identity"].update(opening_hours=[{"days": ["lunes"], "opens": "18:00", "closes": "08:00"}]),
}


@pytest.mark.parametrize("case", INVALID_CATALOG_DOCUMENTS)
def test_invalid_catalog_documents_are_rejected(case):
    document = _example()
    INVALID_CATALOG_DOCUMENTS[case](document)
    with pytest.raises(ValidationError):
        BusinessConfig.model_validate(document)


def test_optional_commercial_models_are_accepted():
    # Planes con cobro anual, solo pago único o instalación + mensual; variantes con y sin precio propio.
    document = _document("saas")
    document["offer"]["plans"][0]["prices"] = [{"currency": "COP", "annual": 1200000}, {"currency": "USD", "price": 300}]
    BusinessConfig.model_validate(document)
    # Un negocio solo con lo esencial: sin estrategia avanzada, entrega, inventario ni ajustes internos.
    minimal = {key: value for key, value in _example().items() if key in {"tenant_slug", "identity", "offer", "payments", "capabilities", "messages"}}
    minimal["identity"] = {key: minimal["identity"][key] for key in ("name", "industry", "description", "value_proposition")}
    BusinessConfig.model_validate(minimal)


def test_faq_limits_are_enforced():
    config = _document("restaurant")
    faq = {"question": "¿Pregunta?", "answer": "Respuesta."}
    for invalid in ([faq] * (MAX_FAQS + 1), [{"question": "¿?", "answer": "x" * 801}], [{"question": " ", "answer": "ok"}]):
        with pytest.raises(ValidationError):
            BusinessConfig.model_validate({**config, "knowledge": {"faqs": invalid}})


def test_profile_validation_rejects_incoherent_values():
    config = BusinessConfigStore(ConfigService().tenants_root).load("restaurant").model_dump(mode="json", exclude_none=True)
    invalid_documents = [
        # Recomendar algo que el negocio no vende.
        {**config, "sales": {**config["sales"], "recommendation_rules": [{"when": "duda", "recommend": "plan_inexistente"}]}},
        {**config, "sales": {**config["sales"], "instructions": ["regla"] * (MAX_PROFILE_ITEMS + 1)}},
        {**config, "sales": {**config["sales"], "discovery": {"questions": ["x" * (MAX_PROFILE_ITEM_CHARS + 1)]}}},
        {**config, "identity": {**config["identity"], "service_modes": ["teletransporte"]}},
        {**config, "identity": {**config["identity"], "location": {"type": "luna"}}},
        {**config, "terms": {**config["terms"], "promotions": [{"name": "Sin detalle", "details": " "}]}},
        {**config, "terms": {**config["terms"], "promotions": [{"name": "Fecha", "details": "x", "valid_until": "mañana"}]}},
        {**config, "response_style": {**config["response_style"], "tone": "x" * 161}},
    ]
    for document in invalid_documents:
        with pytest.raises(ValidationError):
            BusinessConfig.model_validate(document)


def test_store_rejects_documents_of_another_tenant(tmp_path):
    service = copy_tenant(tmp_path, "asesor_ai_prod")
    path = BusinessConfigStore(service.tenants_root).path_for("asesor_ai_prod")
    path.write_text(json.dumps({**_document("asesor_ai_prod"), "tenant_slug": "restaurant"}, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(BusinessConfigError):
        BusinessConfigStore(service.tenants_root).load("asesor_ai_prod")


# ---------------------------------------------------------------------------
# Diagnóstico: los nueve negocios y sus diferencias comerciales
# ---------------------------------------------------------------------------

EXPECTED_DIAGNOSTICS = {
    "agencia_viajes": ["cierre_por_link_sin_link", "datos_sin_aviso_de_tratamiento", "agenda_sin_horarios"],
    "asesor_ai_prod": ["sin_canales_de_atencion", "datos_sin_aviso_de_tratamiento"],
    "clinic": ["datos_sin_aviso_de_tratamiento", "agenda_sin_horarios"],
    "demo": ["datos_sin_aviso_de_tratamiento"],
    "ecommerce": ["modo_catalogo_contradice_oferta", "datos_sin_aviso_de_tratamiento"],
    "escuela_conduccion": ["cierre_por_link_sin_link", "datos_sin_aviso_de_tratamiento", "agenda_sin_horarios"],
    "restaurant": ["cierre_por_link_sin_link", "datos_sin_aviso_de_tratamiento"],
    "saas": ["datos_sin_aviso_de_tratamiento"],
    "tienda_ropa": ["cierre_por_link_sin_link", "entrega_sin_modalidad", "entrega_sin_modalidad", "datos_sin_aviso_de_tratamiento"],
}


@pytest.mark.parametrize("slug", TENANTS)
def test_diagnostics_of_the_nine_businesses(slug):
    config = BusinessConfigStore(ConfigService().tenants_root).load(slug)
    assert [item.code for item in review(config, today=TODAY)] == EXPECTED_DIAGNOSTICS[slug]


def test_the_nine_businesses_cover_both_offer_models_and_their_differences():
    configs = {slug: BusinessConfigStore(ConfigService().tenants_root).load(slug) for slug in TENANTS}
    assert {slug for slug, config in configs.items() if config.offer.model == "catalog"} == {"agencia_viajes", "escuela_conduccion", "restaurant", "tienda_ropa"}
    assert any(len(plan.prices) > 1 for config in configs.values() for plan in config.offer.plans or [])  # varias monedas
    assert any(price.implementation is not None for config in configs.values() for plan in config.offer.plans or [] for price in plan.prices)
    assert any(entry.variants for config in configs.values() for entry in config.inventory.items)  # variantes
    assert {config.sales.closing.strategy for config in configs.values() if config.sales.closing} >= {"booking", "checkout"}


DIAGNOSTIC_CASES = {
    "cierre_por_link_sin_link": lambda d: (d["capabilities"]["closing_methods"].update(payment_link=True), [p.pop("link", None) for p in d["payments"]]),
    "perfil_de_pago_sin_uso": lambda d: d["payments"].append({"id": "otro", "transfer_enabled": False}),
    "modo_catalogo_contradice_oferta": lambda d: d.update(engine={"features": {"pricing_enabled": True, "catalog_mode": False}}),
    "modalidad_sin_entrega": lambda d: d["fulfillment"]["delivery"].update(available=False),
    "entrega_sin_modalidad": lambda d: d["identity"].update(service_modes=["presencial", "domicilio"]),
    "dato_de_cierre_no_solicitado": lambda d: d["sales"].update(closing={"strategy": "checkout", "required_data": ["address"]})
    or d["capabilities"]["data_collection"].update(fields=["nombre"]),
    "recomienda_oferta_no_disponible": lambda d: d["offer"]["catalog"]["items"][1].update(available=False),
    "promocion_vencida": lambda d: d["terms"]["promotions"][0].update(valid_until="2000-01-01"),
    "sin_canales_de_atencion": lambda d: d["capabilities"].update(service_channels=[]),
    "datos_sin_aviso_de_tratamiento": lambda d: d["capabilities"]["data_collection"].pop("consent_notice"),
    "agenda_sin_horarios": lambda d: (d["fulfillment"].update(scheduling={"required": True}), d["identity"].pop("opening_hours")),
}


@pytest.mark.parametrize("code", DIAGNOSTIC_CASES)
def test_each_diagnostic_detects_its_case(code):
    document = _example()
    DIAGNOSTIC_CASES[code](document)
    assert code in {item.code for item in review(BusinessConfig.model_validate(document), today=TODAY)}


# ---------------------------------------------------------------------------
# Correspondencia con el panel
# ---------------------------------------------------------------------------

def test_panel_document_is_valid_against_the_contract():
    """`translateToEngine.test.ts` genera este archivo con el adaptador del panel; aquí lo valida el contrato."""
    config = BusinessConfig.model_validate_json(PANEL_DOCUMENT.read_text(encoding="utf-8"))
    secrets: dict[str, str] = {}
    compiled = compile_business_config(config, lambda ref: secrets.setdefault(ref.secret_ref, f"valor-{len(secrets)}"))
    assert set(secrets) == {"secret_store:principal.link", "secret_store:principal.transfer.0.number"}
    # El producto no disponible viaja en el contrato, pero no se compila para el motor.
    assert [item.available for item in config.offer.catalog.items] == [True, True, False]
    assert [item["name"] for item in compiled["pricing"]["catalog"]["items"]] == ["Café americano", "Croissant de mantequilla"]
