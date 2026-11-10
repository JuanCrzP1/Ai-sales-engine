"""Quién es el negocio: su nombre (en una conversación en curso), su sector y su promesa comercial.

Va en todos los mensajes. En la presentación, el nombre y la descripción completa los da el perfil comercial; en una conversación en
curso ese perfil solo trae las reglas, así que aquí va el nombre para que el asistente nunca olvide para quién vende.
"""
from __future__ import annotations

from app.domain.business_config.engine_policy import MAX_DESCRIPTION_CHARS, MAX_INDUSTRY_CHARS, MAX_VALUE_PROPOSITION_CHARS
from app.infrastructure.ai.prompting.sections.profile import business_profile
from app.infrastructure.ai.prompting.text import as_text, bounded_text, sentence
from app.infrastructure.ai.prompting.view import PromptView

HEADER = "CONTEXTO DEL NEGOCIO:"


def render(view: PromptView) -> str:
    business = view.business
    industry = bounded_text(business.get("industry", ""), max_chars=MAX_INDUSTRY_CHARS)
    description = bounded_text(business.get("description", ""), max_chars=MAX_DESCRIPTION_CHARS)
    promise = bounded_text(business.get("promise", ""), max_chars=MAX_VALUE_PROPOSITION_CHARS)
    lines = []
    if not view.presents_business:
        name = as_text(business_profile(view.runtime).get("name")) or as_text(business.get("name"))
        if name:
            lines.append(sentence(f"Negocio: {name}"))
    if industry or description:
        lines.append(sentence(f"Industria del negocio: {industry or description}"))
    if promise:
        lines.append(sentence(f"Promesa comercial: {promise}"))
    return "\n".join(lines)
