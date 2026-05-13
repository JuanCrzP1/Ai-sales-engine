"""
generate_prompt_snapshot.py
───────────────────────────
Genera el prompt real del tenant asesor_ai_prod en escenarios representativos
y guarda el resultado en results/baseline_prompt.txt y results/baseline_metrics.json.

Uso:
    python experiments/phase_1_pricing_audit/generate_prompt_snapshot.py

El script NO modifica ningún archivo de producción.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ── path setup ────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_DIR = REPO_ROOT / "project"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
sys.path.insert(0, str(PROJECT_DIR))

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ── imports ───────────────────────────────────────────────────────────────────
from app.application.runtime import load_tenant_runtime_yaml  # noqa: E402
from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService  # noqa: E402

TENANT = "asesor_ai_prod"
SCENARIOS = [
    ("new",    "¿Qué precio tiene?"),
    ("active", "¿Qué precio tiene?"),
    ("active", "¿Qué incluye?"),
    ("active", "Está caro."),
]


def _build_prompt(state: str, message: str) -> str:
    runtime = load_tenant_runtime_yaml(TENANT, extra_yaml={"conversation_state": state})
    builder = PromptBuilderService()
    prompt, _, _ = builder.build(
        client_config_id=TENANT,
        user_message=message,
        yaml_config=runtime,
        faq_results=[],
        progression_rules=None,
    )
    return str(prompt or "")


def _extract_pricing_block(prompt: str) -> str:
    """Extrae únicamente el bloque PRICING: del prompt."""
    lines = prompt.splitlines()
    in_block = False
    block_lines: list[str] = []
    for line in lines:
        if line.strip().startswith("PRICING:"):
            in_block = True
        if in_block:
            block_lines.append(line)
    return "\n".join(block_lines)


def _estimate_tokens(text: str) -> int:
    """Estimación simple: ~4 chars por token (aproximación GPT)."""
    return max(1, len(text) // 4)


def main() -> None:
    print(f"Tenant: {TENANT}")
    print(f"Resultados en: {RESULTS_DIR}\n")

    all_snapshots: list[str] = []
    metrics_by_scenario: list[dict] = []

    for state, message in SCENARIOS:
        label = f"[state={state}] {message}"
        print(f"Generando: {label}")
        prompt = _build_prompt(state, message)
        pricing_block = _extract_pricing_block(prompt)

        snapshot_header = f"\n{'='*60}\nEscenario: {label}\n{'='*60}\n"
        all_snapshots.append(snapshot_header + prompt)

        metrics_by_scenario.append({
            "scenario": label,
            "chars": len(prompt),
            "lines": len(prompt.splitlines()),
            "estimated_tokens": _estimate_tokens(prompt),
            "pricing_block_chars": len(pricing_block),
            "pricing_block_lines": len(pricing_block.splitlines()),
            "has_includes": "Incluye:" in pricing_block,
            "has_not_included": "No incluye:" in pricing_block,
            "has_price_framing": "Framing" in pricing_block or "Valor:" in pricing_block,
            "has_roi_hints": "Retorno esperado:" in pricing_block,
        })

    # Escenario principal para el snapshot base: active + "¿Qué precio tiene?"
    main_prompt = _build_prompt("active", "¿Qué precio tiene?")
    main_pricing = _extract_pricing_block(main_prompt)

    baseline_metrics = {
        "tenant": TENANT,
        "scenario": "active / ¿Qué precio tiene?",
        "chars": len(main_prompt),
        "lines": len(main_prompt.splitlines()),
        "estimated_tokens": _estimate_tokens(main_prompt),
        "pricing_block_chars": len(main_pricing),
        "pricing_block_lines": len(main_pricing.splitlines()),
        "has_includes": "Incluye:" in main_pricing,
        "has_not_included": "No incluye:" in main_pricing,
        "has_price_framing": "Framing" in main_pricing or "Valor:" in main_pricing,
        "has_roi_hints": "Retorno esperado:" in main_pricing,
        "scenarios": metrics_by_scenario,
    }

    # Guardar prompt
    snapshot_path = RESULTS_DIR / "baseline_prompt.txt"
    snapshot_path.write_text("\n".join(all_snapshots), encoding="utf-8")
    print(f"\nPrompt guardado en: {snapshot_path}")

    # Guardar métricas
    metrics_path = RESULTS_DIR / "baseline_metrics.json"
    metrics_path.write_text(json.dumps(baseline_metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Métricas guardadas en: {metrics_path}")

    # Resumen en consola
    print("\n── RESUMEN BASELINE ──────────────────────────────────")
    print(f"  Chars totales del prompt:    {baseline_metrics['chars']}")
    print(f"  Líneas totales:              {baseline_metrics['lines']}")
    print(f"  Tokens estimados:            {baseline_metrics['estimated_tokens']}")
    print(f"  Bloque PRICING chars:        {baseline_metrics['pricing_block_chars']}")
    print(f"  Bloque PRICING líneas:       {baseline_metrics['pricing_block_lines']}")
    print(f"  has_includes:                {baseline_metrics['has_includes']}")
    print(f"  has_not_included:            {baseline_metrics['has_not_included']}")
    print(f"  has_price_framing:           {baseline_metrics['has_price_framing']}")
    print(f"  has_roi_hints:               {baseline_metrics['has_roi_hints']}")
    print("──────────────────────────────────────────────────────")


if __name__ == "__main__":
    main()
