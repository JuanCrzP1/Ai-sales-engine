"""Arquitectura del prompt: bloques pequeños, instrucciones fijas en un solo lugar, un presupuesto por bloque y un catálogo grande que
no infla cada mensaje. También la identidad del negocio en todos los mensajes (antes se perdía desde el segundo)."""
from __future__ import annotations

import copy
from pathlib import Path

import pytest

from app.application.runtime import load_tenant_runtime_yaml, runtime_from_sections
from app.domain.business_config import engine_policy as policy
from app.domain.business_config.compiler import compile_business_config
from app.domain.business_config.contract import BusinessConfig
from app.domain.business_config.engine_settings import EngineSettings
from app.domain.memory.contracts import CommercialMemorySignal
from app.infrastructure.ai.prompting import budgets, composer
from app.infrastructure.ai.prompting.sections.profile import business_profile
from app.infrastructure.ai.prompting.view import PromptView
from pipeline_harness import TENANTS, prepared_tenant, stored_document

PROMPTING = Path(__file__).resolve().parents[1] / "project" / "app" / "infrastructure" / "ai" / "prompting"
MAX_MODULE_LINES = 220

STATES = {
    "presentacion": {"conversation_state": "new"},
    "en_curso": {"conversation_state": "active", "memory_context": {"last_intent": "info", "last_pain": "no alcanzo", "last_ai_response": "Claro, te cuento."}},
    "pago": {"conversation_state": "active", "memory_context": {"metodo_pago_elegido": "nequi", "estado_pago": "pendiente", "last_ai_response": "Te paso los datos."}},
    "memoria_fuerte": {"conversation_state": "active", "memory_context": {"last_ai_response": "ok"}},
}


def _view(slug: str, state: str, message: str = "¿Cuánto cuesta?") -> PromptView:
    runtime = load_tenant_runtime_yaml(slug, channel="whatsapp", extra_yaml=copy.deepcopy(STATES[state]))
    runtime["tenant_slug"] = slug
    if state == "memoria_fuerte":
        runtime["commercial_memory_signal"] = CommercialMemorySignal(continuity_brief="Ya eligió.", episodic_hook="Tiene 3 sedes.", context_weight="strong")
    return PromptView(runtime, message)


def _sizes(view: PromptView) -> dict[str, int]:
    return composer._sizes(composer.render_sections(view))


# ---------------------------------------------------------------------------
# Módulos pequeños e instrucciones en un solo lugar
# ---------------------------------------------------------------------------

def test_no_prompt_module_is_a_mega_file():
    sizes = {str(path.relative_to(PROMPTING)): len(path.read_text(encoding="utf-8").splitlines()) for path in PROMPTING.rglob("*.py")}
    assert {name: lines for name, lines in sizes.items() if lines > MAX_MODULE_LINES} == {}


def test_the_fixed_instructions_live_in_one_place():
    """Cambiar cómo vende el asistente es editar `instructions.py`, no buscar textos dentro del código."""
    markers = ("REGLA CRÍTICA", "MODO DE RESPUESTA", "COMPORTAMIENTO CON MEMORIA", "POST-PAGO:", "Flujo: dolor")
    engine = PROMPTING.parents[2]
    offenders = sorted(
        f"{path.relative_to(engine)}: {marker}"
        for path in engine.rglob("*.py")
        if path.name != "instructions.py"
        for marker in markers
        if marker in path.read_text(encoding="utf-8")
    )
    assert offenders == []


# ---------------------------------------------------------------------------
# Presupuesto por bloque
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("slug", TENANTS)
def test_every_block_of_the_nine_businesses_fits_its_budget(slug, state):
    view = _view(slug, state)
    assert budgets.over_budget(_sizes(view)) == {}
    assert len(composer.compose(view)) <= budgets.TOTAL_BUDGET


def test_an_over_budget_block_is_reported_and_never_cut(monkeypatch):
    warnings: list[tuple[str, dict]] = []
    monkeypatch.setattr(composer.logger, "warning", lambda event, extra=None: warnings.append((event, extra or {})))
    monkeypatch.setitem(budgets.SECTION_BUDGETS, "pricing", 10)
    view = _view("saas", "en_curso")
    prompt = composer.compose(view)
    assert ("prompt_section_over_budget", {"tenant": "saas", "section": "pricing", "chars": _sizes(view)["pricing"], "budget": 10}) in warnings
    assert "Precios: " in prompt and "TRANSFER_METHODS:" in prompt


# ---------------------------------------------------------------------------
# Un catálogo grande no infla el prompt
# ---------------------------------------------------------------------------

def _large_business(products: int) -> dict:
    """La hamburguesería de ejemplo con todo al máximo del contrato y `products` productos."""
    document = stored_document("restaurant")
    items = 10
    text = lambda label, index: f"{label} {index} " + "x " * ((policy.MAX_PROFILE_ITEM_CHARS - 20) // 2)  # noqa: E731
    document["identity"].update(differentiators=[text("dif", i) for i in range(policy.MAX_PROFILE_ITEMS)])
    document["sales"].update(**{key: [text(key, i) for i in range(policy.MAX_PROFILE_ITEMS)] for key in ("benefits", "arguments", "instructions")})
    document["terms"]["promotions"] = [{"name": f"Promo {i}", "details": text("detalle", i), "valid_until": "2999-12-31"} for i in range(policy.MAX_PROMOTIONS)]
    categories = [{"id": f"cat_{i}", "name": f"Categoría {i}"} for i in range(policy.MAX_CATEGORIES)]
    template = document["offer"]["catalog"]["items"][0]
    document["offer"]["catalog"].update(
        categories=categories,
        items=[
            {**copy.deepcopy(template), "id": f"producto_{i}", "name": f"Producto número {i}", "category": categories[i % items]["id"],
             "description": f"Descripción del producto {i} " + "detalle " * 30, "features": [f"característica {j}" for j in range(5)]}
            for i in range(products)
        ],
    )
    return document


def _large_view(products: int, message: str) -> PromptView:
    tenant = prepared_tenant("restaurant")
    config = BusinessConfig.model_validate(_large_business(products)).with_engine_settings(EngineSettings.model_validate(tenant.engine_settings))
    runtime = runtime_from_sections("restaurant", compile_business_config(config, lambda ref: tenant.payment_values[ref.secret_ref]), channel="whatsapp")
    runtime.update(conversation_state="new", tenant_slug="restaurant")
    return PromptView(runtime, message)


def test_a_large_catalog_does_not_inflate_the_prompt():
    small, large = (_large_view(products, "¿Qué tienen?") for products in (20, 300))
    assert budgets.over_budget(_sizes(large)) == {}
    assert len(composer.compose(large)) <= budgets.TOTAL_BUDGET
    # Quince veces más productos casi no cambian el tamaño del mensaje.
    assert len(composer.compose(large)) - len(composer.compose(small)) < 1_500


def test_the_product_the_customer_asks_for_reaches_the_prompt():
    blocks = composer.render_sections(_large_view(300, "¿Tienen el producto número 250?"))
    assert "- Producto número 250: Descripción del producto 250" in blocks["profile"]
    assert "Producto número 250 -> COP:" in blocks["pricing"]
    assert "opciones más que no aparecen aquí" in blocks["profile"]
    assert " más." in blocks["pricing"].split("Precios: ", 1)[1].split("\n", 1)[0]


def test_a_business_whose_catalog_fits_receives_it_whole():
    view = _view("restaurant", "presentacion", "¿Qué tienen?")
    blocks = composer.render_sections(view)
    items = view.pricing["catalog"]["items"]
    assert "opciones más" not in blocks["profile"]
    assert all(f"- {item['name']}:" in blocks["profile"] for item in items if item.get("description"))


# ---------------------------------------------------------------------------
# La identidad del negocio en todos los mensajes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("slug", TENANTS)
def test_the_business_identity_is_in_every_message(slug):
    """Antes, desde el segundo mensaje «CONTEXTO DEL NEGOCIO» iba vacío: el asistente ya no sabía para quién vendía."""
    for state in ("en_curso", "pago", "memoria_fuerte"):
        view = _view(slug, state)
        name = business_profile(view.runtime)["name"]
        context = composer.compose(view).split("REGLAS OPERATIVAS:", 1)[0]
        assert f"Negocio: {name}." in context, state
        assert "Industria del negocio: " in context, state
    presentation = composer.compose(_view(slug, "presentacion"))
    assert f"Negocio: {business_profile(_view(slug, 'presentacion').runtime)['name']}" in presentation
