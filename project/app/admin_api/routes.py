"""Rutas de la API del panel: reciben la petición, llaman a `BusinessConfigService` y serializan la respuesta.

Ni base de datos, ni reglas de negocio, ni motor. El servicio es la autoridad: cada guardado pasa por el contrato, y los
datos de pago entran por aquí pero nunca salen. Sus errores se convierten en respuestas HTTP en `errors.py`.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, status

from app.admin_api.errors import UNPROCESSABLE, ApiError
from app.admin_api.schemas import (
    CreateBusiness,
    PublishVersion,
    SaveConfig,
    ValidateConfig,
    config_payload,
    review_payload,
    summary_payload,
    version_payload,
)
from app.business_config_application.service import BusinessConfigService
from app.domain.business_config.errors import BusinessNotFoundError
from app.domain.business_config.validation import is_valid_slug

router = APIRouter(prefix="/api")

PANEL_USER = "panel-local"


def _service(request: Request) -> BusinessConfigService:
    return request.app.state.service


def _business_slug(slug: str) -> str:
    """Un identificador no válido se trata igual que uno inexistente, sin llegar al almacén."""
    if not is_valid_slug(slug):
        raise BusinessNotFoundError(f"{slug!r}: identificador no válido")
    return slug


Service = Annotated[BusinessConfigService, Depends(_service)]
BusinessSlug = Annotated[str, Depends(_business_slug)]


# --------------------------------------------------------------------------- contrato


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/contract")
def contract(request: Request) -> dict[str, Any]:
    """El esquema que define los formularios del panel: se genera del contrato, no se copia."""
    return request.app.state.contract_schema


# --------------------------------------------------------------------------- negocios


@router.get("/businesses")
def list_businesses(service: Service) -> list[dict[str, Any]]:
    return [summary_payload(summary) for summary in service.list_businesses()]


@router.post("/businesses", status_code=status.HTTP_201_CREATED)
def create_business(payload: CreateBusiness, service: Service) -> dict[str, Any]:
    return summary_payload(service.create_business(payload.slug, payload.name))


@router.post("/businesses/import")
def import_existing_businesses(service: Service) -> dict[str, list[str]]:
    """Importa los negocios de `project/config/tenants/` que falten. Lee los YAML, no los modifica; lo ya guardado no se toca."""
    # Solo aquí se leen los YAML: ni siquiera esta migración carga el motor. Se retira con ellos en la Fase 4.
    from app.infrastructure.config.config_service import ConfigService
    from app.infrastructure.config.legacy_store_migration import import_all

    try:
        report = import_all(service, ConfigService())
    except ValueError as exc:
        raise ApiError(UNPROCESSABLE, f"No se pudo importar: {exc}", code="invalid") from exc
    return {"created": report.created, "skipped": report.skipped, "unpublished": report.unpublished}


@router.delete("/businesses/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_business(slug: BusinessSlug, service: Service, confirm: Annotated[str, Query()] = "") -> None:
    """Borra el negocio con sus versiones y datos de pago. Exige repetir el identificador."""
    service.get_business(slug)
    if confirm != slug:
        raise ApiError(status.HTTP_400_BAD_REQUEST, "Confirma el identificador del negocio para eliminarlo.", code="confirmation_required")
    service.delete_business(slug)


# --------------------------------------------------------------------------- configuración


@router.get("/businesses/{slug}/config")
def get_config(slug: BusinessSlug, service: Service) -> dict[str, Any]:
    return config_payload(service.get_editable(slug))


@router.put("/businesses/{slug}/config")
def save_config(slug: BusinessSlug, payload: SaveConfig, service: Service) -> dict[str, Any]:
    service.save_changes(slug, payload.document, payment_values=payload.payment_values, created_by=PANEL_USER, expected_version=payload.base_version)
    return config_payload(service.get_editable(slug))


@router.post("/businesses/{slug}/validate")
def validate_config(slug: BusinessSlug, payload: ValidateConfig, service: Service) -> dict[str, Any]:
    """Valida un documento sin guardarlo."""
    return {"valid": True, "diagnostics": [asdict(item) for item in service.validate(slug, payload.document)]}


@router.get("/businesses/{slug}/review")
def review_config(slug: BusinessSlug, service: Service) -> dict[str, Any]:
    """Diagnóstico de lo que se está editando y si se puede compilar. Nunca devuelve lo compilado: lleva datos de pago."""
    return review_payload(service.review(slug))


# --------------------------------------------------------------------------- versiones


@router.get("/businesses/{slug}/versions")
def list_versions(slug: BusinessSlug, service: Service) -> list[dict[str, Any]]:
    return [version_payload(version) for version in service.history(slug)]


@router.post("/businesses/{slug}/versions/{version}/restore")
def restore_version(slug: BusinessSlug, version: int, service: Service) -> dict[str, Any]:
    """Crea un borrador con el contenido de una versión anterior; no publica nada."""
    service.restore_version(slug, version, created_by=PANEL_USER)
    return config_payload(service.get_editable(slug))


@router.post("/businesses/{slug}/publish")
def publish(slug: BusinessSlug, payload: PublishVersion, service: Service) -> dict[str, Any]:
    """Publica una versión; si no compila o le faltan datos de pago, lo publicado no cambia."""
    service.publish(slug, payload.version)
    return config_payload(service.get_editable(slug))


@router.post("/businesses/{slug}/rollback")
def rollback(slug: BusinessSlug, service: Service) -> dict[str, Any]:
    """Vuelve a publicar la versión publicada anterior."""
    service.rollback(slug)
    return config_payload(service.get_editable(slug))
