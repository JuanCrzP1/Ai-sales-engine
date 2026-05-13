"""
clear_test_memory.py
─────────────────────
Limpia la memoria conversacional en RAM del tenant asesor_ai_prod
para evitar contaminación entre corridas del laboratorio.

Uso:
    python experiments/phase_1_pricing_audit/clear_test_memory.py
    python experiments/phase_1_pricing_audit/clear_test_memory.py --user golden-baseline

Notas:
  - Limpia la memoria RAM (MemoryRepository / SQLMemoryRepository en modo RAM).
  - Si la app está corriendo contra PostgreSQL, la memoria persistida en DB
    no se ve afectada (usar el script scripts/reset_memory.py para eso).
  - Este script es seguro: no modifica ningún archivo de producción.

El script NO modifica ningún archivo de producción.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_DIR = REPO_ROOT / "project"
sys.path.insert(0, str(PROJECT_DIR))

from app.services.ai_service import GLOBAL_MEMORY_REPOSITORY  # noqa: E402

TENANT = "asesor_ai_prod"

DEFAULT_LABELS = ["baseline", "candidate_v1", "candidate_v2"]


def _clear_user(repo, *, tenant: str, user_id: str) -> None:
    key = (tenant, user_id)
    cleared: list[str] = []
    repo.reset_conversation(tenant_slug=tenant, user_id=user_id)
    for attr_name in (
        "_messages_by_user",
        "_last_intent_by_user",
        "_detected_intent_by_user",
        "_last_pain_by_user",
        "_payment_method_by_user",
        "_payment_status_by_user",
        "_mode_by_user",
        "_stage_by_user",
        "_last_user_message_by_user",
        "_last_response_by_user",
        "_last_ai_response_by_user",
        "_conversation_state_by_user",
        "_initial_message_last_sent_by_user",
        "_last_user_message_at_by_user",
    ):
        store = getattr(repo, attr_name, None)
        if isinstance(store, dict) and key not in store:
            cleared.append(attr_name)
    print(f"  [{tenant} / {user_id}] reset ejecutado; stores verificados: {len(cleared)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Limpia la memoria conversacional del laboratorio.")
    parser.add_argument(
        "--user",
        default=None,
        help="User ID específico a limpiar. Si se omite, limpia todos los IDs dorados.",
    )
    parser.add_argument(
        "--tenant",
        default=TENANT,
        help=f"Tenant a limpiar (default: {TENANT})",
    )
    args = parser.parse_args()

    repo = GLOBAL_MEMORY_REPOSITORY
    tenant = str(args.tenant or TENANT).strip().lower() or TENANT
    prefix = f"golden-{tenant}-"
    target_users = {str(args.user).strip().lower()} if args.user else {
        f"{prefix}{label}" for label in DEFAULT_LABELS
    }
    for attr_name in ("_messages_by_user", "_last_response_by_user", "_conversation_state_by_user"):
        store = getattr(repo, attr_name, None)
        if not isinstance(store, dict):
            continue
        for slug, user_id in store.keys():
            if slug == tenant and str(user_id).startswith(prefix):
                target_users.add(str(user_id))

    print(f"Limpiando memoria RAM para tenant: {tenant}")
    print(f"Users: {sorted(target_users)}\n")

    for user_id in sorted(target_users):
        _clear_user(repo, tenant=tenant, user_id=user_id)

    print("\nMemoria limpia. Listo para ejecutar run_golden_conversations.py")


if __name__ == "__main__":
    main()
