"""Validación de lo que entra a BusinessConfig: una sola definición para quien guarda y para quien lee."""
from __future__ import annotations

from typing import Any

from pydantic import TypeAdapter, ValidationError

from app.domain.business_config.contract import BusinessConfig, Slug
from app.domain.business_config.engine_settings import EngineSettings
from app.domain.business_config.errors import BusinessConfigError, FieldIssue, InvalidDocumentError, InvalidFieldsError

_SLUG = TypeAdapter(Slug)


def is_valid_slug(value: str) -> bool:
    try:
        _SLUG.validate_python(value)
    except ValidationError:
        return False
    return True


def check_business_identity(tenant_slug: str, name: str) -> None:
    if not is_valid_slug(tenant_slug):
        message = "Usa solo minúsculas, números y guion bajo, empezando por una letra o un número."
        raise InvalidFieldsError(f"{tenant_slug!r}: identificador de negocio no válido", [FieldIssue("slug", message)])
    if not name.strip():
        raise InvalidFieldsError(f"{tenant_slug}: el negocio necesita un nombre", [FieldIssue("name", "Escribe el nombre del negocio.")])


def validate_document(tenant_slug: str, document: Any) -> BusinessConfig:
    try:
        config = BusinessConfig.model_validate(document)
    except ValidationError as exc:
        raise InvalidDocumentError(
            f"{tenant_slug}: la configuración no cumple el contrato ({exc.error_count()} errores)",
            exc.errors(include_url=False, include_input=False),
        ) from exc
    if config.tenant_slug != tenant_slug:
        raise InvalidFieldsError(
            f"{tenant_slug}: el documento declara el tenant '{config.tenant_slug}'",
            [FieldIssue("tenant_slug", "El documento pertenece a otro negocio.")],
        )
    return config


def validate_engine_settings(tenant_slug: str, document: Any) -> EngineSettings:
    try:
        settings = EngineSettings.model_validate(document)
    except ValidationError as exc:
        raise BusinessConfigError(f"{tenant_slug}: los ajustes técnicos no son válidos ({exc.error_count()} errores)") from exc
    if settings.tenant_slug != tenant_slug:
        raise BusinessConfigError(f"{tenant_slug}: los ajustes técnicos declaran el tenant '{settings.tenant_slug}'")
    return settings
