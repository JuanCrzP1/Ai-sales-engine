"""Cuándo responde el asistente por WhatsApp y Telegram: espera a que el cliente termine de escribir.

La gente parte lo que quiere decir en varios mensajes seguidos («Hola» … «quiero el plan» … «¿cuánto vale?»). Si el asistente
contestaba al primero, respondía a medias y mandaba varias respuestas. Ahora espera unos segundos después de cada mensaje; si llega
otro, vuelve a esperar, y cuando el cliente se detiene responde una sola vez a todo (`application/channels/inbound.py`). Si el cliente
no para de escribir, a los `MAX_REPLY_WAIT_SECONDS` de su primer mensaje sin respuesta le responde igual.

El negocio elige la espera en Cómo atiende (`response_style.reply_delay_seconds`, de 0 a 20 segundos; 0 responde al instante). Si no
la elige, `DEFAULT_REPLY_DELAY_SECONDS`.
"""
from __future__ import annotations

from app.domain.business_config.engine_policy import DEFAULT_REPLY_DELAY_SECONDS, MAX_REPLY_DELAY_SECONDS, MAX_REPLY_WAIT_SECONDS

__all__ = ["DEFAULT_REPLY_DELAY_SECONDS", "MAX_REPLY_WAIT_SECONDS", "reply_delay"]


def reply_delay(sections: dict) -> int:
    """Los segundos que espera el asistente según lo publicado del negocio (`config.response.reply_delay_seconds`)."""
    config = sections.get("config") if isinstance(sections, dict) and isinstance(sections.get("config"), dict) else {}
    response = config.get("response") if isinstance(config.get("response"), dict) else {}
    value = response.get("reply_delay_seconds")
    if isinstance(value, bool) or not isinstance(value, int):
        return DEFAULT_REPLY_DELAY_SECONDS
    return min(max(value, 0), MAX_REPLY_DELAY_SECONDS)
