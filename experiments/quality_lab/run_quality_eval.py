"""Laboratorio de calidad: ¿responde mejor el asistente con el código nuevo? Lo decide la IA real, no una opinión.

Compara BASELINE (un commit) con CANDIDATE (el árbol de trabajo). Cada lado corre en su copia aislada, sin `.env`, con el modelo real
y los mismos escenarios (`scenarios.py`). Luego:
- revisiones exactas por respuesta (`checks.py`): precios inventados, marcador de pago visible, formato, largo, preguntas de más;
- un juez IA (`judge.py`) califica cada conversación con una rúbrica, sin saber qué versión es, y compara las dos a ciegas;
- tokens, caché, tiempo y costo por mensaje.

Usa la clave de OpenRouter del `.env` (nunca la imprime). Tiene costo: antes de correr calcula cuánto costará y no arranca si pasa
de `--max-usd` (USD 0,30 por defecto); al terminar informa lo gastado de verdad.

    python experiments/quality_lab/run_quality_eval.py --experiment <id> --baseline <commit> [--samples 2] [--tenants a,b]
    python experiments/quality_lab/run_quality_eval.py --experiment <id> --rejudge     # vuelve a calificar sin repetir las conversaciones
    python experiments/quality_lab/run_quality_eval.py --experiment <id> --baseline <commit> --tenants a,b --closing-strategy lead_capture

Con `--closing-strategy` los negocios elegidos usan esa estrategia de cierre en los DOS lados (sirve para medir una que ningún
ejemplo usa, como «Capturar datos»): solo se edita su `business-config.json` dentro de cada copia, nunca el repositorio.

Los resultados van a `experiments/quality_lab/results/<id>/`: primero las conversaciones (`captures.json`), después el informe y los
datos. Si el juez falla (por ejemplo, sin saldo), las conversaciones quedan guardadas y se califican después con `--rejudge`.
Un experimento terminado no se sobrescribe.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import statistics
import subprocess
import sys
import tarfile
import tempfile
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
from dotenv import dotenv_values

LAB = Path(__file__).resolve().parent
REPO = LAB.parents[1]
RESULTS = LAB / "results"
sys.path.insert(0, str(LAB))

import costs  # noqa: E402
from checks import check_turn  # noqa: E402
from judge import CRITERIA, compare, score_conversation  # noqa: E402

SAFE_ENV = ("PATH", "HOME", "LANG", "TMPDIR", "SYSTEMROOT", "TEMP", "TMP", "USERPROFILE", "APPDATA", "LOCALAPPDATA")
LAB_FILES = ("__init__.py", "capture.py", "facts.py", "scenarios.py", "standard.py", "escalation_standard.py")


def _git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, check=True).stdout


def _export(commit: str | None, destination: Path) -> None:
    destination.mkdir(parents=True)
    if commit:
        with tarfile.open(fileobj=io.BytesIO(_git("archive", "--format=tar", commit, "project"))) as tar:
            tar.extractall(destination, filter="data")
    else:
        for relative in filter(None, _git("ls-files", "-co", "--exclude-standard", "-z", "--", "project").decode().split("\0")):
            source = REPO / relative
            if source.is_file():
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
    # El arnés es el mismo en los dos lados: solo cambia el motor.
    harness = destination / "experiments" / "quality_lab"
    harness.mkdir(parents=True)
    for name in LAB_FILES:
        shutil.copy2(LAB / name, harness / name)


def _set_closing_strategy(tree: Path, tenants: list[str], strategy: str) -> None:
    """Pone la misma estrategia de cierre en los negocios elegidos de una copia (nunca en el repositorio)."""
    if not tenants:
        raise SystemExit("--closing-strategy necesita --tenants: di en qué negocios cambiarla.")
    for slug in tenants:
        path = tree / "project" / "config" / "tenants" / slug / "business-config.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["sales"].setdefault("closing", {})["strategy"] = strategy
        path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")


def _child_env(key: str, model: str) -> dict[str, str]:
    env = {name: os.environ[name] for name in SAFE_ENV if name in os.environ}
    env.update({"MODE": "test", "DATABASE_URL": "sqlite:///:memory:", "ENABLE_FILE_LOGS": "0", "OPENROUTER_API_KEY": key,
                "OPENROUTER_MODEL": model, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"})
    return env


def _model_prices(model: str) -> tuple[float, float]:
    """Dólares por token (entrada, salida) del modelo, según la lista pública de OpenRouter."""
    for item in httpx.get("https://openrouter.ai/api/v1/models", timeout=30).json()["data"]:
        if item["id"] == model:
            return float(item["pricing"]["prompt"]), float(item["pricing"]["completion"])
    return 0.0, 0.0


def _turn_score(turn: dict) -> float:
    return sum(float(turn.get(name, 0)) for name in CRITERIA)


def _usage(sides: dict, prices: tuple[float, float]) -> dict:
    rows = [call for tenant in sides["results"].values() for sample in tenant["samples"] for turn in sample for call in turn["calls"]]
    prompt = [call["usage"].get("prompt_tokens", 0) for call in rows]
    cached = [((call["usage"].get("prompt_tokens_details") or {}).get("cached_tokens") or 0) for call in rows]
    completion = [call["usage"].get("completion_tokens", 0) for call in rows]
    cost = sum(p * prices[0] + c * prices[1] for p, c in zip(prompt, completion))
    return {
        "llamadas": len(rows),
        "tokens_entrada_promedio": round(statistics.mean(prompt)) if prompt else 0,
        "tokens_en_cache_promedio": round(statistics.mean(cached)) if cached else 0,
        "tokens_salida_promedio": round(statistics.mean(completion)) if completion else 0,
        "ms_promedio": round(statistics.mean(call["ms"] for call in rows)) if rows else 0,
        "costo_usd_sin_cache": round(cost, 4),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--tenants", default="")
    parser.add_argument("--judge-model", default="deepseek/deepseek-chat-v3.1")
    parser.add_argument("--max-usd", type=float, default=0.30, help="Tope de gasto de la corrida; no arranca si el cálculo lo supera")
    parser.add_argument("--rejudge", action="store_true", help="Califica de nuevo las conversaciones ya guardadas")
    parser.add_argument("--closing-strategy", choices=("direct_sale", "lead_capture", "booking", "checkout"),
                        help="Estrategia de cierre para los negocios elegidos, igual en los dos lados")
    args = parser.parse_args()
    output = RESULTS / args.experiment
    captures_file = output / "captures.json"
    if (output / "report.md").exists():
        raise SystemExit(f"{output} ya está terminado: un experimento no se sobrescribe.")
    env_file = dotenv_values(REPO / ".env")
    key, model = str(env_file.get("OPENROUTER_API_KEY") or "").strip(), str(env_file.get("OPENROUTER_MODEL") or "openai/gpt-4o-mini").strip()
    if not key:
        raise SystemExit("Falta OPENROUTER_API_KEY en el .env.")
    tenants_count = len([slug for slug in args.tenants.split(",") if slug]) or 9
    table = costs.prices({model, args.judge_model})
    budget = costs.estimate(conversations=tenants_count * args.samples, turns=tenants_count * args.samples * 10, model=model, judge=args.judge_model,
                            table=table, with_capture=not args.rejudge)
    print(f"Costo calculado: USD {budget:.2f} (tope USD {args.max_usd:.2f}) · asistente {model} · juez {args.judge_model}", flush=True)
    if budget > args.max_usd:
        raise SystemExit("El cálculo supera el tope: baja las muestras, los negocios o sube --max-usd con autorización.")
    if args.rejudge:
        if not captures_file.exists():
            raise SystemExit(f"No hay conversaciones guardadas en {captures_file}.")
        sides = json.loads(captures_file.read_text(encoding="utf-8"))
        return judge_and_report(args, sides, key, model, output)
    if output.exists():
        raise SystemExit(f"{output} ya existe: usa --rejudge para calificar lo guardado o elige otro identificador.")
    baseline_commit = _git("rev-parse", "--short", args.baseline).decode().strip()
    head = _git("rev-parse", "--short", "HEAD").decode().strip()
    pending = bool(_git("status", "--porcelain", "--", "project").strip())
    tenants = [slug for slug in args.tenants.split(",") if slug]

    with tempfile.TemporaryDirectory(prefix="lab-calidad-") as work:
        work_path = Path(work)
        processes = {}
        for label, commit, reference in (("baseline", baseline_commit, baseline_commit), ("candidate", None, f"{head} + cambios" if pending else head)):
            tree = work_path / label
            _export(commit, tree)
            if args.closing_strategy:
                _set_closing_strategy(tree, tenants, args.closing_strategy)
            settings = work_path / f"{label}.json"
            settings.write_text(json.dumps({"label": label, "commit": reference, "samples": args.samples, "tenants": tenants,
                                            "output": str(work_path / f"{label}.out.json")}), encoding="utf-8")
            print(f"[{label}] {reference} | modelo {model}", flush=True)
            processes[label] = subprocess.Popen([sys.executable, "-B", str(tree / "experiments" / "quality_lab" / "capture.py"), str(settings)],
                                                cwd=tree, env=_child_env(key, model), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for label, process in processes.items():
            _stdout, stderr = process.communicate()
            if process.returncode != 0:
                raise SystemExit(f"Falló la captura de {label}:\n" + "\n".join(stderr.strip().splitlines()[-15:]))
        sides = {label: json.loads((work_path / f"{label}.out.json").read_text(encoding="utf-8")) for label in processes}
    output.mkdir(parents=True)
    captures_file.write_text(json.dumps(sides, ensure_ascii=False), encoding="utf-8")
    return judge_and_report(args, sides, key, model, output)


def judge_and_report(args, sides: dict, key: str, model: str, output: Path) -> int:
    prices = _model_prices(model)
    jobs = []
    for slug, data in sides["baseline"]["results"].items():
        facts = data["facts"]
        for sample in range(len(data["samples"])):
            jobs.append((slug, sample, facts))

    def evaluate(job):
        slug, sample, facts = job
        row = {"tenant": slug, "sample": sample}
        conversations = {}
        for label in ("baseline", "candidate"):
            turns = sides[label]["results"][slug]["samples"][sample]
            conversations[label] = turns
            previous = ""
            checks = []
            for turn in turns:
                checks.append(check_turn(turn["reply"], facts=facts, previous_reply=previous, ai_used=turn["ai_used"], format_error=turn["format_error"], kind=turn.get("kind", "")))
                previous = turn["reply"]
            # Las respuestas con datos de pago las arma el motor: el juez las ve como tales.
            scored, usage_judge = score_conversation(key, args.judge_model, facts, turns)
            row[label] = {"checks": checks, "scores": scored.get("turnos", []), "general": scored.get("general", "")}
            row.setdefault("_judge_usage", []).append(usage_judge)
        winner, reason, usage_pair = compare(key, args.judge_model, facts, conversations["baseline"], conversations["candidate"], seed=zlib.crc32(f"{slug}:{sample}".encode()))
        row["pairwise"] = {"ganador": winner, "razon": reason}
        row["_judge_usage"].append(usage_pair)
        return row

    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(evaluate, jobs))
    table = costs.prices({model, args.judge_model})
    assistant_usages = [call["usage"] for side in sides.values() for tenant in side["results"].values() for sample in tenant["samples"] for turn in sample for call in turn["calls"]]
    judge_usages = [usage for row in rows for usage in row.pop("_judge_usage", [])]
    spending = {"asistente_usd": costs.spent(assistant_usages, table[model]) if not args.rejudge else 0.0, "juez_usd": costs.spent(judge_usages, table[args.judge_model])}
    print(f"Gastado de verdad: asistente USD {spending['asistente_usd']:.4f} · juez USD {spending['juez_usd']:.4f}", flush=True)

    data = {"experiment": args.experiment, "baseline": sides["baseline"]["commit"], "candidate": sides["candidate"]["commit"], "model": model,
            "judge_model": args.judge_model, "samples": args.samples, "rows": rows,
            "usage": {label: _usage(sides[label], prices) for label in sides}, "gasto": spending,
            "network_attempts": {label: sides[label]["network_attempts"] for label in sides},
            "transcripts": {label: {slug: [[{k: v for k, v in turn.items() if k not in ("calls", "system_prompt")} for turn in sample] for sample in data_["samples"]]
                                    for slug, data_ in sides[label]["results"].items()} for label in sides},
            "prompts": {label: {slug: {"primer_mensaje": data_["samples"][0][1]["system_prompt"], "ultimo_mensaje": data_["samples"][0][-1]["system_prompt"]}
                                for slug, data_ in sides[label]["results"].items()} for label in sides}}
    (output / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    report = build_report(data)
    (output / "report.md").write_text(report, encoding="utf-8")
    print(report.split("## Por negocio")[0])
    return 0


def _mean(values) -> float:
    values = list(values)
    return round(statistics.mean(values), 2) if values else 0.0


def build_report(data: dict) -> str:
    rows = data["rows"]
    lines = [f"# Calidad: {data['experiment']}", "", f"Baseline `{data['baseline']}` · Candidate `{data['candidate']}` · modelo `{data['model']}` · juez `{data['judge_model']}` · muestras por negocio: {data['samples']}", ""]
    lines += ["## Resumen", "", "| | Baseline | Candidate |", "|---|---|---|"]
    for criterion in CRITERIA:
        values = {label: _mean(turn.get(criterion, 0) for row in rows for turn in row[label]["scores"]) for label in ("baseline", "candidate")}
        lines.append(f"| {criterion} (0-2) | {values['baseline']} | {values['candidate']} |")
    totals = {label: _mean(_turn_score(turn) for row in rows for turn in row[label]["scores"]) for label in ("baseline", "candidate")}
    lines.append(f"| **puntaje por respuesta (0-10)** | **{totals['baseline']}** | **{totals['candidate']}** |")
    for name in ("precios_inventados", "marcador_de_pago_visible", "datos_de_pago_faltantes", "datos_de_pago_sin_pedir", "asesor_callado", "sin_ia", "formato_imperfecto", "demasiado_larga", "varias_preguntas", "repite_respuesta_anterior"):
        counts = {label: sum(1 for row in rows for check in row[label]["checks"] if check[name]) for label in ("baseline", "candidate")}
        lines.append(f"| {name.replace('_', ' ')} | {counts['baseline']} | {counts['candidate']} |")
    for key in ("tokens_entrada_promedio", "tokens_en_cache_promedio", "tokens_salida_promedio", "ms_promedio", "costo_usd_sin_cache"):
        lines.append(f"| {key.replace('_', ' ')} | {data['usage']['baseline'][key]} | {data['usage']['candidate'][key]} |")
    gasto = data.get("gasto") or {}
    lines += ["", f"Gasto de la corrida: asistente USD {gasto.get('asistente_usd', 0):.4f} · juez USD {gasto.get('juez_usd', 0):.4f}."]
    wins = {name: sum(1 for row in rows if row["pairwise"]["ganador"] == name) for name in ("baseline", "candidate", "empate")}
    lines += ["", f"Comparación a ciegas: candidate gana {wins['candidate']}, baseline gana {wins['baseline']}, empates {wins['empate']}.", ""]

    kinds = sorted({turn["kind"] for label in ("baseline",) for slug in data["transcripts"][label] for sample in data["transcripts"][label][slug] for turn in sample})
    lines += ["## Por tipo de mensaje del cliente (puntaje 0-10)", "", "| Tipo | Baseline | Candidate |", "|---|---|---|"]
    for kind in kinds:
        values = {}
        for label in ("baseline", "candidate"):
            scores = []
            for row in rows:
                turns = data["transcripts"][label][row["tenant"]][row["sample"]]
                by_number = {int(turn.get("turno", 0)): turn for turn in row[label]["scores"]}
                scores += [_turn_score(by_number[t["turn"]]) for t in turns if t["kind"] == kind and t["turn"] in by_number]
            values[label] = _mean(scores)
        lines.append(f"| {kind} | {values['baseline']} | {values['candidate']} |")

    lines += ["", "## Por negocio", "", "| Negocio | Baseline | Candidate | A ciegas | Razón del juez |", "|---|---|---|---|---|"]
    for row in rows:
        b, c = (_mean(_turn_score(turn) for turn in row[label]["scores"]) for label in ("baseline", "candidate"))
        lines.append(f"| {row['tenant']} ({row['sample'] + 1}) | {b} | {c} | {row['pairwise']['ganador']} | {row['pairwise']['razon']} |")
    lines += ["", "## Conversaciones", ""]
    for row in rows:
        lines.append(f"### {row['tenant']} (muestra {row['sample'] + 1})")
        for label in ("baseline", "candidate"):
            lines += ["", f"**{label}** — {row[label]['general']}", ""]
            notes = {int(turn.get("turno", 0)): turn for turn in row[label]["scores"]}
            for turn in data["transcripts"][label][row["tenant"]][row["sample"]]:
                score = notes.get(turn["turn"], {})
                lines.append(f"- **Cliente:** {turn['message']}  \n  **Asistente ({_turn_score(score):.0f}/10):** {turn['reply']}  \n  _{score.get('nota', '')}_")
        lines.append("")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
