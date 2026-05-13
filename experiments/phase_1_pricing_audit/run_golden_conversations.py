"""
run_golden_conversations.py
────────────────────────────
Ejecuta una conversación humana secuencial de 10 turnos contra cualquier tenant,
usando el pipeline completo de producción sin modificarlo.

Las respuestas se guardan en results/baseline_conversations.md o en el archivo
indicado por --output. Cada corrida agrega una entrada a results/evolution_log.md.

Uso:
    python experiments/phase_1_pricing_audit/run_golden_conversations.py
    python experiments/phase_1_pricing_audit/run_golden_conversations.py --label candidate_v1 --tenant tienda_de_ropa

El script NO modifica ningún archivo de producción.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_DIR = REPO_ROOT / "project"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
sys.path.insert(0, str(PROJECT_DIR))
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

from app.application.runtime import load_tenant_runtime_yaml  # noqa: E402
from app.services.ai_service import AIService  # noqa: E402

DEFAULT_TENANT = "asesor_ai_prod"

HUMAN_CONVERSATION = [
    "Hola, ¿cómo estás?",
    "Me puedes dar más información.",
    "¿Qué venden exactamente?",
    "¿Cómo funciona eso?",
    "¿Eso me sirve para una tienda de ropa?",
    "¿Qué incluye?",
    "¿Qué no incluye?",
    "¿Y qué precio tiene?",
    "Está como costoso.",
    "Bueno, quiero empezar.",
]

METRIC_KEYS = (
    "chars",
    "lines",
    "estimated_tokens",
    "has_includes",
    "has_not_included",
    "has_price_framing",
    "has_roi_hints",
)

# Etiquetas de evaluación manual (se dejan vacías para llenar después)
EVAL_DIMENSIONS = [
    "claridad_oferta",
    "menciona_includes",
    "menciona_not_included",
    "framing_precio",
    "naturalidad",
    "cta_final",
]


def _tenant_obj(slug: str = DEFAULT_TENANT) -> SimpleNamespace:
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def _ask(service: AIService, *, tenant_slug: str, user_id: str, message: str) -> str:
    runtime_yaml = load_tenant_runtime_yaml(tenant_slug)
    try:
        response, _ai_used, _metadata = service.generate_business_reply(
            tenant=_tenant_obj(tenant_slug),
            bot_config=None,
            user_message=message,
            conversation_history=[],
            faq_results=[],
            yaml_config=runtime_yaml,
            user_id=user_id,
            include_metadata=True,
        )
        return str(response or "").strip()
    except Exception as exc:  # noqa: BLE001
        return f"[ERROR: {exc}]"


def _load_metrics() -> tuple[Path, dict]:
    metrics_path = RESULTS_DIR / "baseline_metrics.json"
    if not metrics_path.exists():
        return metrics_path, {}
    try:
        raw_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return metrics_path, {}
    return metrics_path, {key: raw_metrics.get(key) for key in METRIC_KEYS}


def _append_evolution_log(*, label: str, tenant_slug: str, output_path: Path) -> Path:
    log_path = RESULTS_DIR / "evolution_log.md"
    metrics_path, metrics = _load_metrics()
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    section_lines = [
        f"## {timestamp} - {label}",
        "",
        f"- Label: `{label}`",
        f"- Tenant evaluado: `{tenant_slug}`",
        f"- Archivo generado: `results/{output_path.name}`",
    ]
    if metrics:
        section_lines.append(f"- Metricas fuente: `{metrics_path.name}`")
        for key in METRIC_KEYS:
            section_lines.append(f"- {key}: `{metrics.get(key)}`")
    else:
        section_lines.append("- Metricas fuente: `baseline_metrics.json no disponible`")
    section_lines.extend(["- Observaciones: pendiente de revision", "", "---", ""])

    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else "# Evolution Log\n\n"
    suffix = "" if existing.endswith(("\n", "\r")) else "\n"
    log_path.write_text(existing + suffix + "\n".join(section_lines), encoding="utf-8")
    return log_path


def _build_markdown(
    user_id: str,
    results: list[dict],
    *,
    tenant_slug: str,
    label: str = "baseline",
) -> str:
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Golden Conversations — {label}",
        f"",
        f"- **Tenant:** `{tenant_slug}`",
        f"- **User ID de prueba:** `{user_id}`",
        f"- **Fecha:** {now}",
        f"- **Label:** `{label}`",
        f"- **Modo:** conversación humana secuencial de 10 turnos",
        f"",
        f"---",
        f"",
    ]

    eval_header = " | ".join(f"`{d}`" for d in EVAL_DIMENSIONS)
    eval_empty  = " | ".join("—" for _ in EVAL_DIMENSIONS)

    for i, item in enumerate(results, 1):
        lines += [
            f"## Turno {i}",
            f"",
            f"**Cliente:** {item['question']}",
            f"",
            f"**Asesor:**",
            f"",
            f"> {item['answer']}",
            f"",
            f"**Evaluación manual:**",
            f"",
            f"| {eval_header} |",
            f"| {' | '.join('---' for _ in EVAL_DIMENSIONS)} |",
            f"| {eval_empty} |",
            f"",
            f"---",
            f"",
        ]

    lines += [
        "## Notas generales",
        "",
        "_Completar tras revisión manual._",
        "",
    ]

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ejecuta una conversación humana completa de 10 turnos.")
    parser.add_argument(
        "--output",
        default=str(RESULTS_DIR / "baseline_conversations.md"),
        help="Archivo de salida (default: results/baseline_conversations.md)",
    )
    parser.add_argument(
        "--label",
        default="baseline",
        help="Etiqueta para este run (ej: baseline, candidate_v1)",
    )
    parser.add_argument(
        "--tenant",
        default=DEFAULT_TENANT,
        help=f"Tenant a evaluar (default: {DEFAULT_TENANT})",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    service = AIService()
    tenant_slug = str(args.tenant or DEFAULT_TENANT).strip() or DEFAULT_TENANT
    user_id = f"golden-{tenant_slug}-{args.label}".replace(" ", "-")

    print(f"Tenant:  {tenant_slug}")
    print(f"Label:   {args.label}")
    print(f"User ID: {user_id}")
    print(f"Output:  {output_path}\n")

    results: list[dict] = []

    for i, question in enumerate(HUMAN_CONVERSATION, 1):
        print(f"[{i}/{len(HUMAN_CONVERSATION)}] {question}")
        answer = _ask(service, tenant_slug=tenant_slug, user_id=user_id, message=question)
        print(f"  → {answer[:120]}{'...' if len(answer) > 120 else ''}\n")
        results.append({"question": question, "answer": answer})

    md = _build_markdown(user_id, results, tenant_slug=tenant_slug, label=args.label)
    output_path.write_text(md, encoding="utf-8")
    print(f"Conversaciones guardadas en: {output_path}")
    log_path = _append_evolution_log(label=args.label, tenant_slug=tenant_slug, output_path=output_path)
    print(f"Historial actualizado en: {log_path}")


if __name__ == "__main__":
    main()
