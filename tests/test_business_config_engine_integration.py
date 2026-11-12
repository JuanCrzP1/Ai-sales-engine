"""
Integración del contrato con el motor.

- El motor lee cada negocio solo de su versión publicada en el almacén (la que se publica desde el panel). No necesita carpeta
  YAML y, si el almacén falla o el negocio no tiene versión publicada, no responde con datos viejos: el cliente recibe un
  mensaje neutro y queda la alerta `business_config_unavailable`.
- Cada campo marcado `x-engine: conectado` en el contrato tiene aquí una prueba de que cambiarlo
  cambia lo que hace el motor (`CONNECTED_EVIDENCE`). Lo que el motor no usa todavía está marcado `pendiente`.

Sin llamadas reales a la IA: memoria en RAM y LLM simulado. Cada prueba que cambia un negocio lo publica en un almacén propio
(`publish_document`). Los datos de pago se comparan sin imprimirse (ver `test_payment_data_protection.py`).
"""
from __future__ import annotations

import functools
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from sqlalchemy import update
from sqlalchemy.exc import OperationalError

from app.application.ai_pipeline import UNAVAILABLE_REPLY, AIPipeline
from app.application.pipeline.conversation_flow import get_conversation_state
from app.application.pipeline.response_postprocessor import enforce_max_words
from app.application.runtime import BusinessUnavailableError, load_tenant_runtime_yaml, published_sections, runtime_from_sections
from app.application.runtime import tenant_runtime_loader as loader
from app.domain.business_config.attention import AttentionSettings, handoff_plan, published_attention
from app.domain.business_config.compiler import compile_business_config
from app.domain.business_config.contract import BusinessConfig
from app.domain.business_config.engine_policy import MAX_INDUSTRY_CHARS, MAX_VALUE_PROPOSITION_CHARS, RESPONSE_LENGTH_MAX_WORDS
from app.domain.business_config.payment_data import iter_payment_blocks
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService
from app.infrastructure.ai.prompting.sections import business as business_section, guidance as guidance_section
from app.infrastructure.ai.prompting.sections.knowledge import KNOWLEDGE_HEADER
from app.infrastructure.ai.prompting.view import PromptView
from app.infrastructure.business_config.database import create_business_config_engine
from app.infrastructure.business_config.runtime_access import open_published_reader
from app.infrastructure.business_config.tables import business_configs
from app.infrastructure.config.legacy_field_catalog import contract_fields
from app.infrastructure.persistence.memory_repository import MemoryRepository
from pipeline_harness import TENANTS, TENANTS_DIR, forbid_examples_folder, publish_document, reply, run_conversation, run_with_document, stored_document

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
    return stored_document(slug)


# ---------------------------------------------------------------------------
# Fuente de configuración: solo lo publicado en el almacén
# ---------------------------------------------------------------------------

_no_yaml = forbid_examples_folder


def _say(slug: str, message: str = "¿Qué venden?") -> tuple[str, bool, dict]:
    pipeline = AIPipeline(memory_service=MemoryDomainService(MemoryRepository()))
    pipeline.runtime.generate = lambda prompt, **_kwargs: reply("Hola.")
    return pipeline.run(
        tenant=type("T", (), {"slug": slug, "name": slug, "id": slug})(), user_message=message, user_id="fuente",
        bot_config=None, conversation_history=[], faq_results=[], yaml_config=None, include_metadata=True,
    )


@pytest.mark.parametrize("slug", TENANTS)
def test_the_engine_reads_only_the_published_version(monkeypatch, slug):
    _no_yaml(monkeypatch)
    runtime = load_tenant_runtime_yaml(slug, channel="whatsapp")
    assert runtime == runtime_from_sections(slug, published_sections(slug), channel="whatsapp")
    assert runtime["features"]["pricing_enabled"] is True
    answer, ai_used, _metadata = _say(slug)
    assert ai_used is True and answer


def test_a_business_created_in_the_panel_answers_without_any_yaml_folder(monkeypatch, tmp_path):
    """El caso que bloqueaba los canales: un negocio que nunca tuvo carpeta en `project/config/tenants`."""

    def _new_business(document):
        document["identity"].update(name="Panadería La Espiga", brand_name="La Espiga")

    publish_document(monkeypatch, tmp_path, "restaurant", _new_business, as_slug="panaderia_la_espiga")
    _no_yaml(monkeypatch)  # desde aquí, solo el motor: publicar el ejemplo sí lee su carpeta
    assert not (TENANTS_DIR / "panaderia_la_espiga").exists()
    (prompts, response), = run_conversation("panaderia_la_espiga", [("¿Qué venden?", reply("Pan recién horneado."))], user_id="nuevo")
    assert response == "Pan recién horneado."
    assert "Nombre: La Espiga" in prompts[0]


def test_an_unknown_business_gets_the_neutral_reply_and_an_alert(monkeypatch):
    _no_yaml(monkeypatch)
    errors: list[str] = []
    monkeypatch.setattr(loader.logger, "error", lambda event, **_kwargs: errors.append(event))
    with pytest.raises(BusinessUnavailableError):
        load_tenant_runtime_yaml("negocio_inexistente")
    answer, ai_used, metadata = _say("negocio_inexistente")
    assert (answer, ai_used, metadata["source"]) == (UNAVAILABLE_REPLY, False, "business_unavailable")
    assert errors == ["business_config_unavailable", "business_config_unavailable"]


def test_a_store_failure_never_falls_back_to_yaml(monkeypatch):
    _no_yaml(monkeypatch)

    def _down():
        raise OperationalError("SELECT", {}, Exception("la base no responde"))

    monkeypatch.setattr(loader, "open_published_reader", _down)
    with pytest.raises(BusinessUnavailableError):
        load_tenant_runtime_yaml("restaurant")
    assert _say("restaurant")[:2] == (UNAVAILABLE_REPLY, False)


def _corrupt_published(url: str, change) -> None:
    """Altera lo publicado directamente en la base: el almacén nunca se da por confiable."""
    engine = create_business_config_engine(url)
    with engine.begin() as conn:
        row = conn.execute(business_configs.select().where(business_configs.c.status == "published")).one()
        document = dict(row.document)
        change(document)
        conn.execute(update(business_configs).where(business_configs.c.id == row.id).values(document=document))
    engine.dispose()


@pytest.mark.parametrize(
    "change",
    [lambda d: d.update(schema_version="2.0"), lambda d: d.pop("identity"), lambda d: d.update(tenant_slug="restaurant")],
    ids=["otra_version_del_contrato", "incompleto", "de_otro_negocio"],
)
def test_a_corrupt_published_document_is_never_served(monkeypatch, tmp_path, change):
    url = publish_document(monkeypatch, tmp_path, "saas")
    _corrupt_published(url, change)
    with pytest.raises(BusinessUnavailableError):
        load_tenant_runtime_yaml("saas")
    assert _say("saas")[:2] == (UNAVAILABLE_REPLY, False)


def test_the_fallback_message_is_the_one_written_in_the_panel(monkeypatch, tmp_path):
    """Si la IA no puede responder (aquí, el negocio no tiene clave), el cliente recibe el mensaje del panel; sin él, el neutro."""
    from app.application.pipeline.fallback import PLATFORM_FALLBACK_REPLY

    def _answer_without_ai() -> tuple[str, bool]:
        pipeline = AIPipeline(memory_service=MemoryDomainService(MemoryRepository()), ai_loader=lambda _slug: None)
        return pipeline.run(
            tenant=type("T", (), {"slug": "saas", "name": "saas", "id": "saas"})(), user_message="¿Cuánto cuesta?", user_id="respaldo",
            bot_config=None, conversation_history=[], faq_results=[], yaml_config=None,
        )

    message = "Ahora no podemos responderte por aquí. Escríbenos en un rato, por favor."
    publish_document(monkeypatch, tmp_path / "con", "saas", lambda d: d["messages"].update(fallback=message))
    assert _answer_without_ai() == (message, False)
    publish_document(monkeypatch, tmp_path / "sin", "saas")
    assert _answer_without_ai() == (PLATFORM_FALLBACK_REPLY, False)


def test_the_panel_previews_the_same_neutral_message_the_engine_sends():
    from app.application.pipeline.fallback import PLATFORM_FALLBACK_REPLY

    source = (ROOT_DIR / "apps" / "admin-web" / "src" / "domain" / "assistant" / "fallback.ts").read_text(encoding="utf-8")
    assert f'PLATFORM_FALLBACK_REPLY = "{PLATFORM_FALLBACK_REPLY}";' in source


# ---------------------------------------------------------------------------
# Aislamiento entre negocios
# ---------------------------------------------------------------------------

def test_tenants_stay_isolated(monkeypatch):
    (saas_prompts, _), = run_conversation("asesor_ai_prod", [("¿Qué venden?", reply("Hola."))], user_id="mismo")
    (food_prompts, _), = run_conversation("restaurant", [("¿Qué venden?", reply("Hola."))], user_id="mismo")
    assert "Plan Basico" in saas_prompts[0] and "Hamburguesas" not in saas_prompts[0]
    assert "Hamburguesas" in food_prompts[0] and "Plan Basico" not in food_prompts[0]


# ---------------------------------------------------------------------------
# Longitud de respuesta
# ---------------------------------------------------------------------------

def test_contract_response_length_controls_prompt_and_truncation(monkeypatch):
    long_text = " ".join(["palabra"] * 150) + "."
    (prompts, response), = run_conversation("asesor_ai_prod", [("Explícame todo", reply(long_text))], user_id="longitud")
    assert "Responde en máximo 75 palabras." in prompts[0]
    assert len(response.split()) <= 75
    assert response == enforce_max_words(long_text, 75)


def test_changing_the_contract_changes_response_length(monkeypatch, tmp_path):
    long_text = " ".join(["palabra"] * 150) + "."
    (prompts, response), = run_with_document(
        monkeypatch, tmp_path, "asesor_ai_prod",
        lambda d: d.update(response_style={"length": "long", "max_words": 90}),
        [("Explícame todo", reply(long_text))],
    )
    assert "Responde en máximo 90 palabras." in prompts[0]
    assert len(response.split()) == 90


@pytest.mark.parametrize("length", ["short", "medium", "long"])
@pytest.mark.parametrize("slug", TENANTS)
def test_each_response_length_option_controls_prompt_and_truncation(monkeypatch, tmp_path, slug, length):
    words = RESPONSE_LENGTH_MAX_WORDS[length]
    long_text = " ".join(["palabra"] * 150) + "."
    (prompts, response), = run_with_document(
        monkeypatch, tmp_path, slug, lambda d: d.update(response_style={"length": length}), [("Explícame todo", reply(long_text))]
    )
    assert f"Responde en máximo {words} palabras." in prompts[0]
    assert len(response.split()) == words


@pytest.mark.parametrize("channel", ["whatsapp", "telegram", "web"])
def test_response_length_is_the_same_on_every_channel(monkeypatch, channel):
    runtime = load_tenant_runtime_yaml("asesor_ai_prod", channel=channel)
    assert runtime["channel"] == channel
    assert runtime["config"]["response"] == {"length": "medium", "max_words": 75}


# ---------------------------------------------------------------------------
# Oferta, precios y pagos
# ---------------------------------------------------------------------------

def test_plan_prices_are_said_like_a_salesperson_would(monkeypatch):
    turns = [("Hola, necesito información", reply("Claro.")), ("¿Precio?", reply("Te cuento."))]
    (first, _), (prompts, _) = run_conversation("asesor_ai_prod", turns, user_id="planes")
    line = "- Plan Basico — COP 100.000 de implementación + COP 110.000 al mes · USD 40 de implementación + USD 45 al mes"
    assert line in prompts[0] and line in first[0], "los precios van desde el primer mensaje"


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
    assert "Para cerrar puedes pasarlo con una persona del equipo." in prompts[0]
    assert "enviarle el link de pago" not in prompts[0] and "Datos que pides para cerrar" not in prompts[0]


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


def test_the_attention_messages_reach_the_platform_from_what_was_published(monkeypatch, tmp_path):
    """«Fuera del horario del equipo» y «Cuando la IA retoma» los envía la plataforma (no la IA): llegan desde lo publicado, junto
    con el horario de «Mi negocio», y deciden lo que se le dice al cliente."""
    hours = [{"days": ["lunes", "martes", "miercoles", "jueves", "viernes"], "opens": "08:00", "closes": "18:00"}]

    def mutate(document: dict) -> None:
        document["identity"]["opening_hours"] = hours
        document["messages"].update(after_hours="Atendemos de 8 a 6. Mañana te escribe Laura.", ai_resumed="Perdón la demora, sigo yo.")

    publish_document(monkeypatch, tmp_path, "restaurant", mutate)
    published = published_attention(published_sections("restaurant"))
    assert published.after_hours == "Atendemos de 8 a 6. Mañana te escribe Laura." and published.ai_resumed == "Perdón la demora, sigo yo."
    assert [item.days for item in published.business_hours] == [tuple(hours[0]["days"])]
    # Un martes a las 9 p. m. (hora de Colombia) no hay nadie: la IA sigue y el cliente recibe el mensaje del negocio.
    night = datetime(2026, 11, 11, 2, 0, tzinfo=timezone.utc)
    plan = handoff_plan(AttentionSettings(), published.business_hours, night, after_hours_message=published.after_hours)
    assert (plan.team_available, plan.pause_ai, plan.notice) == (False, False, "Atendemos de 8 a 6. Mañana te escribe Laura.")
    # Sin los mensajes, la plataforma usa los suyos.
    publish_document(monkeypatch, tmp_path / "sin", "restaurant", lambda d: d["identity"].update(opening_hours=hours))
    assert published_attention(published_sections("restaurant")).after_hours is None


def test_conversation_windows_drive_the_conversation_state(monkeypatch, tmp_path):
    default = load_tenant_runtime_yaml("saas")["config"]
    publish_document(monkeypatch, tmp_path, "saas", engine_settings={"conversation": {"active_window_minutes": 60, "reset_hours": 1}})
    custom = load_tenant_runtime_yaml("saas")["config"]

    now = datetime.now(timezone.utc)
    # Por defecto (15 min / 4 h): hace 30 min la conversación está "tibia" y hace 2 h también.
    assert get_conversation_state(now - timedelta(minutes=30), default) == "warm"
    assert get_conversation_state(now - timedelta(hours=2), default) == "warm"
    # Con 60 min / 1 h: hace 30 min sigue activa y hace 2 h empieza de nuevo.
    assert get_conversation_state(now - timedelta(minutes=30), custom) == "active"
    assert get_conversation_state(now - timedelta(hours=2), custom) == "cold"


def test_the_assistant_uses_the_whole_text_up_to_the_contract_limit(monkeypatch, tmp_path):
    """Sin recortes por palabras: el sector y la promesa llegan completos, con el largo máximo que acepta el contrato."""
    industry = ("sector " * 40)[: MAX_INDUSTRY_CHARS - 4] + " fin"
    promise = ("promesa " * 60)[: MAX_VALUE_PROPOSITION_CHARS - 6] + " final"
    assert (len(industry), len(promise)) == (MAX_INDUSTRY_CHARS, MAX_VALUE_PROPOSITION_CHARS)
    (prompts, _), = run_with_document(
        monkeypatch, tmp_path, "saas",
        lambda d: d["identity"].update(industry=industry, value_proposition=promise),
        [("Necesito información", reply("Claro."))],
    )
    assert " ".join(industry.split()) in prompts[0]
    assert " ".join(promise.split()) in prompts[0]


# ---------------------------------------------------------------------------
# Perfil comercial: solo con el contrato
# ---------------------------------------------------------------------------

CONTRACTS_DIR = ROOT_DIR / "project" / "config" / "contracts" / "v1"
PANEL_DOCUMENT = ROOT_DIR / "apps" / "admin-web" / "src" / "test" / "fixtures" / "sampleContractDocument.json"
CATALOG_TENANTS = ["agencia_viajes", "escuela_conduccion", "restaurant", "tienda_ropa"]


def _profile_text(compiled: dict) -> str:
    """El negocio y sus indicaciones, como los arma el prompt a partir de lo compilado."""
    view = PromptView(runtime_from_sections("ejemplo", compiled))
    return f"{business_section.render(view)}\n{guidance_section.render(view)}"


def _profile_block(prompt: str) -> str:
    """Lo que el prompt dice del negocio: desde «EL NEGOCIO» hasta antes de «ESTA CONVERSACIÓN»."""
    assert "EL NEGOCIO\n" in prompt
    return prompt.split("EL NEGOCIO\n", 1)[1].split("ESTA CONVERSACIÓN", 1)[0]


def _stored(slug: str) -> BusinessConfig:
    return open_published_reader().published(slug)


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
    block = _profile_text(compiled)
    assert "Nombre: La Masa Madre" in block and "- Si celebra un cumpleaños: recomienda Torta de chocolate." in block


@pytest.mark.parametrize("slug", TENANTS)
def test_the_profile_block_reaches_the_prompt(monkeypatch, slug):
    (contract_prompts, _), = run_conversation(slug, [("Hola, info", reply("Claro."))], user_id="perfil")
    config = _stored(slug)
    block = _profile_block(contract_prompts[0])
    assert f"Nombre: {config.identity.brand_name or config.identity.name}" in block
    assert f"Tono: {config.response_style.tone.strip().rstrip('.')}. Responde en máximo" in contract_prompts[0]
    for question in (config.sales.discovery.questions if config.sales.discovery else None) or []:
        assert f"- {question}" in block


PROFILE_CASES = {
    "marca": (lambda d: d["identity"].update(brand_name="Sabor Casero"), "Nombre: Sabor Casero"),
    "diferenciadores": (
        lambda d: d["identity"].update(differentiators=["ingredientes locales", "entrega en 30 minutos."]),
        "Lo que lo diferencia: ingredientes locales; entrega en 30 minutos.",
    ),
    "ubicacion": (
        lambda d: d["identity"].update(location={"type": "mixto", "address": "Calle 1 #2-3", "city": "Bogotá", "coverage": {"type": "nacional", "zones": ["Colombia"]}}),
        "Dónde atiende: local físico y atención virtual; Calle 1 #2-3, Bogotá.\nCobertura nacional: Colombia.",
    ),
    "modalidades": (lambda d: d["identity"].update(service_modes=["envio", "recoger"]), "Cómo atiende: con envío, para recoger."),
    "beneficios": (lambda d: d["sales"].update(benefits=["comer bien sin salir de casa"]), "Beneficios para el cliente: comer bien sin salir de casa."),
    "argumentos": (lambda d: d["sales"].update(arguments=["Todo se prepara al momento."]), "Argumentos de venta:\n- Todo se prepara al momento."),
    "preguntas": (
        lambda d: d["sales"].setdefault("discovery", {}).update(questions=["¿Para cuántas personas es el pedido?"]),
        "Preguntas para entender al cliente (una por mensaje y solo si aún no lo sabes):\n- ¿Para cuántas personas es el pedido?",
    ),
    "recomendaciones": (
        lambda d: d["sales"].update(recommendation_rules=[{"when": "pide algo para compartir", "recommend": "hamburguesa_doble"}, {"when": "tiene sed", "recommend": "bebidas"}]),
        "Recomendaciones:\n- Si pide algo para compartir: recomienda Hamburguesa Doble.\n- Si tiene sed: recomienda Bebidas.",
    ),
    "instrucciones": (
        lambda d: d["sales"].update(instructions=["Confirma la dirección antes de cerrar el pedido."]),
        "Instrucciones:\n- Confirma la dirección antes de cerrar el pedido.",
    ),
    "promociones": (
        lambda d: d["terms"].update(promotions=[{"name": "Martes 2x1", "details": "Dos hamburguesas sencillas por el precio de una", "valid_until": "2999-12-31"}]),
        "Promociones vigentes (no ofrezcas otras promociones ni descuentos):\n- Martes 2x1: Dos hamburguesas sencillas por el precio de una (válida hasta 2999-12-31)",
    ),
    "caracteristicas": (
        lambda d: d["offer"]["catalog"]["items"][0].update(features=["pan artesanal", "papas incluidas"]),
        "- Hamburguesa Sencilla — COP 18.000: Carne artesanal, queso y vegetales frescos. Características: pan artesanal, papas incluidas.",
    ),
    "descripcion_producto": (
        lambda d: d["offer"]["catalog"]["items"][0].update(description="Doble carne y salsa de la casa."),
        "- Hamburguesa Sencilla — COP 18.000: Doble carne y salsa de la casa.",
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
    block = _profile_block(prompts[0])
    # Sin esas opciones no queda ninguna de sus líneas; el tono vuelve al de la plataforma.
    for gone in ("Lo que lo diferencia:", "Dónde atiende:", "Cómo atiende:", "Beneficios para el cliente:"):
        assert gone not in block
    assert "Tono: natural y claro. Responde en máximo" in block
    assert "- Hamburguesa Sencilla — COP 18.000\n" in block


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


def test_ongoing_conversation_keeps_the_whole_business(monkeypatch, tmp_path):
    """Antes, en una conversación en curso solo quedaban las reglas del perfil: el asistente olvidaba qué vendía."""
    def _with_rules(document):
        document["sales"]["instructions"] = ["Confirma la dirección antes de cerrar."]

    turns = [("Necesito información", reply("Claro.")), ("¿Y el domicilio?", reply("Te cuento."))]
    (first, _), (second, _) = run_with_document(monkeypatch, tmp_path, "restaurant", _with_rules, turns)
    assert _profile_block(first[0]) == _profile_block(second[0])
    ongoing = _profile_block(second[0])
    assert "Nombre: " in ongoing and "Lo que lo diferencia:" in ongoing and "LO QUE VENDE\n- " in ongoing
    assert "Instrucciones:\n- Confirma la dirección antes de cerrar." in ongoing
    assert "Tono: cercano, agil y orientado a orden. Responde en máximo 60 palabras." in second[0]


def test_active_prompt_stays_within_budget(monkeypatch):
    """Mismo límite que tests/test_memory_context_persistence.py, con lo publicado."""
    runtime = load_tenant_runtime_yaml("asesor_ai_prod", extra_yaml={
        "conversation_state": "active",
        "memory_context": {"last_intent": "price", "last_pain": "mensajes", "last_ai_response": "ok"},
    })
    prompt, _, _ = PromptBuilderService().build(
        client_config_id="asesor_ai_prod", user_message="siguiente", yaml_config=runtime, faq_results=[], progression_rules=None
    )
    assert "Tono: humano, cercano, directo y comercial de cierre. Responde en máximo 75 palabras." in prompt
    # El negocio completo va en todos los mensajes; lo fijo se repite igual y el proveedor lo cobra más barato desde su caché. Es el
    # negocio de ejemplo con más estrategia avanzada (problemas, motivos, objeciones, reglas de cierre): cabe en unos 3.000 tokens.
    assert len(prompt) < 12_500
    # Un negocio con poca estrategia avanzada sigue con un prompt corto.
    small = load_tenant_runtime_yaml("restaurant", extra_yaml={"conversation_state": "active", "memory_context": {"last_ai_response": "ok"}})
    small_prompt, _, _ = PromptBuilderService().build(client_config_id="restaurant", user_message="siguiente", yaml_config=small, faq_results=[], progression_rules=None)
    # Las reglas fijas de pasar a una persona (prompt v4) suman unos 450 caracteres, iguales en cada mensaje y cobrados desde la caché.
    assert len(small_prompt) < 7_000


def test_panel_document_is_valid_and_reaches_the_engine():
    """El documento con el que se prueba el panel (`src/test/fixtures`) debe cumplir el contrato."""
    config = BusinessConfig.model_validate_json(PANEL_DOCUMENT.read_text(encoding="utf-8"))
    secrets = {}
    compiled = compile_business_config(config, lambda ref: secrets.setdefault(ref.secret_ref, f"valor-{len(secrets)}"))
    assert set(secrets) == {"secret_store:principal.link", "secret_store:principal.transfer.0.number"}
    block = _profile_text(compiled)
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
    assert f"{KNOWLEDGE_HEADER}\n- P: ¿Atienden los domingos?\n  R: Sí, de 9 a. m. a 1 p. m." in prompts[0]

    monkeypatch.undo()  # de vuelta al almacén de la suite, con los nueve negocios
    for slug in TENANTS:
        (plain_prompts, _), = run_conversation(slug, [("Hola, info", reply("Claro."))], user_id="sin-faq")
        assert KNOWLEDGE_HEADER not in plain_prompts[0]


@pytest.mark.parametrize("slug", CATALOG_TENANTS)
def test_catalog_prices_reach_the_prompt(monkeypatch, slug):
    config = _stored(slug)
    (prompts, _), = run_conversation(slug, [("¿Cuánto cuesta?", reply("Te cuento."))], user_id="catalogo")
    offer = prompts[0].split("LO QUE VENDE\n", 1)[1].split("\n\n", 1)[0]
    for item in config.offer.catalog.items:
        if item.available:
            assert f"- {item.name} — {item.prices[0].currency} {item.prices[0].amount:,}".replace(",", ".") in offer


# ---------------------------------------------------------------------------
# Evidencia de uso: al cambiar el campo en el contrato, cambia el prompt del motor actual
# ---------------------------------------------------------------------------

def _first_plan(document: dict) -> dict:
    return document["offer"]["plans"][0]


# Fase 3: todo lo que el panel deja configurar llega al motor. Cada caso cambia uno o varios campos y busca su texto en el prompt.
_WEEK = ["lunes", "martes", "miercoles", "jueves", "viernes"]
PHASE_3_CASES = {
    # «EL NEGOCIO»
    "posicionamiento": ("restaurant", lambda d: d["identity"].update(positioning="La hamburguesería del barrio"),
                        "Posicionamiento: La hamburguesería del barrio.", 0),
    "pruebas_de_confianza": ("restaurant", lambda d: d["identity"].update(credibility=["10 años en el barrio", "4,8 estrellas"]),
                             "Pruebas de confianza: 10 años en el barrio; 4,8 estrellas.", 0),
    "cliente_ideal": ("restaurant", lambda d: d["identity"].update(target_customer={
        "segment": "familias", "company_size": "de 2 a 5 personas", "maturity": "piden los fines de semana", "roles": ["mamá", "papá"]}),
        "Cliente ideal: familias (de 2 a 5 personas).\nCómo suele llegar: piden los fines de semana.\nQuién suele escribir o decidir: mamá, papá.", 0),
    "horario": ("restaurant", lambda d: d["identity"].update(opening_hours=[
        {"days": _WEEK, "opens": "11:00", "closes": "22:00"}, {"days": ["sabado", "domingo"], "opens": "12:00", "closes": "23:00"}]),
        "Horario de atención: lunes a viernes de 11:00 a 22:00; sábado y domingo de 12:00 a 23:00.", 0),
    "estilo": ("restaurant", lambda d: d["response_style"].update(voice="alegre y cercana", formality="formal", emojis=False, instructions=["Sin tecnicismos."]),
               "Personalidad de la marca: alegre y cercana.\nTrata al cliente de usted.\nNo uses emojis.\nCómo te expresas:\n- Sin tecnicismos.", 0),
    "estilo_tuteo": ("restaurant", lambda d: d["response_style"].update(formality="informal", emojis=True),
                     "Trata al cliente de tú.\nPuedes usar algún emoji, con moderación.", 0),
    # «LO QUE VENDE»
    "cobro_anual": ("saas", lambda d: _first_plan(d)["prices"][0].update(annual=999000), "COP 999.000 al año", 1),
    "para_quien": ("saas", lambda d: _first_plan(d).update(target="equipos de ventas"), "Para: equipos de ventas.", 1),
    "variantes": ("tienda_ropa", lambda d: d["inventory"]["items"][0]["variants"][0].update(
        attributes={"talla": "XL", "color": "verde"}, stock=0, prices=[{"currency": "COP", "amount": 50000}]),
        "talla XL, color verde (COP 50.000) (agotada)", 1),
    "producto_agotado": ("tienda_ropa", lambda d: [variant.update(stock=0) for variant in d["inventory"]["items"][1]["variants"]],
                         "(agotada). Agotado por ahora: no lo ofrezcas como disponible.", 1),
    "sin_control_de_existencias": ("tienda_ropa", lambda d: d["inventory"].update(track_stock=False), "talla M, color blanco;", 1),
    "aclaracion_del_precio": ("restaurant", lambda d: d["terms"].update(price_note="El domicilio se cobra aparte."),
                              "Sobre el precio: El domicilio se cobra aparte.", 0),
    "mezcla_de_oferta": ("restaurant", lambda d: d["sales"].update(offer_mix={"core": ["hamburguesas"], "upsell": ["papas grandes"], "cross_sell": ["malteada"]}),
                         "Lo principal que vende: hamburguesas.\nMejoras que puedes sugerir (solo si están en lo que vende): papas grandes.\n"
                         "Complementos que puedes sugerir con la compra (solo si están en lo que vende): malteada.", 0),
    "retorno_en_reservas": ("saas", lambda d: (d["terms"].pop("roi_break_even_sales", None), d["terms"].update(roi_break_even_bookings=4)),
                            "Argumento de valor: con 4 reservas el cliente recupera lo que paga.", 1),
    "un_solo_plan": ("demo", lambda d: d["features"].update(multi_plan=False),
                     "Recomienda un solo plan, el que mejor encaje con lo que necesita; no le muestres todos.", 1),
    "una_sola_moneda": ("demo", lambda d: d["features"].update(multi_currency=False), "COP 120.000 al mes:", 1),
    "sin_precios": ("restaurant", lambda d: d["features"].update(pricing_enabled=False), "Los precios los confirma el equipo: no des valores.", 0),
    # «CÓMO COMPRA Y RECIBE EL CLIENTE»
    "domicilio": ("restaurant", lambda d: d["fulfillment"].update(delivery={
        "available": True, "type": "tercero", "zones": ["centro"], "cost": {"type": "fijo", "value": 3500}, "time": {"min": "20 min", "max": "40 min"}}),
        "Domicilio con mensajería externa en centro: cuesta COP 3.500; tarda de 20 min a 40 min.", 0),
    "sin_domicilio": ("restaurant", lambda d: d["fulfillment"]["delivery"].update(available=False), "No hace domicilios.", 0),
    "envio": ("restaurant", lambda d: d["fulfillment"].update(shipping={
        "available": True, "scope": "nacional", "providers": ["Coordinadora"], "cost": {"type": "variable", "value": 8000},
        "time": {"min": "2 días", "max": "4 días"}}),
        "Envíos nacionales con Coordinadora: el costo depende del destino (desde COP 8.000); tarda de 2 días a 4 días.", 0),
    "recogida": ("restaurant", lambda d: d["fulfillment"].update(pickup={"available": True, "instructions": "Pasa por la caja 2"}),
                 "Recogida: Pasa por la caja 2.", 0),
    "agenda": ("restaurant", lambda d: d["fulfillment"].update(scheduling={"required": True}), "Este servicio requiere agendar una cita o reserva.", 0),
    "pasos_y_requisitos": ("restaurant", lambda d: d["sales"].update(solution={"process_steps": ["Elige tu combo", "Paga"], "requirements": ["Ser mayor de edad"]}),
                           "Pasos para comprar o recibir el servicio: 1) Elige tu combo; 2) Paga.\nRequisitos del cliente: Ser mayor de edad.", 0),
    # «CÓMO SE PAGA Y SE CIERRA»
    "financiacion": ("restaurant", lambda d: d["terms"].update(financing={"available": True, "providers": ["Addi"], "options": ["cuotas_sin_interes"]}),
                     "Ofrece financiación: con Addi; modalidades: cuotas sin interes.", 0),
    "datos_del_cierre": ("restaurant", lambda d: d["sales"]["closing"].update(required_data=["license_type", "email"]),
                         "Datos que pides para cerrar: nombre, teléfono, dirección, detalles, tipo de licencia, correo.", 0),
    "mensaje_para_pedir_datos": ("restaurant", lambda d: d["messages"].update(data_request="¿Me regalas tu nombre y dirección?"),
                                 "Para pedirle sus datos, usa este mensaje del negocio: «¿Me regalas tu nombre y dirección?»", 0),
    "mensaje_al_pasar_a_una_persona": ("tienda_ropa", lambda d: d["messages"].update(human_handoff="Ya te comunico con Laura."),
                                       "Si lo pasas con una persona del equipo, usa este mensaje del negocio: «Ya te comunico con Laura.»", 0),
    "restricciones": ("restaurant", lambda d: d["capabilities"].update(restrictions={"disallowed_channels": ["tiktok"], "disallowed_actions": ["envios_internacionales"]}),
                      "Canales por los que el negocio no atiende: tiktok.\nEl negocio no hace: envios internacionales.", 0),
    # «POLÍTICAS DEL NEGOCIO»
    "politicas": ("restaurant", lambda d: d["terms"].update(policies={"warranty": "Si llega frío, lo cambiamos", "returns": "No hay devoluciones",
                                                                       "cancellation": "Puedes cancelar antes de que salga"}),
                  "Garantía: Si llega frío, lo cambiamos.\nCambios y devoluciones: No hay devoluciones.\nCancelaciones y reembolsos: Puedes cancelar antes de que salga.", 0),
    # «EL CLIENTE: QUÉ LO MUEVE Y QUÉ LO FRENA»
    "problemas_en_sus_palabras": ("restaurant", lambda d: d["sales"].update(pain_points=["no sé qué pedir"]), "Así describe sus problemas: no sé qué pedir.", 0),
    "detalle_de_problemas": ("restaurant", lambda d: d["sales"].update(customer_problems=[{
        "id": "hambre_rapida", "impacts": ["llega tarde al trabajo"], "signals": ["tengo afán"], "monetization": ["pierde la hora de almuerzo"],
        "urgency_levels": {"alto": ["te lo llevamos ya"]}, "recommended_angles": ["tiempo"], "solutions": ["combo_express"]}]),
        "- hambre rapida: lo notas si dice «tengo afán»; le pasa esto: llega tarde al trabajo; le cuesta: pierde la hora de almuerzo; "
        "se resuelve con: combo express; si es urgente: «te lo llevamos ya»; háblale desde: tiempo.", 0),
    "casos_de_uso": ("restaurant", lambda d: d["sales"].update(use_cases=[{"name": "almuerzo de oficina", "signals": ["somos 10"], "approach": "combo_familiar"}]),
                     "- almuerzo de oficina: si dice «somos 10», enfócate en combo familiar.", 0),
    "motivos_de_compra": ("restaurant", lambda d: d["sales"].update(motivations=[{
        "motivation": "antojo", "description": "darse un gusto", "signals": ["se me antojó"], "angle": {"signals": ["algo rico"], "messages": ["date el gusto hoy"]}}]),
        "- antojo: darse un gusto; lo notas si dice «se me antojó», «algo rico»; cómo hablarle: «date el gusto hoy».", 0),
    "objeciones": ("restaurant", lambda d: d["sales"].update(objections=[{
        "topic": "price", "acknowledge": ["Te entiendo."], "reframe": ["Es carne artesanal."], "proof": ["4,8 estrellas"], "redirect": ["¿Te la preparo?"],
        "rules": ["No ofrezcas descuentos."]}]),
        "Si duda por el precio (ideas del negocio; dilas con tus palabras):\n- Reconócelo: «Te entiendo.»\n- Replantéalo: «Es carne artesanal.»\n"
        "- Da una prueba: «4,8 estrellas»\n- Vuelve al siguiente paso: «¿Te la preparo?»\n- Regla: No ofrezcas descuentos.", 0),
    # «ESTRATEGIA DE VENTA DEL NEGOCIO»
    "orden_de_la_conversacion": ("restaurant", lambda d: d["sales"].update(conversation_flow={
        "steps": ["detect_pain", "present_solution", "paso_propio"], "required_flow": ["detect_pain", "guide_next_step"], "forbid": ["responder_sin_solucion"],
        "no_skip_steps": True, "guided_process": True}),
        "Orden de la conversación: entender qué necesita → presentarle la opción que lo resuelve → paso propio. No te saltes pasos.\n"
        "Pasos que no pueden faltar: entender qué necesita → guiarlo al siguiente paso.\nGuíalo paso a paso por el proceso.\n"
        "No hagas esto: responder sin ofrecer una solución.", 0),
    "atencion": ("restaurant", lambda d: d["sales"].update(support={"explain_first": False, "sell_after": True, "rules": ["Nunca discutas."]},
                                                            qualification={"detect_offer_fit": True}),
                 "Si pide información, responde breve y conéctala con lo que necesita para avanzar.\nDespués de aclarar su duda, invítalo a avanzar.\n"
                 "Antes de llevarlo a comprar, confirma que la opción le sirve para lo que necesita.\nReglas de atención del negocio:\n- Nunca discutas.", 0),
    "averiguar_y_presentar": ("restaurant", lambda d: d["sales"].update(discovery={"objectives": ["para cuántas personas es"]},
                                                                         offer_presentation={"single_offer": ["muéstrale el combo"], "multiple_offers": ["compara dos opciones"]}),
                              "Lo que debes averiguar del cliente: para cuántas personas es.\nSi hay una sola opción para él: muéstrale el combo.\n"
                              "Si hay varias opciones: compara dos opciones.", 0),
    "cierre": ("restaurant", lambda d: d["sales"].update(closing={
        "strategy": "direct_sale", "purchase_signals": ["me lo llevo"], "high_intent_actions": ["confirmar el pedido"], "next_steps": ["preparar el pedido"],
        "micro_commitments": ["¿te lo dejo listo?"], "rules": ["No frenes un pedido."]}),
        "Señales de que quiere comprar: «me lo llevo».\nSi muestra mucha intención de compra: confirmar el pedido.\n"
        "Siguientes pasos de la venta (guía al cliente hacia ellos; no digas que ya están hechos): preparar el pedido.\n"
        "Compromisos pequeños para avanzar: ¿te lo dejo listo?\nReglas de cierre del negocio:\n- No frenes un pedido.", 0),
    "estrategia_de_cierre": ("restaurant", lambda d: d["sales"]["closing"].update(strategy="booking"), "CÓMO SE VENDE EN ESTE NEGOCIO (servicios con cita)", 0),
}

CONNECTED_CASES = {
    # caso: (negocio, cambio en el documento, texto esperado en el prompt, turno)
    "sector": ("saas", lambda d: d["identity"].update(industry="software contable para tiendas"), "— software contable para tiendas.", 0),
    "promesa": ("saas", lambda d: d["identity"].update(value_proposition="Cuadra tu caja en minutos"), "Promesa: Cuadra tu caja en minutos.", 0),
    "motivos": ("saas", lambda d: d["sales"].update(buying_motivation={"primary": "ahorro", "secondary": "control"}),
                "Por qué le compran: ahorro y control.", 0),
    "impactos": ("saas", lambda d: d["sales"].update(customer_problems=[{"id": "caja", "impacts": ["la caja no cuadra al cierre"]}]),
                 "Problemas que resuelve: la caja no cuadra al cierre.", 0),
    "casos_de_uso": ("saas", lambda d: (d["sales"].pop("customer_problems", None), d["sales"].update(
        use_cases=[{"name": "cierre de caja", "signals": ["no cuadra"], "approach": "conciliar"}])), "Problemas que resuelve: cierre de caja.", 0),
    "incluye": ("saas", lambda d: _first_plan(d).update(includes=["soporte 24/7"]), "Incluye: soporte 24/7.", 1),
    "no_incluye": ("saas", lambda d: _first_plan(d).update(not_included=["hardware"]), "No incluye: hardware.", 1),
    "primer_pago": ("saas", lambda d: _first_plan(d)["prices"][0].update(first_payment=77777), "primer pago de COP 77.777", 1),
    "precio_unico": ("saas", lambda d: _first_plan(d)["prices"][0].update(price=55555), "COP 55.555", 1),
    "categorias": ("restaurant", lambda d: d["offer"]["catalog"]["categories"][0].update(name="Combos"), "Categorías: Combos", 0),
    "condiciones": ("saas", lambda d: d["terms"].update(conditions=["pago anticipado"]), "Condiciones: pago anticipado.", 1),
    "encuadre_precio": ("saas", lambda d: d["terms"].update(price_framing="directo"), "Si duda por el precio, dile con claridad cuánto cuesta y qué recibe, sin rodeos.", 1),
    "retorno": ("saas", lambda d: d["terms"].update(roi_break_even_sales=7), "Argumento de valor: con 7 ventas al mes el cliente recupera lo que paga.", 1),
    "argumento_retorno": ("saas", lambda d: (d["terms"].pop("roi_break_even_sales", None), d["terms"].update(roi_hints=["una venta paga el mes"])),
                          "Argumento de valor: una venta paga el mes.", 1),
    "acciones": ("saas", lambda d: d["capabilities"].update(actions_primary=["cerrar_venta"], actions_support=["seguimiento"]),
                 "Puedes ayudarle a: cerrar venta, seguimiento.", 0),
    "datos_propios_del_negocio": ("saas", lambda d: d["capabilities"]["data_collection"].update(fields=["cedula_de_prueba"]),
                                  "Datos que pides para cerrar: cedula de prueba.", 0),
    "canales": ("saas", lambda d: d["capabilities"].update(service_channels=["whatsapp", "instagram"]),
                "Atiendes por: whatsapp, instagram.", 0),
    "canales_producto": ("saas", lambda d: d["capabilities"].update(product_channels=["telegram"]), "Lo que vende funciona en: telegram.", 0),
    "que_vendes_servicios": ("restaurant", lambda d: d["features"].update(business_model="services"),
                             "CÓMO SE VENDE EN ESTE NEGOCIO (servicios)", 0),
    "tono": ("restaurant", lambda d: d["response_style"].update(tone="paciente y muy claro"), "Tono: paciente y muy claro.", 1),
    "descripcion_plan": ("saas", lambda d: _first_plan(d).update(name="Plan Caja", description="Incluye soporte por chat"),
                         "- Plan Caja — ", 0),
    **{f"fase3_{name}": case for name, case in PHASE_3_CASES.items()},
}


@pytest.mark.parametrize("case", CONNECTED_CASES)
def test_connected_fields_change_the_prompt(monkeypatch, tmp_path, case):
    slug, mutate, expected, turn = CONNECTED_CASES[case]
    before = run_with_document(monkeypatch, tmp_path / "antes", slug, lambda d: None, TWO_TURNS)
    after = run_with_document(monkeypatch, tmp_path / "despues", slug, mutate, TWO_TURNS)
    assert expected not in before[turn][0][0]
    assert expected in after[turn][0][0]


def test_the_after_sale_message_reaches_the_ai_once_the_customer_paid(monkeypatch, tmp_path):
    turns = [("Ya pagué", reply("Gracias, lo reviso.", "buy", payment_status="reportado")), ("¿Cuándo me llega?", reply("Pronto."))]
    message = "Gracias por tu compra, te avisamos cuando salga."
    (_, _), (prompts, _) = run_with_document(monkeypatch, tmp_path, "saas", lambda d: d["messages"].update(after_sale=message), turns)
    assert f"«{message}»" in prompts[0]
    (_, _), (without, _) = run_with_document(monkeypatch, tmp_path / "sin", "saas", lambda d: None, turns)
    assert "Después de la compra, el negocio quiere decirle" not in without[0]


def test_what_only_the_team_sees_or_the_platform_sends_later_never_reaches_the_ai(monkeypatch, tmp_path):
    """La etiqueta de una cuenta y el código de una variante son del equipo; el pago confirmado y el seguimiento los enviará la plataforma."""
    def _team_only(document):
        document["payments"][0]["transfer_methods"][0]["label"] = "Cuenta de Laura"
        document["inventory"]["items"][0]["variants"][0]["sku"] = "CODIGO-INTERNO-9"
        document["messages"].update(payment_confirmed="Pago confirmado, gracias.", follow_up="¿Seguimos con tu pedido?")

    before = run_with_document(monkeypatch, tmp_path / "antes", "tienda_ropa", lambda d: None, TWO_TURNS)
    after = run_with_document(monkeypatch, tmp_path / "despues", "tienda_ropa", _team_only, TWO_TURNS)
    assert [prompts for prompts, _ in after] == [prompts for prompts, _ in before]
    assert not any(text in prompt for prompts, _ in after for prompt in prompts for text in ("Laura", "CODIGO-INTERNO-9", "¿Seguimos con tu pedido?"))


# Campo del contrato marcado `conectado` → prueba de este archivo que demuestra que el motor actual lo usa.
CONNECTED_EVIDENCE: dict[str, str] = {
    "schema_version": "test_a_corrupt_published_document_is_never_served",
    "tenant_slug": "test_a_corrupt_published_document_is_never_served",
    "messages.fallback": "test_the_fallback_message_is_the_one_written_in_the_panel",
    "identity.industry": "test_the_assistant_uses_the_whole_text_up_to_the_contract_limit",
    "identity.value_proposition": "test_the_assistant_uses_the_whole_text_up_to_the_contract_limit",
    "offer.model": "test_tenants_stay_isolated",
    "offer.plans[].id": "test_payment_methods_reach_the_customer",
    "offer.plans[].name": "test_plan_prices_are_said_like_a_salesperson_would",
    "offer.plans[].prices[].currency": "test_plan_prices_are_said_like_a_salesperson_would",
    "offer.plans[].prices[].implementation": "test_plan_prices_are_said_like_a_salesperson_would",
    "offer.plans[].prices[].monthly": "test_plan_prices_are_said_like_a_salesperson_would",
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
    "response_style.length": "test_each_response_length_option_controls_prompt_and_truncation",
    "response_style.max_words": "test_changing_the_contract_changes_response_length",
    "features.business_model": "test_connected_fields_change_the_prompt",
    # Perfil comercial, tono, preguntas frecuentes y precios del catálogo: solo con el contrato.
    "identity.name": "test_the_profile_block_reaches_the_prompt",
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
    # Fase 3: estilo, horarios, cliente ideal, entrega, inventario, políticas, financiación, mensajes y estrategia avanzada.
    "capabilities.restrictions.disallowed_actions": "test_connected_fields_change_the_prompt",
    "capabilities.restrictions.disallowed_channels": "test_connected_fields_change_the_prompt",
    "features.multi_currency": "test_connected_fields_change_the_prompt",
    "features.multi_plan": "test_connected_fields_change_the_prompt",
    "features.pricing_enabled": "test_connected_fields_change_the_prompt",
    "fulfillment.delivery.available": "test_connected_fields_change_the_prompt",
    "fulfillment.delivery.cost.type": "test_connected_fields_change_the_prompt",
    "fulfillment.delivery.cost.value": "test_connected_fields_change_the_prompt",
    "fulfillment.delivery.time.max": "test_connected_fields_change_the_prompt",
    "fulfillment.delivery.time.min": "test_connected_fields_change_the_prompt",
    "fulfillment.delivery.type": "test_connected_fields_change_the_prompt",
    "fulfillment.delivery.zones": "test_connected_fields_change_the_prompt",
    "fulfillment.pickup.available": "test_connected_fields_change_the_prompt",
    "fulfillment.pickup.instructions": "test_connected_fields_change_the_prompt",
    "fulfillment.scheduling.required": "test_connected_fields_change_the_prompt",
    "fulfillment.shipping.available": "test_connected_fields_change_the_prompt",
    "fulfillment.shipping.cost.type": "test_connected_fields_change_the_prompt",
    "fulfillment.shipping.cost.value": "test_connected_fields_change_the_prompt",
    "fulfillment.shipping.providers": "test_connected_fields_change_the_prompt",
    "fulfillment.shipping.scope": "test_connected_fields_change_the_prompt",
    "fulfillment.shipping.time.max": "test_connected_fields_change_the_prompt",
    "fulfillment.shipping.time.min": "test_connected_fields_change_the_prompt",
    "identity.credibility": "test_connected_fields_change_the_prompt",
    "identity.opening_hours[].closes": "test_connected_fields_change_the_prompt",
    "identity.opening_hours[].days": "test_connected_fields_change_the_prompt",
    "identity.opening_hours[].opens": "test_connected_fields_change_the_prompt",
    "identity.positioning": "test_connected_fields_change_the_prompt",
    "identity.target_customer.company_size": "test_connected_fields_change_the_prompt",
    "identity.target_customer.maturity": "test_connected_fields_change_the_prompt",
    "identity.target_customer.roles": "test_connected_fields_change_the_prompt",
    "identity.target_customer.segment": "test_connected_fields_change_the_prompt",
    "inventory.items[].product_id": "test_connected_fields_change_the_prompt",
    "inventory.items[].variants[].attributes": "test_connected_fields_change_the_prompt",
    "inventory.items[].variants[].prices[].amount": "test_connected_fields_change_the_prompt",
    "inventory.items[].variants[].prices[].currency": "test_connected_fields_change_the_prompt",
    "inventory.items[].variants[].stock": "test_connected_fields_change_the_prompt",
    "inventory.track_stock": "test_connected_fields_change_the_prompt",
    "messages.data_request": "test_connected_fields_change_the_prompt",
    "messages.human_handoff": "test_connected_fields_change_the_prompt",
    "offer.plans[].prices[].annual": "test_connected_fields_change_the_prompt",
    "offer.plans[].target": "test_connected_fields_change_the_prompt",
    "response_style.emojis": "test_connected_fields_change_the_prompt",
    "response_style.formality": "test_connected_fields_change_the_prompt",
    "response_style.instructions": "test_connected_fields_change_the_prompt",
    "response_style.voice": "test_connected_fields_change_the_prompt",
    "sales.closing.high_intent_actions": "test_connected_fields_change_the_prompt",
    "sales.closing.micro_commitments": "test_connected_fields_change_the_prompt",
    "sales.closing.next_steps": "test_connected_fields_change_the_prompt",
    "sales.closing.purchase_signals": "test_connected_fields_change_the_prompt",
    "sales.closing.required_data": "test_connected_fields_change_the_prompt",
    "sales.closing.rules": "test_connected_fields_change_the_prompt",
    "sales.closing.strategy": "test_connected_fields_change_the_prompt",
    "sales.conversation_flow.forbid": "test_connected_fields_change_the_prompt",
    "sales.conversation_flow.guided_process": "test_connected_fields_change_the_prompt",
    "sales.conversation_flow.no_skip_steps": "test_connected_fields_change_the_prompt",
    "sales.conversation_flow.required_flow": "test_connected_fields_change_the_prompt",
    "sales.conversation_flow.steps": "test_connected_fields_change_the_prompt",
    "sales.customer_problems[].monetization": "test_connected_fields_change_the_prompt",
    "sales.customer_problems[].recommended_angles": "test_connected_fields_change_the_prompt",
    "sales.customer_problems[].signals": "test_connected_fields_change_the_prompt",
    "sales.customer_problems[].solutions": "test_connected_fields_change_the_prompt",
    "sales.customer_problems[].urgency_levels": "test_connected_fields_change_the_prompt",
    "sales.discovery.objectives": "test_connected_fields_change_the_prompt",
    "sales.motivations[].angle.messages": "test_connected_fields_change_the_prompt",
    "sales.motivations[].angle.signals": "test_connected_fields_change_the_prompt",
    "sales.motivations[].description": "test_connected_fields_change_the_prompt",
    "sales.motivations[].motivation": "test_connected_fields_change_the_prompt",
    "sales.motivations[].signals": "test_connected_fields_change_the_prompt",
    "sales.objections[].acknowledge": "test_connected_fields_change_the_prompt",
    "sales.objections[].proof": "test_connected_fields_change_the_prompt",
    "sales.objections[].redirect": "test_connected_fields_change_the_prompt",
    "sales.objections[].reframe": "test_connected_fields_change_the_prompt",
    "sales.objections[].rules": "test_connected_fields_change_the_prompt",
    "sales.objections[].topic": "test_connected_fields_change_the_prompt",
    "sales.offer_mix.core": "test_connected_fields_change_the_prompt",
    "sales.offer_mix.cross_sell": "test_connected_fields_change_the_prompt",
    "sales.offer_mix.upsell": "test_connected_fields_change_the_prompt",
    "sales.offer_presentation.multiple_offers": "test_connected_fields_change_the_prompt",
    "sales.offer_presentation.single_offer": "test_connected_fields_change_the_prompt",
    "sales.pain_points": "test_connected_fields_change_the_prompt",
    "sales.qualification.detect_offer_fit": "test_connected_fields_change_the_prompt",
    "sales.solution.process_steps": "test_connected_fields_change_the_prompt",
    "sales.solution.requirements": "test_connected_fields_change_the_prompt",
    "sales.support.explain_first": "test_connected_fields_change_the_prompt",
    "sales.support.rules": "test_connected_fields_change_the_prompt",
    "sales.support.sell_after": "test_connected_fields_change_the_prompt",
    "sales.use_cases[].approach": "test_connected_fields_change_the_prompt",
    "sales.use_cases[].signals": "test_connected_fields_change_the_prompt",
    "terms.financing.available": "test_connected_fields_change_the_prompt",
    "terms.financing.options": "test_connected_fields_change_the_prompt",
    "terms.financing.providers": "test_connected_fields_change_the_prompt",
    "terms.policies.cancellation": "test_connected_fields_change_the_prompt",
    "terms.policies.returns": "test_connected_fields_change_the_prompt",
    "terms.policies.warranty": "test_connected_fields_change_the_prompt",
    "terms.price_note": "test_connected_fields_change_the_prompt",
    "terms.roi_break_even_bookings": "test_connected_fields_change_the_prompt",
    "messages.after_sale": "test_the_after_sale_message_reaches_the_ai_once_the_customer_paid",
    "messages.after_hours": "test_the_attention_messages_reach_the_platform_from_what_was_published",
    "messages.ai_resumed": "test_the_attention_messages_reach_the_platform_from_what_was_published",
}


def test_every_connected_field_has_evidence_in_this_file():
    fields = contract_fields(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    connected = {path for path, field in fields.items() if field.engine == "conectado"}
    assert sorted(connected - set(CONNECTED_EVIDENCE)) == [], "campos marcados conectados sin prueba de uso"
    assert sorted(set(CONNECTED_EVIDENCE) - connected) == [], "pruebas de uso para campos no marcados conectados"
    tests = {name for name, value in globals().items() if name.startswith("test_") and callable(value)}
    assert sorted(set(CONNECTED_EVIDENCE.values()) - tests) == []
