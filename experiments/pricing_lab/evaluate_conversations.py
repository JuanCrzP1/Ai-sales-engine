from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from lab_common import load_json, normalize_text, write_json


PRICE_PATTERNS = [
    r"\bprecio\b",
    r"\bcuesta\b",
    r"\bvale\b",
    r"\binversion\b",
    r"\bcop\b",
    r"\busd\b",
    r"\bmensual\b",
    r"\bmes\b",
    r"\bplan\b",
    r"\b\$\s*\d+",
    r"\b\d+[\.,]?\d*\s*(cop|usd|eur|mxn)\b",
]
INCLUDES_PATTERNS = [
    r"\bincluye\b",
    r"\bte incluye\b",
    r"\bvas a tener\b",
    r"\bacceso\b",
    r"\bautomatiza\b",
    r"\bseguimiento\b",
    r"\bagentes?\b",
    r"\brespuestas?\b",
    r"\bsoporte\b",
]
NOT_INCLUDES_PATTERNS = [
    r"\bno incluye\b",
    r"\bno esta incluido\b",
    r"\bno cubre\b",
    r"\bno contempla\b",
    r"\baparte\b",
    r"\badicional\b",
    r"\bextra\b",
    r"\blimita\b",
]
ROI_PATTERNS = [
    r"\bretorno\b",
    r"\broi\b",
    r"\brecuper\w+\b",
    r"\bmas ventas\b",
    r"\bvender mas\b",
    r"\bahorr\w+\b",
    r"\bconversion\b",
    r"\boportunidades\b",
    r"\bclientes\b",
    r"\bingresos\b",
]
CTA_PATTERNS = [
    r"\bquieres que\b",
    r"\bte activo\b",
    r"\bempezamos\b",
    r"\bempezar\b",
    r"\bsiguiente paso\b",
    r"\bagend\w+\b",
    r"\bprueba\b",
    r"\bactivar\b",
    r"\blink\b",
    r"\bpagar\b",
    r"\bte comparto\b",
]
OBJECTION_PATTERNS = [
    r"\bentiendo\b",
    r"\bcaro\b",
    r"\binversion\b",
    r"\bsi te sirve\b",
    r"\bsi lo aprovech\w+\b",
    r"\bvale la pena\b",
    r"\bretorno\b",
    r"\bahorro\b",
]
CLOSING_PATTERNS = [
    r"\barranc\w+\b",
    r"\bempez\w+\b",
    r"\bactivar\b",
    r"\bcontratar\b",
    r"\bpaso\b",
    r"\blink\b",
    r"\bpago\b",
    r"\bimplement\w+\b",
    r"\bte dejo listo\b",
]


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(__import__("re").search(pattern, text) for pattern in patterns)


def evaluate_turn(*, turn_number: int, user_message: str, assistant_reply: str) -> dict[str, Any]:
    normalized_user = normalize_text(user_message)
    normalized_reply = normalize_text(assistant_reply)

    price = _matches_any(normalized_reply, PRICE_PATTERNS)
    includes = _matches_any(normalized_reply, INCLUDES_PATTERNS)
    not_includes = _matches_any(normalized_reply, NOT_INCLUDES_PATTERNS)
    roi = _matches_any(normalized_reply, ROI_PATTERNS)
    cta = _matches_any(normalized_reply, CTA_PATTERNS) or normalized_reply.endswith("?")
    objection = _matches_any(normalized_reply, OBJECTION_PATTERNS) and (
        "caro" in normalized_user or roi or cta
    )
    closing_progress = _matches_any(normalized_reply, CLOSING_PATTERNS) and (cta or price or roi)

    notes: list[str] = []
    if turn_number == 7 and not price:
        notes.append("No respondió precio en el turno esperado.")
    if turn_number == 8 and not includes:
        notes.append("No aterrizó claramente lo que incluye.")
    if turn_number == 9 and not not_includes:
        notes.append("No delimitó lo que no incluye.")
    if turn_number == 10 and not objection:
        notes.append("No manejó la objeción de precio con suficiente claridad.")
    if turn_number >= 5 and not cta:
        notes.append("Falta avance explícito al siguiente paso.")

    return {
        "turn": turn_number,
        "user_message": user_message,
        "assistant_reply": assistant_reply,
        "price": price,
        "includes": includes,
        "not_includes": not_includes,
        "roi": roi,
        "cta": cta,
        "objection_handling": objection,
        "closing_progress": closing_progress,
        "notes": notes,
    }


def score_conversation(turns: list[dict[str, Any]]) -> tuple[dict[str, int], int, str]:
    relevant = {item.get("turn"): item for item in turns}
    score = 0

    turn7 = relevant.get(7, {})
    turn8 = relevant.get(8, {})
    turn9 = relevant.get(9, {})
    turn10 = relevant.get(10, {})

    if turn7.get("price"):
        score += 15
    if turn8.get("includes"):
        score += 10
    if turn9.get("not_includes"):
        score += 10
    if any(item.get("roi") for item in turns if int(item.get("turn", 0)) >= 5):
        score += 15
    if any(item.get("cta") for item in turns if int(item.get("turn", 0)) >= 4):
        score += 15
    if turn10.get("objection_handling"):
        score += 15
    if any(item.get("closing_progress") for item in turns if int(item.get("turn", 0)) >= 6):
        score += 20

    metrics = {
        "price_turns": sum(1 for item in turns if item.get("price")),
        "includes_turns": sum(1 for item in turns if item.get("includes")),
        "not_includes_turns": sum(1 for item in turns if item.get("not_includes")),
        "roi_turns": sum(1 for item in turns if item.get("roi")),
        "cta_turns": sum(1 for item in turns if item.get("cta")),
        "objection_turns": sum(1 for item in turns if item.get("objection_handling")),
        "closing_progress_turns": sum(1 for item in turns if item.get("closing_progress")),
    }

    if score >= 80:
        verdict = "Mejora comercial fuerte"
    elif score >= 60:
        verdict = "Señal comercial aceptable"
    elif score >= 40:
        verdict = "Cobertura comercial parcial"
    else:
        verdict = "Cobertura comercial débil"

    return metrics, score, verdict


def enrich_metrics_payload(payload: dict[str, Any]) -> dict[str, Any]:
    turns = payload.get("conversation") if isinstance(payload.get("conversation"), list) else []
    evaluated_turns = [
        evaluate_turn(
            turn_number=int(item.get("turn", 0)),
            user_message=str(item.get("user_message", "")),
            assistant_reply=str(item.get("assistant_reply", "")),
        )
        for item in turns
    ]
    behavior_metrics, score, verdict = score_conversation(evaluated_turns)
    payload["turn_evaluations"] = evaluated_turns
    payload["behavior_metrics"] = behavior_metrics
    payload["commercial_score"] = score
    payload["verdict"] = verdict
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Evalúa conversaciones ya almacenadas en metrics.json")
    parser.add_argument("--input", required=True, help="Ruta al archivo metrics.json")
    args = parser.parse_args()

    path = Path(args.input).resolve()
    payload = load_json(path)
    if not payload:
        raise SystemExit(f"No se encontró contenido válido en {path}")

    write_json(path, enrich_metrics_payload(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
