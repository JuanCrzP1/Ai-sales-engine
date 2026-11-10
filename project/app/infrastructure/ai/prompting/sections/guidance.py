"""«INDICACIONES DEL NEGOCIO»: cómo quiere vender este negocio. Sus instrucciones, las promociones vigentes, las preguntas para
entender al cliente y qué recomendar en cada caso. Las promociones vencidas no se ofrecen."""
from __future__ import annotations

from datetime import date

from app.infrastructure.ai.prompting.text import as_dict, as_text, bullets, dicts, section, sentence, texts
from app.infrastructure.ai.prompting.view import PromptView

HEADER = "INDICACIONES DEL NEGOCIO"


def _is_current(promotion: dict, today: date) -> bool:
    valid_until = as_text(promotion.get("valid_until"))
    if not valid_until:
        return True
    try:
        return date.fromisoformat(valid_until) >= today
    except ValueError:
        return False  # Una fecha ilegible no se ofrece: nunca una promoción que podría estar vencida.


def _promotion(promotion: dict) -> str:
    name, details = as_text(promotion.get("name")), as_text(promotion.get("details"))
    if not name or not details:
        return ""
    valid_until = as_text(promotion.get("valid_until"))
    return f"{name}: {details} (válida hasta {valid_until})" if valid_until else f"{name}: {details}"


def render(view: PromptView, *, today: date | None = None) -> str:
    profile = as_dict(view.config.get("profile"))
    promotions = [line for promotion in dicts(profile.get("promotions")) if _is_current(promotion, today or date.today()) and (line := _promotion(promotion))]
    recommendations = [
        sentence(f"Si {when}: recomienda {recommend}")
        for rule in dicts(profile.get("recommendations"))
        if (when := as_text(rule.get("when"))) and (recommend := as_text(rule.get("recommend")))
    ]
    lines = []
    if texts(profile.get("instructions")):
        lines += ["Instrucciones:", *bullets(texts(profile.get("instructions")))]
    if promotions:
        lines += ["Promociones vigentes (no ofrezcas otras promociones ni descuentos):", *bullets(promotions)]
    if texts(profile.get("discovery_questions")):
        lines += ["Preguntas para entender al cliente (una por mensaje y solo si aún no lo sabes):", *bullets(texts(profile.get("discovery_questions")))]
    if recommendations:
        lines += ["Recomendaciones:", *bullets(recommendations)]
    return section(HEADER, lines)
