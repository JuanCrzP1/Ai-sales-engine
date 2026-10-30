"""
Integración del contrato con el motor ACTUAL (sin cambios en el motor).

- Con el contrato como fuente, el motor produce exactamente los mismos prompts y respuestas que con
  los YAML, en los nueve negocios: el contrato no cambia el comportamiento de la IA.
- El contrato es opcional por negocio (`BUSINESS_CONFIG_CONTRACT_TENANTS`) y, si es inválido, el
  motor vuelve a los YAML.
- Cada campo marcado `x-engine: conectado` en el contrato tiene aquí una prueba de que cambiarlo
  cambia lo que hace el motor (`CONNECTED_EVIDENCE`). Lo que el motor actual no usa está marcado
  `pendiente`, y sus pruebas de integración futura están en `test_business_config_engine_pending.py`.

Sin base de datos ni llamadas reales a la IA: memoria en RAM y LLM simulado. Los datos de pago se
comparan sin imprimirse.
"""
from __future__ import annotations

import functools
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import app.application.ai_pipeline as ai_pipeline_module
from app.application.pipeline.conversation_flow import get_conversation_state
from app.application.pipeline.response_postprocessor import enforce_max_words
from app.application.runtime import load_tenant_runtime_yaml
from app.application.runtime import tenant_runtime_loader as loader
from app.domain.business_config.engine_policy import PROMPT_WORD_LIMITS, RESPONSE_LENGTH_MAX_WORDS
from app.domain.business_config.payment_data import iter_payment_blocks
from app.infrastructure.config.business_config_store import CONTRACT_FILENAME, BusinessConfigStore
from app.infrastructure.config.config_service import ConfigService
from app.infrastructure.config.legacy_field_catalog import contract_fields
from pipeline_harness import TENANTS, copy_tenant, reply, run_conversation, run_with_document

ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT_DIR / "project" / "config" / "contracts" / "v1" / "business-config.schema.json"

CONVERSATION = [
    ("Hola, necesito información", reply("Claro.")),
    ("¿Cuánto cuesta?", reply("Te cuento los precios.")),
    ("¿Y qué incluye? ¿Hacen envíos?", reply("Te explico lo que incluye.")),
    ("Quiero pagar por Nequi", reply("Listo.", "buy", payment_method="nequi")),
]
TWO_TURNS = [("Necesito información", reply("Claro.")), ("¿Cuál es el precio?", reply("Te cuento."))]


def _document(slug: str) -> dict:
    return json.loads(BusinessConfigStore(ConfigService().tenants_root).path_for(slug).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Fuente de configuración: YAML por defecto, contrato opcional por negocio
# ---------------------------------------------------------------------------

def test_yaml_remains_the_default_source(monkeypatch):
    monkeypatch.delenv(loader.CONTRACT_TENANTS_ENV, raising=False)

    def _fail(*_args, **_kwargs):
        raise AssertionError("el contrato no debía cargarse")

    monkeypatch.setattr(BusinessConfigStore, "load", _fail)
    assert load_tenant_runtime_yaml("asesor_ai_prod")["config"]["response"]["max_words"] == 75


@pytest.mark.parametrize("enabled", ["asesor_ai_prod", "restaurant,asesor_ai_prod", "*"])
def test_contract_source_is_used_only_for_enabled_tenants(monkeypatch, enabled):
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, enabled)
    calls: list[str] = []
    original = BusinessConfigStore.load

    def _spy(self, slug):
        calls.append(slug)
        return original(self, slug)

    monkeypatch.setattr(BusinessConfigStore, "load", _spy)
    load_tenant_runtime_yaml("asesor_ai_prod")
    load_tenant_runtime_yaml("clinic")
    assert calls == (["asesor_ai_prod", "clinic"] if enabled == "*" else ["asesor_ai_prod"])


def test_tenant_aliases_resolve_to_the_same_contract(monkeypatch):
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, "agencia_viajes")
    assert load_tenant_runtime_yaml("viajes") == load_tenant_runtime_yaml("agencia_viajes")
    with pytest.raises(ValueError):
        load_tenant_runtime_yaml("tenant_inexistente")


@pytest.mark.parametrize("broken", ["{ no es json", json.dumps({"tenant_slug": "asesor_ai_prod"}), json.dumps({**_document("asesor_ai_prod"), "schema_version": "2.0"}), None])
def test_invalid_contract_falls_back_to_yaml(monkeypatch, tmp_path, broken):
    service = copy_tenant(tmp_path, "asesor_ai_prod")
    path = service.tenants_root / "asesor_ai_prod" / CONTRACT_FILENAME
    if broken is None:
        path.unlink()
    else:
        path.write_text(broken, encoding="utf-8")
    errors: list[str] = []
    monkeypatch.setattr(loader.logger, "error", lambda event, **kwargs: errors.append(event))

    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, "asesor_ai_prod")
    runtime = load_tenant_runtime_yaml("asesor_ai_prod", config_service=service)
    monkeypatch.delenv(loader.CONTRACT_TENANTS_ENV)
    assert runtime == load_tenant_runtime_yaml("asesor_ai_prod", config_service=service)
    assert errors == ["business_config_contract_invalid"]


def test_store_rejects_documents_of_another_tenant(monkeypatch, tmp_path):
    service = copy_tenant(tmp_path, "asesor_ai_prod")
    path = BusinessConfigStore(service.tenants_root).path_for("asesor_ai_prod")
    path.write_text(json.dumps({**_document("asesor_ai_prod"), "tenant_slug": "restaurant"}, ensure_ascii=False), encoding="utf-8")
    errors: list[str] = []
    monkeypatch.setattr(loader.logger, "error", lambda event, **kwargs: errors.append(event))
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, "asesor_ai_prod")
    runtime = load_tenant_runtime_yaml("asesor_ai_prod", config_service=service)
    assert errors == ["business_config_contract_invalid"]
    assert runtime["business"]["name"] == load_tenant_runtime_yaml("asesor_ai_prod")["business"]["name"]


# ---------------------------------------------------------------------------
# Equivalencia: el contrato no cambia el comportamiento de la IA
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("slug", TENANTS)
def test_runtime_from_contract_equals_runtime_from_yaml(monkeypatch, slug):
    monkeypatch.delenv(loader.CONTRACT_TENANTS_ENV, raising=False)
    from_yaml = load_tenant_runtime_yaml(slug, channel="whatsapp")
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, slug)
    assert load_tenant_runtime_yaml(slug, channel="whatsapp") == from_yaml


@pytest.mark.parametrize("slug", TENANTS)
def test_engine_prompts_and_replies_are_identical_with_contract_source(monkeypatch, slug):
    monkeypatch.delenv(loader.CONTRACT_TENANTS_ENV, raising=False)
    from_yaml = run_conversation(slug, CONVERSATION, user_id="equivalencia")
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, slug)
    from_contract = run_conversation(slug, CONVERSATION, user_id="equivalencia")
    assert all(prompts for prompts, _response in from_contract[:3])
    assert from_contract == from_yaml


def test_tenants_stay_isolated_with_contract_source(monkeypatch):
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, "*")
    (saas_prompts, _), = run_conversation("asesor_ai_prod", [("¿Qué venden?", reply("Hola."))], user_id="mismo")
    (food_prompts, _), = run_conversation("restaurant", [("¿Qué venden?", reply("Hola."))], user_id="mismo")
    assert "Plan Basico" in saas_prompts[0] and "Hamburguesas" not in saas_prompts[0]
    assert "Hamburguesas" in food_prompts[0] and "Plan Basico" not in food_prompts[0]


# ---------------------------------------------------------------------------
# Longitud de respuesta
# ---------------------------------------------------------------------------

def test_contract_response_length_controls_prompt_and_truncation(monkeypatch):
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, "asesor_ai_prod")
    long_text = " ".join(["palabra"] * 150) + "."
    (prompts, response), = run_conversation("asesor_ai_prod", [("Explícame todo", reply(long_text))], user_id="longitud")
    assert "ESTILO: medium, máximo 75 palabras" in prompts[0]
    assert len(response.split()) <= 75
    assert response == enforce_max_words(long_text, 75)


def test_changing_the_contract_changes_response_length(monkeypatch, tmp_path):
    long_text = " ".join(["palabra"] * 150) + "."
    (prompts, response), = run_with_document(
        monkeypatch, tmp_path, "asesor_ai_prod",
        lambda d: d.update(response_style={"length": "long", "max_words": 90}),
        [("Explícame todo", reply(long_text))],
    )
    assert "ESTILO: long, máximo 90 palabras" in prompts[0]
    assert len(response.split()) == 90


@pytest.mark.parametrize("length", ["short", "medium", "long"])
@pytest.mark.parametrize("slug", TENANTS)
def test_each_response_length_option_controls_prompt_and_truncation(monkeypatch, tmp_path, slug, length):
    words = RESPONSE_LENGTH_MAX_WORDS[length]
    long_text = " ".join(["palabra"] * 150) + "."
    (prompts, response), = run_with_document(
        monkeypatch, tmp_path, slug, lambda d: d.update(response_style={"length": length}), [("Explícame todo", reply(long_text))]
    )
    assert f"ESTILO: {length}, máximo {words} palabras" in prompts[0]
    assert len(response.split()) == words


@pytest.mark.parametrize("channel", ["whatsapp", "telegram", "web"])
def test_response_length_is_the_same_on_every_channel(monkeypatch, channel):
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, "*")
    runtime = load_tenant_runtime_yaml("asesor_ai_prod", channel=channel)
    assert runtime["channel"] == channel
    assert runtime["config"]["response"] == {"length": "medium", "max_words": 75}


# ---------------------------------------------------------------------------
# Oferta, precios y pagos
# ---------------------------------------------------------------------------

def test_plan_prices_format_is_unchanged(monkeypatch):
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, "asesor_ai_prod")
    turns = [("Hola, necesito información", reply("Claro.")), ("¿Precio?", reply("Te cuento."))]
    (_, _), (prompts, _) = run_conversation("asesor_ai_prod", turns, user_id="planes")
    assert "Precios: Plan Basico -> COP: implementation=100000, monthly=110000 | USD: implementation=40, monthly=45." in prompts[0]


def test_unavailable_offer_is_not_offered(monkeypatch, tmp_path):
    turns = [("¿Qué planes tienen?", reply("Te cuento."))]
    (before, _), = run_with_document(monkeypatch, tmp_path / "planes_antes", "demo", lambda d: None, turns)
    (after, _), = run_with_document(monkeypatch, tmp_path / "planes_despues", "demo", lambda d: d["offer"]["plans"][1].update(available=False), turns)
    assert "Plan Pro" in before[0] and "Plan Pro" not in after[0] and "Plan Basico" in after[0]

    # Un catálogo: si todos los productos de una categoría dejan de estar disponibles, la categoría no se ofrece.
    def _hide_first_category(document):
        category = document["offer"]["catalog"]["categories"][0]["id"]
        for item in document["offer"]["catalog"]["items"]:
            if item["category"] == category:
                item["available"] = False

    category_name = _document("restaurant")["offer"]["catalog"]["categories"][0]["name"]
    (before, _), = run_with_document(monkeypatch, tmp_path / "catalogo_antes", "restaurant", lambda d: None, turns)
    (after, _), = run_with_document(monkeypatch, tmp_path / "catalogo_despues", "restaurant", _hide_first_category, turns)
    assert category_name in before[0] and category_name not in after[0]


def test_product_category_decides_which_categories_are_offered(monkeypatch, tmp_path):
    categories = _document("restaurant")["offer"]["catalog"]["categories"]
    first, second = categories[0], categories[1]

    def _move_products(document):
        for item in document["offer"]["catalog"]["items"]:
            if item["category"] == first["id"]:
                item["category"] = second["id"]

    turns = [("¿Qué tienen?", reply("Te cuento."))]
    (before, _), = run_with_document(monkeypatch, tmp_path / "antes", "restaurant", lambda d: None, turns)
    (after, _), = run_with_document(monkeypatch, tmp_path / "despues", "restaurant", _move_products, turns)
    assert first["name"] in before[0] and first["name"] not in after[0] and second["name"] in after[0]


def _payment_choices(runtime: dict) -> list[tuple[str, list[str]]]:
    """(método que elige el cliente, datos que el motor debe entregarle) según el runtime resuelto."""
    choices: list[tuple[str, list[str]]] = []
    blocks = iter_payment_blocks(runtime["pricing"])
    link = next((str(block["link"]) for block in blocks if str(block.get("link") or "").strip()), None)
    if link:
        choices.append(("link", [link]))
    seen: set[str] = set()
    for block in blocks:
        transfer = block.get("transfer") or {}
        for method in transfer.get("methods") or [] if transfer.get("enabled") else []:
            if method["type"] in seen:
                continue
            seen.add(method["type"])
            fields = {"nequi": ("number",), "daviplata": ("number",), "bank": ("bank", "account_type", "account_number"), "breb": ("reference",)}
            choices.append((method["type"], [str(method[field]) for field in fields[method["type"]]]))
    return choices


@pytest.mark.parametrize("slug", TENANTS)
def test_payment_methods_reach_the_customer(monkeypatch, slug):
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, slug)
    choices = _payment_choices(load_tenant_runtime_yaml(slug))
    assert choices, "cada negocio tiene al menos un método de pago"
    for method, values in choices:
        (_, response), = run_conversation(slug, [(f"Quiero pagar por {method}", reply("Listo.", "buy", payment_method=method))], user_id=f"pago-{method}")
        delivered = all(value in response for value in values)
        assert delivered, f"{slug}: el motor no entregó los datos de {method}"


def test_disabled_transfers_are_not_delivered(monkeypatch, tmp_path):
    def _disable(document):
        for profile in document["payments"]:
            profile["transfer_enabled"] = False

    turns = [("Quiero pagar por nequi", reply("Listo.", "buy", payment_method="nequi"))]
    (_, enabled), = run_with_document(monkeypatch, tmp_path / "activas", "saas", lambda d: None, turns)
    (_, disabled), = run_with_document(monkeypatch, tmp_path / "inactivas", "saas", _disable, turns)
    assert "nequi usando el número" in enabled
    assert "nequi usando el número" not in disabled


# ---------------------------------------------------------------------------
# Capacidades, mensajes y ajustes del motor
# ---------------------------------------------------------------------------

def test_closing_and_data_collection_toggles_change_the_prompt(monkeypatch, tmp_path):
    def _disable(document):
        document["capabilities"]["closing_methods"]["payment_link"] = False
        document["capabilities"]["closing_methods"]["data_collection"] = False
        document["capabilities"]["data_collection"] = {"enabled": False, "fields": []}

    (prompts, _), = run_with_document(monkeypatch, tmp_path, "saas", _disable, [("Quiero comprar", reply("Listo."))])
    closing_line = prompts[0].split("Métodos activos en este negocio:\n", 1)[1].splitlines()[0]
    assert closing_line == "human_handoff"
    assert "Campos definidos para pedir al cliente:\nsin campos definidos" in prompts[0]


@pytest.mark.parametrize("enabled", [True, False])
def test_welcome_message_toggle(monkeypatch, tmp_path, enabled):
    (prompts, response), = run_with_document(
        monkeypatch, tmp_path, "clinic", lambda d: d["messages"]["welcome"].update(enabled=enabled), [("hola", reply("Respuesta de la IA."))]
    )
    welcome = _document("clinic")["messages"]["welcome"]["text"]
    if enabled:
        assert prompts == [] and response.strip() == welcome.strip()
    else:
        assert prompts and response == "Respuesta de la IA."


def test_payment_report_message_is_optional(monkeypatch, tmp_path):
    turns = [("Ya pagué", reply("Gracias, lo reviso.", "buy", payment_status="reportado"))]
    (_, with_message), = run_with_document(monkeypatch, tmp_path / "con", "saas", lambda d: None, turns)
    (_, without_message), = run_with_document(monkeypatch, tmp_path / "sin", "saas", lambda d: d["messages"].pop("payment_reported"), turns)
    assert with_message.strip() == _document("saas")["messages"]["payment_reported"].strip()
    assert without_message == "Gracias, lo reviso."


def test_payment_confirmed_message_reaches_the_post_payment_prompt(monkeypatch, tmp_path):
    turns = [("Quiero pagar por nequi", reply("Listo.", "buy", payment_method="nequi")), ("Ya casi", reply("Perfecto."))]
    (_, _), (prompts, _) = run_with_document(
        monkeypatch, tmp_path, "saas", lambda d: d["messages"].update(payment_confirmed="¡Pago recibido, gracias!"), turns
    )
    assert "ON_PAYMENT_CONFIRMED_MESSAGE: ¡Pago recibido, gracias!" in prompts[0]


def test_conversation_windows_drive_the_conversation_state(monkeypatch, tmp_path):
    service = copy_tenant(tmp_path, "saas")
    path = BusinessConfigStore(service.tenants_root).path_for("saas")
    document = json.loads(path.read_text(encoding="utf-8"))
    document["engine"]["conversation"] = {"active_window_minutes": 60, "reset_hours": 1}
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, "saas")
    custom = load_tenant_runtime_yaml("saas", config_service=service)["config"]
    default = load_tenant_runtime_yaml("saas")["config"]

    now = datetime.now(timezone.utc)
    # Por defecto (15 min / 4 h): hace 30 min la conversación está "tibia" y hace 2 h también.
    assert get_conversation_state(now - timedelta(minutes=30), default) == "warm"
    assert get_conversation_state(now - timedelta(hours=2), default) == "warm"
    # Con 60 min / 1 h: hace 30 min sigue activa y hace 2 h empieza de nuevo.
    assert get_conversation_state(now - timedelta(minutes=30), custom) == "active"
    assert get_conversation_state(now - timedelta(hours=2), custom) == "cold"


def test_prompt_word_limits_match_the_current_engine(monkeypatch, tmp_path):
    industry = [f"sector{index}" for index in range(PROMPT_WORD_LIMITS["industry"] + 4)]
    promise = [f"promesa{index}" for index in range(PROMPT_WORD_LIMITS["value_proposition"] + 4)]
    (prompts, _), = run_with_document(
        monkeypatch, tmp_path, "saas",
        lambda d: d["identity"].update(industry=" ".join(industry), value_proposition=" ".join(promise)),
        [("Necesito información", reply("Claro."))],
    )
    for words, limit in ((industry, PROMPT_WORD_LIMITS["industry"]), (promise, PROMPT_WORD_LIMITS["value_proposition"])):
        assert " ".join(words[:limit]) in prompts[0]
        assert words[limit] not in prompts[0]


# ---------------------------------------------------------------------------
# Evidencia de uso: al cambiar el campo en el contrato, cambia el prompt del motor actual
# ---------------------------------------------------------------------------

def _first_plan(document: dict) -> dict:
    return document["offer"]["plans"][0]


CONNECTED_CASES = {
    # caso: (negocio, cambio en el documento, texto esperado en el prompt, turno)
    "sector": ("saas", lambda d: d["identity"].update(industry="software contable para tiendas"), "Industria del negocio: software contable para tiendas.", 0),
    "promesa": ("saas", lambda d: d["identity"].update(value_proposition="Cuadra tu caja en minutos"), "Promesa comercial: Cuadra tu caja en minutos.", 0),
    "motivos": ("saas", lambda d: d["sales"].update(buying_motivation={"primary": "ahorro", "secondary": "control"}),
                "Motores de compra del YAML: ahorro y control.", 0),
    "impactos": ("saas", lambda d: d["sales"].update(customer_problems=[{"id": "caja", "impacts": ["la caja no cuadra al cierre"]}]),
                 "Casos típicos: la caja no cuadra al cierre.", 0),
    "casos_de_uso": ("saas", lambda d: (d["sales"].pop("customer_problems", None), d["sales"].update(
        use_cases=[{"name": "cierre de caja", "signals": ["no cuadra"], "approach": "conciliar"}])), "Casos típicos: cierre de caja.", 0),
    "incluye": ("saas", lambda d: _first_plan(d).update(includes=["soporte 24/7"]), "Incluye: soporte 24/7.", 1),
    "no_incluye": ("saas", lambda d: _first_plan(d).update(not_included=["hardware"]), "No incluye: hardware.", 1),
    "primer_pago": ("saas", lambda d: _first_plan(d)["prices"][0].update(first_payment=77777), "first_payment=77777", 1),
    "precio_unico": ("saas", lambda d: _first_plan(d)["prices"][0].update(price=55555), "price=55555", 1),
    "categorias": ("restaurant", lambda d: d["offer"]["catalog"]["categories"][0].update(name="Combos"), "Qué se cobra: Combos", 0),
    "condiciones": ("saas", lambda d: d["terms"].update(conditions=["pago anticipado"]), "Condiciones: pago anticipado.", 1),
    "encuadre_precio": ("saas", lambda d: d["terms"].update(price_framing="directo"), "Si el cliente duda, muéstrale el valor real: directo.", 1),
    "retorno": ("saas", lambda d: d["terms"].update(roi_break_even_sales=7), "Con 7 ventas al mes ya pagó el servicio.", 1),
    "argumento_retorno": ("saas", lambda d: (d["terms"].pop("roi_break_even_sales", None), d["terms"].update(roi_hints=["una venta paga el mes"])),
                          "una venta paga el mes.", 1),
    "acciones": ("saas", lambda d: d["capabilities"].update(actions_primary=["cerrar_venta"], actions_support=["seguimiento"]),
                 "Acciones disponibles: cerrar_venta, seguimiento", 0),
    "canales": ("saas", lambda d: d["capabilities"].update(service_channels=["whatsapp", "instagram"]),
                "CANALES DE ATENCION (business_channels): whatsapp, instagram", 0),
    "canales_producto": ("saas", lambda d: d["capabilities"].update(product_channels=["telegram"]), "CANALES DEL SISTEMA (system_channels): telegram", 0),
    "modo_catalogo": ("restaurant", lambda d: d["engine"].update(features={"pricing_enabled": True, "catalog_mode": False}),
                      "Tiene opciones de servicio disponibles con pricing definido.", 0),
}


@pytest.mark.parametrize("case", CONNECTED_CASES)
def test_connected_fields_change_the_prompt(monkeypatch, tmp_path, case):
    slug, mutate, expected, turn = CONNECTED_CASES[case]
    before = run_with_document(monkeypatch, tmp_path / "antes", slug, lambda d: None, TWO_TURNS)
    after = run_with_document(monkeypatch, tmp_path / "despues", slug, mutate, TWO_TURNS)
    assert expected not in before[turn][0][0]
    assert expected in after[turn][0][0]


# Campo del contrato marcado `conectado` → prueba de este archivo que demuestra que el motor actual lo usa.
CONNECTED_EVIDENCE: dict[str, str] = {
    "schema_version": "test_invalid_contract_falls_back_to_yaml",
    "tenant_slug": "test_store_rejects_documents_of_another_tenant",
    "identity.industry": "test_prompt_word_limits_match_the_current_engine",
    "identity.value_proposition": "test_prompt_word_limits_match_the_current_engine",
    "offer.model": "test_tenants_stay_isolated_with_contract_source",
    "offer.plans[].id": "test_payment_methods_reach_the_customer",
    "offer.plans[].name": "test_plan_prices_format_is_unchanged",
    "offer.plans[].prices[].currency": "test_plan_prices_format_is_unchanged",
    "offer.plans[].prices[].implementation": "test_plan_prices_format_is_unchanged",
    "offer.plans[].prices[].monthly": "test_plan_prices_format_is_unchanged",
    "offer.plans[].prices[].first_payment": "test_connected_fields_change_the_prompt",
    "offer.plans[].prices[].price": "test_connected_fields_change_the_prompt",
    "offer.plans[].includes": "test_connected_fields_change_the_prompt",
    "offer.plans[].not_included": "test_connected_fields_change_the_prompt",
    "offer.plans[].payment_profile": "test_payment_methods_reach_the_customer",
    "offer.plans[].available": "test_unavailable_offer_is_not_offered",
    "offer.catalog.categories[].id": "test_unavailable_offer_is_not_offered",
    "offer.catalog.categories[].name": "test_connected_fields_change_the_prompt",
    "offer.catalog.items[].available": "test_unavailable_offer_is_not_offered",
    "offer.catalog.items[].category": "test_product_category_decides_which_categories_are_offered",
    "offer.catalog.payment_profile": "test_payment_methods_reach_the_customer",
    "terms.conditions": "test_connected_fields_change_the_prompt",
    "terms.price_framing": "test_connected_fields_change_the_prompt",
    "terms.roi_break_even_sales": "test_connected_fields_change_the_prompt",
    "terms.roi_hints": "test_connected_fields_change_the_prompt",
    "payments[].id": "test_payment_methods_reach_the_customer",
    "payments[].link": "test_payment_methods_reach_the_customer",
    "payments[].transfer_enabled": "test_disabled_transfers_are_not_delivered",
    "payments[].transfer_methods[].type": "test_payment_methods_reach_the_customer",
    "payments[].transfer_methods[].number": "test_payment_methods_reach_the_customer",
    "payments[].transfer_methods[].bank": "test_payment_methods_reach_the_customer",
    "payments[].transfer_methods[].account_type": "test_payment_methods_reach_the_customer",
    "payments[].transfer_methods[].account_number": "test_payment_methods_reach_the_customer",
    "payments[].transfer_methods[].reference": "test_payment_methods_reach_the_customer",
    "sales.buying_motivation.primary": "test_connected_fields_change_the_prompt",
    "sales.buying_motivation.secondary": "test_connected_fields_change_the_prompt",
    "sales.customer_problems[].id": "test_connected_fields_change_the_prompt",
    "sales.customer_problems[].impacts": "test_connected_fields_change_the_prompt",
    "sales.use_cases[].name": "test_connected_fields_change_the_prompt",
    "capabilities.service_channels": "test_connected_fields_change_the_prompt",
    "capabilities.product_channels": "test_connected_fields_change_the_prompt",
    "capabilities.actions_primary": "test_connected_fields_change_the_prompt",
    "capabilities.actions_support": "test_connected_fields_change_the_prompt",
    "capabilities.closing_methods.payment_link": "test_closing_and_data_collection_toggles_change_the_prompt",
    "capabilities.closing_methods.human_handoff": "test_closing_and_data_collection_toggles_change_the_prompt",
    "capabilities.closing_methods.data_collection": "test_closing_and_data_collection_toggles_change_the_prompt",
    "capabilities.data_collection.enabled": "test_closing_and_data_collection_toggles_change_the_prompt",
    "capabilities.data_collection.fields": "test_closing_and_data_collection_toggles_change_the_prompt",
    "messages.welcome.enabled": "test_welcome_message_toggle",
    "messages.welcome.text": "test_welcome_message_toggle",
    "messages.payment_reported": "test_payment_report_message_is_optional",
    "messages.payment_confirmed": "test_payment_confirmed_message_reaches_the_post_payment_prompt",
    "response_style.length": "test_each_response_length_option_controls_prompt_and_truncation",
    "response_style.max_words": "test_changing_the_contract_changes_response_length",
    "engine.conversation.active_window_minutes": "test_conversation_windows_drive_the_conversation_state",
    "engine.conversation.reset_hours": "test_conversation_windows_drive_the_conversation_state",
    "engine.features.catalog_mode": "test_connected_fields_change_the_prompt",
    "engine.features.business_model": "test_connected_fields_change_the_prompt",
}


def test_every_connected_field_has_evidence_in_this_file():
    fields = contract_fields(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    connected = {path for path, field in fields.items() if field.engine == "conectado"}
    assert sorted(connected - set(CONNECTED_EVIDENCE)) == [], "campos marcados conectados sin prueba de uso"
    assert sorted(set(CONNECTED_EVIDENCE) - connected) == [], "pruebas de uso para campos no marcados conectados"
    tests = {name for name, value in globals().items() if name.startswith("test_") and callable(value)}
    assert sorted(set(CONNECTED_EVIDENCE.values()) - tests) == []
