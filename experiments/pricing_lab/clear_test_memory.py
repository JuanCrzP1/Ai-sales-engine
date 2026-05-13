from __future__ import annotations

import subprocess
import sys

from lab_common import parse_common_args, resolve_tenant_slug, resolve_user_id
from lab_config import REPO_ROOT


def main() -> int:
    parser = parse_common_args("Limpia memoria conversacional del laboratorio", include_label=False)
    args = parser.parse_args()

    tenant_slug = resolve_tenant_slug(args.tenant)
    user_id = resolve_user_id(args.user_id)
    script_path = REPO_ROOT / "scripts" / "reset_conversation_state.py"

    completed = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--tenant-slug",
            tenant_slug,
            "--user-id",
            user_id,
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
