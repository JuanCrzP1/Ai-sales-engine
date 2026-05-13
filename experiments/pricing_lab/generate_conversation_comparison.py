from __future__ import annotations

from lab_common import CANONICAL_RESULT_FILES, ensure_results_scaffold, load_json, yes_no


def _summary_line(name: str, baseline_value: int, candidate_value: int) -> str:
    delta = candidate_value - baseline_value
    sign = "+" if delta > 0 else ""
    return f"- {name}: baseline={baseline_value}, candidate={candidate_value}, delta={sign}{delta}"


def main() -> int:
    ensure_results_scaffold()
    baseline = load_json(CANONICAL_RESULT_FILES["baseline_metrics"])
    candidate = load_json(CANONICAL_RESULT_FILES["candidate_metrics"])

    if not baseline.get("conversation"):
        raise SystemExit("Falta baseline con conversación ejecutada. Corre run_golden_conversations.py --label baseline primero.")

    baseline_turns = baseline.get("turn_evaluations") if isinstance(baseline.get("turn_evaluations"), list) else []
    candidate_turns = candidate.get("turn_evaluations") if isinstance(candidate.get("turn_evaluations"), list) else []

    # Modo parcial: candidate aún no ejecutado
    candidate_only_baseline = not candidate.get("conversation")
    if candidate_only_baseline:
        empty_turn = {
            "turn": 0,
            "user_message": "",
            "assistant_reply": "Pendiente. Ejecuta run_golden_conversations.py --label candidate_v1.",
            "price": False,
            "includes": False,
            "not_includes": False,
            "roi": False,
            "cta": False,
            "objection_handling": False,
            "closing_progress": False,
        }
        candidate_turns = [
            {**empty_turn, "turn": item.get("turn", i + 1), "user_message": item.get("user_message", "")}
            for i, item in enumerate(baseline_turns)
        ]

    def _metric_line(name: str, baseline_value: int, candidate_value: int | None) -> str:
        if candidate_value is None:
            return f"- {name}: baseline={baseline_value}, candidate=(pendiente)"
        delta = candidate_value - baseline_value
        sign = "+" if delta > 0 else ""
        return f"- {name}: baseline={baseline_value}, candidate={candidate_value}, delta={sign}{delta}"

    c_prompt = candidate.get("prompt_metrics", {}) if not candidate_only_baseline else None
    c_score = candidate.get("commercial_score") if not candidate_only_baseline else None

    sections = [
        "# Comparación conversacional",
        "",
        f"- baseline: {baseline.get('label', 'baseline')} | score={baseline.get('commercial_score', 0)}",
        f"- candidate: {candidate.get('label', 'candidate') if not candidate_only_baseline else '(pendiente)'}",
        "",
        "## Métricas del prompt",
        _metric_line("chars", int(baseline.get("prompt_metrics", {}).get("chars", 0)), int(c_prompt.get("chars", 0)) if c_prompt else None),
        _metric_line("lines", int(baseline.get("prompt_metrics", {}).get("lines", 0)), int(c_prompt.get("lines", 0)) if c_prompt else None),
        _metric_line("estimated_tokens", int(baseline.get("prompt_metrics", {}).get("estimated_tokens", 0)), int(c_prompt.get("estimated_tokens", 0)) if c_prompt else None),
        _metric_line("pricing_block_chars", int(baseline.get("prompt_metrics", {}).get("pricing_block_chars", 0)), int(c_prompt.get("pricing_block_chars", 0)) if c_prompt else None),
        "",
        "## Score comercial",
        _metric_line("commercial_score", int(baseline.get("commercial_score", 0)), int(c_score) if c_score is not None else None),
        "",
    ]

    for baseline_item, candidate_item in zip(baseline_turns, candidate_turns):
        turn_number = int(baseline_item.get("turn", 0))
        user_message = str(baseline_item.get("user_message", ""))
        sections.extend(
            [
                f"# Turno {turn_number} — {user_message}",
                "",
                "## Baseline",
                str(baseline_item.get("assistant_reply", "")).strip() or "Sin respuesta.",
                "",
                "## Candidate",
                str(candidate_item.get("assistant_reply", "")).strip() or "Sin respuesta.",
                "",
                "### Evaluación automática",
                f"- Precio: {yes_no(bool(candidate_item.get('price')))}",
                f"- Incluye: {yes_no(bool(candidate_item.get('includes')))}",
                f"- No incluye: {yes_no(bool(candidate_item.get('not_includes')))}",
                f"- ROI: {yes_no(bool(candidate_item.get('roi')))}",
                f"- CTA: {yes_no(bool(candidate_item.get('cta')))}",
                f"- Manejo de objeciones: {yes_no(bool(candidate_item.get('objection_handling')))}",
                f"- Avance al cierre: {yes_no(bool(candidate_item.get('closing_progress')))}",
                "",
                "### Veredicto Manual",
                "- [ ] Mejoró",
                "- [ ] Igual",
                "- [ ] Empeoró",
                "",
            ]
        )

    CANONICAL_RESULT_FILES["comparison"].write_text("\n".join(sections).strip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
