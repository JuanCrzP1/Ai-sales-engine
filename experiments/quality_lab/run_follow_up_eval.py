"""La evaluación del lector del seguimiento: ¿sabe cuándo conviene escribirle a un cliente que dejó de responder? Con la IA real.

Corre los casos de `follow_up_cases.py` con la función real del motor (`follow_up_reading.reads_follow_up`) y el texto del lector del
árbol de trabajo, varias veces cada uno.

    python experiments/quality_lab/run_follow_up_eval.py --experiment <id> [--samples 5] [--model <modelo>] [--max-usd 0.05]

Usa la clave de OpenRouter del `.env` (nunca la imprime). Tiene costo (centavos): antes de correr calcula cuánto y no arranca si pasa
de `--max-usd`. Los resultados van a `experiments/quality_lab/results/<id>/`. Termina con código 1 si algún caso falla alguna vez.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

from dotenv import dotenv_values

LAB = Path(__file__).resolve().parent
REPO = LAB.parents[1]
RESULTS = LAB / "results"
sys.path[:0] = [str(LAB), str(REPO / "project")]

import costs  # noqa: E402
from follow_up_cases import CASES, FollowUpCase  # noqa: E402

# Una llamada: las instrucciones, unos mensajes y el seguimiento (unos 450 tokens) y un JSON de una clave.
FOLLOW_UP_TOKENS = (450, 10)


def verdict(case: FollowUpCase, read: bool | None) -> str:
    """«bien», «sin lectura», «le escribe a quien cerró» (lo grave) o «no le escribe a quien dejó abierto» (leve)."""
    if read is None:
        return "sin lectura"
    if read == case.send:
        return "bien"
    return "le escribe a quien cerró" if read else "no le escribe a quien dejó abierto"


def run(key: str, model: str, samples: int) -> tuple[list[dict], list[dict]]:
    import logging

    from app.application.follow_up.follow_up_reading import reads_follow_up
    from app.infrastructure.ai.llm_runtime import LLMRuntime

    logging.disable(logging.CRITICAL)
    llm = LLMRuntime()

    def one(job: tuple[int, FollowUpCase, int]) -> tuple[dict, list[dict]]:
        number, case, sample = job
        spent: list[dict] = []
        config = SimpleNamespace(api_key=key, model_name=model, on_usage=lambda _m, prompt, completion, cost: spent.append(
            {"prompt_tokens": prompt, "completion_tokens": completion, **({"cost": cost} if cost is not None else {})}))
        read = reads_follow_up(llm, bot_config=config, messages=list(case.messages), message=case.message)
        return {"case": number, "note": case.note, "sample": sample, "expected": case.send, "read": read, "verdict": verdict(case, read)}, spent

    jobs = [(number, case, sample) for number, case in enumerate(CASES) for sample in range(samples)]
    with ThreadPoolExecutor(max_workers=6) as pool:
        done = list(pool.map(one, jobs))
    return [row for row, _ in done], [usage for _, usages in done for usage in usages]


def build_report(data: dict) -> str:
    rows = data["rows"]
    right = sum(1 for row in rows if row["verdict"] == "bien")
    grave = sum(1 for row in rows if row["verdict"] == "le escribe a quien cerró")
    lines = [
        f"# Lector del seguimiento: {data['experiment']}",
        "",
        f"**IA: {right} de {len(rows)} lecturas correctas** ({grave} graves: le escribe a quien cerró) · modelo `{data['model']}` · "
        f"{len(CASES)} casos, {data['samples']} veces cada uno · gasto USD {data['gasto_usd']:.4f}",
        "",
        "| Caso | Último mensaje del cliente | Conviene escribirle | IA |",
        "|---|---|---|---|",
    ]
    for number, case in enumerate(CASES):
        mine = [row for row in rows if row["case"] == number]
        good = sum(1 for row in mine if row["verdict"] == "bien")
        last = next((text for author, text in reversed(case.messages) if author == "customer"), "(no escribió)")
        lines.append(f"| {'✅' if good == len(mine) else '❌'} {case.note} | «{last}» | {'sí' if case.send else 'no'} | {good} de {len(mine)} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--model", default="", help="Modelo del lector; por omisión, el del .env")
    parser.add_argument("--max-usd", type=float, default=0.05)
    args = parser.parse_args()
    output = RESULTS / args.experiment
    if output.exists():
        raise SystemExit(f"{output} ya existe: un experimento no se sobrescribe; elige otro identificador.")
    env_file = dotenv_values(REPO / ".env")
    key = str(env_file.get("OPENROUTER_API_KEY") or "").strip()
    model = args.model.strip() or str(env_file.get("OPENROUTER_MODEL") or "openai/gpt-4o-mini").strip()
    if not key:
        raise SystemExit("Falta OPENROUTER_API_KEY en el .env.")
    price = costs.prices({model})[model]
    budget = len(CASES) * args.samples * costs._cost(FOLLOW_UP_TOKENS, price)
    print(f"Costo calculado: USD {budget:.3f} (tope USD {args.max_usd:.2f}) · {len(CASES)} casos × {args.samples} · modelo {model}", flush=True)
    if budget > args.max_usd:
        raise SystemExit("El cálculo supera el tope: baja las muestras o sube --max-usd con autorización.")

    os.environ.update({"MODE": "test", "DATABASE_URL": "sqlite:///:memory:", "ENABLE_FILE_LOGS": "0"})
    rows, usages = run(key, model, args.samples)
    data = {"experiment": args.experiment, "model": model, "samples": args.samples, "rows": rows, "gasto_usd": costs.spent(usages, price)}
    output.mkdir(parents=True)
    (output / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    (output / "report.md").write_text(build_report(data), encoding="utf-8")
    right = sum(1 for row in rows if row["verdict"] == "bien")
    print(f"\nIA: {right} de {len(rows)} lecturas correctas · gasto USD {data['gasto_usd']:.4f} · informe: {output / 'report.md'}")
    for row in rows:
        if row["verdict"] != "bien":
            print(f"  ❌ {row['note']}: {row['verdict']}")
    return 0 if right == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
