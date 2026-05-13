from __future__ import annotations

from lab_common import append_evolution_entry, current_commit, ensure_results_scaffold, load_json, metrics_output_path, parse_common_args, resolve_channel, resolve_tenant_slug, resolve_user_id, storage_slot, utc_now_iso, write_json
from lab_config import GOLDEN_TURNS
from evaluate_conversations import enrich_metrics_payload

from app.application.runtime import load_tenant_runtime_yaml
from app.services.ai_service import AIService
from lab_common import tenant_handle


def _ensure_prompt_snapshot(*, label: str, tenant_slug: str, channel: str, user_id: str) -> dict:
    payload = load_json(metrics_output_path(label))
    if payload.get("prompt_metrics"):
        return payload

    from generate_prompt_snapshot import main as snapshot_main
    import sys

    original_argv = list(sys.argv)
    try:
        sys.argv = [
            "generate_prompt_snapshot.py",
            "--label",
            label,
            "--tenant",
            tenant_slug,
            "--channel",
            channel,
            "--user-id",
            user_id,
        ]
        snapshot_main()
    finally:
        sys.argv = original_argv
    return load_json(metrics_output_path(label))


def main() -> int:
    parser = parse_common_args("Ejecuta la golden conversation y registra métricas", include_label=True)
    parser.add_argument("--force", action="store_true", help="Permite sobrescribir baseline")
    args = parser.parse_args()

    ensure_results_scaffold()
    label = str(args.label).strip()
    existing = load_json(metrics_output_path(label))
    if storage_slot(label) == "baseline" and existing.get("conversation") and not args.force:
        raise SystemExit("Baseline ya tiene conversación registrada. Usa --force solo si necesitas regenerarla.")

    tenant_slug = resolve_tenant_slug(args.tenant)
    channel = resolve_channel(args.channel)
    user_id = resolve_user_id(args.user_id)

    payload = _ensure_prompt_snapshot(label=label, tenant_slug=tenant_slug, channel=channel, user_id=user_id)

    service = AIService()
    conversation_rows = []
    for turn_number, user_message in enumerate(GOLDEN_TURNS, start=1):
        runtime_yaml = load_tenant_runtime_yaml(tenant_slug, channel=channel)
        response, ai_used, metadata = service.generate_business_reply(
            tenant=tenant_handle(tenant_slug),
            bot_config=None,
            user_message=user_message,
            conversation_history=[],
            faq_results=[],
            yaml_config=runtime_yaml,
            user_id=user_id,
            include_metadata=True,
        )
        conversation_rows.append(
            {
                "turn": turn_number,
                "user_message": user_message,
                "assistant_reply": str(response or ""),
                "ai_used": bool(ai_used),
                "metadata": metadata if isinstance(metadata, dict) else {},
            }
        )

    payload.update(
        {
            "label": label,
            "storage_slot": storage_slot(label),
            "tenant_slug": tenant_slug,
            "channel": channel,
            "user_id": user_id,
            "run_at": utc_now_iso(),
            "commit": current_commit(),
            "conversation": conversation_rows,
        }
    )
    payload = enrich_metrics_payload(payload)
    write_json(metrics_output_path(label), payload)

    append_evolution_entry(
        {
            "run_at": payload.get("run_at"),
            "label": label,
            "tenant_slug": tenant_slug,
            "commit": payload.get("commit"),
            "prompt_metrics": payload.get("prompt_metrics", {}),
            "behavior_metrics": payload.get("behavior_metrics", {}),
            "commercial_score": payload.get("commercial_score", 0),
            "verdict": payload.get("verdict", "Sin datos"),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
