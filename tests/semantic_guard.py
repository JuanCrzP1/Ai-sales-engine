from __future__ import annotations

import re

def normalize(text: str) -> str:
    return (text or "").lower().strip()


def is_not_passive(text: str) -> bool:
    passive = [
        "si quieres",
        "si deseas",
        "puedo ayudarte",
        "avísame",
        "cuando quieras",
    ]
    return not any(p in text for p in passive)


def has_forward_intent(text: str) -> bool:
    t = normalize(text)

    outcome_signals = [
        "puedes",
        "te permite",
        "con esto",
        "ya puedes",
        "así puedes",
    ]

    action_signals = [
        "empez",
        "avanz",
        "avanc",
        "usar",
        "tener",
        "lograr",
        "hacer",
        "gestionar",
    ]

    has_outcome = any(s in t for s in outcome_signals)
    has_action = any(a in t for a in action_signals)

    return has_outcome or (has_action and is_not_passive(t))


def talks_about_price(text: str) -> bool:
    """True si la respuesta aborda el tema de precio o costo en cualquier forma natural."""
    t = normalize(text)
    price_tokens = [
        "cop", "$", "precio", "vale", "costo", "valor",
        "tarifa", "inversión", "inversion", "mensual",
        "implementación", "implementacion", "cobr", "pag",
        "cuánto", "cuanto",
    ]
    return any(token in t for token in price_tokens) or bool(
        re.search(r"\b\d[\d.]*,\d{3}\b", t)
    )
