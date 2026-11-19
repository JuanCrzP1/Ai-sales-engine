"""La puerta de calidad: ¿cumple el asesor el estándar? Pasa o no pasa, con la IA real.

Corre las conversaciones del estándar (`standard.py`: el chat real de producción del 13 nov 2026 y frases sueltas de clientes) con el
código del árbol de trabajo, en una copia aislada y con el modelo real. Cada regla pasa o no pasa en cada conversación:
- las exactas se comprueban sin opinión (le llegaron los datos, el asesor habló, no se repitió el bloque…);
- las demás las revisa un juez IA: señala cada falla con la frase textual del asesor (sin ella no vale) y un segundo revisor la
  confirma mirando solo ese turno. Un juez solo, leyendo toda la conversación, se equivocaba demasiado.

Un cambio al asesor se publica solo si pasan todas las reglas en todas las conversaciones. Termina con código 1 si alguna no pasa.

Con `--escalation`, las conversaciones y la regla de «Cuándo pasar a una persona» (`escalation_standard.py`). Con `--panel`, las de lo
que configura el negocio en el panel: el trato y el tono, el largo, los emojis, el horario y la forma de cerrar (`panel_standard.py`).

    python experiments/quality_lab/run_standard_gate.py --experiment <id> [--samples 3] [--tenants asesor_ai_prod] [--model <modelo>]
        [--escalation | --panel]

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
import panel_standard  # noqa: E402
from run_quality_eval import REPO, RESULTS, _child_env, _export, _git, _model_prices, _usage  # noqa: E402
from escalation_standard import HANDOFF_MESSAGE, PROFILE as ESCALATION_PROFILE  # noqa: E402
from standard import CONFIRM, EXACT_RULES, JUDGE, JUDGE_RULES, confirm_request, exact_failures, judge_failures, keep_confirmed, transcript  # noqa: E402

# Para calcular el costo antes de correr: las conversaciones del estándar y sus turnos, por negocio y por muestra (con `--escalation`,
# las de paso a persona). Con varios medios de pago; con uno solo son menos.
CONVERSATIONS, TURNS = 10, 33
ESCALATION_CONVERSATIONS, ESCALATION_TURNS = 4, 11
PANEL_CONVERSATIONS, PANEL_TURNS = 3, 9
_METHOD_NAMES = {"bank": "transferencia bancaria", "link": "link de pago", "breb": "Bre-B", "nequi": "Nequi", "daviplata": "Daviplata"}


def _ficha(facts: dict) -> dict:
    """Lo que el juez necesita saber del negocio para revisar las reglas: qué medios de pago tiene y, si las configuró, sus reglas
    para pasar el chat a una persona."""
    ficha = {"medios_de_pago_del_negocio": [_METHOD_NAMES.get(kind, kind) for kind, has in facts["pagos_disponibles"].items() if has]}
    if facts.get("paso_a_persona"):
        ficha["reglas_para_pasar_a_una_persona"] = facts["paso_a_persona"]
    return ficha


def _publish_escalation(tree: Path, tenants: list[str]) -> None:
    """Escribe las reglas de paso a persona del estándar (`escalation_standard.PROFILE`) en los negocios de la copia aislada, antes
    de que la captura los importe: es lo que haría el negocio en el panel. También su mensaje para pasar el chat y el cierre con una
    persona, como el negocio real."""
    for slug in tenants:
        path = tree / "project" / "config" / "tenants" / slug / "business-config.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["escalation"] = ESCALATION_PROFILE
        document.setdefault("messages", {})["human_handoff"] = HANDOFF_MESSAGE
        document["capabilities"]["closing_methods"]["human_handoff"] = True
        path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")


def _publish_panel(tree: Path, tenants: list[str]) -> None:
    """Publica en la copia aislada cada negocio con su perfil del panel (`panel_standard.PROFILES`): trato, tono, largo, emojis,
    horario y forma de cerrar, como los guardaría el negocio en el panel."""
    missing = [slug for slug in tenants if slug not in panel_standard.PROFILES]
    if missing:
        raise SystemExit(f"Sin perfil del panel para: {', '.join(missing)}. Hay perfiles para: {', '.join(panel_standard.PROFILES)}.")
    for slug in tenants:
        path = tree / "project" / "config" / "tenants" / slug / "business-config.json"
        document = panel_standard.publish(json.loads(path.read_text(encoding="utf-8")), panel_standard.PROFILES[slug])
        path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")


def _rules(panel: bool) -> tuple[dict[str, str], dict[str, str]]:
    """Las reglas exactas y las del juez de la corrida. Con `--panel`, las exactas de pagos siguen (marcadores, repetir, pasar sin
    motivo…) y se suman las del panel; el juez revisa solo las del panel."""
    if panel:
        return {**EXACT_RULES, **panel_standard.EXACT_RULES}, panel_standard.JUDGE_RULES
    return EXACT_RULES, JUDGE_RULES


def judge_conversation(key: str, model: str, facts: dict, turns: list[dict], panel: bool = False) -> tuple[dict[str, list[dict]], list[dict], list[dict]]:
    """Las reglas del juez en una conversación: por cada una, dónde no pasa y por qué (lista vacía si pasa); las fallas que reportó
    y no valieron (sin su frase textual, o no confirmadas por el segundo revisor) y lo que gastaron sus llamadas."""
    rules = _rules(panel)[1]
    sheet = json.dumps(panel_standard.ficha(facts, _METHOD_NAMES) if panel else _ficha(facts), ensure_ascii=False)
    user = f"FICHA:\n{sheet}\n\nCONVERSACIÓN:\n{transcript(turns)}"
    verdict, usage = judge._call(key, model, panel_standard.JUDGE if panel else JUDGE, user)
    failures, discarded = judge_failures(verdict, turns, rules)
    usages = [usage]
    confirm_prompt, context = (panel_standard.CONFIRM, f"FICHA:\n{sheet}\n\n") if panel else (CONFIRM, "")

    def confirm(rule: str, conversation: list[dict], failure: dict) -> bool:
        answer, spent = judge._call(key, model, confirm_prompt, confirm_request(rule, conversation, failure, rules, context))
        usages.append(spent)
        return answer.get("confirmada") is True

    # Cada falla que señala el juez la revisa sola un segundo revisor: solo cuentan las que confirma.
    failures, unconfirmed = keep_confirmed(failures, turns, confirm)
    return failures, discarded + unconfirmed, usages


def evaluate(captured: dict, key: str, judge_model: str, panel: bool = False) -> tuple[list[dict], list[dict]]:
    """Cada conversación con las reglas que no pasa (exactas y del juez), y lo que gastó el juez."""
    jobs = [(slug, data["facts"], turns) for slug, data in captured["results"].items() for turns in data["samples"]]

    def run(job):
        slug, facts, turns = job
        judged, discarded, usages = judge_conversation(key, judge_model, facts, turns, panel)
        exact = {**exact_failures(turns), **(panel_standard.exact_failures(turns, facts) if panel else {})}
        row = {"tenant": slug, "conversation": turns[0].get("conversation", ""), "turns": turns, "failures": {**exact, **judged},
               "discarded": discarded}
        return row, usages

    with ThreadPoolExecutor(max_workers=6) as pool:
        done = list(pool.map(run, jobs))
    return [row for row, _usages in done], [usage for _row, usages in done for usage in usages]


def build_report(data: dict) -> str:
    rows = data["rows"]
    exact_rules, judge_rules = _rules(data.get("modo") == "panel")
    rules = {**exact_rules, **judge_rules}
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
        kind = "exacta" if name in exact_rules else "juez"
        lines.append(f"| {'✅' if not broken else '❌'} {name.replace('_', ' ')} ({kind}) | {len(rows) - broken} de {len(rows)} | {text.split('. ')[0].rstrip('.')}. |")
    discarded = sum(len(row.get("discarded") or []) for row in rows)
    per_message = data.get("por_mensaje") or {}
    lines += ["", f"Gasto de la corrida: asesor USD {data['gasto']['asesor_usd']:.4f} · juez USD {data['gasto']['juez_usd']:.4f}. "
              f"Llamadas al modelo por mensaje: {data['llamadas_por_mensaje']}. Fallas que señaló el juez y no valieron (sin su frase "
              f"textual, o que el segundo revisor no confirmó): {discarded}.", ""]
    if per_message:
        lines += [f"Por cada mensaje del cliente: responde en {per_message['segundos_mediana']} s (el 5 % más lento, "
                  f"{per_message['segundos_p95']} s o más) · USD {per_message['usd_por_1000_mensajes']} por cada 1.000 mensajes · "
                  f"fuera de formato: {per_message['fuera_de_formato']} de {per_message['mensajes']} · sin respuesta de la IA: "
                  f"{per_message['sin_respuesta_de_la_ia']} · tokens de razonamiento por mensaje: "
                  f"{per_message['tokens_de_razonamiento_por_mensaje']}.", ""]
    if not passed:
        lines += ["## Lo que no pasó", ""]
        for name in rules:
            for row, failure in failed[name]:
                turn = next((turn for turn in row["turns"] if turn["turn"] == failure["turn"]), None)
                lines.append(f"- **{name.replace('_', ' ')}** · {row['tenant']} · {row['conversation']} · turno {failure['turn']}: {failure['why']}")
                if turn:
                    lines.append(f"  - Cliente: «{turn['message']}»")
                    lines.append(f"  - Asesor: «{' ⏎ '.join(turn['reply'].split(chr(10)))[:420]}»")
                    if turn.get("team_note"):
                        lines.append(f"  - Nota para el equipo: «{turn['team_note']}»")
        lines.append("")
    lines += ["## Las conversaciones", ""]
    for row in rows:
        lines += [f"### {row['tenant']} · {row['conversation']}", ""]
        for turn in row["turns"]:
            lines += [f"**[{turn['turn']}] Cliente:** {turn['message']}", "", f"**[{turn['turn']}] Asesor:** " + turn["reply"].replace("\n", "  \n"), ""]
            if turn.get("team_note"):
                lines += [f"*[{turn['turn']}] Nota para el equipo:* {turn['team_note']}", ""]
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
    parser.add_argument("--escalation", action="store_true", help="Publica los negocios con reglas de paso a persona y corre esas conversaciones")
    parser.add_argument("--panel", action="store_true", help="Publica los negocios con su perfil del panel y corre esas conversaciones")
    args = parser.parse_args()
    if args.escalation and args.panel:
        raise SystemExit("Elige --escalation o --panel, no los dos.")
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
    conversations, turns = (
        (ESCALATION_CONVERSATIONS, ESCALATION_TURNS) if args.escalation else (PANEL_CONVERSATIONS, PANEL_TURNS) if args.panel else (CONVERSATIONS, TURNS)
    )
    budget = costs.estimate_gate(messages=volume * turns, conversations=volume * conversations, model=model, judge=args.judge_model,
                                 models=costs.catalog({model, args.judge_model}), with_capture=not args.rejudge)
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
        if args.escalation:
            _publish_escalation(tree, tenants)
        if args.panel:
            _publish_panel(tree, tenants)
        settings = work_path / "candidate.json"
        settings.write_text(json.dumps({"label": "candidate", "commit": reference, "samples": args.samples, "tenants": tenants, "standard": "panel" if args.panel else True,
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


def _calls_usage(captured: dict) -> list[dict]:
    """Lo que informó OpenRouter de cada llamada al modelo en la captura (tokens y costo)."""
    return [call.get("usage") or {} for data in captured["results"].values() for sample in data["samples"] for turn in sample for call in turn["calls"]]


def per_message(captured: dict, price: tuple[float, float]) -> dict:
    """Lo que vive el cliente en cada mensaje, para comparar modelos: cuánto tarda la respuesta (todas sus llamadas al modelo), cuánto
    cuesta (lo que cobró OpenRouter), cuántas respuestas no vinieron en el formato del motor y cuántas no las respondió la IA. También
    los tokens que el modelo gastó razonando antes de responder."""
    turns = [turn for data in captured["results"].values() for sample in data["samples"] for turn in sample]
    # El saludo configurado del negocio no pasa por la IA: no cuenta.
    answered = [turn for turn in turns if turn.get("source") != "initial_message"]
    if not answered:
        return {}
    seconds = sorted(sum(call.get("ms", 0) for call in turn["calls"]) / 1000 for turn in answered)
    usages = [call.get("usage") or {} for turn in answered for call in turn["calls"]]
    reasoning = sum(((usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0) for usage in usages)
    return {
        "mensajes": len(answered),
        "segundos_mediana": round(seconds[len(seconds) // 2], 1),
        "segundos_p95": round(seconds[min(len(seconds) - 1, int(len(seconds) * 0.95))], 1),
        "usd_por_1000_mensajes": round(costs.spent(usages, price) / len(answered) * 1000, 2),
        "fuera_de_formato": sum(1 for turn in answered if turn.get("format_error")),
        "sin_respuesta_de_la_ia": sum(1 for turn in answered if not turn.get("ai_used")),
        "tokens_de_razonamiento_por_mensaje": round(reasoning / len(answered)),
    }


def report(args, captured: dict, key: str, output: Path) -> int:
    """Revisa las conversaciones capturadas con las reglas del estándar y escribe el informe. Devuelve 0 si pasan todas."""
    model, tenants = str(captured.get("model") or ""), sorted(captured["results"])
    rows, judge_usages = evaluate(captured, key, args.judge_model, args.panel)
    usage = _usage(captured, _model_prices(model))
    messages = sum(len(row["turns"]) for row in rows)
    data = {
        "por_mensaje": per_message(captured, _model_prices(model)),
        "experiment": args.experiment, "modo": "panel" if args.panel else "escalation" if args.escalation else "pagos", "candidate": captured.get("commit"), "model": model, "judge_model": args.judge_model,
        "samples": len(rows) // max(1, len(tenants)) // max(1, len({row["conversation"] for row in rows})),
        "tenants": tenants, "rows": [{key_: value for key_, value in row.items() if key_ != "turns"} | {"turns": [
            {name: turn.get(name, "") for name in ("turn", "message", "expect", "reply", "handoff", "team_note", "source", "ai_words")} for turn in row["turns"]]}
            for row in rows],
        "gasto": {"asesor_usd": costs.spent(_calls_usage(captured), _model_prices(model)),
                  "juez_usd": costs.spent(judge_usages, _model_prices(args.judge_model))},
        "llamadas_por_mensaje": round(usage["llamadas"] / messages, 2) if messages else 0,
    }
    (output / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    (output / "report.md").write_text(build_report(data), encoding="utf-8")
    broken = {name: sum(1 for row in rows if row["failures"][name]) for name in {**_rules(args.panel)[0], **_rules(args.panel)[1]}}
    print(f"\n{'PASA' if not any(broken.values()) else 'NO PASA'} · {len(rows)} conversaciones · informe: {output / 'report.md'}")
    print(f"  por mensaje: {data['por_mensaje']} · gasto real asesor USD {data['gasto']['asesor_usd']:.4f}, juez USD {data['gasto']['juez_usd']:.4f}")
    for name, count in broken.items():
        print(f"  {'✅' if not count else '❌'} {name.replace('_', ' ')}: {len(rows) - count} de {len(rows)}")
    return 0 if not any(broken.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
