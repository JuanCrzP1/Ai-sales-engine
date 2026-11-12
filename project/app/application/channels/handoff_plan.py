"""Qué pasa cuando un chat pasa a una persona, igual en todos los canales (WhatsApp, la API del asistente…).

Junta los ajustes de atención humana del negocio con lo publicado (su horario y su mensaje para fuera del horario) y decide con
`domain/business_config/attention.handoff_plan`. Si algo de eso no se puede leer, el chat pasa a una persona como siempre: la IA
se pausa y no se agrega ningún aviso. La atención humana nunca impide el traspaso.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from app.domain.business_config.attention import AttentionSettings, HandoffPlan, handoff_plan, published_attention
from app.utils.logger import logger

AttentionLoader = Callable[[str], AttentionSettings]
SectionsLoader = Callable[[str], dict]


def plan_handoff(slug: str, *, attention: AttentionLoader, sections: SectionsLoader, now: datetime) -> HandoffPlan:
    try:
        published = published_attention(sections(slug))
        return handoff_plan(attention(slug), published.business_hours, now, after_hours_message=published.after_hours)
    except Exception as exc:  # noqa: BLE001 - la atención humana nunca puede impedir que el chat pase a una persona
        logger.warning("atencion_humana_no_disponible", extra={"tenant": slug, "error": type(exc).__name__})
        return HandoffPlan(team_available=True, pause_ai=True, notice=None)
