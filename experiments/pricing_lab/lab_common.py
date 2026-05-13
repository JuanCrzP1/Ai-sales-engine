from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from lab_config import CANONICAL_RESULT_FILES, DEFAULT_CHANNEL, DEFAULT_TENANT, DEFAULT_USER_ID, PROJECT_DIR, REPO_ROOT, RESULTS_DIR


if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


ENV_FILE = REPO_ROOT / ".env"
if ENV_FILE.exists():
    from dotenv import load_dotenv

    load_dotenv(ENV_FILE, override=False)


def ensure_results_scaffold() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    prompt_placeholder = "Pendiente. Ejecuta generate_prompt_snapshot.py.\n"
    json_placeholder = json.dumps({}, indent=2, ensure_ascii=False) + "\n"
    comparison_placeholder = (
        "# Comparación conversacional\n\n"
        "Pendiente. Ejecuta generate_conversation_comparison.py después de generar baseline y candidate.\n"
    )
    evolution_placeholder = "# Evolution Log\n\nPendiente. Ejecuta run_golden_conversations.py para registrar iteraciones.\n"
    placeholders = {
        "baseline_prompt": prompt_placeholder,
        "candidate_prompt": prompt_placeholder,
        "baseline_metrics": json_placeholder,
        "candidate_metrics": json_placeholder,
        "comparison": comparison_placeholder,
        "evolution": evolution_placeholder,
    }
    for key, path in CANONICAL_RESULT_FILES.items():
        if not path.exists():
            path.write_text(placeholders[key], encoding="utf-8")


def parse_common_args(description: str, *, include_label: bool = False) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    if include_label:
        parser.add_argument("--label", required=True, help="baseline o nombre de iteración candidate")
    parser.add_argument("--tenant", default="", help="Tenant slug a evaluar. Si no se envía, usa PRICING_LAB_TENANT")
    parser.add_argument("--channel", default="", help="Canal runtime. Default: whatsapp")
    parser.add_argument("--user-id", default="", help="Identificador conversacional del laboratorio")
    return parser


def resolve_tenant_slug(arg_value: str) -> str:
    tenant_slug = str(arg_value or DEFAULT_TENANT or "").strip()
    if tenant_slug:
        return tenant_slug
    raise SystemExit(
        "Falta tenant. Usa --tenant <slug> o define PRICING_LAB_TENANT."
    )


def resolve_channel(arg_value: str) -> str:
    return str(arg_value or DEFAULT_CHANNEL or "whatsapp").strip() or "whatsapp"


def resolve_user_id(arg_value: str) -> str:
    return str(arg_value or DEFAULT_USER_ID or "pricing-lab-user").strip() or "pricing-lab-user"


def storage_slot(label: str) -> str:
    normalized = str(label or "").strip().lower()
    return "baseline" if normalized == "baseline" else "candidate"


def prompt_output_path(label: str) -> Path:
    return CANONICAL_RESULT_FILES[f"{storage_slot(label)}_prompt"]


def metrics_output_path(label: str) -> Path:
    return CANONICAL_RESULT_FILES[f"{storage_slot(label)}_metrics"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def estimated_tokens(text: str) -> int:
    compact = re.sub(r"\s+", " ", str(text or "").strip())
    if not compact:
        return 0
    return int(math.ceil(len(compact) / 4))


def extract_pricing_block(prompt_text: str) -> str:
    marker = "\nPRICING:\n"
    if marker in prompt_text:
        return prompt_text.split(marker, 1)[1].strip()
    if prompt_text.startswith("PRICING:\n"):
        return prompt_text.split("PRICING:\n", 1)[1].strip()
    return ""


def build_prompt_metrics(prompt_text: str) -> dict[str, int]:
    pricing_block = extract_pricing_block(prompt_text)
    return {
        "chars": len(prompt_text),
        "lines": len(prompt_text.splitlines()),
        "estimated_tokens": estimated_tokens(prompt_text),
        "pricing_block_chars": len(pricing_block),
    }


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    raw_text = path.read_text(encoding="utf-8").strip()
    if not raw_text:
        return {}
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def yes_no(value: bool) -> str:
    return "Sí" if bool(value) else "No"


def tenant_handle(tenant_slug: str) -> SimpleNamespace:
    return SimpleNamespace(name=tenant_slug, slug=tenant_slug, id=tenant_slug)


def run_git_command(args: list[str]) -> str:
    try:
        completed = subprocess.run(
            args,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return str(completed.stdout or "").strip() or "unknown"


def current_commit() -> str:
    return run_git_command(["git", "rev-parse", "--short", "HEAD"])


def append_evolution_entry(entry: dict[str, Any]) -> None:
    ensure_results_scaffold()
    path = CANONICAL_RESULT_FILES["evolution"]
    current_text = path.read_text(encoding="utf-8") if path.exists() else ""
    if current_text.startswith("# Evolution Log"):
        existing_body = current_text.split("\n", 2)[2] if current_text.count("\n") >= 2 else ""
    else:
        existing_body = current_text.strip()

    prompt_metrics = entry.get("prompt_metrics") if isinstance(entry.get("prompt_metrics"), dict) else {}
    behavior_metrics = entry.get("behavior_metrics") if isinstance(entry.get("behavior_metrics"), dict) else {}
    section = "\n".join(
        [
            f"## {entry.get('run_at', 'unknown')} | {entry.get('label', 'unknown')}",
            f"- fecha: {entry.get('run_at', 'unknown')}",
            f"- label: {entry.get('label', 'unknown')}",
            f"- tenant: {entry.get('tenant_slug', 'unknown')}",
            f"- commit: {entry.get('commit', 'unknown')}",
            f"- métricas del prompt: chars={prompt_metrics.get('chars', 0)}, lines={prompt_metrics.get('lines', 0)}, estimated_tokens={prompt_metrics.get('estimated_tokens', 0)}, pricing_block_chars={prompt_metrics.get('pricing_block_chars', 0)}",
            f"- métricas comerciales: precio={behavior_metrics.get('price_turns', 0)}, incluye={behavior_metrics.get('includes_turns', 0)}, no_incluye={behavior_metrics.get('not_includes_turns', 0)}, roi={behavior_metrics.get('roi_turns', 0)}, cta={behavior_metrics.get('cta_turns', 0)}, objeciones={behavior_metrics.get('objection_turns', 0)}, cierre={behavior_metrics.get('closing_progress_turns', 0)}",
            f"- score total: {entry.get('commercial_score', 0)}",
            f"- veredicto: {entry.get('verdict', 'Sin datos')}",
            "",
        ]
    )
    new_text = "# Evolution Log\n\n" + section + (existing_body.lstrip("\n") if existing_body else "")
    path.write_text(new_text, encoding="utf-8")


def baseline_locked(label: str, force: bool) -> bool:
    return storage_slot(label) == "baseline" and metrics_output_path(label).exists() and load_json(metrics_output_path(label)) and not force
