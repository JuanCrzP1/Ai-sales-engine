"""
Pruebas de integración del contrato que exigen cambios POSTERIORES en el motor (no autorizados aún).

Fallan hoy y deben seguir visibles: documentan comportamiento que el motor actual no tiene. Se
movieron sin cambiar sus aserciones desde `test_business_config_contract.py` y
`test_payment_data_protection.py`. Están marcadas `xfail(strict=True)` (ver `pytestmark`): se ejecutan
en cada corrida y en CI, cuentan como "xfailed" y, si alguna pasa, la suite falla hasta convertirla en
prueba normal.

Dependencias pendientes (ver docs/business-config.md, "Integración pendiente con el motor"):
1. Perfil comercial en el prompt (marca, descripción, diferenciadores, ubicación, modalidades,
   beneficios, argumentos, preguntas, recomendaciones, instrucciones, promociones vigentes, detalle de
   la oferta) y tono en la línea ESTILO. Requiere que el motor lea un bloque de perfil y que el
   compilador lo emita (`config.profile`, hoy no se compila porque ningún lector lo consume).
2. Preguntas frecuentes en el prompt (`config.knowledge`, misma situación).
3. Productos y precios del catálogo en el prompt (el prompt actual de catálogo no los lista).
4. Datos de pago fuera del prompt y del registro `conversation_trace` (el motor actual los escribe).
5. Presupuesto del prompt en conversación activa con el perfil comercial incluido.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import app.application.pipeline.common as pipeline_common
from app.application.runtime import load_tenant_runtime_yaml
from app.application.runtime import tenant_runtime_loader as loader
from app.domain.business_config.compiler import compile_business_config
from app.domain.business_config.contract import BusinessConfig
from app.domain.business_config.payment_data import (
    REDACTED_PAYMENT_VALUE,
    iter_payment_blocks,
    payment_values,
)
from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService
from app.infrastructure.config.business_config_store import BusinessConfigStore
from app.infrastructure.config.config_service import ConfigService
from pipeline_harness import TENANTS, reply, run_conversation, run_with_document

# Se ejecutan siempre y deben fallar mientras el motor no implemente su comportamiento (xfail estricto):
# aparecen como "xfailed" en cada ejecución, y si alguna empieza a pasar la suite falla (XPASS strict),
# lo que obliga a convertirla en prueba normal al integrar esa función del motor.
# Solo cuenta como fallo esperado la excepción con la que hoy falla cada prueba (`raises`): una aserción
# no cumplida, salvo las dos pruebas marcadas abajo. Cualquier otro error (un NameError, un fixture
# roto, una validación que falla) es un fallo real.
# Para ver sus fallos en detalle: `pytest -m engine_pending --runxfail`.
PENDING_REASON = "engine_pending: requiere cambios en el motor aún no autorizados (docs/business-config.md)"
pytestmark = [
    pytest.mark.engine_pending,
    pytest.mark.xfail(strict=True, raises=AssertionError, reason=PENDING_REASON),
]

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
_reply = reply
_run_conversation = run_conversation
_run_with_document = run_with_document


CONTRACTS_DIR = PROJECT_DIR / "config" / "contracts" / "v1"


def _service() -> ConfigService:
    return ConfigService()


def _as_yaml_prompt(prompt: str, runtime: dict) -> str:
    """Prompt del contrato sin lo que solo existe con el contrato: el bloque de perfil comercial (con
    datos del negocio en la presentación, solo reglas en una conversación en curso) y el tono en ESTILO.
    """
    for include_facts in (True, False):
        block = PromptBuilderService.build_business_profile_context(runtime, include_facts=include_facts)
        if block and f"\n\n{block}\n\n" in prompt:
            prompt = prompt.replace(f"\n\n{block}", "", 1)
            break
    tone = runtime["config"]["profile"].get("tone", "").strip()
    return prompt.replace(f"palabras, {tone}.", "palabras, natural y claro.", 1) if tone else prompt


def _profile_block(prompt: str) -> str:
    assert "PERFIL COMERCIAL DEL NEGOCIO:" in prompt
    return prompt.split("PERFIL COMERCIAL DEL NEGOCIO:\n", 1)[1].split("\n\n", 1)[0]


CATALOG_TENANTS = ["agencia_viajes", "escuela_conduccion", "restaurant", "tienda_ropa"]


TWO_TURNS = [("Necesito información", _reply("Claro.")), ("¿Cuál es el precio?", _reply("Te cuento."))]


def _first_plan(document: dict) -> dict:
    return document["offer"]["plans"][0]


PANEL_DOCUMENT = ROOT_DIR / "apps" / "admin-web" / "src" / "test" / "fixtures" / "sampleContractDocument.json"


ENGINE_CASES = {
    "tono": ("restaurant", lambda d: d["response_style"].update(tone="paciente y muy claro"), "máximo 60 palabras, paciente y muy claro.", 1),
    "descripcion_plan": ("saas", lambda d: _first_plan(d).update(name="Plan Caja", description="Incluye soporte por chat"),
                         "- Plan Caja: Incluye soporte por chat", 0),
}


@pytest.mark.parametrize("slug", TENANTS)
def test_engine_prompt_and_reply_are_identical_with_contract_source(monkeypatch, slug):
    turns = [
        ("¿Cuánto cuesta?", _reply("Te cuento los precios.")),
        ("¿Y qué incluye?", _reply("Te explico lo que incluye.")),
        ("Quiero pagar por Nequi", _reply("Listo.", "buy", payment_method="nequi")),
    ]
    monkeypatch.delenv(loader.CONTRACT_TENANTS_ENV, raising=False)
    from_yaml = _run_conversation(slug, turns, user_id="equivalencia")
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, slug)
    from_contract = _run_conversation(slug, turns, user_id="equivalencia")
    runtime = load_tenant_runtime_yaml(slug)

    # Única diferencia intencional: el perfil comercial (bloque y tono). Sin él, prompts y respuestas coinciden.
    assert "PERFIL COMERCIAL DEL NEGOCIO:" in from_contract[0][0][0]
    assert [([_as_yaml_prompt(p, runtime) for p in prompts], reply) for prompts, reply in from_contract] == from_yaml
    assert all("PERFIL COMERCIAL DEL NEGOCIO:" not in p for prompts, _ in from_yaml for p in prompts)
    assert all(prompts for prompts, _response in from_contract)
    assert from_contract[-1][1].startswith("Avanzamos con el siguiente paso.")


@pytest.mark.parametrize("slug", CATALOG_TENANTS)
def test_catalog_prices_reach_the_prompt(monkeypatch, slug):
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, slug)
    config = BusinessConfigStore(_service().tenants_root).load(slug)
    (prompts, _), = _run_conversation(slug, [("¿Cuánto cuesta?", _reply("Te cuento."))], user_id="catalogo")
    prices_line = next(line for line in prompts[0].splitlines() if line.startswith("Precios:"))
    for item in config.offer.catalog.items:
        assert f"{item.name} -> COP: {item.prices[0].amount}" in prices_line


def test_faqs_reach_the_prompt_only_when_configured(monkeypatch, tmp_path):
    faqs = [{"question": "¿Atienden los domingos?", "answer": "Sí, de 9 a. m. a 1 p. m."}]
    (prompts, _), = _run_with_document(
        monkeypatch, tmp_path, "restaurant",
        lambda d: d.update(knowledge={"faqs": faqs}),
        [("¿Abren el domingo?", _reply("Sí."))],
    )
    assert "CONOCIMIENTO DEL NEGOCIO (preguntas frecuentes):\n- P: ¿Atienden los domingos?\n  R: Sí, de 9 a. m. a 1 p. m." in prompts[0]

    monkeypatch.setattr(ai_pipeline_module, "load_tenant_runtime_yaml", load_tenant_runtime_yaml)
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, "*")
    for slug in TENANTS:
        (plain_prompts, _), = _run_conversation(slug, [("Hola, info", _reply("Claro."))], user_id="sin-faq")
        assert "CONOCIMIENTO DEL NEGOCIO" not in plain_prompts[0]


@pytest.mark.xfail(strict=True, raises=KeyError, reason=f"{PENDING_REASON}: el compilador no emite config.knowledge mientras el motor no lo lea")
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
    turns = [("Hola, info", _reply("Claro."))]
    monkeypatch.delenv(loader.CONTRACT_TENANTS_ENV, raising=False)
    (yaml_prompts, _), = _run_conversation(slug, turns, user_id="perfil")
    monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, slug)
    (contract_prompts, _), = _run_conversation(slug, turns, user_id="perfil")

    config = BusinessConfigStore(_service().tenants_root).load(slug)
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
}


@pytest.mark.parametrize("case", PROFILE_CASES)
def test_each_profile_option_reaches_the_prompt(monkeypatch, tmp_path, case):
    mutate, expected = PROFILE_CASES[case]
    turns = [("Hola, info", _reply("Claro."))]
    (before, _), = _run_with_document(monkeypatch, tmp_path / "antes", "restaurant", lambda d: None, turns)
    (after, _), = _run_with_document(monkeypatch, tmp_path / "despues", "restaurant", mutate, turns)
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

    (prompts, _), = _run_with_document(monkeypatch, tmp_path, "restaurant", _clear, [("Hola, info", _reply("Claro."))])
    identity = BusinessConfigStore(_service().tenants_root).load("restaurant").identity
    # Sin opciones del perfil solo quedan el nombre y la descripción, que siempre son obligatorios.
    assert _profile_block(prompts[0]).splitlines() == [f"Negocio: {identity.name}", f"Descripción: {identity.description.strip()}"]


def test_expired_promotions_are_not_offered(monkeypatch, tmp_path):
    promotions = [
        {"name": "Vencida", "details": "Ya no aplica", "valid_until": "2000-01-01"},
        {"name": "Permanente", "details": "Siempre vigente"},
    ]
    (prompts, _), = _run_with_document(
        monkeypatch, tmp_path, "restaurant", lambda d: d["terms"].update(promotions=promotions), [("¿Promociones?", _reply("Claro."))]
    )
    block = _profile_block(prompts[0])
    assert "- Permanente: Siempre vigente" in block
    assert "Vencida" not in block


@pytest.mark.parametrize("case", ENGINE_CASES)
def test_engine_used_fields_change_the_prompt(monkeypatch, tmp_path, case):
    slug, mutate, expected, turn = ENGINE_CASES[case]
    before = _run_with_document(monkeypatch, tmp_path / "antes", slug, lambda d: None, TWO_TURNS)
    after = _run_with_document(monkeypatch, tmp_path / "despues", slug, mutate, TWO_TURNS)
    assert expected not in before[turn][0][0]
    assert expected in after[turn][0][0]


@pytest.mark.xfail(
    strict=True, raises=AttributeError, reason=f"{PENDING_REASON}: el motor no tiene PromptBuilderService.build_business_profile_context"
)
def test_panel_document_is_valid_and_reaches_the_engine():
    """`translateToEngine.test.ts` genera este archivo con el adaptador del panel; aquí lo valida el contrato."""
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


def test_ongoing_conversation_keeps_only_the_profile_rules(monkeypatch, tmp_path):
    def _with_rules(document):
        document["sales"]["instructions"] = ["Confirma la dirección antes de cerrar."]

    turns = [("Necesito información", _reply("Claro.")), ("¿Y el domicilio?", _reply("Te cuento."))]
    (first, _), (second, _) = _run_with_document(monkeypatch, tmp_path, "restaurant", _with_rules, turns)
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
    # asesor_ai_prod no tiene recomendaciones, instrucciones ni promociones: en curso solo cambia el tono.
    assert "PERFIL COMERCIAL DEL NEGOCIO:" not in prompt
    assert "máximo 75 palabras, humano, cercano, directo y comercial de cierre." in prompt
    assert len(prompt) < 2800


def _first_transfer_method(runtime: dict) -> tuple[str, str]:
    for block in iter_payment_blocks(runtime["pricing"]):
        transfer = block.get("transfer") or {}
        for method in transfer.get("methods") or [] if transfer.get("enabled") else []:
            value = next((str(method[field]) for field in ("number", "account_number", "reference") if method.get(field)), "")
            if value:
                return method["type"], value
    raise AssertionError("el negocio no tiene transferencias activas")


def _use_source(monkeypatch, source: str, slug: str) -> None:
    if source == "contract":
        monkeypatch.setenv(loader.CONTRACT_TENANTS_ENV, slug)
    else:
        monkeypatch.delenv(loader.CONTRACT_TENANTS_ENV, raising=False)


@pytest.mark.parametrize("source", ["yaml", "contract"])
@pytest.mark.parametrize("slug", TENANTS)
def test_payment_values_never_reach_the_ai_but_reach_the_customer(monkeypatch, slug, source):
    _use_source(monkeypatch, source, slug)
    runtime = load_tenant_runtime_yaml(slug)
    secrets = payment_values(runtime)
    method, value = _first_transfer_method(runtime)
    assert secrets and value in secrets

    turns = [
        ("¿Cuánto cuesta?", reply("Te cuento los precios.")),
        (f"Quiero pagar por {method}", reply("Listo.", "buy", payment_method=method)),
        ("¿Me repites el dato?", reply("Claro, revisa el mensaje anterior.")),
    ]
    results = run_conversation(slug, turns, user_id="pagos")
    prompts = [prompt for turn_prompts, _ in results for prompt in turn_prompts]

    assert prompts
    for prompt in prompts:
        leaked = [secret for secret in secrets if secret in prompt]
        assert not leaked, f"{slug}/{source}: {len(leaked)} datos de pago en el prompt"
    # El método sigue siendo visible para que la IA guíe la elección, sin su dato.
    assert "TRANSFER_METHODS:" in prompts[0] and f"- {method}:" in prompts[0]
    assert value in results[1][1], "el cliente debe recibir el dato de pago al elegir el método"


def test_payment_value_in_conversation_history_is_redacted_from_the_prompt():
    runtime = load_tenant_runtime_yaml("asesor_ai_prod")
    _method, value = _first_transfer_method(runtime)
    runtime["conversation_state"] = "active"
    runtime["memory_context"] = {"last_ai_response": f"Puedes transferir usando {value}.", "last_intent": "buy"}

    prompt, _metadata, _context = PromptBuilderService().build(
        client_config_id="asesor_ai_prod", user_message="¿Ya te llegó?", yaml_config=runtime, faq_results=[], progression_rules=None
    )
    assert value not in prompt
    assert f"Puedes transferir usando {REDACTED_PAYMENT_VALUE}." in prompt


@pytest.mark.parametrize("source", ["yaml", "contract"])
def test_conversation_trace_log_never_stores_payment_values(monkeypatch, source):
    _use_source(monkeypatch, source, "saas")
    method, value = _first_transfer_method(load_tenant_runtime_yaml("saas"))
    traces: list[dict] = []

    class _CaptureLogger:
        def info(self, event, extra=None, **_kwargs):
            if event == "conversation_trace":
                traces.append(extra or {})

    monkeypatch.setattr(pipeline_common, "logger", _CaptureLogger())
    (_, response), = run_conversation("saas", [(f"Pago por {method}", reply("Listo.", "buy", payment_method=method))], user_id="log")

    assert value in response
    assert traces and value not in traces[-1]["ai_response"]
    assert REDACTED_PAYMENT_VALUE in traces[-1]["ai_response"]
