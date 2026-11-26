"""El lector del saludo: si el primer mensaje del cliente es solo un saludo, entendido por la IA en una llamada corta.

Este sistema es AI-first: aquí no hay reglas de palabras. Si el negocio escribió su saludo (Mensajes → Bienvenida) y la conversación
empieza, una llamada corta y exacta al modelo del negocio (con su clave, y su consumo queda en su cuenta) dice si el cliente solo
saluda. Si sí, le llega el saludo del negocio tal cual (`conversation_flow.py`); si además pide, pregunta o cuenta algo, responde la
IA. Solo se pregunta cuando hace falta: en el primer mensaje y si hay saludo configurado; los demás mensajes no gastan nada.

Si el lector no responde (sin clave, un error del proveedor, una respuesta que no se entiende), no sale el saludo fijo: responde la
IA, que también saluda. Nunca se adivina con palabras. Hasta el 26 nov 2026 lo decidía una lista de saludos colombianos; el texto
del lector está en `infrastructure/ai/prompting/greeting_reader.py` y se mide con `experiments/quality_lab/run_greeting_eval.py`.
"""
from __future__ import annotations

import json

from app.infrastructure.ai.prompting.greeting_reader import GREETING_READER, greeting_turn
from app.utils.logger import logger

# Un JSON de una sola clave: no hace falta más.
MAX_TOKENS = 20


def _json(raw: str) -> dict | None:
    text = str(raw or "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def reads_as_greeting(runtime, *, bot_config, user_message: str, tenant: str = "") -> bool | None:
    """True si el cliente solo saluda, False si además pide, pregunta o cuenta algo, None si no hay lectura."""
    classify = getattr(runtime, "classify", None)
    if not callable(classify) or not str(user_message or "").strip():
        return None
    try:
        raw = classify(GREETING_READER, user_message=greeting_turn(user_message), bot_config=bot_config, max_tokens=MAX_TOKENS)
    except Exception as error:  # noqa: BLE001 - sin lector, responde la IA
        logger.warning("saludo_lectura_fallida", extra={"tenant": tenant, "error": type(error).__name__})
        return None
    answer = _json(raw)
    if answer is None or not isinstance(answer.get("solo_saluda"), bool):
        logger.warning("saludo_lectura_fallida", extra={"tenant": tenant, "error": "formato"})
        return None
    logger.info("saludo_lectura", extra={"tenant": tenant, "greets_only": answer["solo_saluda"]})
    return answer["solo_saluda"]
