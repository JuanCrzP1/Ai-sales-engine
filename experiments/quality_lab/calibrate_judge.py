"""¿Un juez barato califica como el exigente? Se comprueba antes de usarlo, con conversaciones ya guardadas (sin repetirlas).

Cada juez califica las mismas conversaciones con la misma ficha; se compara con el de referencia: diferencia promedio por respuesta y,
sobre todo, si detecta las mismas respuestas con fallas (las que el de referencia no califica con 10).

    python experiments/quality_lab/calibrate_judge.py --experiment exp_20261110_calidad_prompt_v2 \\
        --reference openai/gpt-4.1 --candidates deepseek/deepseek-chat-v3.1,google/gemini-2.5-flash --tenants restaurant,saas,clinic,tienda_ropa
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import dotenv_values

LAB = Path(__file__).resolve().parent
REPO = LAB.parents[1]
sys.path[:0] = [str(LAB), str(REPO / "project")]
os.environ.update({"MODE": "test", "DATABASE_URL": "sqlite:///:memory:"})

import costs  # noqa: E402
from judge import CRITERIA, score_conversation  # noqa: E402

ESTIMATED_TOKENS = costs.RUBRIC_TOKENS


def _facts(slug: str) -> dict:
    """La ficha del negocio con el código actual, armada desde sus YAML de ejemplo (sin almacén ni datos de pago)."""
    import logging

    logging.disable(logging.CRITICAL)
    from app.application.runtime import runtime_from_sections
    from app.domain.business_config.compiler import compile_business_config
    from app.domain.business_config.contract import BusinessConfig
    from app.domain.business_config.engine_settings import EngineSettings
    from app.infrastructure.ai.prompting.business_model import detect_business_model
    from app.infrastructure.business_config.example_businesses import load_example
    from facts import business_facts

    tenant = load_example(slug)
    config = BusinessConfig.model_validate(tenant.document).with_engine_settings(EngineSettings.model_validate(tenant.engine_settings))
    runtime = runtime_from_sections(slug, compile_business_config(config, lambda ref: tenant.payment_values[ref.secret_ref]))
    return business_facts(runtime, detect_business_model(runtime))


def _totals(scored: dict) -> dict[int, float]:
    return {int(turn.get("turno", 0)): sum(float(turn.get(name, 0)) for name in CRITERIA) for turn in scored.get("turnos", [])}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--reference", default="openai/gpt-4.1")
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--tenants", default="restaurant,saas,clinic,tienda_ropa")
    parser.add_argument("--max-usd", type=float, default=0.30)
    args = parser.parse_args()
    key = str(dotenv_values(REPO / ".env").get("OPENROUTER_API_KEY") or "").strip()
    data = json.loads((LAB / "results" / args.experiment / "data.json").read_text(encoding="utf-8"))
    judges = [args.reference, *[model for model in args.candidates.split(",") if model]]
    conversations = [(slug, label, data["transcripts"][label][slug][0]) for slug in args.tenants.split(",") for label in ("baseline", "candidate")]
    table = costs.prices(set(judges))
    budget = sum(len(conversations) * (ESTIMATED_TOKENS[0] * table[j][0] + ESTIMATED_TOKENS[1] * table[j][1]) for j in judges)
    print(f"{len(conversations)} conversaciones × {len(judges)} jueces · costo calculado USD {budget:.2f} (tope USD {args.max_usd:.2f})", flush=True)
    if budget > args.max_usd:
        raise SystemExit("El cálculo supera el tope.")
    facts = {slug: _facts(slug) for slug in args.tenants.split(",")}

    def run(job):
        judge, (slug, label, turns) = job
        scored, usage = score_conversation(key, judge, facts[slug], turns)
        return judge, slug, label, _totals(scored), usage

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(run, [(judge, conversation) for judge in judges for conversation in conversations]))
    by_judge: dict[str, dict] = {judge: {} for judge in judges}
    usages: dict[str, list] = {judge: [] for judge in judges}
    for judge, slug, label, totals, usage in results:
        by_judge[judge][(slug, label)] = totals
        usages[judge].append(usage)

    reference = by_judge[args.reference]
    flagged = {(conv, turn) for conv, totals in reference.items() for turn, total in totals.items() if total < 10}
    print(f"\nEl juez de referencia ({args.reference}) marca {len(flagged)} respuestas con fallas.\n")
    print("| Juez | Diferencia promedio por respuesta | Fallas que también detecta | Marca de más | Costo real |")
    print("|---|---|---|---|---|")
    for judge in judges:
        diffs, caught, extra = [], 0, 0
        for conv, totals in reference.items():
            for turn, total in totals.items():
                mine = by_judge[judge].get(conv, {}).get(turn)
                if mine is None:
                    continue
                diffs.append(abs(mine - total))
                caught += (conv, turn) in flagged and mine < 10
                extra += (conv, turn) not in flagged and mine < 10
        print(f"| {judge} | {statistics.mean(diffs):.2f} | {caught}/{len(flagged)} | {extra} | USD {costs.spent(usages[judge], table[judge]):.4f} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
