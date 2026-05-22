"""Memory Lab — Phase 2 Validation.

BASELINE vs CANDIDATO para 12 escenarios de continuidad.

Diseño:
  - BASELINE: usuario fresco — sin memoria previa — el AI no tiene contexto.
  - CANDIDATO: usuario sembrado — turno de setup primero, luego turno de prueba.
  - Misma pregunta en ambos. El CANDIDATO debería responder diferente gracias a la memoria.

Qué valida:
  ✅ continuidad corta / larga
  ✅ follow-up de dolor
  ✅ pricing (ya vio precio)
  ✅ objeción (ya dijo "caro")
  ✅ reenganche cold
  ✅ demo / cierre
  ✅ usuario que vuelve horas después
  ✅ naturalidad: NO debe haber lenguaje CRM/sistema en respuesta
  ✅ impacto comercial: candidato avanza más hacia acción

Uso:
  python run_memory_lab.py --label phase2_memory_v1 [--tenant asesor_ai_prod]
"""
from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LAB_DIR = Path(__file__).resolve().parent
REPO_ROOT = LAB_DIR.parents[1]
PROJECT_DIR = REPO_ROOT / "project"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

ENV_FILE = REPO_ROOT / ".env"
if ENV_FILE.exists():
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE, override=False)

from lab_common import (
    normalize_text,
    parse_common_args,
    resolve_channel,
    resolve_tenant_slug,
    tenant_handle,
    utc_now_iso,
    write_json,
)
from lab_config import RESULTS_DIR


# ---------------------------------------------------------------------------
# 12 escenarios de continuidad
# ---------------------------------------------------------------------------

@dataclass
class MemoryScenario:
    id: str
    description: str
    seed_message: str   # Turno 1: planta memoria (solo para CANDIDATO)
    test_message: str   # Turno 2: mensaje que ambos reciben


SCENARIOS: list[MemoryScenario] = [
    MemoryScenario(
        id="continuidad_corta",
        description="Usuario vuelve después de un intercambio breve",
        seed_message="Hola, recibo muchos mensajes de clientes y no alcanzo a contestar todos",
        test_message="Entonces, ¿me explicás cómo funciona eso?",
    ),
    MemoryScenario(
        id="continuidad_larga",
        description="Usuario con historial rico — dolor + precio + objeción",
        seed_message="Yo pierdo leads todos los días porque no respondo rápido, necesito algo que me ayude",
        test_message="Bueno, ¿y cómo arrancamos?",
    ),
    MemoryScenario(
        id="follow_up_dolor",
        description="AI debe referenciar el dolor sin que el usuario lo repita",
        seed_message="Mi problema es que los clientes se me enfrían cuando tardo en responder",
        test_message="¿De verdad me puede ayudar con eso?",
    ),
    MemoryScenario(
        id="pricing_ya_vio",
        description="Usuario que ya vio el precio pregunta cómo pagar",
        seed_message="¿Cuánto cuesta el plan mensual?",
        test_message="Está bien, ¿cómo hago para pagar?",
    ),
    MemoryScenario(
        id="objecion_caro",
        description="Usuario que dijo 'está caro' regresa con interés",
        seed_message="Me parece caro, no sé si vale la pena",
        test_message="Pensándolo bien, ¿qué me garantizan?",
    ),
    MemoryScenario(
        id="reenganche_cold",
        description="Usuario que estuvo en contacto y se enfrió vuelve",
        seed_message="Oye me interesa pero lo voy a pensar, hablamos después",
        test_message="Hola de nuevo, ¿siguen con lo mismo?",
    ),
    MemoryScenario(
        id="demo_siguiente_paso",
        description="Usuario que pidió demo pregunta qué sigue",
        seed_message="¿Tienen alguna demo o prueba que pueda ver antes de comprar?",
        test_message="Ya vi la info, ¿qué sería el siguiente paso?",
    ),
    MemoryScenario(
        id="cierre",
        description="Usuario con toda la info lista para cerrar",
        seed_message="Me explicaste todo, el precio me parece bien y quiero empezar",
        test_message="¿Qué necesitan de mi parte para activarlo?",
    ),
    MemoryScenario(
        id="vuelve_horas_despues",
        description="Usuario warm regresa horas después con la misma intención",
        seed_message="Me interesa el servicio, pero tengo que revisar con mi socio",
        test_message="Ya hablé con él, le parece bien. ¿Cómo seguimos?",
    ),
    MemoryScenario(
        id="ya_hablo_antes",
        description="Usuario active vuelve en la misma sesión",
        seed_message="Tengo un negocio de ropa y recibo pedidos por WhatsApp, muchos se me van porque tardo",
        test_message="¿Cómo manejan eso con tiendas como la mía?",
    ),
    MemoryScenario(
        id="ya_dijo_dolor",
        description="Usuario que explicó su dolor ahora pregunta cómo funciona",
        seed_message="El problema mío es que trabajo solo y no puedo responder todo el día",
        test_message="¿Esto lo puedo manejar yo solo o necesito contratar a alguien?",
    ),
    MemoryScenario(
        id="ya_vio_precio_objeta",
        description="Usuario que vio precio y objetó quiere entender el valor",
        seed_message="Vi que cuesta bastante, ¿y si no me funciona qué pasa?",
        test_message="¿Cómo sé que vale la inversión para mi negocio?",
    ),
]


# ---------------------------------------------------------------------------
# Evaluación de naturalidad y comercialidad
# ---------------------------------------------------------------------------

# Palabras que NO deben aparecer en la respuesta del candidato
# (indicarían que el contexto de memoria sonó a CRM/sistema)
_CRM_MARKERS = [
    r"\bya habl\w+\b",
    r"\bya describi\w+\b",
    r"\bya recibi\w+\b",
    r"\bcontexto previo\b",
    r"\b[uú]ltima intenci\w+\b",
    r"\bdolor detectado\b",
    r"\bdato previo\b",
    r"\bsituaci[oó]n del cliente\b",
    r"\besta persona ya\b",
    r"\bregistro\b.*\bcliente\b",
    r"\bbase de datos\b",
    r"\bcrm\b",
]

# Indicadores de que la respuesta avanza comercialmente
_COMMERCIAL_ADVANCE = [
    r"\bempez\w+\b",
    r"\barranc\w+\b",
    r"\bactivar\b",
    r"\bsiguiente paso\b",
    r"\bpago\b",
    r"\blink\b",
    r"\bprueba\b",
    r"\baccion\b",
    r"\bte ayudo\b",
    r"\bte lo explico\b",
    r"\bte cuento\b",
    r"\bpuedo mostrarte\b",
]


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKD", str(text or ""))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.lower()


def _matches_any(text: str, patterns: list[str]) -> list[str]:
    norm = _norm(text)
    found = []
    for pattern in patterns:
        m = re.search(pattern, norm)
        if m:
            found.append(m.group(0))
    return found


def evaluate_memory_turn(*, baseline_reply: str, candidate_reply: str) -> dict[str, Any]:
    crm_in_candidate = _matches_any(candidate_reply, _CRM_MARKERS)
    crm_in_baseline = _matches_any(baseline_reply, _CRM_MARKERS)

    commercial_in_candidate = _matches_any(candidate_reply, _COMMERCIAL_ADVANCE)
    commercial_in_baseline = _matches_any(baseline_reply, _COMMERCIAL_ADVANCE)

    candidate_words = len(candidate_reply.split())
    baseline_words = len(baseline_reply.split())

    return {
        "crm_markers_in_candidate": crm_in_candidate,
        "crm_markers_in_baseline": crm_in_baseline,
        "crm_free": len(crm_in_candidate) == 0,
        "candidate_commercial_signals": commercial_in_candidate,
        "baseline_commercial_signals": commercial_in_baseline,
        "candidate_advances_more": len(commercial_in_candidate) > len(commercial_in_baseline),
        "candidate_words": candidate_words,
        "baseline_words": baseline_words,
        "word_delta": candidate_words - baseline_words,
    }


# ---------------------------------------------------------------------------
# Core: run one scenario
# ---------------------------------------------------------------------------

def run_scenario(
    scenario: MemoryScenario,
    *,
    service: Any,
    tenant_slug: str,
    channel: str,
    tenant: Any,
    runtime_yaml_fn: Any,
) -> dict[str, Any]:
    from app.application.runtime import load_tenant_runtime_yaml

    base_user = f"lab-mem-base-{scenario.id}"
    cand_user = f"lab-mem-cand-{scenario.id}"

    # BASELINE: send test message directly (no prior memory)
    baseline_yaml = load_tenant_runtime_yaml(tenant_slug, channel=channel)
    baseline_reply, _, _ = service.generate_business_reply(
        tenant=tenant,
        bot_config=None,
        user_message=scenario.test_message,
        conversation_history=[],
        faq_results=[],
        yaml_config=baseline_yaml,
        user_id=base_user,
        include_metadata=True,
    )

    # CANDIDATO: seed memory with setup turn, then send test message
    seed_yaml = load_tenant_runtime_yaml(tenant_slug, channel=channel)
    service.generate_business_reply(
        tenant=tenant,
        bot_config=None,
        user_message=scenario.seed_message,
        conversation_history=[],
        faq_results=[],
        yaml_config=seed_yaml,
        user_id=cand_user,
        include_metadata=True,
    )

    cand_yaml = load_tenant_runtime_yaml(tenant_slug, channel=channel)
    candidate_reply, _, _ = service.generate_business_reply(
        tenant=tenant,
        bot_config=None,
        user_message=scenario.test_message,
        conversation_history=[],
        faq_results=[],
        yaml_config=cand_yaml,
        user_id=cand_user,
        include_metadata=True,
    )

    baseline_reply = str(baseline_reply or "")
    candidate_reply = str(candidate_reply or "")

    evaluation = evaluate_memory_turn(
        baseline_reply=baseline_reply,
        candidate_reply=candidate_reply,
    )

    return {
        "scenario_id": scenario.id,
        "description": scenario.description,
        "seed_message": scenario.seed_message,
        "test_message": scenario.test_message,
        "baseline_reply": baseline_reply,
        "candidate_reply": candidate_reply,
        "evaluation": evaluation,
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _icon(value: bool) -> str:
    return "✅" if value else "❌"


def build_markdown_report(results: list[dict], *, label: str, tenant_slug: str, run_at: str) -> str:
    lines = [
        "# Memory Lab — Validación Fase 2",
        "",
        f"- **label**: {label}",
        f"- **tenant**: {tenant_slug}",
        f"- **run_at**: {run_at}",
        f"- **escenarios**: {len(results)}",
        "",
        "---",
        "",
        "## Resumen",
        "",
    ]

    crm_free_count = sum(1 for r in results if r["evaluation"]["crm_free"])
    candidate_advances = sum(1 for r in results if r["evaluation"]["candidate_advances_more"])

    lines += [
        f"| Métrica | Resultado |",
        f"|---|---|",
        f"| Sin marcadores CRM en candidato | {crm_free_count}/{len(results)} |",
        f"| Candidato avanza más comercialmente | {candidate_advances}/{len(results)} |",
        "",
        "---",
        "",
    ]

    for r in results:
        ev = r["evaluation"]
        lines += [
            f"## {r['scenario_id']} — {r['description']}",
            "",
            f"**Setup (solo candidato)**: _{r['seed_message']}_",
            f"**Mensaje de prueba (ambos)**: _{r['test_message']}_",
            "",
            "### Baseline (sin memoria)",
            "",
            r["baseline_reply"] or "_(sin respuesta)_",
            "",
            "### Candidato (con memoria sembrada)",
            "",
            r["candidate_reply"] or "_(sin respuesta)_",
            "",
            "### Evaluación",
            "",
            f"| Check | Resultado |",
            f"|---|---|",
            f"| Sin lenguaje CRM/sistema | {_icon(ev['crm_free'])} |",
            f"| Candidato avanza más hacia acción | {_icon(ev['candidate_advances_more'])} |",
            f"| Palabras baseline / candidato | {ev['baseline_words']} / {ev['candidate_words']} (delta {ev['word_delta']:+d}) |",
        ]

        if ev["crm_markers_in_candidate"]:
            lines.append(f"| ⚠️ Marcadores CRM detectados | `{', '.join(ev['crm_markers_in_candidate'])}` |")

        if ev["candidate_commercial_signals"]:
            lines.append(f"| Señales comerciales candidato | `{', '.join(ev['candidate_commercial_signals'][:3])}` |")

        lines += ["", "---", ""]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = parse_common_args("Memory Lab — BASELINE vs CANDIDATO (12 escenarios)", include_label=True)
    args = parser.parse_args()

    tenant_slug = resolve_tenant_slug(args.tenant)
    channel = resolve_channel(args.channel)
    label = str(args.label).strip()
    run_at = utc_now_iso()

    from app.application.runtime import load_tenant_runtime_yaml
    from app.services.ai_service import AIService

    service = AIService()
    th = tenant_handle(tenant_slug)

    print(f"\n[memory-lab] tenant={tenant_slug} | channel={channel} | label={label}")
    print(f"[memory-lab] {len(SCENARIOS)} escenarios × 2 ramas (baseline + candidato)\n")

    results = []
    for i, scenario in enumerate(SCENARIOS, 1):
        print(f"  [{i:02d}/{len(SCENARIOS)}] {scenario.id} …", end=" ", flush=True)
        try:
            result = run_scenario(
                scenario,
                service=service,
                tenant_slug=tenant_slug,
                channel=channel,
                tenant=th,
                runtime_yaml_fn=load_tenant_runtime_yaml,
            )
            ev = result["evaluation"]
            crm_ok = _icon(ev["crm_free"])
            adv = _icon(ev["candidate_advances_more"])
            print(f"crm_free={crm_ok} avanza={adv}")
        except Exception as exc:
            print(f"ERROR: {exc}")
            result = {
                "scenario_id": scenario.id,
                "description": scenario.description,
                "seed_message": scenario.seed_message,
                "test_message": scenario.test_message,
                "baseline_reply": "",
                "candidate_reply": "",
                "evaluation": {
                    "crm_free": False,
                    "candidate_advances_more": False,
                    "error": str(exc),
                },
            }
        results.append(result)

    # Save JSON payload
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = RESULTS_DIR / f"memory_lab_{label}.json"
    write_json(json_path, {
        "label": label,
        "tenant_slug": tenant_slug,
        "channel": channel,
        "run_at": run_at,
        "scenarios": results,
    })

    # Save markdown report
    md_report = build_markdown_report(results, label=label, tenant_slug=tenant_slug, run_at=run_at)
    md_path = RESULTS_DIR / f"memory_lab_{label}.md"
    md_path.write_text(md_report, encoding="utf-8")

    crm_free = sum(1 for r in results if r["evaluation"].get("crm_free", False))
    advances = sum(1 for r in results if r["evaluation"].get("candidate_advances_more", False))

    print(f"\n[memory-lab] Completado.")
    print(f"  Sin CRM:  {crm_free}/{len(results)}")
    print(f"  Avanza+:  {advances}/{len(results)}")
    print(f"  JSON:  {json_path}")
    print(f"  MD:    {md_path}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
