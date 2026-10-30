"""
migrate_tenants_to_contract.py

Convierte los cinco YAML de cada negocio (`project/config/tenants/<slug>/`) al contrato global y
escribe `business-config.json` en la misma carpeta, junto con un informe de importación y diagnóstico.

Garantías antes de escribir cada documento:
  - cumple el contrato (validación Pydantic);
  - compilado de nuevo, reproduce exactamente las secciones YAML de origen (sin pérdida);
  - no contiene ningún dato de pago sensible (links, números, cuentas, referencias).

No modifica ni elimina los YAML, no usa base de datos ni red.

Usage:
  python scripts/migrate_tenants_to_contract.py          # escribe documentos e informe
  python scripts/migrate_tenants_to_contract.py --check  # no escribe; falla si algo está desactualizado
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "project"
REPORT_PATH = PROJECT_DIR / "config" / "contracts" / "v1" / "migration-report.md"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.application.runtime.tenant_runtime_loader import _load_legacy_sections  # noqa: E402
from app.domain.business_config.compiler import compile_business_config  # noqa: E402
from app.domain.business_config.diagnostics import review  # noqa: E402
from app.domain.business_config.payment_data import payment_values  # noqa: E402
from app.infrastructure.config.business_config_store import BusinessConfigStore  # noqa: E402
from app.infrastructure.config.config_service import ConfigService  # noqa: E402
from app.infrastructure.config.legacy_yaml_importer import import_legacy_sections  # noqa: E402
from app.infrastructure.config.payment_secrets import LegacyYamlSecretResolver  # noqa: E402


def build() -> tuple[dict[Path, str], str, list[tuple[str, str]]]:
    """Documentos por ruta, informe y errores, sin escribir nada."""
    service = ConfigService()
    store = BusinessConfigStore(service.tenants_root)
    slugs = sorted(path.name for path in service.tenants_root.iterdir() if path.is_dir() and not path.name.startswith("."))
    documents: dict[Path, str] = {}
    rows: list[tuple[str, str, int, int, int]] = []
    findings: list[tuple[str, str, str, str]] = []
    errors: list[tuple[str, str]] = []

    for slug in slugs:
        try:
            sections = _load_legacy_sections(service, slug)
            result = import_legacy_sections(slug, sections)
            if compile_business_config(result.config, LegacyYamlSecretResolver(lambda s=sections: s)) != sections:
                raise ValueError("la compilación no reproduce las secciones YAML de origen")
            document = store.dump(result.config)
            leaked = [value for value in payment_values(sections) if value in document]
            if leaked:
                raise ValueError(f"el documento contiene {len(leaked)} datos de pago sensibles")
            documents[store.path_for(slug)] = document
            rows.append((slug, result.config.offer.model, result.typed_fields, result.compatibility_fields, result.secret_refs))
            findings += [(slug, item.kind, item.code, item.message) for item in review(result.config)]
        except Exception as exc:
            errors.append((slug, str(exc)))

    lines = [
        "# Informe de migración a BusinessConfig v1",
        "",
        "Generado por `scripts/migrate_tenants_to_contract.py`. Cada documento se validó contra el contrato,",
        "se comprobó que compilado reproduce exactamente sus YAML de origen y que no contiene datos de pago.",
        "",
        f"- Negocios encontrados: {len(slugs)}",
        f"- Negocios migrados: {len(rows)}",
        f"- Errores: {len(errors)}",
        "",
        "| Negocio | Oferta | Campos tipados | Campos en compatibilidad | Referencias a secretos |",
        "|---|---|---|---|---|",
        *[f"| {slug} | {model} | {typed} | {compat} | {secrets} |" for slug, model, typed, compat, secrets in rows],
        "",
        f"Totales: {sum(r[2] for r in rows)} campos tipados, {sum(r[3] for r in rows)} en compatibilidad, "
        f"{sum(r[4] for r in rows)} referencias a secretos.",
        "",
        "## Diagnóstico de los documentos",
        "",
        "Documentos válidos con datos que el negocio debe decidir o completar (`app/domain/business_config/diagnostics.py`).",
        "No se corrigen automáticamente: cambiarían la configuración comercial del negocio.",
        "",
        "| Negocio | Tipo | Código | Detalle |",
        "|---|---|---|---|",
        *[f"| {slug} | {kind} | `{code}` | {message} |" for slug, kind, code, message in findings],
    ]
    if errors:
        lines += ["", "## Errores", "", *[f"- {slug}: {message}" for slug, message in errors]]
    return documents, "\n".join(lines) + "\n", errors


def main() -> int:
    documents, report, errors = build()
    for slug, message in errors:
        print(f"[error]    {slug}: {message}")
    if "--check" in sys.argv[1:]:
        outdated = [path for path, text in documents.items() if not path.is_file() or path.read_text(encoding="utf-8") != text]
        if not REPORT_PATH.is_file() or REPORT_PATH.read_text(encoding="utf-8") != report:
            outdated.append(REPORT_PATH)
        for path in outdated:
            print(f"[outdated] {path.relative_to(REPO_ROOT)}")
        print(f"[{'ok' if not outdated and not errors else 'fail'}] {len(documents)} documentos")
        return 1 if outdated or errors else 0
    for path, text in documents.items():
        path.write_text(text, encoding="utf-8")
        print(f"[migrated] {path.parent.name}")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\nmigrados={len(documents)} errores={len(errors)} informe={REPORT_PATH.relative_to(REPO_ROOT)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
