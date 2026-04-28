from __future__ import annotations


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
        "usar",
        "tener",
        "lograr",
        "hacer",
        "gestionar",
    ]

    has_outcome = any(s in t for s in outcome_signals)
    has_action = any(a in t for a in action_signals)

    return has_outcome or (has_action and is_not_passive(t))
