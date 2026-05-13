from __future__ import annotations

from lab_common import build_prompt_metrics, current_commit, ensure_results_scaffold, metrics_output_path, parse_common_args, prompt_output_path, resolve_channel, resolve_tenant_slug, resolve_user_id, storage_slot, utc_now_iso, write_json
from lab_config import GOLDEN_TURNS

from app.application.runtime import load_tenant_runtime_yaml
from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService


def main() -> int:
    parser = parse_common_args("Genera snapshot del prompt comercial", include_label=True)
    parser.add_argument("--seed-message", default="", help="Mensaje usado para construir el snapshot")
    parser.add_argument("--force", action="store_true", help="Permite sobrescribir baseline")
    args = parser.parse_args()

    ensure_results_scaffold()
    label = str(args.label).strip()
    if storage_slot(label) == "baseline":
        existing_metrics = metrics_output_path(label)
        if existing_metrics.exists() and existing_metrics.read_text(encoding="utf-8").strip() not in {"", "{}"} and not args.force:
            raise SystemExit("Baseline ya existe. Usa --force solo si quieres reemplazar la referencia permanente.")

    tenant_slug = resolve_tenant_slug(args.tenant)
    channel = resolve_channel(args.channel)
    user_id = resolve_user_id(args.user_id)
    seed_message = str(args.seed_message or GOLDEN_TURNS[0]).strip() or GOLDEN_TURNS[0]

    runtime_yaml = load_tenant_runtime_yaml(tenant_slug, channel=channel)
    runtime_yaml["user_id"] = user_id

    prompt_text, prompt_metadata, context = PromptBuilderService().build(
        client_config_id=tenant_slug,
        user_message=seed_message,
        yaml_config=runtime_yaml,
        faq_results=[],
        progression_rules=None,
    )

    prompt_text = str(prompt_text or "")
    prompt_output_path(label).write_text(prompt_text + ("\n" if prompt_text and not prompt_text.endswith("\n") else ""), encoding="utf-8")

    payload = {
        "label": label,
        "storage_slot": storage_slot(label),
        "tenant_slug": tenant_slug,
        "channel": channel,
        "user_id": user_id,
        "run_at": utc_now_iso(),
        "commit": current_commit(),
        "seed_message": seed_message,
        "prompt_metrics": build_prompt_metrics(prompt_text),
        "prompt_metadata": prompt_metadata if isinstance(prompt_metadata, dict) else {},
        "prompt_context": context if isinstance(context, dict) else {},
    }
    write_json(metrics_output_path(label), payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
