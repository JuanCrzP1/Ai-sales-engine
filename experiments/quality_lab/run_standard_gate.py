"""La puerta de calidad: ¿cumple el asesor el estándar? Pasa o no pasa, con la IA real.

Corre las conversaciones del estándar (`standard.py`: el chat real de producción del 13 nov 2026 y frases sueltas de clientes) con el
código del árbol de trabajo, en una copia aislada y con el modelo real. Cada regla pasa o no pasa en cada conversación:
- las exactas se comprueban sin opinión (le llegaron los datos, el asesor habló, no se repitió el bloque…);
- las demás las revisa un juez IA: señala cada falla con la frase textual del asesor (sin ella no vale) y un segundo revisor la
  confirma mirando solo ese turno. Un juez solo, leyendo toda la conversación, se equivocaba demasiado.

Un cambio al asesor se publica solo si pasan todas las reglas en todas las conversaciones. Termina con código 1 si alguna no pasa.

    python experiments/quality_lab/run_standard_gate.py --experiment <id> [--samples 3] [--tenants asesor_ai_prod] [--model <modelo>]

Usa la clave de OpenRouter del `.env` (nunca la imprime). Tiene costo: antes de correr calcula cuánto costará y no arranca si pasa de
`--max-usd`. Los resultados van a `experiments/quality_lab/results/<id>/` (informe, datos y conversaciones, sin datos de pago). Un
experimento terminado no se sobrescribe.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import dotenv_values

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

import costs  # noqa: E402
import judge  # noqa: E402
from run_quality_eval import REPO, RESULTS, _child_env, _export, _git, _model_prices, _usage  # noqa: E402
from standard import CONFIRM, EXACT_RULES, JUDGE, JUDGE_RULES, confirm_request, exact_failures, judge_failures, keep_confirmed  # noqa: E402

# Para calcular el costo antes de correr: las conversaciones del estándar y sus turnos, por negocio y por muestra.
CONVERSATIONS, TURNS = 6, 23
_METHOD_NAMES = {"bank": "transferencia bancaria", "link": "link de pago", "breb": "Bre-B", "nequi": "Nequi", "daviplata": "Daviplata"}


def _ficha(facts: dict) -> dict:
    """Lo que el juez necesita saber del negocio para revisar las reglas: qué medios de pago tiene."""
    return {"medios_de_pago_del_negocio": [_METHOD_NAMES.get(kind, kind) for kind, has in facts["pagos_disponibles"].items() if has]}


def judge_conversation(key: str, model: str, facts: dict, turns: list[dict]) -> tuple[dict[str, list[dict]], list[dict], list[dict]]:
    """Las reglas del juez en una conversación: por cada una, dónde no pasa y por qué (lista vacía si pasa); las fallas que reportó
    y no valieron (sin su frase textual, o no confirmadas por el segundo revisor) y lo que gastaron sus llamadas."""
    user = f"FICHA:\n{json.dumps(_ficha(facts), ensure_ascii=False)}\n\nCONVERSACIÓN:\n{judge._transcript(turns)}"
    verdict, usage = judge._call(key, model, JUDGE, user)
    failures, discarded = judge_failures(verdict, turns)
    usages = [usage]

    def confirm(rule: str, conversation: list[dict], failure: dict) -> bool:
        answer, spent = judge._call(key, model, CONFIRM, confirm_request(rule, conversation, failure))
        usages.append(spent)
        return answer.get("confirmada") is True

    # Cada falla que señala el juez la revisa sola un segundo revisor: solo cuentan las que confirma.
    failures, unconfirmed = keep_confirmed(failures, turns, confirm)
    return failures, discarded + unconfirmed, usages


def evaluate(captured: dict, key: str, judge_model: str) -> tuple[list[dict], list[dict]]:
    """Cada conversación con las reglas que no pasa (exactas y del juez), y lo que gastó el juez."""
    jobs = [(slug, data["facts"], turns) for slug, data in captured["results"].items() for turns in data["samples"]]

    def run(job):
        slug, facts, turns = job
        judged, discarded, usages = judge_conversation(key, judge_model, facts, turns)
        row = {"tenant": slug, "conversation": turns[0].get("conversation", ""), "turns": turns, "failures": {**exact_failures(turns), **judged},
               "discarded": discarded}
        return row, usages

    with ThreadPoolExecutor(max_workers=6) as pool:
        done = list(pool.map(run, jobs))
    return [row for row, _usages in done], [usage for _row, usages in done for usage in usages]


def build_report(data: dict) -> str:
    rows = data["rows"]
    rules = {**EXACT_RULES, **JUDGE_RULES}
    failed = {name: [(row, failure) for row in rows for failure in row["failures"][name]] for name in rules}
    passed = all(not items for items in failed.values())
    lines = [
        f"# Estándar del asesor: {data['experiment']}",
        "",
        f"**{'PASA' if passed else 'NO PASA'}** · código `{data['candidate']}` · modelo `{data['model']}` · juez `{data['judge_model']}` · "
        f"{len(rows)} conversaciones ({data['samples']} muestras por negocio: {', '.join(data['tenants'])})",
        "",
        "| Regla | Pasa | Qué exige |",
        "|---|---|---|",
    ]
    for name, text in rules.items():
        broken = len({(id(row)) for row, _failure in failed[name]})
        kind = "exacta" if name in EXACT_RULES else "juez"
        lines.append(f"| {'✅' if not broken else '❌'} {name.replace('_', ' ')} ({kind}) | {len(rows) - broken} de {len(rows)} | {text.split('. ')[0].rstrip('.')}. |")
    discarded = sum(len(row.get("discarded") or []) for row in rows)
    lines += ["", f"Gasto de la corrida: asesor USD {data['gasto']['asesor_usd']:.4f} · juez USD {data['gasto']['juez_usd']:.4f}. "
              f"Llamadas al modelo por mensaje: {data['llamadas_por_mensaje']}. Fallas que señaló el juez y no valieron (sin su frase "
              f"textual, o que el segundo revisor no confirmó): {discarded}.", ""]
    if not passed:
        lines += ["## Lo que no pasó", ""]
        for name in rules:
            for row, failure in failed[name]:
                turn = next((turn for turn in row["turns"] if turn["turn"] == failure["turn"]), None)
                lines.append(f"- **{name.replace('_', ' ')}** · {row['tenant']} · {row['conversation']} · turno {failure['turn']}: {failure['why']}")
                if turn:
                    lines.append(f"  - Cliente: «{turn['message']}»")
                    lines.append(f"  - Asesor: «{' ⏎ '.join(turn['reply'].split(chr(10)))[:420]}»")
        lines.append("")
    lines += ["## Las conversaciones", ""]
    for row in rows:
        lines += [f"### {row['tenant']} · {row['conversation']}", ""]
        for turn in row["turns"]:
            lines += [f"**[{turn['turn']}] Cliente:** {turn['message']}", "", f"**[{turn['turn']}] Asesor:** " + turn["reply"].replace("\n", "  \n"), ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--tenants", default="asesor_ai_prod")
    parser.add_argument("--model", default="", help="Modelo del asesor; por omisión, el del .env")
    # El juez barato del otro laboratorio (deepseek) marcaba fallas donde no las había; con las mismas conversaciones, este fue el más
    # sensato de cuatro (13 nov 2026).
    parser.add_argument("--judge-model", default="google/gemini-2.5-flash")
    parser.add_argument("--max-usd", type=float, default=0.30, help="Tope de gasto de la corrida; no arranca si el cálculo lo supera")
    parser.add_argument("--rejudge", action="store_true", help="Revisa de nuevo las conversaciones ya guardadas, sin repetirlas")
    args = parser.parse_args()
    output = RESULTS / args.experiment
    if output.exists() and not args.rejudge:
        raise SystemExit(f"{output} ya existe: un experimento no se sobrescribe; usa --rejudge para revisar lo guardado o elige otro identificador.")
    env_file = dotenv_values(REPO / ".env")
    key = str(env_file.get("OPENROUTER_API_KEY") or "").strip()
    model = args.model.strip() or str(env_file.get("OPENROUTER_MODEL") or "openai/gpt-4o-mini").strip()
    if not key:
        raise SystemExit("Falta OPENROUTER_API_KEY en el .env.")
    tenants = [slug for slug in args.tenants.split(",") if slug]
    volume = len(tenants) * args.samples
    budget = costs.estimate(conversations=volume * CONVERSATIONS, turns=volume * TURNS, model=model, judge=args.judge_model,
                            table=costs.prices({model, args.judge_model}), with_capture=not args.rejudge)
    print(f"Costo calculado: USD {budget:.2f} (tope USD {args.max_usd:.2f}) · asesor {model} · juez {args.judge_model}", flush=True)
    if budget > args.max_usd:
        raise SystemExit("El cálculo supera el tope: baja las muestras, los negocios o sube --max-usd con autorización.")
    if args.rejudge:
        if not (output / "captures.json").exists():
            raise SystemExit(f"No hay conversaciones guardadas en {output}.")
        captured = json.loads((output / "captures.json").read_text(encoding="utf-8"))
        return report(args, captured, key, output)
    head = _git("rev-parse", "--short", "HEAD").decode().strip()
    reference = f"{head} + cambios" if _git("status", "--porcelain", "--", "project").strip() else head

    with tempfile.TemporaryDirectory(prefix="lab-estandar-") as work:
        work_path = Path(work)
        tree = work_path / "candidate"
        _export(None, tree)
        settings = work_path / "candidate.json"
        settings.write_text(json.dumps({"label": "candidate", "commit": reference, "samples": args.samples, "tenants": tenants, "standard": True,
                                        "output": str(work_path / "candidate.out.json")}), encoding="utf-8")
        print(f"[asesor] {reference} | modelo {model}", flush=True)
        process = subprocess.run([sys.executable, "-B", str(tree / "experiments" / "quality_lab" / "capture.py"), str(settings)],
                                 cwd=tree, env=_child_env(key, model), capture_output=True, text=True)
        if process.returncode != 0:
            raise SystemExit("Falló la captura:\n" + "\n".join(process.stderr.strip().splitlines()[-15:]))
        captured = json.loads((work_path / "candidate.out.json").read_text(encoding="utf-8"))
    output.mkdir(parents=True)
    (output / "captures.json").write_text(json.dumps(captured, ensure_ascii=False), encoding="utf-8")
    return report(args, captured, key, output)


def report(args, captured: dict, key: str, output: Path) -> int:
    """Revisa las conversaciones capturadas con las reglas del estándar y escribe el informe. Devuelve 0 si pasan todas."""
    model, tenants = str(captured.get("model") or ""), sorted(captured["results"])
    rows, judge_usages = evaluate(captured, key, args.judge_model)
    usage = _usage(captured, _model_prices(model))
    messages = sum(len(row["turns"]) for row in rows)
    data = {
        "experiment": args.experiment, "candidate": captured.get("commit"), "model": model, "judge_model": args.judge_model,
        "samples": len(rows) // max(1, len(tenants)) // max(1, len({row["conversation"] for row in rows})),
        "tenants": tenants, "rows": [{key_: value for key_, value in row.items() if key_ != "turns"} | {"turns": [
            {name: turn[name] for name in ("turn", "message", "expect", "reply", "handoff")} for turn in row["turns"]]} for row in rows],
        "gasto": {"asesor_usd": usage["costo_usd_sin_cache"], "juez_usd": costs.spent(judge_usages, _model_prices(args.judge_model))},
        "llamadas_por_mensaje": round(usage["llamadas"] / messages, 2) if messages else 0,
    }
    (output / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    (output / "report.md").write_text(build_report(data), encoding="utf-8")
    broken = {name: sum(1 for row in rows if row["failures"][name]) for name in {**EXACT_RULES, **JUDGE_RULES}}
    print(f"\n{'PASA' if not any(broken.values()) else 'NO PASA'} · {len(rows)} conversaciones · informe: {output / 'report.md'}")
    for name, count in broken.items():
        print(f"  {'✅' if not count else '❌'} {name.replace('_', ' ')}: {len(rows) - count} de {len(rows)}")
    return 0 if not any(broken.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
