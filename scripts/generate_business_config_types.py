"""
generate_business_config_types.py

Genera los tipos TypeScript del contrato global para el panel administrativo
(`apps/admin-web/src/contracts/businessConfig.v1.ts`) desde el JSON Schema publicado y las
políticas del motor, para que el frontend no mantenga una copia manual del contrato.

Usage:
  python scripts/generate_business_config_types.py          # escribe el archivo
  python scripts/generate_business_config_types.py --check  # falla si está desactualizado
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "project"
SCHEMA_PATH = PROJECT_DIR / "config" / "contracts" / "v1" / "business-config.schema.json"
OUTPUT_PATH = REPO_ROOT / "apps" / "admin-web" / "src" / "contracts" / "businessConfig.v1.ts"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.domain.business_config import engine_policy  # noqa: E402
from app.domain.business_config.contract import SCHEMA_VERSION  # noqa: E402


def _type(schema: dict) -> str:
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if "const" in schema:
        return json.dumps(schema["const"], ensure_ascii=False)
    if "enum" in schema:
        return " | ".join(json.dumps(value, ensure_ascii=False) for value in schema["enum"])
    if "anyOf" in schema:
        parts: list[str] = []
        for option in schema["anyOf"]:
            rendered = _type(option)
            if rendered not in parts:
                parts.append(rendered)
        if "number" in parts and "integer" in parts:
            parts.remove("integer")
        return " | ".join("number" if part == "integer" else part for part in parts)
    kind = schema.get("type")
    if kind == "array":
        item = _type(schema.get("items", {}))
        return f"({item})[]" if "|" in item else f"{item}[]"
    if kind == "object":
        extra = schema.get("additionalProperties")
        if isinstance(extra, dict):
            return f"Record<string, {_type(extra)}>"
        if extra is True or "properties" not in schema:
            return "Record<string, unknown>"
        return "unknown"
    return {"string": "string", "integer": "number", "number": "number", "boolean": "boolean", "null": "null"}.get(kind, "unknown")


def _doc(schema: dict) -> str:
    """Descripción del campo con sus marcas explícitas del contrato (audiencia y estado en el motor)."""
    parts = [" ".join(schema["description"].split())] if schema.get("description") else []
    marks = [f"{label}: {schema[key]}" for key, label in (("x-audience", "audiencia"), ("x-engine", "motor")) if key in schema]
    if marks:
        parts.append(f"[{'; '.join(marks)}]")
    return " ".join(parts)


def _interface(name: str, schema: dict) -> str:
    if "properties" not in schema:
        return f"export type {name} = {_type(schema)};"
    required = set(schema.get("required", []))
    lines = []
    if schema.get("description"):
        lines.append(f"/** {' '.join(schema['description'].split())} */")
    lines.append(f"export interface {name} {{")
    for field, field_schema in schema["properties"].items():
        if doc := _doc(field_schema):
            lines.append(f"  /** {doc} */")
        optional = "" if field in required else "?"
        lines.append(f"  {field}{optional}: {_type(field_schema)};")
    lines.append("}")
    return "\n".join(lines)


def render_types() -> str:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    blocks = [_interface(name, definition) for name, definition in schema.get("$defs", {}).items()]
    blocks.append(_interface("BusinessConfig", schema))
    constants = [
        f'export const SCHEMA_VERSION = "{SCHEMA_VERSION}";',
        f"export const RESPONSE_LENGTH_MAX_WORDS = {json.dumps(engine_policy.RESPONSE_LENGTH_MAX_WORDS)} as const;",
        f"export const MIN_MAX_WORDS = {engine_policy.MIN_MAX_WORDS};",
        f"export const MAX_FAQS = {engine_policy.MAX_FAQS};",
        f"export const MAX_FAQ_QUESTION_CHARS = {engine_policy.MAX_FAQ_QUESTION_CHARS};",
        f"export const MAX_FAQ_ANSWER_CHARS = {engine_policy.MAX_FAQ_ANSWER_CHARS};",
        "export const RESPONSE_LENGTH_WORD_RANGES = "
        f"{json.dumps({length: list(bounds) for length, bounds in engine_policy.RESPONSE_LENGTH_WORD_RANGES.items()})} as const;",
        f"export const MAX_PROFILE_ITEMS = {engine_policy.MAX_PROFILE_ITEMS};",
        f"export const MAX_PROFILE_ITEM_CHARS = {engine_policy.MAX_PROFILE_ITEM_CHARS};",
        f"export const MAX_TONE_CHARS = {engine_policy.MAX_TONE_CHARS};",
        f"export const MAX_PROMOTIONS = {engine_policy.MAX_PROMOTIONS};",
        f"export const PROMPT_WORD_LIMITS = {json.dumps(engine_policy.PROMPT_WORD_LIMITS)} as const;",
        f"export const PROMPT_MAX_PROBLEMS = {engine_policy.PROMPT_MAX_PROBLEMS};",
        f"export const PROMPT_MAX_CATEGORIES = {engine_policy.PROMPT_MAX_CATEGORIES};",
    ]
    header = (
        "// ARCHIVO GENERADO por scripts/generate_business_config_types.py. No editar a mano.\n"
        "// Fuente: project/config/contracts/v1/business-config.schema.json y\n"
        "// project/app/domain/business_config/engine_policy.py.\n"
        "// Marcas: `audiencia` (cliente, avanzado, operador, sistema) y `motor` (conectado, pendiente,\n"
        "// conservado); un campo sin marca toma la de su sección. Ver docs/business-config.md.\n"
    )
    return header + "\n" + "\n".join(constants) + "\n\n" + "\n\n".join(blocks) + "\n"


def main() -> int:
    rendered = render_types()
    if "--check" in sys.argv[1:]:
        current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
        if current != rendered:
            print(f"[outdated] {OUTPUT_PATH.relative_to(REPO_ROOT)}")
            return 1
        print(f"[ok] {OUTPUT_PATH.relative_to(REPO_ROOT)}")
        return 0
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    print(f"[written] {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
