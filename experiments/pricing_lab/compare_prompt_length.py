from __future__ import annotations

from lab_common import CANONICAL_RESULT_FILES, load_json


def main() -> int:
    baseline = load_json(CANONICAL_RESULT_FILES["baseline_metrics"])
    candidate = load_json(CANONICAL_RESULT_FILES["candidate_metrics"])
    if not baseline.get("prompt_metrics"):
        raise SystemExit("Falta snapshot baseline. Corre generate_prompt_snapshot.py --label baseline primero.")

    baseline_metrics = baseline.get("prompt_metrics", {})
    candidate_metrics = candidate.get("prompt_metrics", {}) if candidate.get("prompt_metrics") else None

    print(f"{'metric':<25} {'baseline':>10} {'candidate':>12} {'delta':>8}")
    print("-" * 58)
    for key in ("chars", "lines", "estimated_tokens", "pricing_block_chars"):
        base_value = int(baseline_metrics.get(key, 0))
        if candidate_metrics is not None:
            candidate_value = int(candidate_metrics.get(key, 0))
            delta = candidate_value - base_value
            sign = "+" if delta > 0 else ""
            print(f"{key:<25} {base_value:>10} {candidate_value:>12} {sign}{delta:>7}")
        else:
            print(f"{key:<25} {base_value:>10} {'(pendiente)':>12} {'n/a':>8}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
