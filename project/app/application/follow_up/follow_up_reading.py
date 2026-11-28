"""El lector del seguimiento: antes de escribirle a un cliente que dejó de responder, la IA lee el final del chat y dice si conviene.

Este sistema es AI-first: aquí no hay reglas de palabras. Una llamada corta y exacta al modelo del negocio (con su clave, y su consumo
queda en su cuenta) dice si el cliente dejó la conversación abierta o la cerró («no me interesa», «ya compré en otro lado», «no me
escriban»). Solo se pregunta cuando un seguimiento ya toca, así que no cuesta nada mientras no haya nada que enviar.

Si el lector no responde (sin clave, un error del proveedor, una respuesta que no se entiende), no se envía nada: la próxima revisión lo
vuelve a intentar. Nunca se adivina. El texto del lector está en `infrastructure/ai/prompting/follow_up_reader.py` y se mide con
`experiments/quality_lab/run_follow_up_eval.py`.
"""
from __future__ import annotations

import json

from app.infrastructure.ai.prompting.follow_up_reader import FOLLOW_UP_READER, follow_up_turn
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


def reads_follow_up(runtime, *, bot_config, messages: list[tuple[str, str]], message: str, tenant: str = "") -> bool | None:
    """True si conviene enviar el seguimiento, False si el cliente cerró la conversación, None si no hay lectura."""
    classify = getattr(runtime, "classify", None)
    if not callable(classify) or not messages:
        return None
    try:
        raw = classify(FOLLOW_UP_READER, user_message=follow_up_turn(messages, message), bot_config=bot_config, max_tokens=MAX_TOKENS)
    except Exception as error:  # noqa: BLE001 - sin lector no se envía: la próxima revisión lo intenta de nuevo
        logger.warning("seguimiento_lectura_fallida", extra={"tenant": tenant, "error": type(error).__name__})
        return None
    answer = _json(raw)
    if answer is None or not isinstance(answer.get("enviar"), bool):
        logger.warning("seguimiento_lectura_fallida", extra={"tenant": tenant, "error": "formato"})
        return None
    logger.info("seguimiento_lectura", extra={"tenant": tenant, "send": answer["enviar"]})
    return answer["enviar"]
