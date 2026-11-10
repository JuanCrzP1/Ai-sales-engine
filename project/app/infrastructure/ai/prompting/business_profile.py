"""Bloque «PERFIL COMERCIAL DEL NEGOCIO» del prompt y tono de su línea de estilo.

Salen de `config.profile`, que solo existe cuando la configuración del negocio viene del contrato
(`app/domain/business_config/commercial_profile.py`): con los YAML no hay bloque y la línea de estilo es la de siempre.

- En la presentación van los datos del negocio y sus reglas; en una conversación en curso, solo las reglas (instrucciones y
  promociones vigentes), para que el prompt no crezca en cada turno.
- Las promociones vencidas no se ofrecen.
- Las descripciones se recortan con `PROMPT_WORD_LIMITS`, los mismos límites que el panel le muestra al negocio.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from app.domain.business_config.engine_policy import PROMPT_WORD_LIMITS

PROFILE_HEADER = "PERFIL COMERCIAL DEL NEGOCIO:"
DEFAULT_TONE = "natural y claro"
DISCOVERY_HEADER = "Preguntas para entender al cliente (como máximo una por mensaje y solo si aún no lo sabes):"
PROMOTIONS_HEADER = "Promociones vigentes (no ofrezcas otras promociones ni descuentos):"

_LOCATION_TYPES = {"virtual": "atención virtual", "fisico": "local físico", "mixto": "local físico y atención virtual"}
_SERVICE_MODES = {"virtual": "virtual", "presencial": "presencial", "domicilio": "a domicilio", "recoger": "para recoger", "envio": "con envío"}
_SENTENCE_ENDINGS = (".", "!", "?", "…")


def _dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _dicts(value: Any) -> list[dict]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _texts(value: Any) -> list[str]:
    return [text for item in value if (text := str(item or "").strip())] if isinstance(value, list) else []


def _sentence(text: str) -> str:
    text = text.strip()
    return text if not text or text.endswith(_SENTENCE_ENDINGS) else f"{text}."


def _shorten(value: Any, max_words: int) -> str:
    return " ".join(str(value or "").split()[:max_words])


def _section(header: str, items: list[str]) -> list[str]:
    return [header, *(f"- {item}" for item in items)] if items else []


def business_profile(runtime: dict) -> dict:
    """El perfil compilado desde el contrato; vacío si la configuración viene de los YAML."""
    return _dict(_dict(_dict(runtime).get("config")).get("profile"))


def response_tone(runtime: dict) -> str:
    """El tono para la línea ESTILO: el del negocio o, sin perfil, el de siempre."""
    return str(business_profile(runtime).get("tone") or "").strip() or DEFAULT_TONE


def _location_lines(location: dict) -> list[str]:
    kind = str(location.get("type") or "").strip()
    if not kind:
        return []
    place = ", ".join(_texts([location.get("address"), location.get("city")]))
    where = _LOCATION_TYPES.get(kind, kind)
    lines = [_sentence(f"Ubicación: {where}; {place}" if place else f"Ubicación: {where}")]
    coverage = _dict(location.get("coverage"))
    scope = str(coverage.get("type") or "").strip()
    if scope:
        zones = ", ".join(_texts(coverage.get("zones")))
        lines.append(_sentence(f"Cobertura {scope}: {zones}" if zones else f"Cobertura {scope}"))
    return lines


def _offer_details(runtime: dict) -> list[str]:
    """Planes y productos que se ofrecen, con su descripción y características. Salen de `pricing`, como el resto del prompt."""
    pricing = _dict(_dict(runtime).get("pricing"))
    details = []
    for offer in [*_dicts(pricing.get("plans")), *_dicts(_dict(pricing.get("catalog")).get("items"))]:
        name = str(offer.get("name") or "").strip()
        description = _shorten(offer.get("description"), PROMPT_WORD_LIMITS["offer_description"])
        features = _texts(offer.get("features"))
        parts = [_sentence(description)] if description else []
        if features:
            parts.append(_sentence(f"Características: {', '.join(features)}"))
        if name and parts:
            details.append(f"{name}: {' '.join(parts)}")
    return details


def _fact_lines(profile: dict, runtime: dict) -> list[str]:
    """Quién es el negocio y qué ofrece: solo en la presentación."""
    lines = []
    name = str(profile.get("name") or "").strip()
    if name:
        lines.append(f"Negocio: {name}")
    description = _shorten(profile.get("description"), PROMPT_WORD_LIMITS["description"])
    if description:
        lines.append(f"Descripción: {description}")
    differentiators = _texts(profile.get("differentiators"))
    if differentiators:
        lines.append(_sentence(f"Diferenciadores: {'; '.join(differentiators)}"))
    lines += _location_lines(_dict(profile.get("location")))
    modes = [_SERVICE_MODES.get(mode, mode) for mode in _texts(profile.get("service_modes"))]
    if modes:
        lines.append(_sentence(f"Modalidades de atención: {', '.join(modes)}"))
    benefits = _texts(profile.get("benefits"))
    if benefits:
        lines.append(_sentence(f"Beneficios para el cliente: {'; '.join(benefits)}"))
    lines += _section("Argumentos de venta:", _texts(profile.get("arguments")))
    lines += _section(DISCOVERY_HEADER, _texts(profile.get("discovery_questions")))
    recommendations = [
        _sentence(f"Si {when}: recomienda {recommend}")
        for rule in _dicts(profile.get("recommendations"))
        if (when := str(rule.get("when") or "").strip()) and (recommend := str(rule.get("recommend") or "").strip())
    ]
    lines += _section("Recomendaciones:", recommendations)
    lines += _section("Detalle de la oferta:", _offer_details(runtime))
    return lines


def _is_current(promotion: dict, today: date) -> bool:
    valid_until = str(promotion.get("valid_until") or "").strip()
    if not valid_until:
        return True
    try:
        return date.fromisoformat(valid_until) >= today
    except ValueError:
        return False  # Una fecha ilegible no se ofrece: nunca una promoción que podría estar vencida.


def _promotion_line(promotion: dict) -> str:
    name, details = str(promotion.get("name") or "").strip(), str(promotion.get("details") or "").strip()
    if not name or not details:
        return ""
    valid_until = str(promotion.get("valid_until") or "").strip()
    return f"{name}: {details} (válida hasta {valid_until})" if valid_until else f"{name}: {details}"


def _rule_lines(profile: dict, today: date) -> list[str]:
    """Cómo debe vender: en todos los turnos."""
    promotions = [line for promotion in _dicts(profile.get("promotions")) if _is_current(promotion, today) and (line := _promotion_line(promotion))]
    return _section("Instrucciones del negocio:", _texts(profile.get("instructions"))) + _section(PROMOTIONS_HEADER, promotions)


def build_business_profile_context(runtime: dict, *, include_facts: bool = True, today: date | None = None) -> str:
    """El bloque del perfil, o "" si no hay perfil o, en una conversación en curso, no hay reglas que recordar."""
    profile = business_profile(runtime)
    if not profile:
        return ""
    lines = (_fact_lines(profile, runtime) if include_facts else []) + _rule_lines(profile, today or date.today())
    return "\n".join([PROFILE_HEADER, *lines]) if lines else ""
