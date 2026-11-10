"""Cuánto puede ocupar cada bloque del prompt, en caracteres (unos 4 por token).

Salen de los límites del contrato y de la política del prompt, con margen: un negocio con todo al máximo cabe. El compositor mide cada
bloque en cada mensaje y deja `prompt_section_over_budget` en el registro si alguno se pasa; no recorta nada, para no perder datos
del negocio. Las pruebas comprueban que los nueve negocios de ejemplo y uno con todo al máximo caben.
"""
from __future__ import annotations

from app.domain.business_config.engine_policy import (
    FAQ_PROMPT_MAX_CHARS,
    MAX_MESSAGE_CHARS,
    MAX_PROFILE_ITEM_CHARS,
    MAX_PROFILE_ITEMS,
    MAX_PROMOTIONS,
    OFFER_DETAILS_PROMPT_MAX_CHARS,
    PRICE_LIST_PROMPT_MAX_CHARS,
)

# Listas del perfil comercial con hasta MAX_PROFILE_ITEMS entradas de MAX_PROFILE_ITEM_CHARS: diferenciadores, beneficios, argumentos,
# preguntas para entender al cliente e instrucciones; más las promociones y el detalle de la oferta.
_PROFILE_LISTS = 5 * MAX_PROFILE_ITEMS * MAX_PROFILE_ITEM_CHARS + MAX_PROMOTIONS * MAX_PROFILE_ITEM_CHARS

SECTION_BUDGETS: dict[str, int] = {
    "identity": 600,
    "rules": 600,
    "capabilities": 1_500,
    "profile": _PROFILE_LISTS + OFFER_DETAILS_PROMPT_MAX_CHARS + 2_000,
    "knowledge": FAQ_PROMPT_MAX_CHARS + 100,
    "behavior": 1_000,
    "sales": 1_500,
    "memory": 3_000,
    "style": 400,
    "pricing": PRICE_LIST_PROMPT_MAX_CHARS + 2_500,
    "post_payment": 2 * MAX_MESSAGE_CHARS + 400,
    "continuity": 1_500,
}
# Todo el prompt de un mensaje, sin el marco del canal ni el formato de respuesta (fijos, unos 1.800 caracteres).
TOTAL_BUDGET = 32_000


def over_budget(sizes: dict[str, int]) -> dict[str, tuple[int, int]]:
    """Los bloques que se pasan de su presupuesto: nombre → (caracteres, presupuesto)."""
    return {name: (size, SECTION_BUDGETS[name]) for name, size in sizes.items() if size > SECTION_BUDGETS.get(name, TOTAL_BUDGET)}
