"""La evaluación del lector de pagos: ¿entiende bien qué pide el cliente sobre el pago? Con la IA real, caso por caso.

El lector (`application/pipeline/payment_reading.py`) es una llamada corta, antes del asesor, que dice si con este mensaje el cliente
debe recibir los datos para pagar, de qué medio, y si dice que ya pagó. Si se equivoca, todo lo demás se equivoca con él: el motor
le indica al asesor algo falso (19 nov 2026: «Me convence, lo quiero» leído como «pide los datos»). Aquí se corren los casos de
`reader_cases.py` con la función real del motor (`read_customer_message`) y el texto del lector del árbol de trabajo, varias veces
cada uno, y se dice cuántas veces acertó.

    python experiments/quality_lab/run_reader_eval.py --experiment <id> [--samples 3] [--model <modelo>] [--max-usd 0.05]

Usa la clave de OpenRouter del `.env` (nunca la imprime) con el negocio de ejemplo `asesor_ai_prod`, importado en un almacén temporal.
Tiene costo (centavos): antes de correr calcula cuánto y no arranca si pasa de `--max-usd`. Los resultados van a
`experiments/quality_lab/results/<id>/`. Termina con código 1 si algún caso falla alguna vez.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

from dotenv import dotenv_values

LAB = Path(__file__).resolve().parent
REPO = LAB.parents[1]
RESULTS = LAB / "results"
sys.path[:0] = [str(LAB), str(REPO / "project")]

import costs  # noqa: E402
from reader_cases import CASES, ReaderCase  # noqa: E402

SLUG = "asesor_ai_prod"
# Una llamada del lector: sus instrucciones con los medios, el contexto y el mensaje (unos 650 tokens) y un JSON corto de respuesta.
READER_TOKENS = (700, 40)


def mistakes(case: ReaderCase, reading) -> list[str]:
    """En qué se equivocó el lector en ese caso ([] si acertó). `reading` es lo que devolvió el motor (None si no hubo lectura)."""
    if reading is None:
        return ["no hubo lectura"]
    wrong = []
    if reading.wants_details != case.wants_details:
        wrong.append("dijo que recibe los datos" if reading.wants_details else "dijo que no recibe los datos")
    if case.wants_details and case.method and reading.method.split(":")[0] != case.method:
        wrong.append(f"medio «{reading.method or 'ninguno'}» en vez de «{case.method}»")
    if reading.says_paid != case.says_paid:
        wrong.append("dijo que ya pagó" if reading.says_paid else "no vio que ya pagó")
    return wrong


def _prepare_store(work: Path) -> None:
    """El negocio de ejemplo en un almacén temporal, como lo publica el panel. Antes de importar el motor: lee el entorno al cargar."""
    from cryptography.fernet import Fernet

    os.environ.update({
        "MODE": "test",
        "DATABASE_URL": "sqlite:///:memory:",
        "BUSINESS_CONFIG_DATABASE_URL": f"sqlite:///{(work / 'negocios.sqlite3').as_posix()}",
        "BUSINESS_CONFIG_SECRETS_KEY": Fernet.generate_key().decode(),
        "ENABLE_FILE_LOGS": "0",
    })
    from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
    from app.infrastructure.business_config.example_businesses import import_examples

    engine = create_business_config_engine(os.environ["BUSINESS_CONFIG_DATABASE_URL"])
    create_local_schema(engine)
    import_examples(build_business_config_service(engine, secrets_key=os.environ["BUSINESS_CONFIG_SECRETS_KEY"]))
    engine.dispose()


def run(key: str, model: str, samples: int) -> tuple[list[dict], list[dict]]:
    """Cada caso, `samples` veces, con la función real del lector: lo que leyó y en qué se equivocó. Y lo que costó cada llamada."""
    import logging

    from app.application.pipeline.payment_delivery import AWAITING_PAYMENT
    from app.application.pipeline.payment_reading import read_customer_message
    from app.application.runtime import load_tenant_runtime_yaml
    from app.domain.operations.operational_state import OperationalState
    from app.infrastructure.ai.llm_runtime import LLMRuntime

    logging.disable(logging.CRITICAL)
    base = load_tenant_runtime_yaml(SLUG, channel="whatsapp")
    llm = LLMRuntime()

    def one(job: tuple[ReaderCase, int]) -> tuple[dict, list[dict]]:
        case, sample = job
        spent: list[dict] = []
        config = SimpleNamespace(api_key=key, model_name=model, on_usage=lambda _m, prompt, completion, cost: spent.append(
            {"prompt_tokens": prompt, "completion_tokens": completion, **({"cost": cost} if cost is not None else {})}))
        runtime = {**base, "conversation_history": [{"role": "assistant", "text": case.last_reply}] if case.last_reply else []}
        # Ya le llegaron los datos de ese medio y falta que pague: así lo sabe el motor.
        state = OperationalState(active_process="payment", active_option=case.sent, pending_action=AWAITING_PAYMENT) if case.sent else None
        reading = read_customer_message(llm, bot_config=config, runtime_yaml=runtime, user_message=case.message, state=state,
                                        remembered=case.sent, tenant=SLUG)
        row = {"case": case.name, "sample": sample, "message": case.message, "last_reply": case.last_reply,
               "expected": {"wants_details": case.wants_details, "method": case.method, "says_paid": case.says_paid},
               "read": None if reading is None else {"wants_details": reading.wants_details, "method": reading.method, "says_paid": reading.says_paid},
               "mistakes": mistakes(case, reading)}
        return row, spent

    jobs = [(case, sample) for case in CASES for sample in range(samples)]
    with ThreadPoolExecutor(max_workers=6) as pool:
        done = list(pool.map(one, jobs))
    return [row for row, _ in done], [usage for _, usages in done for usage in usages]


def build_report(data: dict) -> str:
    rows, samples = data["rows"], data["samples"]
    right = sum(1 for row in rows if not row["mistakes"])
    lines = [
        f"# Lector de pagos: {data['experiment']}",
        "",
        f"**{right} de {len(rows)} lecturas correctas** · modelo `{data['model']}` · {len(CASES)} casos, {samples} veces cada uno · "
        f"gasto USD {data['gasto_usd']:.4f}",
        "",
        "| Caso | Mensaje | Debe recibir los datos | Acierta |",
        "|---|---|---|---|",
    ]
    for case in CASES:
        mine = [row for row in rows if row["case"] == case.name]
        good = sum(1 for row in mine if not row["mistakes"])
        lines.append(f"| {'✅' if good == len(mine) else '❌'} {case.name} | «{case.message}» | {'sí' if case.wants_details else 'no'}"
                     f"{f' ({case.method})' if case.method else ''}{' · ya pagó' if case.says_paid else ''} | {good} de {len(mine)} |")
    wrong = [row for row in rows if row["mistakes"]]
    if wrong:
        lines += ["", "## Lo que leyó mal", ""]
        for row in wrong:
            context = f" (el asesor le había dicho: «{row['last_reply']}»)" if row["last_reply"] else ""
            lines.append(f"- **{row['case']}** · «{row['message']}»{context}: {'; '.join(row['mistakes'])}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--samples", type=int, default=3)
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
    budget = len(CASES) * args.samples * costs._cost(READER_TOKENS, price)
    print(f"Costo calculado: USD {budget:.3f} (tope USD {args.max_usd:.2f}) · {len(CASES)} casos × {args.samples} · modelo {model}", flush=True)
    if budget > args.max_usd:
        raise SystemExit("El cálculo supera el tope: baja las muestras o sube --max-usd con autorización.")

    with tempfile.TemporaryDirectory(prefix="lab-lector-") as work:
        _prepare_store(Path(work))
        rows, usages = run(key, model, args.samples)
    data = {"experiment": args.experiment, "model": model, "samples": args.samples, "rows": rows, "gasto_usd": costs.spent(usages, price)}
    output.mkdir(parents=True)
    (output / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    (output / "report.md").write_text(build_report(data), encoding="utf-8")
    right = sum(1 for row in rows if not row["mistakes"])
    print(f"\n{right} de {len(rows)} lecturas correctas · gasto USD {data['gasto_usd']:.4f} · informe: {output / 'report.md'}")
    for case in CASES:
        mine = [row for row in rows if row["case"] == case.name]
        good = sum(1 for row in mine if not row["mistakes"])
        print(f"  {'✅' if good == len(mine) else '❌'} {case.name}: {good} de {len(mine)}")
    return 0 if right == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
