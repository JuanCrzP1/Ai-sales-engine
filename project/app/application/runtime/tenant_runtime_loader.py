"""La configuración de cada negocio para el motor, mensaje a mensaje: siempre la versión publicada desde el panel.

El motor la lee del almacén de BusinessConfig (`runtime_access`: la base de Neon en la nube o el SQLite local) y la compila a las
secciones que consume. No hay otra fuente: ningún negocio necesita una carpeta YAML, y si el almacén falla el motor no responde
con datos viejos: lo informa con `BusinessUnavailableError` y el llamador da un mensaje neutro.
"""
from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError

from app.application.runtime.runtime_yaml_builder import RuntimeYamlBuilder
from app.domain.business_config.compiler import compile_business_config
from app.domain.business_config.errors import BusinessConfigError, SecretResolutionError
from app.infrastructure.business_config.runtime_access import open_published_reader
from app.utils.logger import logger

# Interruptores de la oferta que lee el motor en el nivel superior del runtime (`SalesFlow`, `prompt_builder`).
_FEATURE_DEFAULTS = {"pricing_enabled": True, "multi_currency": False, "multi_plan": False, "catalog_mode": False, "business_model": ""}


class BusinessUnavailableError(RuntimeError):
    """No se pudo leer la configuración publicada del negocio: no existe, no tiene versión publicada o el almacén falló."""


def _deep_merge(base: dict, incoming: dict) -> dict:
    result = dict(base)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            if not value:
                result[key] = {}
            else:
                result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _assemble_runtime_yaml(sections: dict[str, dict], channel: str | None = None) -> dict:
    config_section = dict(sections.get("config") or {})
    features = config_section.get("features") if isinstance(config_section.get("features"), dict) else {}
    runtime_yaml = {
        "sales": dict(sections.get("sales") or {}),
        "business": dict(sections.get("business") or {}),
        "pricing": dict(sections.get("pricing") or {}),
        "inventory": dict(sections.get("inventory") or {}),
        "config": config_section,
        "features": {**_FEATURE_DEFAULTS, **features},
        "capabilities": dict(config_section.get("capabilities") or {}),
        "post_payment": dict(config_section.get("post_payment") or {}),
    }

    normalized_channel = str(channel or "").strip().lower()
    if normalized_channel:
        runtime_yaml["channel"] = normalized_channel

    return runtime_yaml


def runtime_from_sections(tenant_slug: str, sections: dict[str, dict], *, channel: str | None = None) -> dict:
    """El runtime que usa el motor, armado desde lo compilado de una versión concreta (lo usa el área de pruebas del panel)."""
    return RuntimeYamlBuilder().build(tenant_slug=tenant_slug, partial_yaml=_assemble_runtime_yaml(sections, channel=channel))


def published_sections(tenant_slug: str) -> dict[str, dict]:
    """Lo publicado del negocio, compilado a las secciones del motor, con sus datos de pago descifrados."""
    reader = open_published_reader()
    return compile_business_config(reader.published(tenant_slug), reader.payment_resolver(tenant_slug))


def load_tenant_runtime_yaml(tenant_slug: str, *, channel: str | None = None, extra_yaml: dict | None = None) -> dict:
    slug = str(tenant_slug or "").strip()
    if not slug:
        raise BusinessUnavailableError("falta el negocio del mensaje")
    try:
        sections = published_sections(slug)
    except (BusinessConfigError, SecretResolutionError, SQLAlchemyError, ValueError) as exc:
        # Alerta, no respaldo: un negocio nunca responde con datos que no publicó. Del error solo el tipo: el texto de un error de
        # base de datos puede incluir datos de conexión.
        logger.error("business_config_unavailable", extra={"tenant": slug, "error": type(exc).__name__})
        raise BusinessUnavailableError(f"{slug}: sin configuración publicada disponible") from exc

    runtime_yaml = _assemble_runtime_yaml(sections, channel=channel)
    if isinstance(extra_yaml, dict) and extra_yaml:
        runtime_yaml = _deep_merge(runtime_yaml, extra_yaml)
    return RuntimeYamlBuilder().build(tenant_slug=slug, partial_yaml=runtime_yaml)
