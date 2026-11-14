"""Políticas internas del motor que el negocio no puede modificar, y límites del contrato.

Valores que el runtime actual aplica (comprobados en el código del motor; este módulo no los cambia):
- longitud de respuesta: `ai_execution.py` y `prompting/sections/style.py` usan "short" y 80 palabras cuando la
  configuración no trae valores, con un mínimo de 20 palabras.
- ventanas de conversación: `conversation_flow.py` usa 15 minutos (activa) y 4 horas (reinicio); un 0 se trata
  como "sin valor".
- largo de los textos del negocio (`MAX_*_CHARS`) y de sus listas: el asistente los usa completos.
- definición común del cierre (`COMMON_CLOSING_POLICY`): ver la constante.

Opciones de longitud para el negocio: cada una fija el límite de palabras que el motor escribe en el
prompt y aplica al recortar la respuesta. Son los valores que ya usaban los negocios (`short`=60,
`medium`=75) y el panel administrativo (`long`=100).
"""
from __future__ import annotations

from typing import Literal

ResponseLength = Literal["short", "medium", "long"]

DEFAULT_RESPONSE_LENGTH: ResponseLength = "short"
DEFAULT_MAX_WORDS = 80
MIN_MAX_WORDS = 20

RESPONSE_LENGTH_MAX_WORDS: dict[str, int] = {"short": 60, "medium": 75, "long": 100}

# Rango permitido del ajuste avanzado `max_words` para cada opción: empieza después del límite de la
# opción anterior, para que "Cortas" nunca supere a "Equilibradas" ni "Equilibradas" a "Detalladas".
# "Detalladas" no tiene tope: el negocio puede pedir respuestas tan largas como necesite.
RESPONSE_LENGTH_WORD_RANGES: dict[str, tuple[int, int | None]] = {
    "short": (MIN_MAX_WORDS, RESPONSE_LENGTH_MAX_WORDS["short"]),
    "medium": (RESPONSE_LENGTH_MAX_WORDS["short"] + 1, RESPONSE_LENGTH_MAX_WORDS["medium"]),
    "long": (RESPONSE_LENGTH_MAX_WORDS["medium"] + 1, None),
}

DEFAULT_ACTIVE_WINDOW_MINUTES = 15
DEFAULT_RESET_HOURS = 4

# Definición común del cierre: los mismos valores para todos los negocios, que no la configuran. Está fuera del
# contrato comercial y de los ajustes técnicos; el compilador la añade a `sales.closing` para que el motor reciba lo
# mismo que con los YAML, y el importador rechaza un YAML con otros valores. Hoy ninguna lógica del motor la lee.
COMMON_CLOSING_POLICY: dict[str, dict] = {
    # La acción final cambia según el momento de la conversación: el siguiente paso sale de la respuesta de la IA.
    "next_step": {"action": "dynamic"},
    # Objetivo esperado según el tipo de cierre (`sales.closing.strategy`).
    "behavior": {
        "direct_sale": {"goal": "confirmar_compra"},  # cuando el usuario ya quiere avanzar
        "lead_capture": {"goal": "capturar_datos"},  # cuando aún falta información básica
        "booking": {"goal": "agendar"},  # cuando hay que coordinar una agenda, una demo o una reserva
        "checkout": {"goal": "enviar_pago"},  # cuando toca llevar al pago
    },
}

# Límites del contrato (validación de los documentos). Las preguntas frecuentes, las listas de frases, el tono y las
# promociones llegan al motor cuando la configuración viene del contrato; las políticas todavía no: ver docs/business-config.md.
MAX_FAQS = 30
MAX_FAQ_QUESTION_CHARS = 200
MAX_FAQ_ANSWER_CHARS = 800
MAX_PROFILE_ITEMS = 10
MAX_PROFILE_ITEM_CHARS = 300
MAX_TONE_CHARS = 160
MAX_PROMOTIONS = 10
MAX_POLICY_CHARS = 800
MAX_MESSAGE_CHARS = 800
# «Cuándo pasar a una persona» (`contract/escalation.py`): temas por lista y el largo de cada uno.
MAX_ESCALATION_TOPICS = 15
MAX_ESCALATION_TOPIC_CHARS = 120

# Largo máximo de los textos del negocio que usa el asistente, en caracteres. El contrato no acepta más y el panel no deja
# escribir más (con un contador): el asistente usa cada texto completo, nunca un recorte.
MAX_INDUSTRY_CHARS = 80
MAX_DESCRIPTION_CHARS = 500
MAX_VALUE_PROPOSITION_CHARS = 300
MAX_OFFER_DESCRIPTION_CHARS = 300
# Listas que el asistente usa completas.
MAX_CATEGORIES = 20
MAX_CUSTOMER_PROBLEMS = 10
# Caracteres de preguntas frecuentes por prompt. Si todas caben, van todas; si no, las más relacionadas con el mensaje del cliente.
# Con el máximo del contrato (30 de hasta 1000 caracteres) llenarían el prompt.
FAQ_PROMPT_MAX_CHARS = 1500
# La oferta en el prompt (planes o productos, con su precio y su detalle), con el mismo criterio: si todo cabe, va todo; si no, lo más
# relacionado con lo que pregunta el cliente y un aviso de que hay más. El contrato no limita cuántos productos tiene un negocio.
OFFER_PROMPT_MAX_CHARS = 4000
# La estrategia avanzada en el prompt («EL CLIENTE» y «ESTRATEGIA DE VENTA»), con el mismo criterio. El contrato no limita cuántas
# objeciones, problemas o motivos escribe un negocio: si no cabe todo, va lo más relacionado con lo que dice el cliente.
CUSTOMER_PROMPT_MAX_CHARS = 5000
STRATEGY_PROMPT_MAX_CHARS = 5000
