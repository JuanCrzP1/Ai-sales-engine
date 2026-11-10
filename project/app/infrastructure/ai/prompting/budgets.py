"""Cuánto puede ocupar cada capa del prompt, en caracteres (unos 4 por token).

Salen de los límites del contrato y de la política del prompt, con margen: un negocio con todo al máximo cabe. El compositor mide cada
capa en cada mensaje y deja `prompt_section_over_budget` en el registro si alguna se pasa; no recorta nada, para no perder datos del
negocio. Las pruebas comprueban que los nueve negocios de ejemplo y uno con todo al máximo caben.
"""
from __future__ import annotations

from app.domain.business_config.engine_policy import (
    FAQ_PROMPT_MAX_CHARS,
    MAX_DESCRIPTION_CHARS,
    MAX_PROFILE_ITEM_CHARS,
    MAX_PROFILE_ITEMS,
    MAX_PROMOTIONS,
    MAX_VALUE_PROPOSITION_CHARS,
    OFFER_PROMPT_MAX_CHARS,
)

# Una lista del perfil comercial al máximo del contrato.
_PROFILE_LIST = MAX_PROFILE_ITEMS * MAX_PROFILE_ITEM_CHARS

SECTION_BUDGETS: dict[str, int] = {
    "platform": 4_500,
    "playbook": 800,
    # Descripción, promesa, diferenciadores, beneficios y argumentos al máximo, más ubicación, motivos y tono.
    "business": MAX_DESCRIPTION_CHARS + MAX_VALUE_PROPOSITION_CHARS + 3 * _PROFILE_LIST + 2_000,
    "offer": OFFER_PROMPT_MAX_CHARS + 1_500,
    "payments": 1_500,
    # Instrucciones, preguntas para entender al cliente, promociones y recomendaciones al máximo.
    "guidance": 3 * _PROFILE_LIST + MAX_PROMOTIONS * MAX_PROFILE_ITEM_CHARS + 600,
    "knowledge": FAQ_PROMPT_MAX_CHARS + 100,
    "conversation": 3_000,
}
TOTAL_BUDGET = 40_000


def over_budget(sizes: dict[str, int]) -> dict[str, tuple[int, int]]:
    """Las capas que se pasan de su presupuesto: nombre → (caracteres, presupuesto)."""
    return {name: (size, SECTION_BUDGETS[name]) for name, size in sizes.items() if size > SECTION_BUDGETS.get(name, TOTAL_BUDGET)}
