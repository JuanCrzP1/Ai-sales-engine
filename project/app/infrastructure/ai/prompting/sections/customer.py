"""«EL CLIENTE: QUÉ LO MUEVE Y QUÉ LO FRENA»: la estrategia avanzada del negocio sobre su cliente. Cómo describe sus problemas, cómo
reconocer cada problema y qué le cuesta, los casos típicos, sus motivos de compra y cómo responder cuando duda.

Las frases del negocio van entre comillas: son ideas para que la IA las diga con sus palabras, no un guion. «EL NEGOCIO» ya trae el
primer impacto de cada problema; aquí va el detalle completo. Si todo cabe en `CUSTOMER_PROMPT_MAX_CHARS`, va todo; si no, lo más
relacionado con lo que dice el cliente (`relevance.py`).
"""
from __future__ import annotations

from app.domain.business_config.engine_policy import CUSTOMER_PROMPT_MAX_CHARS
from app.infrastructure.ai.prompting import relevance
from app.infrastructure.ai.prompting.text import as_dict, as_text, dedupe, readable, section, sentence, texts
from app.infrastructure.ai.prompting.view import PromptView
from app.infrastructure.ai.prompting.vocabulary import OBJECTIONS, quoted, said

HEADER = "EL CLIENTE: QUÉ LO MUEVE Y QUÉ LO FRENA"
_URGENCY = (("alto", "Si es urgente"), ("medio", "Si no es tan urgente"), ("bajo", "Si no tiene prisa"))
# Cómo responder una objeción, por capas (`sales.objections[]`): una línea por capa, para que una objeción larga no quede fuera entera.
_LAYERS = (("acknowledge", "Reconócelo"), ("reframe", "Replantéalo"), ("proof", "Da una prueba"), ("redirect", "Vuelve al siguiente paso"))
Entry = tuple[str | None, str]


def _problem(problem_id: str, cluster: dict, solutions: list[str]) -> str:
    urgency = as_dict(cluster.get("urgency_levels"))
    parts = [
        f"lo notas si dice {quoted(texts(cluster.get('signals')))}" if texts(cluster.get("signals")) else "",
        f"le pasa esto: {'; '.join(texts(cluster.get('impacts')))}" if texts(cluster.get("impacts")) else "",
        f"le cuesta: {'; '.join(texts(cluster.get('monetization')))}" if texts(cluster.get("monetization")) else "",
        f"se resuelve con: {', '.join(readable(item) for item in solutions)}" if solutions else "",
        *(f"{label.lower()}: {quoted(texts(urgency.get(level)))}" for level, label in _URGENCY if texts(urgency.get(level))),
        f"háblale desde: {', '.join(readable(item) for item in texts(cluster.get('recommended_angles')))}" if texts(cluster.get("recommended_angles")) else "",
    ]
    return sentence(f"{readable(problem_id)}: {'; '.join(part for part in parts if part)}") if any(parts) else ""


def _problems(view: PromptView) -> list[str]:
    clusters = as_dict(as_dict(view.sales.get("pain")).get("clusters"))
    mapping = as_dict(as_dict(view.sales.get("solution")).get("mapping"))
    return [line for problem_id, cluster in clusters.items() if (line := _problem(str(problem_id), as_dict(cluster), texts(mapping.get(problem_id))))]


def _use_cases(view: PromptView) -> list[str]:
    lines = []
    for case in [as_dict(item) for item in view.business.get("use_cases") or []]:
        name, approach, signals = as_text(case.get("nombre") or case.get("name")), as_text(case.get("enfoque") or case.get("approach")), texts(case.get("senales") or case.get("signals"))
        if name and (approach or signals):
            when = f"si dice {quoted(signals)}, " if signals else ""
            lines.append(sentence(f"{name}: {when}enfócate en {readable(approach)}" if approach else f"{name}: {when.rstrip(', ')}"))
    return lines


def _motivations(view: PromptView) -> list[str]:
    drivers, angles = as_dict(view.business.get("value_drivers")), as_dict(view.sales.get("angles"))
    lines = []
    for motive in dedupe([*map(str, drivers), *map(str, angles)]):
        driver, angle = as_dict(drivers.get(motive)), as_dict(angles.get(motive))
        signals = dedupe([*texts(driver.get("triggers")), *texts(angle.get("when"))])
        parts = [
            as_text(driver.get("description")),
            f"lo notas si dice {quoted(signals)}" if signals else "",
            f"cómo hablarle: {quoted(texts(angle.get('execution')))}" if texts(angle.get("execution")) else "",
        ]
        if any(parts):
            lines.append(sentence(f"{readable(motive)}: {'; '.join(part for part in parts if part)}"))
    return lines


def _objections(view: PromptView) -> list[Entry]:
    """Cada objeción es un grupo («Si duda por el precio…») con una línea por capa y por regla."""
    entries: list[Entry] = []
    for topic, objection in as_dict(view.sales.get("objection")).items():
        objection = as_dict(objection)
        layers = as_dict(objection.get("layers"))
        title = f"Si duda por {said(topic, OBJECTIONS)} (ideas del negocio; dilas con tus palabras):"
        entries += [(title, f"{verb}: {quoted(texts(layers.get(key)))}") for key, verb in _LAYERS if texts(layers.get(key))]
        entries += [(title, sentence(f"Regla: {rule}")) for rule in texts(objection.get("hard_rules"))]
    return entries


def render(view: PromptView) -> str:
    pain_points = texts(view.business.get("pain_points"))
    blocks = (("Problemas que trae:", _problems(view)), ("Casos típicos:", _use_cases(view)), ("Motivos de compra:", _motivations(view)))
    entries: list[Entry] = [(None, sentence(f"Así describe sus problemas: {'; '.join(pain_points)}"))] if pain_points else []
    entries += [(title, item) for title, items in blocks for item in items]
    entries += _objections(view)
    return section(HEADER, relevance.grouped_lines(entries, query=view.relevance_query, max_chars=CUSTOMER_PROMPT_MAX_CHARS))
