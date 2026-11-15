"""Elegir el modelo del asesor: compara corridas de la puerta de calidad (`run_standard_gate.py`) hechas con el mismo código, las mismas
conversaciones y el mismo juez, cambiando solo el modelo (`--model`).

La regla de decisión se fijó antes de ver resultados (14 nov 2026), para que el resultado no la acomode:
1. Queda fuera el modelo con alguna falla crítica (`CRITICAL`): un error con los datos de pago, que no pase el chat al equipo cuando
   debe o una respuesta que el motor no pudo usar (el cliente recibe «Hubo un problema…»). Con dinero de por medio, estos errores no
   se compensan con nada.
2. Queda fuera el que tarda demasiado: el 5 % más lento de sus respuestas pasa de `MAX_P95_SECONDS`.
3. De los que quedan, gana el que tiene más conversaciones sin ninguna falla. Si dos quedan a `TIE_CONVERSATIONS` o menos, gana el más
   barato.

    python experiments/quality_lab/compare_models.py --experiments <id1>,<id2>,... --output <id>

Escribe `results/<id>/comparison.md` con la tabla y el veredicto. No llama a ningún modelo: lee los `data.json` de cada corrida.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
RESULTS = LAB / "results"
sys.path.insert(0, str(LAB))

from standard import EXACT_RULES, JUDGE_RULES  # noqa: E402

# Las reglas cuya falla deja fuera a un modelo: tocan el dinero del cliente o lo dejan sin atención.
CRITICAL = (
    "el_asesor_habla",
    "datos_cuando_los_necesita",
    "sin_datos_sin_pedirlos",
    "no_repite_el_bloque",
    "sin_marcadores",
    "sin_numeros_de_pago_falsos",
    "pasa_al_equipo_cuando_debe",
    "nota_para_el_equipo",
    "no_dice_nada_falso_del_pago",
    "no_pide_el_dato_de_pago",
)
# Por WhatsApp, una respuesta que tarda más de esto ya se siente lenta.
MAX_P95_SECONDS = 8.0
# Con tres muestras, una conversación de diferencia es ruido: entonces decide el precio.
TIE_CONVERSATIONS = 1


def summarize(data: dict) -> dict:
    """Una corrida en una fila: qué modelo, cuántas conversaciones pasan todo, sus fallas (críticas y de calidad), velocidad y costo."""
    rows = data["rows"]
    per_message = data.get("por_mensaje") or {}
    failing = {rule: sum(1 for row in rows if row["failures"].get(rule)) for rule in {**EXACT_RULES, **JUDGE_RULES}}
    critical = {rule: count for rule, count in failing.items() if rule in CRITICAL and count}
    # Sin respuesta de la IA, el cliente recibe «Hubo un problema…». Fuera de formato, en cambio, recibe la respuesta: solo se pierde
    # la intención (`ai_orchestrator.py`).
    unanswered = int(per_message.get("sin_respuesta_de_la_ia") or 0)
    if unanswered:
        critical["sin_respuesta_de_la_ia"] = unanswered
    quality = {rule: count for rule, count in failing.items() if rule not in CRITICAL and count}
    if per_message.get("fuera_de_formato"):
        quality["fuera_de_formato"] = int(per_message["fuera_de_formato"])
    return {
        "experiment": data["experiment"],
        "model": data["model"],
        "conversations": len(rows),
        "clean": sum(1 for row in rows if not any(row["failures"].values())),
        "critical": critical,
        "quality": quality,
        "p50": per_message.get("segundos_mediana"),
        "p95": per_message.get("segundos_p95"),
        "usd_1000": per_message.get("usd_por_1000_mensajes"),
        "reasoning": per_message.get("tokens_de_razonamiento_por_mensaje", 0),
    }


def merge(runs: list[dict]) -> list[dict]:
    """Una fila por modelo con todas sus corridas (por ejemplo, la de pagos y la de «Cuándo pasar a una persona»): se suman las
    conversaciones y las fallas. De la velocidad queda la peor (el 5 % más lento de la corrida más lenta) y la mediana y el costo se
    promedian por conversación."""
    merged: dict[str, dict] = {}
    for run in runs:
        item = merged.get(run["model"])
        if item is None:
            merged[run["model"]] = {**run, "critical": dict(run["critical"]), "quality": dict(run["quality"]), "experiments": [run["experiment"]]}
            continue
        total = item["conversations"] + run["conversations"]
        for field in ("p50", "usd_1000"):
            if item[field] is not None and run[field] is not None:
                item[field] = round((item[field] * item["conversations"] + run[field] * run["conversations"]) / total, 2)
        item["p95"] = max(value for value in (item["p95"], run["p95"]) if value is not None) if (item["p95"] or run["p95"]) else None
        for field in ("critical", "quality"):
            for rule, count in run[field].items():
                item[field][rule] = item[field].get(rule, 0) + count
        item["conversations"], item["clean"] = total, item["clean"] + run["clean"]
        item["experiments"].append(run["experiment"])
    return list(merged.values())


def decide(models: list[dict]) -> tuple[dict | None, dict[str, str]]:
    """El modelo que gana según la regla del módulo (o None si ninguno califica) y, de cada uno, por qué queda fuera o en qué puesto."""
    why: dict[str, str] = {}
    eligible = []
    for item in models:
        if item["critical"]:
            why[item["model"]] = "fuera: " + ", ".join(f"{rule.replace('_', ' ')} ({count})" for rule, count in item["critical"].items())
        elif item["p95"] is None or item["p95"] > MAX_P95_SECONDS:
            why[item["model"]] = f"fuera: el 5 % más lento tarda {item['p95']} s (máximo {MAX_P95_SECONDS:g} s)"
        else:
            eligible.append(item)
    if not eligible:
        return None, why
    best_clean = max(item["clean"] for item in eligible)
    contenders = [item for item in eligible if best_clean - item["clean"] <= TIE_CONVERSATIONS]
    winner = min(contenders, key=lambda item: (item["usd_1000"] if item["usd_1000"] is not None else float("inf"), -item["clean"]))
    for item in eligible:
        if item is winner:
            why[item["model"]] = "gana"
        elif item in contenders:
            why[item["model"]] = "empata en calidad, pero cuesta más"
        else:
            why[item["model"]] = f"califica, pero tiene {best_clean - item['clean']} conversaciones limpias menos que el mejor"
    return winner, why


def build(models: list[dict]) -> str:
    winner, why = decide(models)
    lines = [
        "# Elegir el modelo del asesor",
        "",
        "Mismo código, mismas conversaciones y mismo juez; solo cambia el modelo. Regla de decisión fijada antes de ver resultados "
        f"(`compare_models.py`): fuera con cualquier falla crítica o si el 5 % más lento pasa de {MAX_P95_SECONDS:g} s; de los que quedan, "
        f"más conversaciones sin fallas, y con {TIE_CONVERSATIONS} o menos de diferencia, el más barato.",
        "",
        "| Modelo | Conversaciones sin fallas | Fallas críticas | Fallas de calidad | Respuesta (mediana · 5 % más lento) | USD por 1.000 mensajes | Veredicto |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in sorted(models, key=lambda item: -item["clean"]):
        critical = ", ".join(f"{rule.replace('_', ' ')} {count}" for rule, count in item["critical"].items()) or "—"
        quality = ", ".join(f"{rule.replace('_', ' ')} {count}" for rule, count in item["quality"].items()) or "—"
        lines.append(f"| `{item['model']}` | {item['clean']} de {item['conversations']} | {critical} | {quality} | {item['p50']} s · {item['p95']} s "
                     f"| {item['usd_1000']} | {why[item['model']]} |")
    lines += ["", f"**Veredicto:** {'`' + winner['model'] + '`' if winner else 'ningún modelo califica'}.", "",
              "Corridas: " + ", ".join(f"`{name}`" for item in models for name in item.get("experiments", [item["experiment"]])) + "."]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiments", required=True, help="Corridas de la puerta, separadas por coma")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    models = merge([summarize(json.loads((RESULTS / name / "data.json").read_text(encoding="utf-8"))) for name in args.experiments.split(",") if name])
    report = build(models)
    output = RESULTS / args.output
    output.mkdir(parents=True, exist_ok=True)
    (output / "comparison.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
