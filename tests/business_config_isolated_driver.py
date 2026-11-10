"""Operaciones del almacén de BusinessConfig, para ejecutarlas en un proceso aparte (no es un archivo de pruebas).

Lo lanza `test_business_config_yaml_independence.py` sobre una copia mínima del código, sin YAML ni motor.
Registra cualquier intento de abrir un YAML, un `.env` o un archivo del proyecto original. Recibe el escenario
en JSON por la entrada estándar y devuelve hechos en JSON por la salida; los datos de pago solo salen como
huella, nunca como valor.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

FORBIDDEN_ROOT = os.path.abspath(os.environ["BC_FORBIDDEN_ROOT"])
opened: list[str] = []


def _audit(event: str, args: tuple) -> None:
    if event != "open" or not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    path = os.path.abspath(os.fsdecode(args[0]))
    name = os.path.basename(path).lower()
    if name.endswith((".yaml", ".yml")) or name.startswith(".env") or path.startswith(FORBIDDEN_ROOT):
        opened.append(path)


sys.addaudithook(_audit)

FORBIDDEN_MODULES = (
    "yaml",
    "app.api",
    "app.application",
    "app.config",
    "app.connectors",
    "app.database",
    "app.infrastructure.ai",
    "app.infrastructure.config",
    "app.infrastructure.db",
    "app.models",
    "app.repositories",
    "app.services",
)


def digest(value) -> str:
    canonical = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def open_service():
    from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema

    engine = create_business_config_engine()
    create_local_schema(engine)
    return build_business_config_service(engine), engine


def _dump(config) -> dict:
    return config.model_dump(mode="json", exclude_none=True)


def cycle(spec: dict) -> dict:
    """Todo el ciclo de un negocio nuevo, que nunca tuvo carpeta ni YAML."""
    service, engine = open_service()
    slug = spec["slug"]
    facts: dict = {}
    created = service.create_business(slug, "Negocio nuevo", document=spec["document"], payment_values=spec["values"])
    facts["created_draft"] = created.draft_version
    facts["recovered_draft"] = service.get_draft(slug).version.version
    service.publish(slug, 1)
    facts["draft_after_publish"] = service.get_draft(slug) is None
    facts["published_digest_1"] = digest(service.compile_sections(slug))

    edited = _dump(service.get_version(slug, 1).config)
    edited["identity"]["name"] = "Nombre editado"
    link_ref = edited["payments"][0]["link"]["secret_ref"]
    version = service.save_changes(slug, edited, payment_values={link_ref: spec["new_link"]}, created_by="prueba").version
    facts["edited_draft_name"] = service.get_draft(slug).config.identity.name
    facts["published_name_before"] = service.get_published(slug).identity.name
    service.publish(slug, version)
    facts["published_name_after"] = service.get_published(slug).identity.name
    facts["new_link_compiled"] = service.compile_sections(slug)["pricing"]["catalog"]["payment"]["link"] == spec["new_link"]
    facts["history"] = [[item.version, item.status] for item in service.history(slug)]

    facts["rollback_to"] = service.rollback(slug)
    facts["digest_after_rollback"] = digest(service.compile_sections(slug))
    facts["restored"] = service.restore_version(slug, version).version
    facts["restored_name"] = service.get_draft(slug).config.identity.name
    facts["businesses"] = [item.slug for item in service.list_businesses()]
    engine.dispose()
    return facts


def reopen(spec: dict) -> dict:
    """Otro proceso sobre la misma base: lo que sobrevive a cerrar y volver a abrir la aplicación."""
    service, engine = open_service()
    slug = spec["slug"]
    facts = {
        "businesses": [item.slug for item in service.list_businesses()],
        "draft": service.get_draft(slug).version.version,
        "published_name": service.get_published(slug).identity.name,
        "digest": digest(service.compile_sections(slug)),
        "history": [[item.version, item.status] for item in service.history(slug)],
    }
    engine.dispose()
    return facts


def nine(spec: dict) -> dict:
    """Los negocios importados, ya sin YAML: compilan a su referencia (lo de sus YAML, más el perfil comercial), se recuperan, se
    editan, se publican y se revierten."""
    from app.domain.business_config.compiler import comparable_with_yaml

    service, engine = open_service()

    def yaml_digest(slug: str) -> str:
        return digest(comparable_with_yaml(service.compile_sections(slug)))

    facts: dict = {"businesses": [item.slug for item in service.list_businesses()], "by_slug": {}}
    for slug in spec["slugs"]:
        before = yaml_digest(slug)
        document = _dump(service.get_published(slug))
        document["identity"]["description"] += " (editado)"
        version = service.save_changes(slug, document).version
        recovered = service.get_draft(slug).config.identity.description == document["identity"]["description"]
        service.publish(slug, version)
        edited = yaml_digest(slug)
        rollback_to = service.rollback(slug)
        facts["by_slug"][slug] = {
            "digest": before,
            "edited_changes_compilation": edited != before,
            "draft_recovered": recovered,
            "rollback_to": rollback_to,
            "digest_after_rollback": yaml_digest(slug),
            "history": [[item.version, item.status] for item in service.history(slug)],
        }
    engine.dispose()
    return facts


def main() -> None:
    spec = json.load(sys.stdin)
    import app

    facts = {"cycle": cycle, "reopen": reopen, "nine": nine}[spec["scenario"]](spec)
    print(
        json.dumps(
            {
                "facts": facts,
                "opened": opened,
                "forbidden_modules": sorted(name for name in sys.modules if name.startswith(FORBIDDEN_MODULES)),
                "app_location": os.path.abspath(app.__file__),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
