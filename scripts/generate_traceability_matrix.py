"""
generate_traceability_matrix.py

Genera la matriz de trazabilidad de la configuración antigua (los cinco YAML de cada negocio) al
contrato BusinessConfig v1 (`docs/business-config-traceability.md`) desde el catálogo
`project/app/infrastructure/config/legacy_field_catalog.py`, los YAML reales de los negocios y el
JSON Schema publicado, que aporta la referencia de cada campo del contrato (audiencia y estado en el
motor). No incluye ningún valor de configuración: solo rutas, significado y estado.

Usage:
  python scripts/generate_traceability_matrix.py          # escribe el archivo
  python scripts/generate_traceability_matrix.py --check  # falla si está desactualizado
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "project"
OUTPUT_PATH = REPO_ROOT / "docs" / "business-config-traceability.md"
SCHEMA_PATH = PROJECT_DIR / "config" / "contracts" / "v1" / "business-config.schema.json"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
os.environ.setdefault("MODE", "test")

from app.application.runtime.tenant_runtime_loader import _load_legacy_sections  # noqa: E402
from app.infrastructure.config.business_config_store import CONTRACT_FILENAME  # noqa: E402
from app.infrastructure.config.config_service import ConfigService  # noqa: E402
from app.infrastructure.config.legacy_field_catalog import (  # noqa: E402
    CATALOG,
    CONSERVED,
    DERIVED_CONTRACT_FIELDS,
    NEW_CONTRACT_FIELDS,
    SOURCE_FILES,
    LegacyField,
    contract_fields,
    covering_leaf,
    destination_path,
    find_entry,
    legacy_leaves,
)

CLASSES = {
    "A": "configuración que edita el cliente",
    "B": "configuración comercial avanzada",
    "C": "configuración interna del motor",
    "D": "información sensible (datos de pago)",
    "E": "derivada, obsoleta o redundante",
}


def _tenants(service: ConfigService) -> list[str]:
    return sorted(path.name for path in service.tenants_root.iterdir() if (path / CONTRACT_FILENAME).is_file())


def _destination(entry: LegacyField, pattern: str) -> str:
    if entry.kind == "compatibility":
        return "`compatibility` (misma ruta)"
    destination = entry.destination.removeprefix("secret:")
    if entry.pattern.endswith(".**"):
        destination = destination[:-2] + pattern[len(entry.pattern) - 2:]
    destination = destination.replace("[{i}]", "[]").replace("[{j}]", "[]")
    return f"referencia en `{destination}`" if entry.kind == "secret" else f"`{destination}`"


def _cell(text: str) -> str:
    return text.replace("|", "\\|") or "—"


def render_matrix() -> str:
    service = ConfigService()
    tenants = _tenants(service)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    fields = contract_fields(schema)
    origins: dict[str, set[str]] = defaultdict(set)
    rows: dict[str, set[str]] = defaultdict(set)
    summary: dict[str, Counter] = {}
    for slug in tenants:
        counts: Counter = Counter()
        for leaf in legacy_leaves(_load_legacy_sections(service, slug)):
            entry = find_entry(leaf.pattern)
            if entry is None:
                raise SystemExit(f"{slug}: campo sin catalogar {leaf.pattern}")
            if entry.kind != "compatibility" and (covering := covering_leaf(destination_path(entry, leaf), set(fields))):
                origins[covering].add(entry.pattern)
            rows[leaf.pattern].add(slug)
            counts["total"] += 1
            counts[entry.kind] += 1
            counts[entry.category] += 1
        summary[slug] = counts

    lines = [
        "# Matriz de trazabilidad: YAML antiguos → BusinessConfig v1",
        "",
        "> Archivo generado por `scripts/generate_traceability_matrix.py` desde",
        "> `project/app/infrastructure/config/legacy_field_catalog.py`. No editar a mano: `--check` falla si",
        "> está desactualizado y `tests/test_business_config_traceability.py` lo comprueba.",
        "",
        "Cada fila es un campo de los YAML de origen (`business.yaml`, `sales.yaml`, `pricing.yaml`,",
        "`inventory.yaml`, `config.yaml`). No se muestran valores, solo rutas.",
        "",
        "- **Conservado en los datos:** todos los campos, en todos los negocios. Lo comprueba",
        f"  `{CONSERVED}`: el valor original está en el destino declarado.",
        "- **Representado en el contrato:** la columna Destino. `compatibility` significa que el dato se",
        "  conserva con su ruta original pero no forma parte del contrato (ver Justificación).",
        "- **Interfaz:** `pantalla` (el panel tiene un control), `modelo` (el modelo y el adaptador del panel",
        "  lo admiten, pero aún no hay pantalla) o `no`.",
        "- **Motor:** `sí` solo con evidencia (columna Prueba) de que el motor actual lo usa; `no` si solo está",
        "  representado. Las pruebas de uso están en `tests/test_business_config_engine_integration.py`.",
        "- `[]` es un índice de lista; `<nombre>` una clave variable (id de problema, moneda...).",
        "",
        "Clases: " + "; ".join(f"**{key}** {value}" for key, value in CLASSES.items()) + ".",
        "",
        "## Resumen por negocio",
        "",
        "| Negocio | Campos | Tipados | Datos de pago (referencias) | En compatibilidad | A | B | C | D | E |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for slug, counts in summary.items():
        lines.append(
            f"| {slug} | {counts['total']} | {counts['typed']} | {counts['secret']} | {counts['compatibility']} | "
            + " | ".join(str(counts[key]) for key in "ABCDE")
            + " |"
        )
    totals = sum(summary.values(), Counter())
    lines.append(
        f"| **Total** | {totals['total']} | {totals['typed']} | {totals['secret']} | {totals['compatibility']} | "
        + " | ".join(str(totals[key]) for key in "ABCDE")
        + " |"
    )

    for section, filename in SOURCE_FILES.items():
        patterns = sorted(pattern for pattern in rows if pattern.split(".", 1)[0].split("[", 1)[0] == section)
        lines += [
            "",
            f"## {filename}",
            "",
            "| Campo antiguo | Negocios | Significado | Clase | Destino | Transformación | Interfaz | Motor | Justificación | Prueba |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        for pattern in patterns:
            entry = find_entry(pattern)
            assert entry is not None
            owners = "todos" if rows[pattern] == set(tenants) else ", ".join(sorted(rows[pattern]))
            tests = ", ".join(f"`{name}`" for name in entry.evidence)
            lines.append(
                f"| `{pattern}` | {owners} | {_cell(entry.meaning)} | {entry.category} | {_destination(entry, pattern)} | "
                f"{_cell(entry.transform)} | {entry.panel} | {_cell(entry.engine)} | {_cell(entry.note)} | {tests or '—'} |"
            )

    panel_of = {entry.pattern: entry.panel for entry in CATALOG}
    status = Counter((field.audience, field.engine) for field in fields.values())
    lines += [
        "",
        "## Referencia de campos del contrato",
        "",
        "Generada del JSON Schema (`x-audience`, `x-engine`). Cada campo hoja del contrato, con quién lo configura,",
        "si el motor actual lo usa y de dónde viene.",
        "",
        "- **Audiencia:** `cliente` (lo configura el negocio), `avanzado` (estrategia comercial detallada, opcional),",
        "  `operador` (ajustes internos del motor) o `sistema`.",
        "- **Motor:** `conectado` (el motor actual lo usa; prueba en `tests/test_business_config_engine_integration.py`),",
        "  `pendiente` (representado y conservado, sin uso en el motor actual) o `conservado` (`compatibility`).",
        "- **Origen:** campo de los YAML, `nuevo` (solo existe en el contrato) o `derivado` (lo crea la importación).",
        "",
        "| Audiencia | Conectados | Pendientes | Conservados |",
        "|---|---|---|---|",
        *[
            f"| {audience} | {status[(audience, 'conectado')]} | {status[(audience, 'pendiente')]} | {status[(audience, 'conservado')]} |"
            for audience in ("cliente", "avanzado", "operador", "sistema")
        ],
        f"| **Total** | {sum(v for (_, e), v in status.items() if e == 'conectado')} | "
        f"{sum(v for (_, e), v in status.items() if e == 'pendiente')} | {sum(v for (_, e), v in status.items() if e == 'conservado')} |",
        "",
        "| Campo | Audiencia | Motor | Origen | Interfaz | Descripción |",
        "|---|---|---|---|---|---|",
    ]
    for path, field in sorted(fields.items()):
        if path in NEW_CONTRACT_FIELDS:
            meaning, panel = NEW_CONTRACT_FIELDS[path]
            origin, description = "nuevo", field.description or meaning
        elif path in DERIVED_CONTRACT_FIELDS:
            origin, panel, description = "derivado", "—", field.description or DERIVED_CONTRACT_FIELDS[path]
        else:
            patterns = sorted(origins.get(path, ()))
            origin = ", ".join(f"`{pattern}`" for pattern in patterns) or "—"
            panels = sorted({panel_of[pattern] for pattern in patterns})
            panel = "/".join(panels) or "—"
            description = field.description or (find_entry(patterns[0]).meaning if patterns else "")
        lines.append(f"| `{path}` | {field.audience} | {field.engine} | {origin} | {panel} | {_cell(description)} |")

    lines += [
        "",
        "## Campos del contrato que crea la importación",
        "",
        "Se derivan de claves o de la estructura de los YAML, no de un valor concreto.",
        "",
        "| Campo | Origen |",
        "|---|---|",
        *[f"| `{path}` | {origin} |" for path, origin in sorted(DERIVED_CONTRACT_FIELDS.items())],
        "",
    ]
    schema_version = schema["properties"]["schema_version"]["const"]
    lines.insert(2, f"Versión del contrato: `{schema_version}`. Negocios: {len(tenants)}. Patrones catalogados: {len(CATALOG)}.\n")
    return "\n".join(lines)


def main() -> int:
    rendered = render_matrix()
    if "--check" in sys.argv[1:]:
        current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
        if current != rendered:
            print(f"[outdated] {OUTPUT_PATH.relative_to(REPO_ROOT)}")
            return 1
        print(f"[ok] {OUTPUT_PATH.relative_to(REPO_ROOT)}")
        return 0
    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    print(f"[written] {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
