"""
Integración del contrato con el motor.

- Con el contrato como fuente, el motor produce los mismos prompts y respuestas que con los YAML, en los nueve negocios, más
  lo que solo existe en el contrato: el perfil comercial (bloque del prompt y tono), las preguntas frecuentes y las
  características de cada producto. Un negocio que sigue con sus YAML no cambia.
- El contrato es opcional por negocio (`BUSINESS_CONFIG_CONTRACT_TENANTS`) y, si es inválido, el
  motor vuelve a los YAML.
- Cada campo marcado `x-engine: conectado` en el contrato tiene aquí una prueba de que cambiarlo
  cambia lo que hace el motor (`CONNECTED_EVIDENCE`). Lo que el motor no usa todavía está marcado `pendiente`.

Sin base de datos ni llamadas reales a la IA: memoria en RAM y LLM simulado. Los datos de pago se
comparan sin imprimirse (ver `test_payment_data_protection.py`).
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
from app.domain.business_config.compiler import comparable_with_yaml, compile_business_config
from app.domain.business_config.contract import BusinessConfig
from app.domain.business_config.engine_policy import PROMPT_WORD_LIMITS, RESPONSE_LENGTH_MAX_WORDS
from app.domain.business_config.payment_data import iter_payment_blocks
from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService
from app.infrastructure.config.business_config_store import CONTRACT_FILENAME, BusinessConfigStore
from app.infrastructure.config.config_service import ConfigService
from app.infrastructure.config.legacy_field_catalog import contract_fields
from pipeline_harness import TENANTS, as_yaml_prompt, copy_tenant, reply, run_conversation, run_with_document

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
# Equivalencia: con el contrato, el motor hace lo mismo que con los YAML, más el perfil comercial
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("slug", TENANTS)
def test_runtime_from_contract_equals_runtime_from_yaml(monkeypatch, slug):
    monkeypatch.delenv(loader.CONTRACT_TENANTS_ENV, raising=False)
    from_yaml = load_tenant_runtime_yaml(slug, channel="whatsapp")
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, slug)
    from_contract = load_tenant_runtime_yaml(slug, channel="whatsapp")
    # Lo único que añade el contrato es el perfil comercial: ninguno de los nueve tiene preguntas frecuentes.
    assert set(from_contract["config"]) - set(from_yaml["config"]) == {"profile"}
    assert comparable_with_yaml(from_contract) == from_yaml


@pytest.mark.parametrize("slug", TENANTS)
def test_engine_prompts_and_replies_are_identical_with_contract_source(monkeypatch, slug):
    monkeypatch.delenv(loader.CONTRACT_TENANTS_ENV, raising=False)
    from_yaml = run_conversation(slug, CONVERSATION, user_id="equivalencia")
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, slug)
    from_contract = run_conversation(slug, CONVERSATION, user_id="equivalencia")
    runtime = load_tenant_runtime_yaml(slug)

    # Única diferencia intencional: el perfil comercial (bloque y tono). Sin él, prompts y respuestas coinciden.
    assert "PERFIL COMERCIAL DEL NEGOCIO:" in from_contract[0][0][0]
    assert all("PERFIL COMERCIAL DEL NEGOCIO:" not in prompt for prompts, _ in from_yaml for prompt in prompts)
    assert all(prompts for prompts, _response in from_contract[:3])
    assert [([as_yaml_prompt(prompt, runtime) for prompt in prompts], response) for prompts, response in from_contract] == from_yaml
    assert from_contract[-1][1].startswith("Avanzamos con el siguiente paso.")


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


def test_inactive_payment_methods_are_not_delivered(monkeypatch, tmp_path):
    def _pause_nequi(document):
        for profile in document["payments"]:
            for method in profile["transfer_methods"]:
                if method["type"] == "nequi":
                    method["enabled"] = False

    def _pause_link(document):
        for profile in document["payments"]:
            profile["link_enabled"] = False

    by_nequi = [("Quiero pagar por nequi", reply("Listo.", "buy", payment_method="nequi"))]
    (_, active), = run_with_document(monkeypatch, tmp_path / "activa", "saas", lambda d: None, by_nequi)
    (_, paused), = run_with_document(monkeypatch, tmp_path / "pausada", "saas", _pause_nequi, by_nequi)
    assert "nequi usando el número" in active
    assert "nequi usando el número" not in paused

    by_link = [("Quiero pagar por link", reply("Listo.", "buy", payment_method="link"))]
    (_, active), = run_with_document(monkeypatch, tmp_path / "enlace_activo", "saas", lambda d: None, by_link)
    (_, paused), = run_with_document(monkeypatch, tmp_path / "enlace_pausado", "saas", _pause_link, by_link)
    assert "Puedes pagar aquí" in active
    assert "Puedes pagar aquí" not in paused


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
    path = BusinessConfigStore(service.tenants_root).engine_settings_path_for("saas")
    settings = json.loads(path.read_text(encoding="utf-8"))
    settings["conversation"] = {"active_window_minutes": 60, "reset_hours": 1}
    path.write_text(json.dumps(settings, ensure_ascii=False), encoding="utf-8")
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
# Perfil comercial: solo con el contrato
# ---------------------------------------------------------------------------

CONTRACTS_DIR = ROOT_DIR / "project" / "config" / "contracts" / "v1"
PANEL_DOCUMENT = ROOT_DIR / "apps" / "admin-web" / "src" / "test" / "fixtures" / "sampleContractDocument.json"
CATALOG_TENANTS = ["agencia_viajes", "escuela_conduccion", "restaurant", "tienda_ropa"]


def _profile_block(prompt: str) -> str:
    assert "PERFIL COMERCIAL DEL NEGOCIO:" in prompt
    return prompt.split("PERFIL COMERCIAL DEL NEGOCIO:\n", 1)[1].split("\n\n", 1)[0]


def _stored(slug: str) -> BusinessConfig:
    return BusinessConfigStore(ConfigService().tenants_root).load(slug)


def test_example_document_compiles_with_every_option():
    config = BusinessConfig.model_validate_json((CONTRACTS_DIR / "business-config.example.json").read_text(encoding="utf-8"))
    compiled = compile_business_config(config, lambda ref: "valor-de-prueba")
    assert compiled["config"]["response"] == {"length": "medium", "max_words": 75}
    assert len(compiled["config"]["knowledge"]["faqs"]) == 2
    assert compiled["pricing"]["catalog"]["items"][0]["price"] == {"COP": 18000}
    assert compiled["pricing"]["catalog"]["items"][1]["features"] == ["para 12 porciones", "decoración personalizada"]
    profile = compiled["config"]["profile"]
    assert profile["name"] == "La Masa Madre" and profile["tone"] == "cercano y alegre"
    assert profile["recommendations"] == [{"when": "celebra un cumpleaños", "recommend": "Torta de chocolate"}]
    assert profile["promotions"] == [{"name": "Lunes de pan", "details": "10 % de descuento en panes los lunes", "valid_until": "2030-12-31"}]
    block = PromptBuilderService.build_business_profile_context(compiled)
    assert "Negocio: La Masa Madre" in block and "- Si celebra un cumpleaños: recomienda Torta de chocolate." in block


@pytest.mark.parametrize("slug", TENANTS)
def test_profile_block_exists_only_with_contract_source(monkeypatch, slug):
    turns = [("Hola, info", reply("Claro."))]
    monkeypatch.delenv(loader.CONTRACT_TENANTS_ENV, raising=False)
    (yaml_prompts, _), = run_conversation(slug, turns, user_id="perfil")
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, slug)
    (contract_prompts, _), = run_conversation(slug, turns, user_id="perfil")

    config = _stored(slug)
    assert "PERFIL COMERCIAL DEL NEGOCIO:" not in yaml_prompts[0]
    block = _profile_block(contract_prompts[0])
    assert f"Negocio: {config.identity.name}" in block
    assert f"palabras, {config.response_style.tone.strip()}." in contract_prompts[0]
    assert "palabras, natural y claro." in yaml_prompts[0]
    for question in (config.sales.discovery.questions if config.sales.discovery else None) or []:
        assert f"- {question}" in block


PROFILE_CASES = {
    "marca": (lambda d: d["identity"].update(brand_name="Sabor Casero"), "Negocio: Sabor Casero"),
    "diferenciadores": (
        lambda d: d["identity"].update(differentiators=["ingredientes locales", "entrega en 30 minutos."]),
        "Diferenciadores: ingredientes locales; entrega en 30 minutos.",
    ),
    "ubicacion": (
        lambda d: d["identity"].update(location={"type": "mixto", "address": "Calle 1 #2-3", "city": "Bogotá", "coverage": {"type": "nacional", "zones": ["Colombia"]}}),
        "Ubicación: local físico y atención virtual; Calle 1 #2-3, Bogotá.\nCobertura nacional: Colombia.",
    ),
    "modalidades": (lambda d: d["identity"].update(service_modes=["envio", "recoger"]), "Modalidades de atención: con envío, para recoger."),
    "beneficios": (lambda d: d["sales"].update(benefits=["comer bien sin salir de casa"]), "Beneficios para el cliente: comer bien sin salir de casa."),
    "argumentos": (lambda d: d["sales"].update(arguments=["Todo se prepara al momento."]), "Argumentos de venta:\n- Todo se prepara al momento."),
    "preguntas": (
        lambda d: d["sales"].setdefault("discovery", {}).update(questions=["¿Para cuántas personas es el pedido?"]),
        "Preguntas para entender al cliente (como máximo una por mensaje y solo si aún no lo sabes):\n- ¿Para cuántas personas es el pedido?",
    ),
    "recomendaciones": (
        lambda d: d["sales"].update(recommendation_rules=[{"when": "pide algo para compartir", "recommend": "hamburguesa_doble"}, {"when": "tiene sed", "recommend": "bebidas"}]),
        "Recomendaciones:\n- Si pide algo para compartir: recomienda Hamburguesa Doble.\n- Si tiene sed: recomienda Bebidas.",
    ),
    "instrucciones": (
        lambda d: d["sales"].update(instructions=["Confirma la dirección antes de cerrar el pedido."]),
        "Instrucciones del negocio:\n- Confirma la dirección antes de cerrar el pedido.",
    ),
    "promociones": (
        lambda d: d["terms"].update(promotions=[{"name": "Martes 2x1", "details": "Dos hamburguesas sencillas por el precio de una", "valid_until": "2999-12-31"}]),
        "Promociones vigentes (no ofrezcas otras promociones ni descuentos):\n- Martes 2x1: Dos hamburguesas sencillas por el precio de una (válida hasta 2999-12-31)",
    ),
    "caracteristicas": (
        lambda d: d["offer"]["catalog"]["items"][0].update(features=["pan artesanal", "papas incluidas"]),
        "- Hamburguesa Sencilla: Carne artesanal, queso y vegetales frescos. Características: pan artesanal, papas incluidas.",
    ),
    "descripcion_producto": (
        lambda d: d["offer"]["catalog"]["items"][0].update(description="Doble carne y salsa de la casa."),
        "- Hamburguesa Sencilla: Doble carne y salsa de la casa.",
    ),
}


@pytest.mark.parametrize("case", PROFILE_CASES)
def test_each_profile_option_reaches_the_prompt(monkeypatch, tmp_path, case):
    mutate, expected = PROFILE_CASES[case]
    turns = [("Hola, info", reply("Claro."))]
    (before, _), = run_with_document(monkeypatch, tmp_path / "antes", "restaurant", lambda d: None, turns)
    (after, _), = run_with_document(monkeypatch, tmp_path / "despues", "restaurant", mutate, turns)
    assert expected not in before[0]
    assert expected in _profile_block(after[0])


def test_removing_profile_options_removes_them_from_the_prompt(monkeypatch, tmp_path):
    def _clear(document):
        for key in ("differentiators", "location", "service_modes"):
            document["identity"].pop(key, None)
        document["response_style"].pop("tone", None)
        document["sales"].pop("benefits", None)
        for item in document["offer"]["catalog"]["items"]:
            item.pop("description", None)

    (prompts, _), = run_with_document(monkeypatch, tmp_path, "restaurant", _clear, [("Hola, info", reply("Claro."))])
    identity = _stored("restaurant").identity
    # Sin opciones del perfil solo quedan el nombre y la descripción, que siempre son obligatorios.
    assert _profile_block(prompts[0]).splitlines() == [f"Negocio: {identity.name}", f"Descripción: {identity.description.strip()}"]


def test_expired_promotions_are_not_offered(monkeypatch, tmp_path):
    promotions = [
        {"name": "Vencida", "details": "Ya no aplica", "valid_until": "2000-01-01"},
        {"name": "Permanente", "details": "Siempre vigente"},
    ]
    (prompts, _), = run_with_document(
        monkeypatch, tmp_path, "restaurant", lambda d: d["terms"].update(promotions=promotions), [("¿Promociones?", reply("Claro."))]
    )
    block = _profile_block(prompts[0])
    assert "- Permanente: Siempre vigente" in block
    assert "Vencida" not in block


def test_ongoing_conversation_keeps_only_the_profile_rules(monkeypatch, tmp_path):
    def _with_rules(document):
        document["sales"]["instructions"] = ["Confirma la dirección antes de cerrar."]

    turns = [("Necesito información", reply("Claro.")), ("¿Y el domicilio?", reply("Te cuento."))]
    (first, _), (second, _) = run_with_document(monkeypatch, tmp_path, "restaurant", _with_rules, turns)
    assert "Negocio: " in _profile_block(first[0]) and "Diferenciadores:" in _profile_block(first[0])
    ongoing = _profile_block(second[0])
    assert "Negocio: " not in ongoing and "Diferenciadores:" not in ongoing and "Detalle de la oferta:" not in ongoing
    assert ongoing.splitlines() == ["Instrucciones del negocio:", "- Confirma la dirección antes de cerrar."]
    assert "máximo 60 palabras, cercano, agil y orientado a orden." in second[0]


def test_active_prompt_stays_within_budget_with_contract_source(monkeypatch):
    """Mismo límite que tests/test_memory_context_persistence.py, ahora con la fuente del contrato."""
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, "asesor_ai_prod")
    runtime = load_tenant_runtime_yaml("asesor_ai_prod", extra_yaml={
        "conversation_state": "active",
        "memory_context": {"last_intent": "price", "last_pain": "mensajes", "last_ai_response": "ok"},
    })
    prompt, _, _ = PromptBuilderService().build(
        client_config_id="asesor_ai_prod", user_message="siguiente", yaml_config=runtime, faq_results=[], progression_rules=None
    )
    # asesor_ai_prod no tiene instrucciones ni promociones, las reglas que siguen en una conversación en curso: solo cambia el tono.
    assert "PERFIL COMERCIAL DEL NEGOCIO:" not in prompt
    assert "máximo 75 palabras, humano, cercano, directo y comercial de cierre." in prompt
    assert len(prompt) < 2800


def test_panel_document_is_valid_and_reaches_the_engine():
    """El documento con el que se prueba el panel (`src/test/fixtures`) debe cumplir el contrato."""
    config = BusinessConfig.model_validate_json(PANEL_DOCUMENT.read_text(encoding="utf-8"))
    secrets = {}
    compiled = compile_business_config(config, lambda ref: secrets.setdefault(ref.secret_ref, f"valor-{len(secrets)}"))
    assert set(secrets) == {"secret_store:principal.link", "secret_store:principal.transfer.0.number"}
    block = PromptBuilderService.build_business_profile_context(compiled)
    assert compiled["config"]["profile"]["tone"] == "cercano y amable"
    assert "- Si pide café: recomienda Croissant de mantequilla." in block
    assert "Desayuno del lunes: 10 % de descuento en desayunos los lunes" in block
    # El producto no disponible viaja en el contrato, pero el motor no lo ofrece.
    assert [item.available for item in config.offer.catalog.items] == [True, True, False]
    assert [item["name"] for item in compiled["pricing"]["catalog"]["items"]] == ["Café americano", "Croissant de mantequilla"]


def test_recommendations_to_something_not_offered_are_dropped(monkeypatch, tmp_path):
    rules = [{"when": "quiere algo nuevo", "recommend": "no_existe"}, {"when": "tiene sed", "recommend": "bebidas"}]
    (prompts, _), = run_with_document(
        monkeypatch, tmp_path, "restaurant", lambda d: d["sales"].update(recommendation_rules=rules), [("Hola, info", reply("Claro."))]
    )
    block = _profile_block(prompts[0])
    assert "- Si tiene sed: recomienda Bebidas." in block
    assert "quiere algo nuevo" not in block and "no_existe" not in block


# ---------------------------------------------------------------------------
# Preguntas frecuentes y precios del catálogo: solo con el contrato
# ---------------------------------------------------------------------------

def test_faqs_reach_the_prompt_only_when_configured(monkeypatch, tmp_path):
    faqs = [{"question": "¿Atienden los domingos?", "answer": "Sí, de 9 a. m. a 1 p. m."}]
    (prompts, _), = run_with_document(
        monkeypatch, tmp_path, "restaurant",
        lambda d: d.update(knowledge={"faqs": faqs}),
        [("¿Abren el domingo?", reply("Sí."))],
    )
    assert "CONOCIMIENTO DEL NEGOCIO (preguntas frecuentes):\n- P: ¿Atienden los domingos?\n  R: Sí, de 9 a. m. a 1 p. m." in prompts[0]

    monkeypatch.setattr(ai_pipeline_module, "load_tenant_runtime_yaml", load_tenant_runtime_yaml)
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, "*")
    for slug in TENANTS:
        (plain_prompts, _), = run_conversation(slug, [("Hola, info", reply("Claro."))], user_id="sin-faq")
        assert "CONOCIMIENTO DEL NEGOCIO" not in plain_prompts[0]


@pytest.mark.parametrize("slug", CATALOG_TENANTS)
def test_catalog_prices_reach_the_prompt(monkeypatch, slug):
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, slug)
    config = _stored(slug)
    (prompts, _), = run_conversation(slug, [("¿Cuánto cuesta?", reply("Te cuento."))], user_id="catalogo")
    prices_line = next(line for line in prompts[0].splitlines() if line.startswith("Precios:"))
    for item in config.offer.catalog.items:
        assert f"{item.name} -> COP: {item.prices[0].amount}" in prices_line


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
    "datos_propios_del_negocio": ("saas", lambda d: d["capabilities"]["data_collection"].update(fields=["cedula_de_prueba"]),
                                  "Campos definidos para pedir al cliente:\ncedula_de_prueba", 0),
    "canales": ("saas", lambda d: d["capabilities"].update(service_channels=["whatsapp", "instagram"]),
                "CANALES DE ATENCION (business_channels): whatsapp, instagram", 0),
    "canales_producto": ("saas", lambda d: d["capabilities"].update(product_channels=["telegram"]), "CANALES DEL SISTEMA (system_channels): telegram", 0),
    "modo_catalogo": ("restaurant", lambda d: d.update(features={"pricing_enabled": True, "catalog_mode": False}),
                      "Tiene opciones de servicio disponibles con pricing definido.", 0),
    "tono": ("restaurant", lambda d: d["response_style"].update(tone="paciente y muy claro"), "máximo 60 palabras, paciente y muy claro.", 1),
    "descripcion_plan": ("saas", lambda d: _first_plan(d).update(name="Plan Caja", description="Incluye soporte por chat"),
                         "- Plan Caja: Incluye soporte por chat", 0),
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
    "payments[].link_enabled": "test_inactive_payment_methods_are_not_delivered",
    "payments[].transfer_enabled": "test_disabled_transfers_are_not_delivered",
    "payments[].transfer_methods[].enabled": "test_inactive_payment_methods_are_not_delivered",
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
    "features.catalog_mode": "test_connected_fields_change_the_prompt",
    "features.business_model": "test_connected_fields_change_the_prompt",
    # Perfil comercial, tono, preguntas frecuentes y precios del catálogo: solo con el contrato.
    "identity.name": "test_profile_block_exists_only_with_contract_source",
    "identity.brand_name": "test_each_profile_option_reaches_the_prompt",
    "identity.description": "test_removing_profile_options_removes_them_from_the_prompt",
    "identity.differentiators": "test_each_profile_option_reaches_the_prompt",
    "identity.location.type": "test_each_profile_option_reaches_the_prompt",
    "identity.location.address": "test_each_profile_option_reaches_the_prompt",
    "identity.location.city": "test_each_profile_option_reaches_the_prompt",
    "identity.location.coverage.type": "test_each_profile_option_reaches_the_prompt",
    "identity.location.coverage.zones": "test_each_profile_option_reaches_the_prompt",
    "identity.service_modes": "test_each_profile_option_reaches_the_prompt",
    "offer.plans[].description": "test_connected_fields_change_the_prompt",
    "offer.catalog.items[].id": "test_each_profile_option_reaches_the_prompt",
    "offer.catalog.items[].name": "test_catalog_prices_reach_the_prompt",
    "offer.catalog.items[].description": "test_each_profile_option_reaches_the_prompt",
    "offer.catalog.items[].prices[].currency": "test_catalog_prices_reach_the_prompt",
    "offer.catalog.items[].prices[].amount": "test_catalog_prices_reach_the_prompt",
    "offer.catalog.items[].features": "test_each_profile_option_reaches_the_prompt",
    "sales.benefits": "test_each_profile_option_reaches_the_prompt",
    "sales.arguments": "test_each_profile_option_reaches_the_prompt",
    "sales.discovery.questions": "test_each_profile_option_reaches_the_prompt",
    "sales.recommendation_rules[].when": "test_each_profile_option_reaches_the_prompt",
    "sales.recommendation_rules[].recommend": "test_each_profile_option_reaches_the_prompt",
    "sales.instructions": "test_each_profile_option_reaches_the_prompt",
    "terms.promotions[].name": "test_each_profile_option_reaches_the_prompt",
    "terms.promotions[].details": "test_each_profile_option_reaches_the_prompt",
    "terms.promotions[].valid_until": "test_expired_promotions_are_not_offered",
    "response_style.tone": "test_connected_fields_change_the_prompt",
    "knowledge.faqs[].question": "test_faqs_reach_the_prompt_only_when_configured",
    "knowledge.faqs[].answer": "test_faqs_reach_the_prompt_only_when_configured",
}


def test_every_connected_field_has_evidence_in_this_file():
    fields = contract_fields(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    connected = {path for path, field in fields.items() if field.engine == "conectado"}
    assert sorted(connected - set(CONNECTED_EVIDENCE)) == [], "campos marcados conectados sin prueba de uso"
    assert sorted(set(CONNECTED_EVIDENCE) - connected) == [], "pruebas de uso para campos no marcados conectados"
    tests = {name for name, value in globals().items() if name.startswith("test_") and callable(value)}
    assert sorted(set(CONNECTED_EVIDENCE.values()) - tests) == []
