"""La evaluación del lector del saludo: ¿entiende cuándo el primer mensaje del cliente es solo un saludo? Con la IA real, caso por caso.

Corre los casos de `greeting_cases.py` con la función real del motor (`greeting_reading.reads_as_greeting`) y el texto del lector del
árbol de trabajo, varias veces cada uno. Gratis, también los corre con la lista de palabras que hubo hasta el 26 nov 2026
(`--old-rule`, si existe en el árbol), para comparar con los mismos casos.

    python experiments/quality_lab/run_greeting_eval.py --experiment <id> [--samples 5] [--model <modelo>] [--max-usd 0.05]

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
from greeting_cases import CASES, GreetingCase  # noqa: E402

# Una llamada: las instrucciones y el mensaje (unos 250 tokens) y un JSON de una clave.
GREETING_TOKENS = (260, 12)


def verdict(case: GreetingCase, read: bool | None) -> str:
    """«bien», «sin lectura», «saludo fijo a quien preguntó» (lo grave) o «respondió la IA a un saludo» (leve)."""
    if read is None:
        return "sin lectura"
    if read == case.greets_only:
        return "bien"
    return "saludo fijo a quien preguntó" if read else "respondió la IA a un saludo"


def old_rule(message: str) -> bool | None:
    """La lista de palabras de antes, si el árbol todavía la tiene (para comparar); None si ya no existe."""
    try:
        from app.application.pipeline.conversation_flow import is_greeting_only
    except ImportError:
        return None
    return is_greeting_only(message)


def run(key: str, model: str, samples: int) -> tuple[list[dict], list[dict]]:
    import logging

    from app.application.pipeline.greeting_reading import reads_as_greeting
    from app.infrastructure.ai.llm_runtime import LLMRuntime

    logging.disable(logging.CRITICAL)
    llm = LLMRuntime()

    def one(job: tuple[GreetingCase, int]) -> tuple[dict, list[dict]]:
        case, sample = job
        spent: list[dict] = []
        config = SimpleNamespace(api_key=key, model_name=model, on_usage=lambda _m, prompt, completion, cost: spent.append(
            {"prompt_tokens": prompt, "completion_tokens": completion, **({"cost": cost} if cost is not None else {})}))
        read = reads_as_greeting(llm, bot_config=config, user_message=case.message)
        return {"message": case.message, "sample": sample, "expected": case.greets_only, "read": read, "verdict": verdict(case, read)}, spent

    jobs = [(case, sample) for case in CASES for sample in range(samples)]
    with ThreadPoolExecutor(max_workers=6) as pool:
        done = list(pool.map(one, jobs))
    return [row for row, _ in done], [usage for _, usages in done for usage in usages]


def build_report(data: dict) -> str:
    rows = data["rows"]
    right = sum(1 for row in rows if row["verdict"] == "bien")
    grave = sum(1 for row in rows if row["verdict"] == "saludo fijo a quien preguntó")
    lines = [
        f"# Lector del saludo: {data['experiment']}",
        "",
        f"**IA: {right} de {len(rows)} lecturas correctas** ({grave} graves: saludo fijo a quien preguntó) · modelo `{data['model']}` · "
        f"{len(CASES)} casos, {data['samples']} veces cada uno · gasto USD {data['gasto_usd']:.4f}",
    ]
    if data.get("old_rule"):
        old = data["old_rule"]
        lines += ["", f"**Lista de palabras de antes: {sum(1 for row in old if row['verdict'] == 'bien')} de {len(old)} casos.**"]
    lines += ["", "| Mensaje | De dónde / qué prueba | Solo saluda | IA | Lista de antes |", "|---|---|---|---|---|"]
    old_by_message = {row["message"]: row for row in data.get("old_rule") or []}
    for case in CASES:
        mine = [row for row in rows if row["message"] == case.message]
        good = sum(1 for row in mine if row["verdict"] == "bien")
        old = old_by_message.get(case.message)
        lines.append(f"| {'✅' if good == len(mine) else '❌'} «{case.message}» | {case.note} | {'sí' if case.greets_only else 'no'} | "
                     f"{good} de {len(mine)} | {'—' if old is None else ('✅' if old['verdict'] == 'bien' else '❌ ' + old['verdict'])} |")
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
    budget = len(CASES) * args.samples * costs._cost(GREETING_TOKENS, price)
    print(f"Costo calculado: USD {budget:.3f} (tope USD {args.max_usd:.2f}) · {len(CASES)} casos × {args.samples} · modelo {model}", flush=True)
    if budget > args.max_usd:
        raise SystemExit("El cálculo supera el tope: baja las muestras o sube --max-usd con autorización.")

    os.environ.update({"MODE": "test", "DATABASE_URL": "sqlite:///:memory:", "ENABLE_FILE_LOGS": "0"})
    old = [
        {"message": case.message, "read": read, "verdict": verdict(case, read)}
        for case in CASES if (read := old_rule(case.message)) is not None
    ]
    rows, usages = run(key, model, args.samples)
    data = {"experiment": args.experiment, "model": model, "samples": args.samples, "rows": rows, "old_rule": old,
            "gasto_usd": costs.spent(usages, price)}
    output.mkdir(parents=True)
    (output / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    (output / "report.md").write_text(build_report(data), encoding="utf-8")
    right = sum(1 for row in rows if row["verdict"] == "bien")
    print(f"\nIA: {right} de {len(rows)} lecturas correctas · gasto USD {data['gasto_usd']:.4f} · informe: {output / 'report.md'}")
    if old:
        print(f"Lista de palabras de antes: {sum(1 for row in old if row['verdict'] == 'bien')} de {len(old)} casos")
    for row in rows:
        if row["verdict"] != "bien":
            print(f"  ❌ «{row['message']}»: {row['verdict']}")
    return 0 if right == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
