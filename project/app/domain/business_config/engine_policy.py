"""Políticas internas del motor que el negocio no puede modificar, y límites del contrato.

Valores que el runtime actual aplica (comprobados en el código del motor; este módulo no los cambia):
- longitud de respuesta: `ai_execution.py` y `prompt_builder.py` usan "short" y 80 palabras cuando la
  configuración no trae valores, con un mínimo de 20 palabras.
- ventanas de conversación: `ConfigService.DEFAULT_CONVERSATION` y `conversation_flow.py` usan
  15 minutos (activa) y 4 horas (reinicio); un 0 se trata como "sin valor".
- recortes del prompt (`PROMPT_WORD_LIMITS`, `PROMPT_MAX_*`): ver cada constante.
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

# Recortes que el prompt actual aplica a los textos del negocio (en palabras). El panel los muestra
# al cliente para que sepa qué parte de cada texto usa el asistente.
# - industry y value_proposition: siempre (`PromptBuilderService`, sector y promesa comercial).
# - description: en el perfil comercial, cuando la configuración viene del contrato (y en el contexto del negocio cuando
#   falta `industry`, que el contrato exige).
# - offer_description: la descripción de cada plan y producto en el detalle de la oferta del perfil comercial.
PROMPT_WORD_LIMITS: dict[str, int] = {
    "industry": 8,
    "value_proposition": 30,
    "description": 20,
    "offer_description": 25,
}
# El prompt actual menciona como máximo estos problemas del cliente y categorías del catálogo.
PROMPT_MAX_PROBLEMS = 2
PROMPT_MAX_CATEGORIES = 4
# Caracteres de preguntas frecuentes por prompt. Si todas caben, van todas; si no, las más relacionadas con el mensaje del cliente.
# Con el máximo del contrato (30 de hasta 1000 caracteres) llenarían el prompt.
FAQ_PROMPT_MAX_CHARS = 1500
