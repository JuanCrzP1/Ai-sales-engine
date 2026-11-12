"""Arquitectura del prompt: capas ordenadas de lo fijo a lo cambiante, bloques pequeños, instrucciones fijas en un solo lugar,
presupuesto por capa, un catálogo grande que no infla cada mensaje y la conversación como mensajes, sin datos de pago."""
from __future__ import annotations

import copy
from pathlib import Path

import pytest

from app.application.runtime import load_tenant_runtime_yaml, runtime_from_sections
from app.domain.business_config import engine_policy as policy
from app.domain.business_config.compiler import compile_business_config
from app.domain.business_config.contract import BusinessConfig
from app.domain.business_config.engine_settings import EngineSettings
from app.domain.business_config.payment_data import REDACTED_PAYMENT_VALUE, payment_values
from app.domain.memory.contracts import CommercialMemorySignal
from app.infrastructure.ai.prompting import budgets, composer, instructions
from app.infrastructure.ai.prompting.history import recent_messages
from app.infrastructure.ai.prompting.sections import playbook
from app.infrastructure.ai.prompting.view import PromptView
from app.services.ai.output_contract import OUTPUT_CONTRACT
from pipeline_harness import TENANTS, prepared_tenant, stored_document

PROMPTING = Path(__file__).resolve().parents[1] / "project" / "app" / "infrastructure" / "ai" / "prompting"
MAX_MODULE_LINES = 200
LAYERS = ("platform", "playbook", "business", "offer", "delivery", "payments", "policies", "guidance", "customer", "strategy", "knowledge", "conversation")

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
    return {name: len(text) for name, text in composer.render_sections(view).items()}


# ---------------------------------------------------------------------------
# Módulos pequeños, instrucciones en un solo lugar y capas en orden
# ---------------------------------------------------------------------------

def test_no_prompt_module_is_a_mega_file():
    sizes = {str(path.relative_to(PROMPTING)): len(path.read_text(encoding="utf-8").splitlines()) for path in PROMPTING.rglob("*.py")}
    assert {name: lines for name, lines in sizes.items() if lines > MAX_MODULE_LINES} == {}


def test_the_fixed_instructions_live_in_one_place():
    """Cambiar cómo vende el asistente es editar `instructions.py`, no buscar textos dentro del código."""
    markers = ("LA VERDAD PRIMERO", "CÓMO RESPONDES", "CÓMO SE VENDE EN ESTE NEGOCIO", "Nunca escribas números de cuenta")
    engine = PROMPTING.parents[2]
    offenders = sorted(
        f"{path.relative_to(engine)}: {marker}"
        for path in engine.rglob("*.py")
        if path.name != "instructions.py"
        for marker in markers
        if marker in path.read_text(encoding="utf-8")
    )
    assert offenders == []


@pytest.mark.parametrize("slug", TENANTS)
def test_the_layers_go_from_the_fixed_to_the_changing(slug):
    """Lo igual para todos va primero (el proveedor lo reutiliza de su caché); lo de este mensaje, al final."""
    views = [_view(slug, state) for state in STATES]
    prompts = [composer.compose(view) for view in views]
    assert all(prompt.startswith(f"{instructions.PLATFORM}\n\n{OUTPUT_CONTRACT}\n\n") for prompt in prompts)
    assert list(composer.render_sections(views[0])) == list(LAYERS)
    # Todo lo que va antes de «ESTA CONVERSACIÓN» es igual en todos los mensajes del mismo negocio.
    prefixes = {prompt.split(instructions.CONVERSATION_HEADER, 1)[0] for prompt in prompts}
    assert len(prefixes) == 1
    assert prompts[0].rsplit("\n\n", 1)[1].startswith(instructions.CONVERSATION_HEADER)


def test_each_kind_of_business_gets_its_own_playbook():
    kinds = {slug: playbook.business_kind(_view(slug, "presentacion")) for slug in TENANTS}
    assert kinds["restaurant"] == "catalog" and kinds["tienda_ropa"] == "catalog"
    assert kinds["asesor_ai_prod"] == "plans" and kinds["saas"] == "plans"
    assert set(kinds.values()) <= set(instructions.PLAYBOOKS)


def test_a_booking_business_gets_the_booking_playbook():
    runtime = load_tenant_runtime_yaml("clinic")
    runtime["sales"] = {**runtime["sales"], "closing": {**(runtime["sales"].get("closing") or {}), "strategy": "booking"}}
    assert playbook.business_kind(PromptView(runtime)) == "booking"


def _with_closing(slug: str, strategy: str | None) -> PromptView:
    runtime = load_tenant_runtime_yaml(slug)
    closing = {k: v for k, v in (runtime["sales"].get("closing") or {}).items() if k != "strategy"}
    if strategy is not None:
        closing["strategy"] = strategy
    runtime["sales"] = {**runtime["sales"], "closing": closing}
    return PromptView(runtime)


@pytest.mark.parametrize("slug", ["restaurant", "saas", "tienda_ropa"])
def test_each_closing_strategy_tells_the_ai_how_to_close(slug):
    """Confirmar la compra, enviar el pago y capturar datos cierran distinto en el mismo negocio; agendar usa el manual con cita."""
    closings = {strategy: playbook.render(_with_closing(slug, strategy)) for strategy in ("direct_sale", "checkout", "lead_capture", "booking")}
    assert len(set(closings.values())) == 4
    for strategy in ("direct_sale", "checkout", "lead_capture"):
        assert closings[strategy].endswith(instructions.CLOSING_STRATEGIES[strategy].strip())
    assert "confirma con él lo que decidió" in closings["direct_sale"]
    assert "directo al pago" in closings["checkout"]
    assert "No le pidas que pague" in closings["lead_capture"] and "llévalo a pagar" not in closings["lead_capture"]
    assert closings["booking"] == f"{instructions.PLAYBOOKS['booking'].strip()}\n{instructions.PLAYBOOK_CLOSINGS['booking'].strip()}"


def test_without_a_closing_strategy_the_business_type_decides_how_to_close():
    view = _with_closing("restaurant", None)
    assert playbook.render(view).endswith(instructions.PLAYBOOK_CLOSINGS["catalog"])


def test_every_closing_strategy_of_the_contract_has_its_closing():
    from typing import get_args

    from app.domain.business_config.contract.sales import ClosingStrategy

    assert set(get_args(ClosingStrategy)) == {*instructions.CLOSING_STRATEGIES, "booking"}


# ---------------------------------------------------------------------------
# Presupuesto por capa
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("slug", TENANTS)
def test_every_layer_of_the_nine_businesses_fits_its_budget(slug, state):
    view = _view(slug, state)
    assert budgets.over_budget(_sizes(view)) == {}
    assert len(composer.compose(view)) <= budgets.TOTAL_BUDGET


def test_an_over_budget_layer_is_reported_and_never_cut(monkeypatch):
    warnings: list[tuple[str, dict]] = []
    monkeypatch.setattr(composer.logger, "warning", lambda event, extra=None: warnings.append((event, extra or {})))
    monkeypatch.setitem(budgets.SECTION_BUDGETS, "offer", 10)
    view = _view("saas", "en_curso")
    prompt = composer.compose(view)
    assert ("prompt_section_over_budget", {"tenant": "saas", "section": "offer", "chars": _sizes(view)["offer"], "budget": 10}) in warnings
    assert composer.render_sections(view)["offer"] in prompt


# ---------------------------------------------------------------------------
# Un catálogo grande no infla el prompt
# ---------------------------------------------------------------------------

def _large_business(products: int) -> dict:
    """La hamburguesería de ejemplo con todo al máximo del contrato y `products` productos."""
    document = stored_document("restaurant")
    text = lambda label, index: f"{label} {index} " + "x " * ((policy.MAX_PROFILE_ITEM_CHARS - 20) // 2)  # noqa: E731
    document["identity"].update(differentiators=[text("dif", i) for i in range(policy.MAX_PROFILE_ITEMS)])
    document["sales"].update(**{key: [text(key, i) for i in range(policy.MAX_PROFILE_ITEMS)] for key in ("benefits", "arguments", "instructions")})
    document["terms"]["promotions"] = [{"name": f"Promo {i}", "details": text("detalle", i), "valid_until": "2999-12-31"} for i in range(policy.MAX_PROMOTIONS)]
    # Lo que conectó la Fase 3, también al máximo del contrato.
    long_text = lambda size: "palabra " * (size // 8)  # noqa: E731
    document["identity"].update(credibility=[text("prueba", i) for i in range(policy.MAX_PROFILE_ITEMS)])
    document["response_style"]["instructions"] = [text("estilo", i) for i in range(policy.MAX_PROFILE_ITEMS)]
    document["terms"]["policies"] = {key: long_text(policy.MAX_POLICY_CHARS) for key in ("warranty", "returns", "cancellation")}
    document["messages"].update(**{key: long_text(policy.MAX_MESSAGE_CHARS) for key in ("data_request", "human_handoff", "after_sale")})
    document["sales"]["solution"] = {key: [text("paso", i) for i in range(policy.MAX_PROFILE_ITEMS)] for key in ("process_steps", "requirements")}
    document["sales"]["objections"] = [
        {"topic": topic, **{layer: [text("capa", i) for i in range(policy.MAX_PROFILE_ITEMS)] for layer in ("acknowledge", "reframe", "proof", "redirect", "rules")}}
        for topic in ("precio", "tiempo", "confianza", "competencia", "garantia", "envio", "calidad", "porciones", "sabor", "domicilio")
    ]
    document["sales"]["closing"].update(**{key: [text("cierre", i) for i in range(policy.MAX_PROFILE_ITEMS)]
                                           for key in ("purchase_signals", "high_intent_actions", "next_steps", "micro_commitments", "rules")})
    document["sales"]["support"] = {"explain_first": True, "rules": [text("regla", i) for i in range(policy.MAX_PROFILE_ITEMS)]}
    categories = [{"id": f"cat_{i}", "name": f"Categoría {i}"} for i in range(policy.MAX_CATEGORIES)]
    template = document["offer"]["catalog"]["items"][0]
    document["offer"]["catalog"].update(
        categories=categories,
        items=[
            {**copy.deepcopy(template), "id": f"producto_{i}", "name": f"Producto número {i}", "category": categories[i % 10]["id"],
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


def test_a_huge_sales_strategy_stays_within_its_cap_and_keeps_what_the_customer_talks_about():
    """Diez objeciones al máximo, reglas de cierre y de atención: la estrategia no crece sin límite y la objeción de la que habla el
    cliente llega al prompt."""
    layers = composer.render_sections(_large_view(20, "¿Y si no me gusta el sabor?"))
    assert len(layers["customer"]) <= policy.CUSTOMER_PROMPT_MAX_CHARS + len("EL CLIENTE: QUÉ LO MUEVE Y QUÉ LO FRENA") + 200
    assert len(layers["strategy"]) <= policy.STRATEGY_PROMPT_MAX_CHARS + len("ESTRATEGIA DE VENTA DEL NEGOCIO") + 200
    assert "Si duda por sabor (ideas del negocio" in layers["customer"]
    assert "Si duda por domicilio (ideas del negocio" not in layers["customer"]


def test_the_product_the_customer_asks_for_reaches_the_prompt():
    offer = composer.render_sections(_large_view(300, "¿Tienen el producto número 250?"))["offer"]
    assert "- Producto número 250 — COP 18.000: Descripción del producto 250" in offer
    assert "opciones más que no aparecen aquí" in offer


def test_a_business_whose_catalog_fits_receives_it_whole():
    view = _view("restaurant", "presentacion", "¿Qué tienen?")
    offer = composer.render_sections(view)["offer"]
    assert "opciones más" not in offer
    assert all(f"- {item['name']} — " in offer for item in view.pricing["catalog"]["items"])


# ---------------------------------------------------------------------------
# El negocio en todos los mensajes y la conversación como mensajes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("slug", TENANTS)
def test_the_business_is_in_every_message(slug):
    """Antes, desde el segundo mensaje el asistente dejaba de recibir quién era el negocio y qué vendía."""
    for state in STATES:
        blocks = composer.render_sections(_view(slug, state))
        assert blocks["business"].startswith("EL NEGOCIO\nNombre: "), state
        assert blocks["offer"].startswith("LO QUE VENDE\n- "), state


def test_the_conversation_goes_as_messages_without_payment_data():
    runtime = load_tenant_runtime_yaml("saas")
    secret = next(iter(payment_values(runtime)))
    runtime["conversation_history"] = [
        {"role": "user", "text": "Quiero pagar por nequi"},
        {"role": "assistant", "text": f"Listo, el número es {secret}."},
        {"role": "user", "text": "x " * 600},
    ]
    messages = recent_messages(runtime)
    assert [message["role"] for message in messages] == ["user", "assistant", "user"]
    assert secret not in str(messages) and REDACTED_PAYMENT_VALUE in messages[1]["content"]
    assert len(messages[2]["content"]) <= 701
