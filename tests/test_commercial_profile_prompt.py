"""Perfil comercial y preguntas frecuentes: cómo se compilan desde el contrato y cómo entran al prompt.

Unitarias de `app/domain/business_config/commercial_profile.py`, `app/infrastructure/ai/prompting/business_profile.py` y
`app/infrastructure/ai/prompting/business_knowledge.py`. Lo que se comprueba con el motor completo está en
`test_business_config_engine_integration.py`.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from app.domain.business_config.commercial_profile import compile_knowledge, compile_profile
from app.domain.business_config.contract import BusinessConfig
from app.domain.business_config.engine_policy import FAQ_PROMPT_MAX_CHARS, PROMPT_WORD_LIMITS
from app.infrastructure.ai.prompting.business_knowledge import KNOWLEDGE_HEADER, build_knowledge_context, select_faqs
from app.infrastructure.ai.prompting.business_profile import (
    DEFAULT_TONE,
    PROFILE_HEADER,
    build_business_profile_context,
    response_tone,
)

PROJECT_DIR = Path(__file__).resolve().parents[1] / "project"
EXAMPLE = PROJECT_DIR / "config" / "contracts" / "v1" / "business-config.example.json"
TENANTS_DIR = PROJECT_DIR / "config" / "tenants"


def _example(mutate=None) -> BusinessConfig:
    document = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    if mutate:
        mutate(document)
    return BusinessConfig.model_validate(document)


def _runtime(profile: dict, pricing: dict | None = None, knowledge: dict | None = None) -> dict:
    config: dict = {"profile": profile}
    if knowledge is not None:
        config["knowledge"] = knowledge
    return {"config": config, "pricing": pricing or {}}


# ---------------------------------------------------------------------------
# Compilación desde el contrato
# ---------------------------------------------------------------------------

def test_recommendations_only_point_to_what_is_offered():
    def _mutate(document):
        document["offer"]["catalog"]["items"][1]["available"] = False  # la torta deja de ofrecerse, y con ella su categoría
        document["sales"]["recommendation_rules"] = [
            {"when": "celebra un cumpleaños", "recommend": "torta_chocolate"},
            {"when": "quiere algo dulce", "recommend": "tortas"},
            {"when": "quiere pan", "recommend": "pan_masa_madre"},
            {"when": "busca algo para el desayuno", "recommend": "panes"},
            {"when": "pide algo que no existe", "recommend": "no_existe"},
        ]

    assert compile_profile(_example(_mutate))["recommendations"] == [
        {"when": "quiere pan", "recommend": "Pan de masa madre"},
        {"when": "busca algo para el desayuno", "recommend": "Panes"},
    ]


def test_recommendations_to_plans_use_the_plan_name():
    document = json.loads((TENANTS_DIR / "asesor_ai_prod" / "business-config.json").read_text(encoding="utf-8"))
    # Su otra regla apunta a `plan_pro`, que no existe: no se recomienda.
    assert compile_profile(BusinessConfig.model_validate(document))["recommendations"] == [{"when": "seguimiento", "recommend": "Plan Basico"}]


def test_the_tone_is_compiled_without_its_final_period_and_is_optional():
    assert compile_profile(_example(lambda d: d["response_style"].update(tone="cercano y alegre.")))["tone"] == "cercano y alegre"
    assert "tone" not in compile_profile(_example(lambda d: d["response_style"].pop("tone")))


def test_knowledge_is_only_compiled_when_there_are_faqs():
    assert compile_knowledge(_example(lambda d: d["knowledge"].update(faqs=[]))) is None
    assert len(compile_knowledge(_example())["faqs"]) == 2


# ---------------------------------------------------------------------------
# Bloque del perfil
# ---------------------------------------------------------------------------

def test_without_profile_there_is_no_block_and_the_tone_is_the_usual_one():
    assert build_business_profile_context({"config": {}}) == ""
    assert response_tone({"config": {}}) == DEFAULT_TONE


def test_descriptions_use_the_same_word_limits_the_panel_shows():
    description = " ".join(f"palabra{index}" for index in range(40))
    runtime = _runtime(
        {"name": "Negocio", "description": description},
        pricing={"catalog": {"items": [{"name": "Producto", "description": description, "price": {"COP": 1}}]}},
    )
    block = build_business_profile_context(runtime)
    business_line = next(line for line in block.splitlines() if line.startswith("Descripción:"))
    product_line = next(line for line in block.splitlines() if line.startswith("- Producto:"))
    assert len(business_line.removeprefix("Descripción: ").split()) == PROMPT_WORD_LIMITS["description"]
    assert len(product_line.removeprefix("- Producto: ").split()) == PROMPT_WORD_LIMITS["offer_description"]


def test_an_ongoing_conversation_without_rules_has_no_block():
    runtime = _runtime({"name": "Negocio", "description": "Hace cosas", "differentiators": ["rápido"]})
    assert build_business_profile_context(runtime, include_facts=False) == ""
    assert build_business_profile_context(runtime).startswith(f"{PROFILE_HEADER}\nNegocio: Negocio\nDescripción: Hace cosas")


def test_promotions_expire_by_date_and_an_unreadable_date_is_not_offered():
    promotions = [
        {"name": "Hoy", "details": "Vence hoy", "valid_until": "2026-11-10"},
        {"name": "Ayer", "details": "Venció ayer", "valid_until": "2026-11-09"},
        {"name": "Ilegible", "details": "Fecha rota", "valid_until": "pronto"},
    ]
    block = build_business_profile_context(_runtime({"name": "N", "description": "D", "promotions": promotions}), today=date(2026, 11, 10))
    assert "- Hoy: Vence hoy (válida hasta 2026-11-10)" in block
    assert "Ayer" not in block and "Ilegible" not in block


# ---------------------------------------------------------------------------
# Preguntas frecuentes
# ---------------------------------------------------------------------------

def _faq(index: int, topic: str) -> tuple[str, str]:
    return f"¿Pregunta {index} sobre {topic}?", "Respuesta larga. " * 40


def test_all_faqs_go_when_they_fit():
    faqs = [("¿Abren los domingos?", "Sí."), ("¿Hacen envíos?", "Sí, a toda la ciudad.")]
    assert select_faqs(faqs, "hola") == faqs
    assert build_knowledge_context(_runtime({}, knowledge={"faqs": [{"question": q, "answer": a} for q, a in faqs]})) == (
        f"{KNOWLEDGE_HEADER}\n- P: ¿Abren los domingos?\n  R: Sí.\n- P: ¿Hacen envíos?\n  R: Sí, a toda la ciudad."
    )


def test_when_they_do_not_fit_the_most_related_go_in_the_business_order():
    faqs = [_faq(index, "pagos") for index in range(5)] + [_faq(5, "domingos"), _faq(6, "envíos")]
    chosen = select_faqs(faqs, "¿Abren el domingo?")
    assert faqs[5] in chosen, "«domingo» y «domingos» cuentan como la misma palabra"
    assert sum(len(f"- P: {q}\n  R: {a}") + 1 for q, a in chosen) <= FAQ_PROMPT_MAX_CHARS
    assert chosen == [faq for faq in faqs if faq in chosen], "se escriben en el orden del negocio"
    assert len(chosen) < len(faqs)


def test_without_faqs_there_is_no_block():
    assert build_knowledge_context({"config": {"profile": {"name": "N"}}}, user_message="hola") == ""
