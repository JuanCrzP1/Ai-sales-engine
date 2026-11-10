"""Perfil comercial y conocimiento del negocio: lo que el motor solo recibe cuando la configuración viene del contrato.

El compilador los deja en `config.profile` y `config.knowledge`, dos claves que no existen en los YAML: un negocio que sigue con sus
YAML no cambia, y el motor solo añade el perfil al prompt cuando lo encuentra.

- Las recomendaciones apuntan por id a un plan, un producto o una categoría: aquí se cambia el id por su nombre. Las que apuntan a
  algo que no se ofrece se descartan, para que la IA nunca recomiende algo inexistente; el diagnóstico ya se las señala al negocio.
- Las promociones se compilan todas, con su fecha: el motor descarta las vencidas cada vez que arma el prompt, sin volver a publicar.
- Los textos se compilan completos: los recortes que aplica el prompt (`PROMPT_WORD_LIMITS`) los decide el motor al usarlos.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.domain.business_config.contract import BusinessConfig


def _put_list(target: dict[str, Any], key: str, values: Iterable[Any] | None) -> None:
    items = list(values or [])
    if items:
        target[key] = items


def _offered_names(config: BusinessConfig) -> dict[str, str]:
    """El nombre de lo que se ofrece, por id: planes y productos disponibles, y las categorías que tienen alguno disponible."""
    offer = config.offer
    names: dict[str, str] = {}
    if offer.catalog is not None:
        items = [item for item in offer.catalog.items if item.available]
        offered_categories = {item.category for item in items}
        names.update({category.id: category.name for category in offer.catalog.categories if category.id in offered_categories})
        names.update({item.id: item.name for item in items})
    names.update({plan.id: plan.name for plan in offer.plans or [] if plan.available})
    return names


def _tone(config: BusinessConfig) -> str:
    """El tono como cláusula de la línea de estilo del prompt: sin el punto final, que pone el motor."""
    return (config.response_style.tone or "").strip().rstrip(".").strip()


def compile_profile(config: BusinessConfig) -> dict[str, Any]:
    """Quién es el negocio y cómo vende. Siempre trae nombre y descripción, que el contrato exige; el resto, solo si está configurado."""
    identity, sales = config.identity, config.sales
    profile: dict[str, Any] = {
        "name": (identity.brand_name or identity.name).strip(),
        "description": identity.description.strip(),
    }
    tone = _tone(config)
    if tone:
        profile["tone"] = tone
    _put_list(profile, "differentiators", identity.differentiators)
    if identity.location is not None:
        profile["location"] = identity.location.model_dump(mode="json", exclude_none=True)
    _put_list(profile, "service_modes", identity.service_modes)
    _put_list(profile, "benefits", sales.benefits)
    _put_list(profile, "arguments", sales.arguments)
    _put_list(profile, "discovery_questions", sales.discovery.questions if sales.discovery is not None else None)
    names = _offered_names(config)
    _put_list(
        profile,
        "recommendations",
        ({"when": rule.when, "recommend": names[rule.recommend]} for rule in sales.recommendation_rules or [] if rule.recommend in names),
    )
    _put_list(profile, "instructions", sales.instructions)
    _put_list(profile, "promotions", (promotion.model_dump(mode="json", exclude_none=True) for promotion in config.terms.promotions or []))
    return profile


def compile_knowledge(config: BusinessConfig) -> dict[str, Any] | None:
    """Las preguntas frecuentes con su respuesta oficial; None si el negocio no tiene."""
    faqs = [{"question": faq.question.strip(), "answer": faq.answer.strip()} for faq in config.knowledge.faqs]
    return {"faqs": faqs} if faqs else None
