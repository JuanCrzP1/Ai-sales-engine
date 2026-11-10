"""«EL NEGOCIO»: quién es, qué promete, a quién se dirige, dónde, cuándo y cómo atiende, por qué le compran y cómo habla. Va en todos
los mensajes.

Sale del perfil comercial que compila el contrato (`config.profile`) y de la sección `business`. Los textos van completos: el contrato
limita su largo y el panel no deja escribir más.
"""
from __future__ import annotations

from app.domain.business_config.engine_policy import MAX_CUSTOMER_PROBLEMS, MAX_DESCRIPTION_CHARS, MAX_INDUSTRY_CHARS, MAX_VALUE_PROPOSITION_CHARS
from app.infrastructure.ai.prompting.text import as_dict, as_text, bounded_text, bullets, dicts, one_line, section, sentence, texts
from app.infrastructure.ai.prompting.view import PromptView
from app.infrastructure.ai.prompting.vocabulary import joined

HEADER = "EL NEGOCIO"
DEFAULT_TONE = "natural y claro"
_LOCATION_TYPES = {"virtual": "atención virtual", "fisico": "local físico", "mixto": "local físico y atención virtual"}
_SERVICE_MODES = {"virtual": "virtual", "presencial": "presencial", "domicilio": "a domicilio", "recoger": "para recoger", "envio": "con envío"}
_WEEKDAYS = ("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo")
_DAY_NAMES = {"miercoles": "miércoles", "sabado": "sábado"}
_FORMALITY = {
    "informal": "Trata al cliente de tú.",
    "neutral": "Usa un trato neutral: amable y respetuoso, sin demasiada confianza.",
    "formal": "Trata al cliente de usted.",
}
_EMOJIS = {True: "Puedes usar algún emoji, con moderación.", False: "No uses emojis."}


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


def _days(days: list[str]) -> str:
    """«lunes a viernes», «sábado y domingo», «lunes, miércoles y viernes»: tres o más días seguidos van como rango."""
    runs: list[list[int]] = []
    for index in sorted({_WEEKDAYS.index(day) for day in days if day in _WEEKDAYS}):
        if runs and index == runs[-1][1] + 1:
            runs[-1][1] = index
        else:
            runs.append([index, index])
    name = lambda index: _DAY_NAMES.get(_WEEKDAYS[index], _WEEKDAYS[index])  # noqa: E731
    parts = [f"{name(start)} a {name(end)}" if end - start >= 2 else ", ".join(name(i) for i in range(start, end + 1)) for start, end in runs]
    return joined(", ".join(parts).split(", "))


def _opening_hours(data: dict) -> str:
    entries = [
        f"{_days(texts(hours.get('days')))} de {as_text(hours.get('opens'))} a {as_text(hours.get('closes'))}"
        for hours in dicts(data.get("opening_hours"))
        if texts(hours.get("days")) and as_text(hours.get("opens")) and as_text(hours.get("closes"))
    ]
    return sentence(f"Horario de atención: {'; '.join(entries)}") if entries else ""


def _target_customer(business: dict) -> list[str]:
    target = as_dict(business.get("customer_profile"))
    segment, size = one_line(target.get("segment")), one_line(target.get("company_size"))
    if not segment:
        return []
    maturity, roles = one_line(target.get("maturity")), texts(target.get("roles"))
    return [
        sentence(f"Cliente ideal: {segment}" + (f" ({size})" if size else "")),
        sentence(f"Cómo suele llegar: {maturity}") if maturity else "",
        sentence(f"Quién suele escribir o decidir: {', '.join(roles)}") if roles else "",
    ]


def _style(view: PromptView, data: dict) -> list[str]:
    """Cómo habla: tono y largo, personalidad, trato, emojis y sus indicaciones."""
    voice = one_line(view.business.get("voice"))
    instructions = texts(data.get("style_instructions"))
    emojis = data.get("emojis")
    return [
        f"Tono: {tone(view)}. Responde en máximo {max_words(view)} palabras.",
        sentence(f"Personalidad de la marca: {voice}") if voice else "",
        _FORMALITY.get(as_text(data.get("formality")), ""),
        _EMOJIS[emojis] if isinstance(emojis, bool) else "",
        *(["Cómo te expresas:", *bullets(instructions)] if instructions else []),
    ]


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
    positioning, credibility = one_line(business.get("positioning")), texts(business.get("credibility"))
    lines = [
        sentence(f"Nombre: {name}" + (f" — {industry}" if industry else "")) if name else sentence(f"Sector: {industry}") if industry else "",
        sentence(f"Qué es: {description}") if description else "",
        sentence(f"Promesa: {promise}") if promise else "",
        sentence(f"Posicionamiento: {positioning}") if positioning else "",
        sentence(f"Lo que lo diferencia: {'; '.join(texts(data.get('differentiators')))}") if texts(data.get("differentiators")) else "",
        sentence(f"Pruebas de confianza: {'; '.join(credibility)}") if credibility else "",
        *_target_customer(business),
        *_location(as_dict(data.get("location"))),
        sentence(f"Cómo atiende: {', '.join(modes)}") if modes else "",
        _opening_hours(data),
        sentence(f"Por qué le compran: {' y '.join(reasons)}") if reasons else "",
        sentence(f"Problemas que resuelve: {'; '.join(problems)}") if problems else "",
        sentence(f"Beneficios para el cliente: {'; '.join(texts(data.get('benefits')))}") if texts(data.get("benefits")) else "",
        *(["Argumentos de venta:", *(f"- {one_line(item)}" for item in texts(data.get("arguments")))] if texts(data.get("arguments")) else []),
        *_style(view, data),
    ]
    return section(HEADER, lines)
