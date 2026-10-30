"""
export_business_config_schema.py

Genera el JSON Schema del contrato global desde los modelos Pydantic
(`project/app/domain/business_config/contract.py`), que son su única fuente.

Usage:
  python scripts/export_business_config_schema.py          # escribe el esquema
  python scripts/export_business_config_schema.py --check  # falla si el archivo está desactualizado
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "project"
SCHEMA_PATH = PROJECT_DIR / "config" / "contracts" / "v1" / "business-config.schema.json"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.domain.business_config.contract import SCHEMA_VERSION, BusinessConfig  # noqa: E402


def render_schema() -> str:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://ai-sales-engine/contracts/business-config/v{SCHEMA_VERSION}",
        **BusinessConfig.model_json_schema(),
    }
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    rendered = render_schema()
    if "--check" in sys.argv[1:]:
        current = SCHEMA_PATH.read_text(encoding="utf-8") if SCHEMA_PATH.exists() else ""
        if current != rendered:
            print(f"[outdated] {SCHEMA_PATH.relative_to(REPO_ROOT)}")
            return 1
        print(f"[ok] {SCHEMA_PATH.relative_to(REPO_ROOT)}")
        return 0
    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_PATH.write_text(rendered, encoding="utf-8")
    print(f"[written] {SCHEMA_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
