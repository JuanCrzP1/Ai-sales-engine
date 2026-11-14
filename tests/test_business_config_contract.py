"""
Contrato global de configuración (BusinessConfig v1): pruebas unitarias, sin ejecutar el motor.

Valida: esquema y tipos generados desde el modelo canónico, marcas de audiencia y estado en el motor,
migración sin pérdida de los nueve negocios (compilado = YAML de origen, más el perfil comercial), ausencia
de datos de pago en los documentos, que los campos solo del contrato llegan al motor únicamente por sus claves
propias, validaciones, diagnóstico de los nueve negocios y correspondencia con el documento que produce el panel.
La integración con el motor está en `test_business_config_engine_integration.py`.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import shutil
from datetime import date
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from app.domain.business_config.contract.escalation import Escalation
from app.domain.business_config.compiler import comparable_with_yaml, compile_business_config
from app.domain.business_config.contract import BusinessConfig, business_config_json_schema
from app.domain.business_config.diagnostics import review
from app.domain.business_config.engine_settings import EngineSettings
from app.domain.business_config.engine_policy import (
    DEFAULT_MAX_WORDS,
    DEFAULT_RESPONSE_LENGTH,
    MAX_FAQ_ANSWER_CHARS,
    MAX_FAQ_QUESTION_CHARS,
    MAX_FAQS,
    MAX_MESSAGE_CHARS,
    MAX_POLICY_CHARS,
    MAX_PROFILE_ITEM_CHARS,
    MAX_PROFILE_ITEMS,
    MAX_PROMOTIONS,
    MAX_TONE_CHARS,
    MIN_MAX_WORDS,
    RESPONSE_LENGTH_MAX_WORDS,
    RESPONSE_LENGTH_WORD_RANGES,
)
from app.domain.business_config.payment_data import payment_values
from app.domain.business_config.errors import BusinessConfigError
from app.infrastructure.business_config.example_businesses import (
    CONTRACT_FILENAME,
    ENGINE_SETTINGS_FILENAME,
    EXAMPLES_DIR,
    load_example,
)
from app.infrastructure.config.legacy_field_catalog import contract_fields
from pipeline_harness import TENANTS, engine_sections

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
    return engine_sections(slug)


def _document(slug: str) -> dict:
    return copy.deepcopy(load_example(slug).document)


def _example() -> dict:
    return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))


def _schema() -> dict:
    return json.loads((CONTRACTS_DIR / "business-config.schema.json").read_text(encoding="utf-8"))


def _engine_settings(slug: str) -> dict:
    return copy.deepcopy(load_example(slug).engine_settings)


def _compile(document: dict, slug: str | None = None, *, settings: dict | None = None) -> dict:
    config = BusinessConfig.model_validate(document)
    if settings is not None:
        config.with_engine_settings(EngineSettings.model_validate(settings))
    if slug is None:
        return compile_business_config(config, lambda ref: f"valor:{ref.secret_ref}")
    return compile_business_config(config, load_example(slug).payment_resolver())


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
    assert properties["features"]["x-audience"] == "avanzado"
    # Lo técnico no forma parte del documento comercial.
    assert "engine" not in properties and "compatibility" not in properties


def test_every_contract_field_has_an_audience_and_an_engine_status():
    fields = contract_fields(_schema())
    assert len(fields) > 150
    for path, field in fields.items():
        assert field.audience in {"cliente", "avanzado", "sistema"}, path
        assert field.engine in {"conectado", "pendiente", "programado", "solo panel"}, path
    # Todo lo que el panel deja configurar llega al motor, salvo lo que es solo del equipo o lo enviará la plataforma ante un evento.
    assert {path: field.engine for path, field in fields.items() if field.engine != "conectado"} == {
        "payments[].transfer_methods[].label": "solo panel",
        "inventory.items[].variants[].sku": "solo panel",
        "messages.payment_confirmed": "programado",
        "messages.follow_up": "programado",
    }
    # Los interruptores y el flujo de conversación son decisiones comerciales.
    assert all(fields[path].audience == "avanzado" for path in fields if path.startswith(("features.", "sales.conversation_flow.")))
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
    assert load_example(slug).config().tenant_slug == slug


@pytest.mark.parametrize("slug", TENANTS)
def test_compiled_document_reproduces_the_original_yaml_exactly(slug):
    """Sin pérdida: lo que el motor recibe desde el contrato es idéntico a lo que recibía de sus YAML, más el perfil comercial."""
    assert comparable_with_yaml(_compile(_document(slug), slug, settings=_engine_settings(slug))) == _sections(slug)


def test_documents_contain_no_payment_secrets_of_any_tenant():
    secrets = set().union(*(payment_values(_sections(slug)) for slug in TENANTS))
    assert secrets, "los ejemplos tienen datos de pago (en su payment-values.json)"
    for slug in TENANTS:
        for path in (EXAMPLES_DIR / slug / CONTRACT_FILENAME, EXAMPLES_DIR / slug / ENGINE_SETTINGS_FILENAME):
            document = path.read_text(encoding="utf-8")
            leaked = [value for value in secrets if value in document]
            assert not leaked, f"{path.name} de {slug}: {len(leaked)} datos de pago"


@pytest.mark.parametrize("slug", TENANTS)
def test_offer_prices_and_payment_methods_are_preserved(slug):
    pricing = _sections(slug)["pricing"]
    config = load_example(slug).config()
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

def _with_style_hours_policies_and_messages(document: dict) -> dict:
    document = copy.deepcopy(document)
    document["identity"].update(opening_hours=[{"days": ["lunes"], "opens": "08:00", "closes": "18:00"}])
    document["terms"].update(policies={"warranty": "30 días", "returns": "Cambios en 5 días", "cancellation": "Hasta 1 día antes"})
    document["messages"].update(after_sale="Gracias", data_request="Tus datos", follow_up="¿Seguimos?", human_handoff="Te paso con alguien")
    document["response_style"].update(formality="formal", emojis=False, instructions=["sin tecnicismos"])
    return document


def _with_every_contract_only_field(document: dict) -> dict:
    document = _with_style_hours_policies_and_messages(document)
    document["offer"]["catalog"]["items"][0]["features"] = ["pan artesanal"]
    document["terms"].update(promotions=[{"name": "Promo", "details": "2x1", "valid_until": "2999-12-31"}])
    document["sales"].update(instructions=["Confirma la dirección."])
    document["knowledge"] = {"faqs": [{"question": "¿Abren domingos?", "answer": "Sí."}]}
    return document


def test_the_follow_up_message_is_kept_for_the_platform_and_never_compiled_for_the_ai():
    base = _document("restaurant")
    document = copy.deepcopy(base)
    document["messages"]["follow_up"] = "¿Seguimos?"
    assert _compile(document, "restaurant") == _compile(base, "restaurant")


def test_contract_only_fields_reach_the_engine_only_through_their_own_keys():
    base = _document("restaurant")
    compiled, plain = _compile(_with_every_contract_only_field(base), "restaurant"), _compile(base, "restaurant")
    assert compiled["config"]["knowledge"] == {"faqs": [{"question": "¿Abren domingos?", "answer": "Sí."}]}
    assert compiled["config"]["profile"]["instructions"] == ["Confirma la dirección."]
    assert compiled["config"]["profile"]["promotions"] == [{"name": "Promo", "details": "2x1", "valid_until": "2999-12-31"}]
    assert compiled["pricing"]["catalog"]["items"][0].pop("features") == ["pan artesanal"]
    profile = compiled["config"]["profile"]
    assert profile["opening_hours"] == [{"days": ["lunes"], "opens": "08:00", "closes": "18:00"}]
    assert profile["policies"] == {"warranty": "30 días", "returns": "Cambios en 5 días", "cancellation": "Hasta 1 día antes"}
    assert (profile["formality"], profile["emojis"], profile["style_instructions"]) == ("formal", False, ["sin tecnicismos"])
    # Los mensajes que usa la IA; el de seguimiento lo enviará la plataforma.
    assert compiled["config"]["messages"] == {"after_sale": "Gracias", "data_request": "Tus datos", "human_handoff": "Te paso con alguien"}
    assert comparable_with_yaml(compiled) == comparable_with_yaml(plain)


def test_commercial_fields_return_to_their_original_yaml_route():
    """Marca, recomendaciones, motivos, soluciones e interruptores vuelven a la ruta y la forma de los YAML."""
    document = _document("restaurant")
    document["identity"]["brand_name"] = "Marca"
    document["identity"]["location"] = {"type": "fisico", "city": "Bogotá"}
    document["sales"]["recommendation_rules"] = [{"when": "tiene hambre", "recommend": "plan_x"}]
    document["sales"]["customer_problems"] = [{"id": "demora", "solutions": ["respuesta inmediata"]}]
    document["sales"]["motivations"] = [
        {"motivation": "tiempo", "description": "Ahorrar tiempo", "signals": ["rápido"]},
        {"motivation": "dinero", "description": "Ahorrar dinero", "angle": {"signals": ["caro"], "messages": ["se paga solo"]}},
    ]
    document["sales"]["conversation_flow"] = {"required_flow": ["detect_pain"], "forbid": ["responder_sin_solucion"], "no_skip_steps": True}
    document["features"] = {"pricing_enabled": False, "catalog_mode": True, "multi_currency": True, "multi_plan": False}
    compiled = _compile(document, "restaurant")
    assert compiled["business"]["brand_name"] == "Marca" and compiled["business"]["city"] == "Bogotá"
    assert compiled["sales"]["offer"]["recommendation_rules"] == [{"condition": "tiene hambre", "recommend": "plan_x"}]
    assert compiled["sales"]["solution"]["mapping"] == {"demora": ["respuesta inmediata"]}
    assert "solutions" not in compiled["sales"]["pain"]["clusters"]["demora"]
    assert compiled["business"]["value_drivers"] == {
        "tiempo": {"description": "Ahorrar tiempo", "triggers": ["rápido"]},
        "dinero": {"description": "Ahorrar dinero", "triggers": []},
    }
    assert compiled["sales"]["angles"] == {"dinero": {"when": ["caro"], "execution": ["se paga solo"]}}
    assert compiled["sales"]["progression_rules"] == {"required_flow": ["detect_pain"], "forbid": ["responder_sin_solucion"]}
    assert compiled["sales"]["conversation_flow"] == {"rules": {"no_skip_steps": True}}
    assert compiled["config"]["features"] == {"pricing_enabled": False, "catalog_mode": True, "multi_currency": True, "multi_plan": False}


@pytest.mark.parametrize("enabled", [True, False])
def test_both_greeting_modes_are_kept_with_their_text(enabled):
    document = _document("demo")
    document["messages"]["welcome"]["enabled"] = enabled
    compiled = _compile(document, "demo")["config"]["initial_message"]
    assert compiled == {"enabled": enabled, "text": _sections("demo")["config"]["initial_message"]["text"]}


def test_example_document_compiles_to_the_engine_shape():
    compiled = _compile(_example())
    assert set(compiled) == {"business", "sales", "pricing", "inventory", "config"}
    assert compiled["config"]["response"] == {"length": "medium", "max_words": 75}
    assert compiled["pricing"]["catalog"]["items"][0] == {
        "id": "pan_masa_madre", "name": "Pan de masa madre", "category": "panes", "description": "Hogaza de 800 g", "price": {"COP": 18000},
    }
    # Lo que solo existe en el contrato y el motor ya lee va a sus claves propias; el precio por variante todavía no se compila.
    assert {"profile", "knowledge"} <= set(compiled["config"])
    assert compiled["inventory"]["items"][0]["variants"][1] == {
        "sku": "torta_chocolate_24", "attributes": {"porciones": 24}, "stock": 1, "prices": [{"currency": "COP", "amount": 95000}],
    }


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
def test_features_are_derived_when_missing(slug):
    # Documento como lo crearía un negocio nuevo: sin interruptores ni ajustes técnicos.
    document = _document(slug)
    document.pop("features")
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
    "dato_vacio": lambda d: d["capabilities"]["data_collection"].update(fields=[" "]),
    "cierre_por_datos_sin_pedirlos": lambda d: d["capabilities"]["data_collection"].update(enabled=False, fields=[]),
    "planes_y_catalogo_a_la_vez": lambda d: d["offer"].update(catalog=_example()["offer"]["catalog"]),
    "modelo_mixto": lambda d: d["offer"].update(model="mixed"),
    "impuestos_incluidos": lambda d: d["terms"].update(prices_include_taxes=True),
    "aviso_de_datos": lambda d: d["capabilities"]["data_collection"].update(consent_notice="Aviso"),
    "cuando_pasar_a_una_persona": lambda d: d["capabilities"].update(human_handoff_when=["pide hablar con alguien"]),
    "promesas_prohibidas": lambda d: d["capabilities"].setdefault("restrictions", {}).update(forbidden_claims=["sin gluten"]),
    "indicaciones_de_pago": lambda d: d["payments"][0].update(instructions="Envía el comprobante"),
    "criterios_de_calificacion": lambda d: d["sales"].setdefault("qualification", {}).update(criteria=["vive en la ciudad"]),
    "descripcion_vacia": lambda d: d["identity"].update(description=" "),
    "campo_desconocido": lambda d: d.update(campo_desconocido=True),
    "ajustes_tecnicos_en_el_documento": lambda d: d.update(engine={"conversation": {"active_window_minutes": 15, "reset_hours": 4}}),
    "datos_heredados_en_el_documento": lambda d: d.update(compatibility={"config": {}}),
    "interruptor_sin_booleano": lambda d: d["features"].update(pricing_enabled="quizas"),
    "tipo_de_negocio_desconocido": lambda d: d["features"].update(business_model="otro"),
    "paso_con_espacios": lambda d: d["sales"]["conversation_flow"].update(steps=["otro paso"]),
    "extension_desconocida": lambda d: d["response_style"].update(length="enorme"),
    "cierre_desconocido": lambda d: d["sales"]["closing"].update(strategy="otro"),
    "version_desconocida": lambda d: d.update(schema_version="2.0"),
    "motivo_sin_explicacion": lambda d: d["sales"].update(buying_motivation={"primary": "inexistente"}),
    "angulo_sin_motivo": lambda d: d["sales"]["motivations"].append({"motivation": "inexistente", "angle": {"signals": [], "messages": []}}),
    "motivo_sin_contenido": lambda d: d["sales"]["motivations"].append({"motivation": "vacio"}),
    "motivo_repetido": lambda d: d["sales"]["motivations"].append(dict(d["sales"]["motivations"][0])),
    "problema_con_angulo_inexistente": lambda d: d["sales"]["customer_problems"][0].update(recommended_angles=["inexistente"]),
    "problema_sin_soluciones": lambda d: d["sales"]["customer_problems"][0].update(solutions=[]),
    "politica_demasiado_larga": lambda d: d["terms"].update(policies={"returns": "x" * (MAX_POLICY_CHARS + 1)}),
}


@pytest.mark.parametrize("case", INVALID_PLAN_DOCUMENTS)
def test_invalid_documents_are_rejected(case):
    document = _document("asesor_ai_prod")
    motivations = document["sales"]["motivations"]
    assert all(entry.get("description") and entry.get("angle") for entry in motivations)
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
    "catalogo_y_planes_a_la_vez": lambda d: d["offer"].update(plans=_document("demo")["offer"]["plans"]),
    "nada_disponible": lambda d: [item.update(available=False) for item in d["offer"]["catalog"]["items"]],
    "horario_invertido": lambda d: d["identity"].update(opening_hours=[{"days": ["lunes"], "opens": "18:00", "closes": "08:00"}]),
    "horario_con_dia_repetido": lambda d: d["identity"].update(opening_hours=[{"days": ["lunes", "lunes"], "opens": "08:00", "closes": "18:00"}]),
    "hora_sin_formato": lambda d: d["identity"].update(opening_hours=[{"days": ["lunes"], "opens": "8am", "closes": "18:00"}]),
    "formalidad_desconocida": lambda d: d["response_style"].update(formality="muy_formal"),
    "emojis_sin_booleano": lambda d: d["response_style"].update(emojis="a veces"),
    "instruccion_de_estilo_larga": lambda d: d["response_style"].update(instructions=["x" * (MAX_PROFILE_ITEM_CHARS + 1)]),
    "instruccion_comercial_vacia": lambda d: d["sales"].update(instructions=[" "]),
    "mensaje_posventa_largo": lambda d: d["messages"].update(after_sale="x" * (MAX_MESSAGE_CHARS + 1)),
    "mensaje_pedir_datos_vacio": lambda d: d["messages"].update(data_request=" "),
    "mensaje_seguimiento_largo": lambda d: d["messages"].update(follow_up="x" * (MAX_MESSAGE_CHARS + 1)),
    "mensaje_transferencia_largo": lambda d: d["messages"].update(human_handoff="x" * (MAX_MESSAGE_CHARS + 1)),
    "saludo_largo": lambda d: d["messages"]["welcome"].update(text="x" * (MAX_MESSAGE_CHARS + 1)),
    "precio_de_variante_negativo": lambda d: _first_variant(d).update(prices=[{"currency": "COP", "amount": -1}]),
    "producto_no_disponible_sin_booleano": lambda d: d["offer"]["catalog"]["items"][0].update(available="quizas"),
    "caracteristica_vacia": lambda d: d["offer"]["catalog"]["items"][0].update(features=[" "]),
    "promocion_repetida": lambda d: d["terms"].update(promotions=[{"name": "2x1", "details": "a"}, {"name": "2x1", "details": "b"}]),
    "pregunta_repetida": lambda d: d.update(knowledge={"faqs": [{"question": "¿Abren?", "answer": "Sí"}, {"question": "¿Abren?", "answer": "No"}]}),
    "politica_vacia": lambda d: d["terms"].update(policies={"warranty": " "}),
}


@pytest.mark.parametrize("case", INVALID_CATALOG_DOCUMENTS)
def test_invalid_catalog_documents_are_rejected(case):
    document = _example()
    INVALID_CATALOG_DOCUMENTS[case](document)
    with pytest.raises(ValidationError):
        BusinessConfig.model_validate(document)


INVALID_ENGINE_SETTINGS = {
    "ventana_cero": lambda d: d.update(conversation={"active_window_minutes": 0, "reset_hours": 4}),
    "bandera_desconocida": lambda d: d["flags"].update(otra=True),
    "nivel_de_registro_desconocido": lambda d: d["flags"].update(log_level="todo"),
    "seccion_heredada_desconocida": lambda d: d["legacy"].update(otra_seccion={}),
    "campo_desconocido": lambda d: d.update(features={}),
}


@pytest.mark.parametrize("case", INVALID_ENGINE_SETTINGS)
def test_invalid_engine_settings_are_rejected(case):
    settings = _engine_settings("asesor_ai_prod")
    INVALID_ENGINE_SETTINGS[case](settings)
    with pytest.raises(ValidationError):
        EngineSettings.model_validate(settings)


def test_conflict_between_legacy_data_and_the_contract_is_not_hidden():
    settings = _engine_settings("restaurant")
    settings["legacy"].setdefault("business", {})["industry"] = "otro sector"
    with pytest.raises(ValueError, match="conflicto"):
        _compile(_document("restaurant"), "restaurant", settings=settings)


def test_optional_commercial_models_are_accepted():
    # Planes con cobro anual, solo pago único o instalación + mensual; variantes con y sin precio propio.
    document = _document("saas")
    document["offer"]["plans"][0]["prices"] = [{"currency": "COP", "annual": 1200000}, {"currency": "USD", "price": 300}]
    BusinessConfig.model_validate(document)
    # Un negocio solo con lo esencial: sin estrategia avanzada, entrega, inventario ni ajustes internos.
    minimal = {key: value for key, value in _example().items() if key in {"tenant_slug", "identity", "offer", "payments", "capabilities", "messages"}}
    minimal["identity"] = {key: minimal["identity"][key] for key in ("name", "industry", "description", "value_proposition")}
    BusinessConfig.model_validate(minimal)


def test_commercial_fields_of_the_contract_are_accepted_together():
    """Horarios, estilo, instrucciones, mensajes, cobros, variantes, disponibilidad, promociones, preguntas y políticas."""
    document = _example()
    document["identity"]["opening_hours"] = [{"days": ["lunes", "martes"], "opens": "08:00", "closes": "18:00"}]
    document["response_style"].update(formality="formal", emojis=False, instructions=["Sin tecnicismos."])
    document["sales"]["instructions"] = ["Ofrece primero lo más vendido."]
    document["messages"].update(after_sale="Gracias", data_request="Tus datos", follow_up="¿Seguimos?", human_handoff="Te paso con alguien")
    first_item = document["offer"]["catalog"]["items"][0]
    first_item.update(features=["Masa madre"], available=False)
    document["terms"].update(promotions=[{"name": "2x1", "details": "Martes", "valid_until": "2999-12-31"}], policies={"warranty": "30 días"})
    document["knowledge"] = {"faqs": [{"question": "¿Abren domingos?", "answer": "Sí."}]}
    config = BusinessConfig.model_validate(document)
    assert config.response_style.formality == "formal" and config.identity.opening_hours[0].days == ["lunes", "martes"]
    plan = {"id": "p", "name": "Plan", "available": False, "prices": [{"currency": "COP", "annual": 1200, "first_payment": 100, "monthly": 120}]}
    saas = _document("saas")
    saas["offer"]["plans"].append(plan)
    assert BusinessConfig.model_validate(saas).offer.plans[-1].prices[0].annual == 1200


def test_faq_limits_are_enforced():
    config = _document("restaurant")
    faq = {"question": "¿Pregunta?", "answer": "Respuesta."}
    for invalid in ([faq] * (MAX_FAQS + 1), [{"question": "¿?", "answer": "x" * 801}], [{"question": " ", "answer": "ok"}]):
        with pytest.raises(ValidationError):
            BusinessConfig.model_validate({**config, "knowledge": {"faqs": invalid}})


def test_profile_validation_rejects_incoherent_values():
    config = load_example("restaurant").config().model_dump(mode="json", exclude_none=True)
    invalid_documents = [
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


def test_recommendation_outside_the_offer_is_kept_and_reported():
    """Regla comercial existente en dos negocios: se conserva tal cual y el diagnóstico la señala."""
    document = _document("restaurant")
    document["sales"]["recommendation_rules"] = [{"when": "duda", "recommend": "plan_inexistente"}]
    config = BusinessConfig.model_validate(document)
    assert "recomienda_oferta_no_disponible" in {item.code for item in review(config, today=TODAY)}


# ---------------------------------------------------------------------------
# Campos obligatorios, tipos y formatos, límites, duplicados y opciones
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = [
    ("tenant_slug",),
    ("identity",),
    ("identity", "name"),
    ("identity", "industry"),
    ("identity", "description"),
    ("identity", "value_proposition"),
    ("offer",),
    ("offer", "model"),
    ("capabilities",),
    ("capabilities", "closing_methods"),
    ("capabilities", "data_collection"),
    ("messages",),
    ("messages", "welcome"),
    ("messages", "welcome", "enabled"),
]


@pytest.mark.parametrize("path", REQUIRED_FIELDS, ids=".".join)
def test_required_fields_cannot_be_omitted(path):
    document = _example()
    node = document
    for key in path[:-1]:
        node = node[key]
    del node[path[-1]]
    with pytest.raises(ValidationError):
        BusinessConfig.model_validate(document)


def test_only_the_documented_sections_are_required():
    assert set(_schema()["required"]) == {path[0] for path in REQUIRED_FIELDS}


INVALID_TYPES_AND_FORMATS = {
    "identificador_de_negocio": lambda d: d.update(tenant_slug="Con Mayusculas"),
    "version_numerica": lambda d: d.update(schema_version=1),
    "nombre_numerico": lambda d: d["identity"].update(name=123),
    "diferenciadores_sin_lista": lambda d: d["identity"].update(differentiators="uno solo"),
    "moneda_en_minusculas": lambda d: d["offer"]["catalog"]["items"][0]["prices"][0].update(currency="cop"),
    "moneda_larga": lambda d: d["offer"]["catalog"]["items"][0]["prices"][0].update(currency="COPE"),
    "precio_negativo": lambda d: d["offer"]["catalog"]["items"][0]["prices"][0].update(amount=-1),
    "precio_de_texto": lambda d: d["offer"]["catalog"]["items"][0]["prices"][0].update(amount="mucho"),
    "id_de_producto_con_espacios": lambda d: d["offer"]["catalog"]["items"][0].update(id="con espacios"),
    "fecha_de_promocion": lambda d: d["terms"]["promotions"][0].update(valid_until="31/12/2030"),
    "hora_imposible": lambda d: d["identity"]["opening_hours"][0].update(opens="25:00"),
    "dia_desconocido": lambda d: d["identity"]["opening_hours"][0].update(days=["festivo"]),
    "existencias_negativas": lambda d: d["inventory"]["items"][0]["variants"][0].update(stock=-1),
    "referencia_sin_origen": lambda d: d["payments"][0]["transfer_methods"][0].update(number={"secret_ref": "sin_origen"}),
    "numero_de_pago_en_claro": lambda d: d["payments"][0]["transfer_methods"][0].update(number="3001234567"),
    "link_de_pago_en_claro": lambda d: d["payments"][0].update(link="https://pagos.ejemplo/abc"),
    "interruptor_de_saludo_de_texto": lambda d: d["messages"]["welcome"].update(enabled="quizas"),
    "palabras_de_texto": lambda d: d["response_style"].update(max_words="muchas"),
}


@pytest.mark.parametrize("case", INVALID_TYPES_AND_FORMATS)
def test_wrong_types_and_formats_are_rejected(case):
    document = _example()
    INVALID_TYPES_AND_FORMATS[case](document)
    with pytest.raises(ValidationError):
        BusinessConfig.model_validate(document)


def _texts(count: int) -> list[str]:
    return [f"elemento {index}" for index in range(count)]


# Nombre: (cómo poner un valor de tamaño n, tamaño máximo admitido).
TEXT_AND_LIST_LIMITS = {
    "frase_de_diferenciador": (lambda d, n: d["identity"].update(differentiators=["x" * n]), MAX_PROFILE_ITEM_CHARS),
    "lista_de_diferenciadores": (lambda d, n: d["identity"].update(differentiators=_texts(n)), MAX_PROFILE_ITEMS),
    "zonas_de_cobertura": (lambda d, n: d["identity"]["location"]["coverage"].update(zones=_texts(n)), MAX_PROFILE_ITEMS),
    "tono": (lambda d, n: d["response_style"].update(tone="x" * n), MAX_TONE_CHARS),
    "voz": (lambda d, n: d["response_style"].update(voice="x" * n), MAX_TONE_CHARS),
    "instruccion_de_estilo": (lambda d, n: d["response_style"].update(instructions=["x" * n]), MAX_PROFILE_ITEM_CHARS),
    "instrucciones_de_estilo": (lambda d, n: d["response_style"].update(instructions=_texts(n)), MAX_PROFILE_ITEMS),
    "instruccion_comercial": (lambda d, n: d["sales"].update(instructions=["x" * n]), MAX_PROFILE_ITEM_CHARS),
    "instrucciones_comerciales": (lambda d, n: d["sales"].update(instructions=_texts(n)), MAX_PROFILE_ITEMS),
    "caracteristica_de_producto": (lambda d, n: d["offer"]["catalog"]["items"][0].update(features=["x" * n]), MAX_PROFILE_ITEM_CHARS),
    "nombre_de_promocion": (lambda d, n: d["terms"].update(promotions=[{"name": "x" * n, "details": "y"}]), MAX_PROFILE_ITEM_CHARS),
    "detalle_de_promocion": (lambda d, n: d["terms"].update(promotions=[{"name": "y", "details": "x" * n}]), MAX_PROFILE_ITEM_CHARS),
    "promociones": (lambda d, n: d["terms"].update(promotions=[{"name": text, "details": "y"} for text in _texts(n)]), MAX_PROMOTIONS),
    "garantia": (lambda d, n: d["terms"].update(policies={"warranty": "x" * n}), MAX_POLICY_CHARS),
    "devoluciones": (lambda d, n: d["terms"].update(policies={"returns": "x" * n}), MAX_POLICY_CHARS),
    "cancelacion": (lambda d, n: d["terms"].update(policies={"cancellation": "x" * n}), MAX_POLICY_CHARS),
    "saludo": (lambda d, n: d["messages"]["welcome"].update(text="x" * n), MAX_MESSAGE_CHARS),
    "pago_reportado": (lambda d, n: d["messages"].update(payment_reported="x" * n), MAX_MESSAGE_CHARS),
    "pago_confirmado": (lambda d, n: d["messages"].update(payment_confirmed="x" * n), MAX_MESSAGE_CHARS),
    "posventa": (lambda d, n: d["messages"].update(after_sale="x" * n), MAX_MESSAGE_CHARS),
    "pedir_datos": (lambda d, n: d["messages"].update(data_request="x" * n), MAX_MESSAGE_CHARS),
    "seguimiento": (lambda d, n: d["messages"].update(follow_up="x" * n), MAX_MESSAGE_CHARS),
    "transferencia": (lambda d, n: d["messages"].update(human_handoff="x" * n), MAX_MESSAGE_CHARS),
    "pregunta_frecuente": (lambda d, n: d["knowledge"].update(faqs=[{"question": "x" * n, "answer": "y"}]), MAX_FAQ_QUESTION_CHARS),
    "respuesta_frecuente": (lambda d, n: d["knowledge"].update(faqs=[{"question": "y", "answer": "x" * n}]), MAX_FAQ_ANSWER_CHARS),
    "preguntas_frecuentes": (lambda d, n: d["knowledge"].update(faqs=[{"question": text, "answer": "y"} for text in _texts(n)]), MAX_FAQS),
    "datos_a_pedir": (lambda d, n: d["capabilities"]["data_collection"].update(fields=_texts(n)), MAX_PROFILE_ITEMS),
}


@pytest.mark.parametrize("case", TEXT_AND_LIST_LIMITS)
def test_limits_accept_the_maximum_and_reject_one_more(case):
    apply, maximum = TEXT_AND_LIST_LIMITS[case]
    document = _example()
    apply(document, maximum)
    BusinessConfig.model_validate(document)
    apply(document, maximum + 1)
    with pytest.raises(ValidationError):
        BusinessConfig.model_validate(document)


DUPLICATES = {
    "id_de_plan": ("demo", lambda d: d["offer"]["plans"][1].update(id=d["offer"]["plans"][0]["id"])),
    "moneda_de_plan": ("demo", lambda d: d["offer"]["plans"][0]["prices"].append(dict(d["offer"]["plans"][0]["prices"][0]))),
    "categoria": (None, lambda d: d["offer"]["catalog"]["categories"].append(dict(d["offer"]["catalog"]["categories"][0]))),
    "producto": (None, lambda d: d["offer"]["catalog"]["items"].append(copy.deepcopy(d["offer"]["catalog"]["items"][0]))),
    "moneda_de_producto": (None, lambda d: d["offer"]["catalog"]["items"][0]["prices"].append(dict(d["offer"]["catalog"]["items"][0]["prices"][0]))),
    "perfil_de_pago": (None, lambda d: d["payments"].append(copy.deepcopy(d["payments"][0]))),
    "problema": ("asesor_ai_prod", lambda d: d["sales"]["customer_problems"].append(copy.deepcopy(d["sales"]["customer_problems"][0]))),
    "objecion": ("asesor_ai_prod", lambda d: d["sales"]["objections"].append(copy.deepcopy(d["sales"]["objections"][0]))),
}


@pytest.mark.parametrize("case", DUPLICATES)
def test_duplicates_are_rejected(case):
    slug, mutate = DUPLICATES[case]
    document = _document(slug) if slug else _example()
    mutate(document)
    with pytest.raises(ValidationError):
        BusinessConfig.model_validate(document)


_SECRET = {"secret_ref": "secret_store:dato"}
# Cada opción cerrada del contrato: cómo ponerla en un documento. Una opción nueva exige añadirla aquí.
OPTION_SETTERS = {
    "escalation.on_request": lambda d, v: d.update(escalation={"on_request": v}),
    "features.business_model": lambda d, v: d.update(features={"pricing_enabled": True, "catalog_mode": True, "business_model": v}),
    "fulfillment.delivery.cost.type": lambda d, v: d["fulfillment"]["delivery"].update(cost={"type": v, "value": 0}),
    "fulfillment.delivery.type": lambda d, v: d["fulfillment"]["delivery"].update(type=v),
    "fulfillment.shipping.cost.type": lambda d, v: d["fulfillment"].update(shipping={"available": True, "cost": {"type": v, "value": 0}}),
    "fulfillment.shipping.scope": lambda d, v: d["fulfillment"].update(shipping={"available": True, "scope": v}),
    "identity.location.coverage.type": lambda d, v: d["identity"]["location"]["coverage"].update(type=v),
    "identity.location.type": lambda d, v: d["identity"]["location"].update(type=v),
    "identity.opening_hours[].days": lambda d, v: d["identity"]["opening_hours"][0].update(days=[v]),
    "identity.service_modes": lambda d, v: d["identity"].update(service_modes=[v]),
    "payments[].transfer_methods[].type": lambda d, v: d["payments"][0].update(
        transfer_methods=[{"type": v, "number": _SECRET, "bank": "Banco", "account_type": "ahorros", "account_number": _SECRET, "reference": _SECRET, "name": "Nu"}]
    ),
    "response_style.formality": lambda d, v: d["response_style"].update(formality=v),
    "response_style.length": lambda d, v: d["response_style"].update(length=v),
    "sales.closing.strategy": lambda d, v: d["sales"].update(closing={"strategy": v}),
    "terms.price_framing": lambda d, v: d["terms"].update(price_framing=v),
}


def _closed_options() -> dict[str, list[str]]:
    fields = contract_fields(_schema())
    return {
        path: field.value_type.removeprefix("lista de ").split(" \\| ")
        for path, field in fields.items()
        if " \\| " in field.value_type
    }


def test_lists_the_yaml_leave_open_stay_open():
    """Los YAML no limitan estas listas: cada negocio puede tener sus datos y sus pasos, y llegan al motor tal cual."""
    document = _document("escuela_conduccion")
    fields = ["nombre", "cedula", "licencia_anterior"]
    steps = ["detect_pain", "validar_documentos", "guide_next_step"]
    document["capabilities"]["data_collection"]["fields"] = fields
    document["sales"]["conversation_flow"].update(steps=steps, required_flow=steps[:2])
    compiled = _compile(document, "escuela_conduccion")
    assert compiled["config"]["capabilities"]["data_collection"]["fields"] == fields
    assert compiled["sales"]["conversation_flow"]["steps"] == steps
    assert compiled["sales"]["progression_rules"]["required_flow"] == steps[:2]


def test_every_closed_option_of_the_contract_is_covered():
    assert set(_closed_options()) - {"offer.model"} == set(OPTION_SETTERS)


@pytest.mark.parametrize("path", OPTION_SETTERS)
def test_every_value_of_each_option_is_accepted_and_others_are_rejected(path):
    for value in _closed_options()[path]:
        document = _example()
        OPTION_SETTERS[path](document, value)
        BusinessConfig.model_validate(document)
    document = _example()
    OPTION_SETTERS[path](document, "opcion_inexistente")
    with pytest.raises(ValidationError):
        BusinessConfig.model_validate(document)


@pytest.mark.parametrize(
    "slug, offer_model, business_model",
    [
        ("agencia_viajes", "catalog", "catalog"),
        ("asesor_ai_prod", "plans", "saas"),
        ("clinic", "plans", "service_booking"),
        ("demo", "plans", None),
        ("ecommerce", "plans", "catalog"),
        ("escuela_conduccion", "catalog", "services"),
        ("restaurant", "catalog", "catalog"),
        ("saas", "plans", "saas"),
        ("tienda_ropa", "catalog", "catalog"),
    ],
)
def test_the_same_contract_serves_each_business_model(slug, offer_model, business_model):
    config = BusinessConfig.model_validate(_document(slug))
    assert config.offer.model == offer_model and config.features.business_model == business_model
    assert (config.offer.plans is not None) == (offer_model == "plans")
    assert (config.offer.catalog is not None) == (offer_model == "catalog")


@pytest.mark.parametrize("retired, now", [("checkout", "catalog"), ("process", "services")])
def test_a_document_saved_with_a_retired_option_is_still_read(retired, now):
    """Antes de unificar «Qué vendes» había «Checkout», «Proceso» y el modo catálogo: lo guardado así se sigue leyendo."""
    document = _document("restaurant")
    document["features"] = {"pricing_enabled": True, "catalog_mode": False, "business_model": retired}
    config = BusinessConfig.model_validate(document)
    assert config.features.business_model == now
    assert "catalog_mode" not in config.model_dump(mode="json")["features"]


@pytest.mark.parametrize(
    "offer_model_slug, business_model, catalog_mode",
    [("restaurant", None, True), ("saas", None, False), ("saas", "catalog", True), ("restaurant", "services", True), ("saas", "services", False)],
)
def test_the_engine_still_receives_catalog_mode_deduced(offer_model_slug, business_model, catalog_mode):
    """El modo catálogo ya no se escribe: vende productos si su oferta es un catálogo o si dijo que vende productos."""
    document = _document(offer_model_slug)
    document["features"] = {"pricing_enabled": True, **({"business_model": business_model} if business_model else {})}
    assert _compile(document, offer_model_slug)["config"]["features"]["catalog_mode"] is catalog_mode


# ---------------------------------------------------------------------------
# Lo técnico, fuera del contrato comercial
# ---------------------------------------------------------------------------

TECHNICAL_FIELD_TOKENS = (
    "token", "api_key", "apikey", "password", "credential", "secret", "webhook", "openrouter", "openai", "anthropic",
    "temperature", "embedding", "database", "jwt", "twilio", "environment", "log_level", "ai_first",
    "allow_fallback", "active_window", "reset_hours", "ai_provider", "base_url", "timeout",
)
# Términos cortos: se comparan como palabra completa ("fulfillment" contiene "llm").
TECHNICAL_FIELD_WORDS = {"llm", "dsn", "provider", "debug"}


def test_the_commercial_contract_has_no_technical_fields():
    paths = contract_fields(_schema())
    secrets_file = yaml.safe_load((ROOT_DIR / "project" / "config" / "system" / "secrets.yaml").read_text(encoding="utf-8"))
    for path in paths:
        lowered = path.lower()
        words = set(lowered.replace("[]", "").replace(".", "_").split("_"))
        assert not any(token in lowered for token in TECHNICAL_FIELD_TOKENS), f"{path}: campo técnico en el contrato comercial"
        assert not words & TECHNICAL_FIELD_WORDS, f"{path}: campo técnico en el contrato comercial"
        assert not set(lowered.replace("[]", "").split(".")) & {name.lower() for name in secrets_file}, path
    assert {"engine", "compatibility", "provider", "channels_credentials"}.isdisjoint(_schema()["properties"])


def test_engine_settings_only_hold_technical_parameters():
    assert set(EngineSettings.model_fields) == {"schema_version", "tenant_slug", "conversation", "flags", "legacy"}


@pytest.mark.parametrize("slug", TENANTS)
def test_documents_contain_no_credentials(slug):
    secrets_file = yaml.safe_load((ROOT_DIR / "project" / "config" / "system" / "secrets.yaml").read_text(encoding="utf-8"))
    credentials = [str(value) for value in secrets_file.values() if value and len(str(value)) >= 8 and "${" not in str(value)]
    for path in (EXAMPLES_DIR / slug / CONTRACT_FILENAME, EXAMPLES_DIR / slug / ENGINE_SETTINGS_FILENAME):
        text = path.read_text(encoding="utf-8")
        assert not any(marker in text for marker in ("sk-or-", "Bearer ", "postgresql://", "sqlite://")), path.name
        assert [value for value in credentials if value in text] == [], path.name


def test_payment_data_are_kept_apart_from_channel_credentials():
    from app.infrastructure.business_config import payment_secret_store
    from app.infrastructure.business_config.tables import metadata

    assert "tenant_secrets" not in metadata.tables, "las credenciales de canales pertenecen a las integraciones"
    assert payment_secret_store.SECRETS_KEY_ENV == "BUSINESS_CONFIG_SECRETS_KEY"
    source = (ROOT_DIR / "project" / "app" / "infrastructure" / "business_config" / "payment_secret_store.py").read_text(encoding="utf-8")
    assert "connector_secrets_key" not in source.lower()


def _copy_example(tmp_path: Path, slug: str) -> Path:
    shutil.copytree(EXAMPLES_DIR / slug, tmp_path / slug)
    return tmp_path / slug


def test_an_example_rejects_engine_settings_of_another_tenant(tmp_path):
    path = _copy_example(tmp_path, "saas") / ENGINE_SETTINGS_FILENAME
    path.write_text(json.dumps({**_engine_settings("saas"), "tenant_slug": "restaurant"}), encoding="utf-8")
    with pytest.raises(BusinessConfigError):
        load_example("saas", tmp_path).config()
    path.write_text("{ no es json", encoding="utf-8")
    with pytest.raises(BusinessConfigError):
        load_example("saas", tmp_path)
    path.unlink()
    assert load_example("saas", tmp_path).config().engine_settings is None  # opcional: el motor usa sus valores por defecto


def test_an_example_rejects_documents_of_another_tenant(tmp_path):
    path = _copy_example(tmp_path, "asesor_ai_prod") / CONTRACT_FILENAME
    path.write_text(json.dumps({**_document("asesor_ai_prod"), "tenant_slug": "restaurant"}, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(BusinessConfigError):
        load_example("asesor_ai_prod", tmp_path)


# ---------------------------------------------------------------------------
# Diagnóstico: los nueve negocios y sus diferencias comerciales
# ---------------------------------------------------------------------------

# Los avisos en vivo del panel (`LIVE_ADVISORY_CODES`) también cuentan: sin motivo de compra ni problemas del cliente, el panel ya avisaba.
EXPECTED_DIAGNOSTICS = {
    "agencia_viajes": ["cierre_por_link_sin_link", "agenda_sin_horarios"],
    "asesor_ai_prod": ["recomienda_oferta_no_disponible", "sin_canales_de_atencion"],
    "clinic": ["agenda_sin_horarios", "sin_problemas_del_cliente"],
    "demo": ["recomienda_oferta_no_disponible", "recomienda_oferta_no_disponible"],
    "ecommerce": ["sin_problemas_del_cliente"],
    "escuela_conduccion": ["cierre_por_link_sin_link", "agenda_sin_horarios"],
    "restaurant": ["cierre_por_link_sin_link", "sin_problemas_del_cliente"],
    "saas": ["sin_problemas_del_cliente"],
    "tienda_ropa": ["cierre_por_link_sin_link", "entrega_sin_modalidad", "entrega_sin_modalidad", "sin_problemas_del_cliente"],
}


@pytest.mark.parametrize("slug", TENANTS)
def test_diagnostics_of_the_nine_businesses(slug):
    config = load_example(slug).config()
    assert [item.code for item in review(config, today=TODAY)] == EXPECTED_DIAGNOSTICS[slug]


def test_the_nine_businesses_cover_both_offer_models_and_their_differences():
    configs = {slug: load_example(slug).config() for slug in TENANTS}
    assert {slug for slug, config in configs.items() if config.offer.model == "catalog"} == {"agencia_viajes", "escuela_conduccion", "restaurant", "tienda_ropa"}
    assert any(len(plan.prices) > 1 for config in configs.values() for plan in config.offer.plans or [])  # varias monedas
    assert any(price.implementation is not None for config in configs.values() for plan in config.offer.plans or [] for price in plan.prices)
    assert any(entry.variants for config in configs.values() for entry in config.inventory.items)  # variantes
    assert {config.sales.closing.strategy for config in configs.values() if config.sales.closing} >= {"booking", "checkout"}


DIAGNOSTIC_CASES = {
    "cierre_por_link_sin_link": lambda d: (d["capabilities"]["closing_methods"].update(payment_link=True), [p.pop("link", None) for p in d["payments"]]),
    "perfil_de_pago_sin_uso": lambda d: d["payments"].append({"id": "otro", "transfer_enabled": False}),
    "transferencias_sin_cuentas_activas": lambda d: d["payments"][0].update(
        transfer_enabled=True, transfer_methods=[{"type": "nequi", "number": {"secret_ref": "secret_store:numero"}, "enabled": False}]
    ),
    "multi_moneda_contradice_oferta": lambda d: (
        d.update(features={"pricing_enabled": True, "catalog_mode": True, "multi_currency": False}),
        d["offer"]["catalog"]["items"][0]["prices"].append({"currency": "USD", "amount": 5}),
    ),
    "modalidad_sin_entrega": lambda d: d["fulfillment"]["delivery"].update(available=False),
    "entrega_sin_modalidad": lambda d: d["identity"].update(service_modes=["presencial", "domicilio"]),
    "dato_de_cierre_no_solicitado": lambda d: d["sales"].update(closing={"strategy": "checkout", "required_data": ["address"]})
    or d["capabilities"]["data_collection"].update(fields=["nombre"]),
    "recomienda_oferta_no_disponible": lambda d: d["offer"]["catalog"]["items"][1].update(available=False),
    "promocion_vencida": lambda d: d["terms"]["promotions"][0].update(valid_until="2000-01-01"),
    "sin_canales_de_atencion": lambda d: d["capabilities"].update(service_channels=[]),
    "agenda_sin_horarios": lambda d: (d["fulfillment"].update(scheduling={"required": True}), d["identity"].pop("opening_hours")),
}


@pytest.mark.parametrize("code", DIAGNOSTIC_CASES)
def test_each_diagnostic_detects_its_case(code):
    document = _example()
    DIAGNOSTIC_CASES[code](document)
    assert code in {item.code for item in review(BusinessConfig.model_validate(document), today=TODAY)}


def test_multi_plan_false_with_several_plans_is_reported():
    document = _document("demo")
    document["features"]["multi_plan"] = False
    assert "multi_plan_contradice_oferta" in {item.code for item in review(BusinessConfig.model_validate(document), today=TODAY)}


# ---------------------------------------------------------------------------
# Correspondencia con el panel
# ---------------------------------------------------------------------------

def test_panel_document_is_valid_against_the_contract():
    """El documento con el que se prueba el panel (`src/test/fixtures`) debe cumplir el contrato."""
    config = BusinessConfig.model_validate_json(PANEL_DOCUMENT.read_text(encoding="utf-8"))
    secrets: dict[str, str] = {}
    compiled = compile_business_config(config, lambda ref: secrets.setdefault(ref.secret_ref, f"valor-{len(secrets)}"))
    assert set(secrets) == {"secret_store:principal.link", "secret_store:principal.transfer.0.number"}
    # El producto no disponible viaja en el contrato, pero no se compila para el motor.
    assert [item.available for item in config.offer.catalog.items] == [True, True, False]
    assert [item["name"] for item in compiled["pricing"]["catalog"]["items"]] == ["Café americano", "Croissant de mantequilla"]


# ---------------------------------------------------------------------------
# Largo de los textos que usa el asistente: completos, hasta el máximo del contrato
# ---------------------------------------------------------------------------

def test_the_texts_the_assistant_uses_have_a_maximum_length():
    from app.domain.business_config.engine_policy import (
        MAX_CATEGORIES,
        MAX_DESCRIPTION_CHARS,
        MAX_INDUSTRY_CHARS,
        MAX_OFFER_DESCRIPTION_CHARS,
        MAX_VALUE_PROPOSITION_CHARS,
    )

    schema = business_config_json_schema()
    identity = schema["$defs"]["Identity"]["properties"]
    assert (identity["industry"]["maxLength"], identity["description"]["maxLength"], identity["value_proposition"]["maxLength"]) == (
        MAX_INDUSTRY_CHARS,
        MAX_DESCRIPTION_CHARS,
        MAX_VALUE_PROPOSITION_CHARS,
    )
    assert schema["$defs"]["Catalog"]["properties"]["categories"]["maxItems"] == MAX_CATEGORIES
    assert MAX_OFFER_DESCRIPTION_CHARS >= 200


@pytest.mark.parametrize(
    ("template", "reason"),
    [
        ("Paga por {medio} y avísame", "{datos}"),
        ("Paga aquí: {datos} con {monto}", "{monto}"),
    ],
)
def test_a_payment_template_without_the_data_or_with_unknown_markers_is_rejected(template, reason):
    from app.domain.business_config.contract.assistant import Messages, WelcomeMessage

    with pytest.raises(ValidationError) as rejected:
        Messages(welcome=WelcomeMessage(enabled=False), payment_details=template)
    assert reason in str(rejected.value)
    assert Messages(welcome=WelcomeMessage(enabled=False), payment_details="*{medio}*\n{datos}\n{titular}").payment_details


def test_the_payment_message_drops_lines_left_empty_and_never_uses_a_broken_template():
    from app.domain.business_config.payment_message import DEFAULT_PAYMENT_DETAILS, method_parts, render_payment_details

    medio, datos = method_parts("bank", {"bank": "Bancolombia", "account_type": "ahorros", "account_number": "1234567890"})
    assert (medio, datos) == ("Bancolombia", "Cuenta de ahorros\n1234567890")
    message = render_payment_details(None, medio=medio, datos=datos)
    assert "*Bancolombia*\nCuenta de ahorros\n1234567890\n\nCuando pagues" in message and "A nombre de" not in message
    assert render_payment_details("Sin datos", medio="Nequi", datos="300") == render_payment_details(DEFAULT_PAYMENT_DETAILS, medio="Nequi", datos="300")
    assert method_parts("breb", {"reference": "@cafe"}) == ("Bre-B", "Llave: @cafe") and method_parts("nequi", {}) == ("", "")


# ---------------------------------------------------------------------------
# «Cuándo pasar a una persona» (`contract/escalation.py`)
# ---------------------------------------------------------------------------


def test_without_escalation_rules_the_assistant_behaves_as_before():
    """Un documento sin la sección (todos los publicados antes del 14 nov 2026) queda con las reglas por defecto, y no se compilan."""
    document = _example()
    document.pop("escalation", None)
    config = BusinessConfig.model_validate(document)
    assert config.escalation is None
    assert "escalation" not in config.model_dump(mode="json", exclude_none=True), "se guarda sin la sección"
    default = Escalation()
    assert default.is_default and default.on_request == "always" and default.when_stuck is False
    assert "escalation" not in compile_business_config(config, lambda ref: f"valor:{ref.secret_ref}")["config"]


@pytest.mark.parametrize(
    "escalation",
    [
        {"always_topics": ["Reembolsos", "reembolsos "]},
        {"never_topics": ["precios", "Precios"]},
        {"always_topics": ["reembolsos"], "never_topics": ["Reembolsos"]},
        {"always_topics": ["x" * 121]},
        {"always_topics": [f"tema {n}" for n in range(16)]},
        {"on_request": "never"},
    ],
)
def test_escalation_rules_that_contradict_or_overflow_are_rejected(escalation):
    document = _example()
    document["escalation"] = escalation
    with pytest.raises(ValidationError):
        BusinessConfig.model_validate(document)
