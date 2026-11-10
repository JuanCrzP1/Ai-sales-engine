"""Cuánto puede ocupar cada capa del prompt, en caracteres (unos 4 por token).

Salen de los límites del contrato y de la política del prompt, con margen: un negocio con todo al máximo cabe. El compositor mide cada
capa en cada mensaje y deja `prompt_section_over_budget` en el registro si alguna se pasa; no recorta nada, para no perder datos del
negocio. Las pruebas comprueban que los nueve negocios de ejemplo y uno con todo al máximo caben.

Lo que el contrato no limita (productos, preguntas frecuentes, objeciones, reglas) ya llega acotado por relevancia (`relevance.py`). Un
negocio típico usa de 5.000 a 12.000 caracteres (unos 1.500 a 3.000 tokens); el total es el techo con todo al máximo del contrato.
"""
from __future__ import annotations

from app.domain.business_config.engine_policy import (
    CUSTOMER_PROMPT_MAX_CHARS,
    FAQ_PROMPT_MAX_CHARS,
    MAX_DESCRIPTION_CHARS,
    MAX_MESSAGE_CHARS,
    MAX_POLICY_CHARS,
    MAX_PROFILE_ITEM_CHARS,
    MAX_PROFILE_ITEMS,
    MAX_PROMOTIONS,
    MAX_TONE_CHARS,
    MAX_VALUE_PROPOSITION_CHARS,
    OFFER_PROMPT_MAX_CHARS,
    STRATEGY_PROMPT_MAX_CHARS,
)

# Una lista del perfil comercial al máximo del contrato.
_PROFILE_LIST = MAX_PROFILE_ITEMS * MAX_PROFILE_ITEM_CHARS

SECTION_BUDGETS: dict[str, int] = {
    "platform": 4_500,
    "playbook": 800,
    # Descripción, promesa, diferenciadores, pruebas de confianza, beneficios, argumentos e indicaciones de estilo al máximo, más
    # posicionamiento, cliente ideal, ubicación, horario, motivos, tono y personalidad.
    "business": MAX_DESCRIPTION_CHARS + MAX_VALUE_PROPOSITION_CHARS + 5 * _PROFILE_LIST + 2 * MAX_TONE_CHARS + 3_000,
    # Las ofertas que caben, más categorías, mejoras, complementos, condiciones y argumentos de valor.
    "offer": OFFER_PROMPT_MAX_CHARS + 2_500,
    # Pasos y requisitos al máximo, más domicilio, envío, recogida y agenda.
    "delivery": 2 * _PROFILE_LIST + 1_500,
    # Medios, financiación, cierre, datos y canales, más los mensajes del negocio para pedir datos y para pasar a una persona.
    "payments": 2 * MAX_MESSAGE_CHARS + 2_000,
    "policies": 3 * MAX_POLICY_CHARS + 300,
    # Instrucciones, preguntas para entender al cliente, promociones y recomendaciones al máximo.
    "guidance": 3 * _PROFILE_LIST + MAX_PROMOTIONS * MAX_PROFILE_ITEM_CHARS + 600,
    # Estrategia avanzada: problemas, casos, motivos y objeciones; y orden, atención, presentación y cierre. Acotadas por relevancia.
    "customer": CUSTOMER_PROMPT_MAX_CHARS + 200,
    "strategy": STRATEGY_PROMPT_MAX_CHARS + 200,
    "knowledge": FAQ_PROMPT_MAX_CHARS + 100,
    "conversation": 3_000,
}
# Con todo al máximo del contrato el prompt mide unos 49.000 caracteres más las preguntas frecuentes y la conversación (unos 14.000
# tokens): pasarse de aquí solo ocurre si un texto sin límite propio (posicionamiento, señales del cliente) se sale de lo normal.
TOTAL_BUDGET = 56_000


def over_budget(sizes: dict[str, int]) -> dict[str, tuple[int, int]]:
    """Las capas que se pasan de su presupuesto: nombre → (caracteres, presupuesto)."""
    return {name: (size, SECTION_BUDGETS[name]) for name, size in sizes.items() if size > SECTION_BUDGETS.get(name, TOTAL_BUDGET)}
