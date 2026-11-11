"""Los negocios de ejemplo (`project/config/tenants/<slug>/`): siembran este equipo, la rama de pruebas de Neon, las pruebas
automáticas y los laboratorios. Nunca se cargan en producción: allí cada cuenta crea sus negocios.

Cada uno tiene tres archivos, en el formato del contrato:
- `business-config.json`: el documento comercial, tal como lo guarda el almacén (los datos de pago son referencias
  `secret_store:`, nunca valores).
- `engine-settings.json`: sus ajustes técnicos.
- `payment-values.json`: los datos de pago de ejemplo de cada referencia (números y links ficticios). Al importarlo se guardan
  cifrados, como los de cualquier negocio.

Son la fuente de verdad de los ejemplos: para cambiar uno, se edita su JSON (o se edita en el panel y se exporta). Antes eran YAML;
se convirtieron una sola vez y el resultado era idéntico al que importaba la migración anterior.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.business_config_application.service import BusinessConfigService
from app.domain.business_config.compiler import compile_business_config
from app.domain.business_config.contract import BusinessConfig, SecretRef
from app.domain.business_config.errors import BusinessConfigError
from app.domain.business_config.payment_data import iter_secret_refs
from app.domain.business_config.validation import validate_document, validate_engine_settings

EXAMPLES_DIR = Path(__file__).resolve().parents[3] / "config" / "tenants"
CONTRACT_FILENAME = "business-config.json"
ENGINE_SETTINGS_FILENAME = "engine-settings.json"
PAYMENT_VALUES_FILENAME = "payment-values.json"
AUTHOR = "negocios de ejemplo"


@dataclass(frozen=True)
class ExampleBusiness:
    """Un negocio de ejemplo listo para el almacén: su documento, sus datos de pago y sus ajustes técnicos."""

    slug: str
    name: str
    document: dict[str, Any]
    payment_values: dict[str, str]
    engine_settings: dict[str, Any]

    def config(self) -> BusinessConfig:
        """El documento validado, con sus ajustes técnicos."""
        settings = validate_engine_settings(self.slug, self.engine_settings) if self.engine_settings else None
        return validate_document(self.slug, self.document).with_engine_settings(settings)

    def payment_resolver(self) -> Callable[[SecretRef], str]:
        return lambda ref: self.payment_values[ref.secret_ref]


@dataclass(frozen=True)
class ImportReport:
    created: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    # Ya existían con versiones, pero sin ninguna publicada: no se tocan y requieren revisión.
    unpublished: list[str] = field(default_factory=list)


def example_slugs(root: Path = EXAMPLES_DIR) -> list[str]:
    return sorted(path.name for path in Path(root).iterdir() if (path / CONTRACT_FILENAME).is_file())


def _read_json(path: Path, slug: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BusinessConfigError(f"{slug}: {path.name} no se puede leer ({type(exc).__name__})") from exc


def load_example(slug: str, root: Path = EXAMPLES_DIR) -> ExampleBusiness:
    """Lee y comprueba un negocio de ejemplo: el documento cumple el contrato, cada referencia de pago tiene su valor y compila."""
    folder = Path(root) / slug
    if not (folder / CONTRACT_FILENAME).is_file():
        raise BusinessConfigError(f"{slug}: no es un negocio de ejemplo (falta {CONTRACT_FILENAME})")
    document = _read_json(folder / CONTRACT_FILENAME, slug)
    settings_path = folder / ENGINE_SETTINGS_FILENAME
    engine_settings = _read_json(settings_path, slug) if settings_path.is_file() else {}
    values_path = folder / PAYMENT_VALUES_FILENAME
    payment_values = _read_json(values_path, slug) if values_path.is_file() else {}
    refs = {holder["secret_ref"] for holder in iter_secret_refs(document)}
    missing = sorted(refs - set(payment_values))
    if missing:
        raise BusinessConfigError(f"{slug}: faltan datos de pago de ejemplo en {PAYMENT_VALUES_FILENAME}: {', '.join(missing)}")
    example = ExampleBusiness(slug, str(document["identity"]["name"]), document, {ref: payment_values[ref] for ref in sorted(refs)}, engine_settings)
    compile_business_config(example.config(), example.payment_resolver())
    return example


def import_example(service: BusinessConfigService, example: ExampleBusiness, *, already_registered: bool = False) -> None:
    """Crea el negocio (si hace falta), guarda su documento con sus datos de pago cifrados, sus ajustes técnicos, y lo publica."""
    if not already_registered:
        service.create_business(example.slug, example.name)
    version = service.save_changes(example.slug, example.document, payment_values=example.payment_values, created_by=AUTHOR)
    service.save_engine_settings(example.slug, example.engine_settings)
    service.publish(example.slug, version.version)


def import_examples(service: BusinessConfigService, root: Path = EXAMPLES_DIR) -> ImportReport:
    """Importa los ejemplos que faltan. Nunca toca un negocio que ya tenga versiones; uno registrado sin versiones se completa."""
    service.verify_payment_key()
    existing = {summary.slug: summary for summary in service.list_businesses()}
    slugs = example_slugs(root)
    pending = [slug for slug in slugs if slug not in existing or existing[slug].latest_version is None]
    # Primero se leen y comprueban todos, después se escribe: si uno falla, no se escribe ninguno.
    examples = [load_example(slug, root) for slug in pending]
    for example in examples:
        import_example(service, example, already_registered=example.slug in existing)
    skipped = [slug for slug in slugs if slug not in pending]
    return ImportReport(pending, skipped, [slug for slug in skipped if existing[slug].published_version is None])
