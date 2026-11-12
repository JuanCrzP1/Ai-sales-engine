"""Rutas de la API del panel: reciben la petición, llaman a `BusinessConfigService` y serializan la respuesta.

Ni base de datos, ni reglas de negocio, ni motor. El servicio es la autoridad: cada guardado pasa por el contrato, y los
datos de pago entran por aquí pero nunca salen. Sus errores se convierten en respuestas HTTP en `errors.py`.

Quién pide: en la nube, el usuario del token de la sesión, que solo llega a sus negocios (un negocio ajeno responde igual que
uno inexistente); en este equipo, el operador local. Toda ruta de un negocio pasa por `BusinessSlug`, que lo comprueba.
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
    template_payload,
    version_payload,
)
from app.business_config_application.access import BusinessAccess
from app.business_config_application.service import BusinessConfigService
from app.business_config_application.templates import BusinessTemplateCatalog
from app.domain.business_config.access import LOCAL_OPERATOR, Principal
from app.domain.business_config.errors import BusinessNotFoundError, VersionNotFoundError
from app.domain.business_config.templates import TemplateNotFoundError
from app.domain.business_config.validation import is_valid_slug

router = APIRouter(prefix="/api")


def _service(request: Request) -> BusinessConfigService:
    return request.app.state.service


def _access(request: Request) -> BusinessAccess:
    return request.app.state.access


def _templates(request: Request) -> BusinessTemplateCatalog:
    return request.app.state.templates


def _in_the_cloud(request: Request) -> bool:
    return getattr(request.app.state, "verifier", None) is not None


def _principal(request: Request) -> Principal:
    """En la nube, el usuario del token de la sesión; sin token válido, 401. En este equipo, el operador local."""
    verifier = getattr(request.app.state, "verifier", None)
    if verifier is None:
        # API local: su middleware ya rechazó toda petición que no venga de este equipo.
        return LOCAL_OPERATOR
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    principal = verifier.verify(token.strip()) if scheme.lower() == "bearer" else None
    if principal is None:
        raise ApiError(status.HTTP_401_UNAUTHORIZED, "Tu sesión terminó. Vuelve a entrar.", code="unauthenticated")
    # El correo de la cuenta, para los avisos por correo de sus negocios (como mucho cada 10 minutos por proceso).
    attention = getattr(request.app.state, "attention", None)
    if attention is not None:
        attention.remember_account(principal)
    return principal


Service = Annotated[BusinessConfigService, Depends(_service)]
Access = Annotated[BusinessAccess, Depends(_access)]
CurrentUser = Annotated[Principal, Depends(_principal)]


def _business_slug(slug: str, user: CurrentUser, access: Access) -> str:
    """Un identificador no válido, un negocio inexistente y uno ajeno responden igual: 404, sin llegar a sus datos."""
    if not is_valid_slug(slug):
        raise BusinessNotFoundError(f"{slug!r}: identificador no válido")
    access.require(user, slug)
    return slug


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
def list_businesses(user: CurrentUser, access: Access) -> list[dict[str, Any]]:
    return [summary_payload(summary) for summary in access.list_for(user)]


@router.get("/business-templates")
def business_templates(request: Request) -> list[dict[str, Any]]:
    """Las plantillas para empezar un negocio. «Empezar de cero» la ofrece el panel: es no elegir ninguna."""
    return [template_payload(template) for template in _templates(request).list()]


@router.post("/businesses", status_code=status.HTTP_201_CREATED)
def create_business(request: Request, payload: CreateBusiness, user: CurrentUser, access: Access) -> dict[str, Any]:
    """Crea el negocio vacío o, con una plantilla, con su primer borrador ya escrito (sin publicar)."""
    document = None
    if payload.template:
        try:
            template = _templates(request).get(payload.template)
        except TemplateNotFoundError:
            raise ApiError(UNPROCESSABLE, "Esa plantilla no existe.", code="invalid", issues=[{"path": "template", "message": "Elige otra plantilla."}]) from None
        document = template.instantiate(payload.slug, payload.name)
    created = access.create_for(user, payload.slug, payload.name, document=document)
    # El negocio nuevo ya sabe adónde avisar por correo a su dueño.
    attention = getattr(request.app.state, "attention", None)
    if attention is not None:
        attention.remember_account(user, force=True)
    return summary_payload(created)


@router.post("/businesses/import")
def import_existing_businesses(request: Request, service: Service) -> dict[str, list[str]]:
    """Importa los negocios de ejemplo que falten (`project/config/tenants/`); lo ya guardado no se toca.

    Solo en este equipo: en la nube los negocios los crea cada cuenta y la API no recibe el importador."""
    importer = getattr(request.app.state, "examples", None)
    if importer is None or _in_the_cloud(request):
        raise ApiError(status.HTTP_404_NOT_FOUND, "No disponible.", code="not_found")
    try:
        report = importer(service)
    except ValueError as exc:
        raise ApiError(UNPROCESSABLE, f"No se pudo importar: {exc}", code="invalid") from exc
    return {"created": report.created, "skipped": report.skipped, "unpublished": report.unpublished}


@router.delete("/businesses/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_business(request: Request, slug: BusinessSlug, user: CurrentUser, confirm: Annotated[str, Query(max_length=200)] = "") -> None:
    """Elimina el negocio y todo lo suyo, para siempre. Solo su dueño, escribiendo su nombre (`confirm`). Ver
    `BusinessDeletionService`."""
    request.app.state.deletion.delete(user, slug, confirm)


# --------------------------------------------------------------------------- configuración


@router.get("/businesses/{slug}/config")
def get_config(slug: BusinessSlug, service: Service) -> dict[str, Any]:
    return config_payload(service.get_editable(slug))


@router.put("/businesses/{slug}/config")
def save_config(slug: BusinessSlug, payload: SaveConfig, service: Service, user: CurrentUser) -> dict[str, Any]:
    service.save_changes(slug, payload.document, payment_values=payload.payment_values, created_by=user.label, expected_version=payload.base_version)
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


@router.get("/businesses/{slug}/versions/{version}")
def get_version(slug: BusinessSlug, version: int, service: Service) -> dict[str, Any]:
    """Una versión con su documento, para comparar lo que se edita con lo publicado. Como el borrador, los datos de pago van
    solo como referencias: nunca su valor."""
    try:
        stored = service.get_version(slug, version)
    except VersionNotFoundError as exc:
        raise ApiError(status.HTTP_404_NOT_FOUND, "Esa versión no existe.", code="not_found") from exc
    return {"version": version_payload(stored.version), "document": stored.config.model_dump(mode="json", exclude_none=True)}


@router.post("/businesses/{slug}/versions/{version}/restore")
def restore_version(slug: BusinessSlug, version: int, service: Service, user: CurrentUser) -> dict[str, Any]:
    """Crea un borrador con el contenido de una versión anterior; no publica nada."""
    service.restore_version(slug, version, created_by=user.label)
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
