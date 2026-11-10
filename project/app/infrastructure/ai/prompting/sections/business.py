"""«EL NEGOCIO»: quién es, qué promete, dónde y cómo atiende, por qué le compran y cómo habla. Va en todos los mensajes.

Sale del perfil comercial que compila el contrato (`config.profile`) y de la sección `business`. Los textos van completos: el contrato
limita su largo y el panel no deja escribir más.
"""
from __future__ import annotations

from app.domain.business_config.engine_policy import MAX_CUSTOMER_PROBLEMS, MAX_DESCRIPTION_CHARS, MAX_INDUSTRY_CHARS, MAX_VALUE_PROPOSITION_CHARS
from app.infrastructure.ai.prompting.text import as_dict, as_text, bounded_text, dicts, one_line, section, sentence, texts
from app.infrastructure.ai.prompting.view import PromptView

HEADER = "EL NEGOCIO"
DEFAULT_TONE = "natural y claro"
_LOCATION_TYPES = {"virtual": "atención virtual", "fisico": "local físico", "mixto": "local físico y atención virtual"}
_SERVICE_MODES = {"virtual": "virtual", "presencial": "presencial", "domicilio": "a domicilio", "recoger": "para recoger", "envio": "con envío"}


def profile(view: PromptView) -> dict:
    """El perfil comercial compilado desde el contrato."""
    return as_dict(view.config.get("profile"))


def tone(view: PromptView) -> str:
    return as_text(profile(view).get("tone")) or DEFAULT_TONE


def max_words(view: PromptView) -> int:
    response = as_dict(view.config.get("response"))
    try:
        return max(20, int(view.runtime.get("response_max_words") or response.get("max_words") or 80))
    except (TypeError, ValueError):
        return 80


def _location(location: dict) -> list[str]:
    kind = as_text(location.get("type"))
    if not kind:
        return []
    place = ", ".join(texts([location.get("address"), location.get("city")]))
    where = _LOCATION_TYPES.get(kind, kind)
    lines = [sentence(f"Dónde atiende: {where}; {place}" if place else f"Dónde atiende: {where}")]
    coverage = as_dict(location.get("coverage"))
    scope = as_text(coverage.get("type"))
    if scope:
        zones = ", ".join(texts(coverage.get("zones")))
        lines.append(sentence(f"Cobertura {scope}: {zones}" if zones else f"Cobertura {scope}"))
    return lines


def _customer_problems(sales: dict, business: dict) -> list[str]:
    """El primer impacto de cada problema del cliente o, si no hay, los casos de uso (de la venta o, si no, del negocio)."""
    impacts = []
    for cluster in as_dict(as_dict(sales.get("pain")).get("clusters")).values():
        first = next(iter(texts(as_dict(cluster).get("impacts"))), "")
        if first:
            impacts.append(first)
        if len(impacts) >= MAX_CUSTOMER_PROBLEMS:
            break
    if impacts:
        return impacts
    use_cases = dicts(sales.get("use_cases")) or dicts(business.get("use_cases"))
    return [name for item in use_cases[:MAX_CUSTOMER_PROBLEMS] if (name := as_text(item.get("nombre") or item.get("name")))]


def render(view: PromptView) -> str:
    business, data = view.business, profile(view)
    name = as_text(data.get("name")) or as_text(business.get("name"))
    industry = bounded_text(business.get("industry"), max_chars=MAX_INDUSTRY_CHARS)
    description = bounded_text(data.get("description") or business.get("description"), max_chars=MAX_DESCRIPTION_CHARS)
    promise = bounded_text(business.get("promise"), max_chars=MAX_VALUE_PROPOSITION_CHARS)
    motivations = as_dict(view.sales.get("buying_motivation")) or as_dict(business.get("buying_motivation"))
    reasons = [text for text in (as_text(motivations.get("primary")), as_text(motivations.get("secondary"))) if text]
    modes = [_SERVICE_MODES.get(mode, mode) for mode in texts(data.get("service_modes"))]
    problems = _customer_problems(view.sales, business)
    lines = [
        sentence(f"Nombre: {name}" + (f" — {industry}" if industry else "")) if name else sentence(f"Sector: {industry}") if industry else "",
        sentence(f"Qué es: {description}") if description else "",
        sentence(f"Promesa: {promise}") if promise else "",
        sentence(f"Lo que lo diferencia: {'; '.join(texts(data.get('differentiators')))}") if texts(data.get("differentiators")) else "",
        *_location(as_dict(data.get("location"))),
        sentence(f"Cómo atiende: {', '.join(modes)}") if modes else "",
        sentence(f"Por qué le compran: {' y '.join(reasons)}") if reasons else "",
        sentence(f"Problemas que resuelve: {'; '.join(problems)}") if problems else "",
        sentence(f"Beneficios para el cliente: {'; '.join(texts(data.get('benefits')))}") if texts(data.get("benefits")) else "",
        *(["Argumentos de venta:", *(f"- {one_line(item)}" for item in texts(data.get("arguments")))] if texts(data.get("arguments")) else []),
        f"Tono: {tone(view)}. Responde en máximo {max_words(view)} palabras.",
    ]
    return section(HEADER, lines)
