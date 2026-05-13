"""
compare_prompt_length.py
────────────────────────
Compara métricas de longitud y señal comercial entre dos archivos de prompt:
el baseline y un candidato generado por una versión experimental.

Uso:
    python experiments/phase_1_pricing_audit/compare_prompt_length.py
    python experiments/phase_1_pricing_audit/compare_prompt_length.py --candidate results/candidate_prompt.txt

El script NO modifica ningún archivo de producción.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_DIR = REPO_ROOT / "project"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
sys.path.insert(0, str(PROJECT_DIR))


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _extract_pricing_block(prompt: str) -> str:
    lines = prompt.splitlines()
    in_block = False
    block_lines: list[str] = []
    for line in lines:
        if line.strip().startswith("PRICING:"):
            in_block = True
        if in_block:
            block_lines.append(line)
    return "\n".join(block_lines)


def _measure(text: str, label: str) -> dict:
    pricing = _extract_pricing_block(text)
    return {
        "label": label,
        "chars": len(text),
        "lines": len(text.splitlines()),
        "estimated_tokens": _estimate_tokens(text),
        "pricing_block_chars": len(pricing),
        "pricing_block_lines": len(pricing.splitlines()),
        "has_includes": "Incluye:" in pricing,
        "has_not_included": "No incluye:" in pricing,
        "has_price_framing": "Framing" in pricing or "Valor:" in pricing,
        "has_roi_hints": "Retorno esperado:" in pricing,
    }


def _delta(a: int, b: int) -> str:
    diff = b - a
    sign = "+" if diff > 0 else ""
    return f"{sign}{diff}"


def _bool_delta(a: bool, b: bool) -> str:
    if a == b:
        return "igual"
    return "✓ mejorado" if b and not a else "✗ regresión"


def _print_comparison(baseline: dict, candidate: dict) -> None:
    print("\n══ COMPARACIÓN DE PROMPTS ══════════════════════════════════")
    print(f"  {'Métrica':<28} {'Baseline':>10} {'Candidato':>10} {'Delta':>8}")
    print(f"  {'-'*60}")

    int_fields = [
        ("chars",               "Chars totales"),
        ("lines",               "Líneas totales"),
        ("estimated_tokens",    "Tokens estimados"),
        ("pricing_block_chars", "PRICING chars"),
        ("pricing_block_lines", "PRICING líneas"),
    ]
    for key, label in int_fields:
        b_val = baseline[key]
        c_val = candidate[key]
        d = _delta(b_val, c_val)
        warn = " ⚠" if key in ("chars", "estimated_tokens") and c_val > b_val + 50 else ""
        print(f"  {label:<28} {b_val:>10} {c_val:>10} {d:>8}{warn}")

    print()
    bool_fields = [
        ("has_includes",      "has_includes"),
        ("has_not_included",  "has_not_included"),
        ("has_price_framing", "has_price_framing"),
        ("has_roi_hints",     "has_roi_hints"),
    ]
    for key, label in bool_fields:
        b_val = baseline[key]
        c_val = candidate[key]
        status = _bool_delta(b_val, c_val)
        print(f"  {label:<28} {str(b_val):>10} {str(c_val):>10}   {status}")

    print("══════════════════════════════════════════════════════════")

    # Veredicto
    prompt_ok = candidate["chars"] <= baseline["chars"] + 50
    includes_ok = candidate["has_includes"]
    not_included_ok = candidate["has_not_included"]
    approved = prompt_ok and includes_ok and not_included_ok

    print("\n── VEREDICTO ──")
    print(f"  Prompt no creció materialmente: {'✓' if prompt_ok else '✗'}")
    print(f"  has_includes = true:             {'✓' if includes_ok else '✗'}")
    print(f"  has_not_included = true:         {'✓' if not_included_ok else '✗'}")
    print(f"\n  {'✅ APROBADO para pasar a producción' if approved else '❌ NO aprobado — revisar métricas'}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Compara dos prompts: baseline vs candidato.")
    parser.add_argument(
        "--baseline",
        default=str(RESULTS_DIR / "baseline_prompt.txt"),
        help="Ruta al prompt baseline (default: results/baseline_prompt.txt)",
    )
    parser.add_argument(
        "--candidate",
        default=str(RESULTS_DIR / "candidate_prompt.txt"),
        help="Ruta al prompt candidato (default: results/candidate_prompt.txt)",
    )
    args = parser.parse_args()

    baseline_path = Path(args.baseline)
    candidate_path = Path(args.candidate)

    if not baseline_path.exists():
        print(f"ERROR: baseline no encontrado en {baseline_path}")
        print("Ejecuta primero: python experiments/phase_1_pricing_audit/generate_prompt_snapshot.py")
        sys.exit(1)

    if not candidate_path.exists():
        print(f"ERROR: candidato no encontrado en {candidate_path}")
        print("Genera el candidato con una versión modificada de generate_prompt_snapshot.py")
        sys.exit(1)

    baseline_text = baseline_path.read_text(encoding="utf-8")
    candidate_text = candidate_path.read_text(encoding="utf-8")

    baseline_m = _measure(baseline_text, "baseline")
    candidate_m = _measure(candidate_text, "candidato")

    _print_comparison(baseline_m, candidate_m)

    # Guardar comparación en JSON
    comparison = {"baseline": baseline_m, "candidate": candidate_m}
    out_path = RESULTS_DIR / "comparison_result.json"
    out_path.write_text(json.dumps(comparison, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Comparación guardada en: {out_path}")


if __name__ == "__main__":
    main()
