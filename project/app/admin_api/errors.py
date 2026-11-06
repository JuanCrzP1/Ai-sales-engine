"""Errores de la API: traduce los del dominio a respuestas HTTP, con mensajes en español que nunca repiten los valores recibidos."""
from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from dataclasses import asdict
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.business_config.errors import (
    BusinessAlreadyExistsError,
    BusinessConfigError,
    BusinessNotFoundError,
    InvalidDocumentError,
    InvalidFieldsError,
    PaymentDataUnavailableError,
    PublicationError,
    SecretResolutionError,
    VersionConflictError,
)

logger = logging.getLogger("admin-api")

UNPROCESSABLE = 422
# Sin detalles técnicos: quien administra el negocio lo corrige reemplazando el dato, y la referencia interna no le sirve.
PAYMENT_PROBLEM = "Falta un dato de pago o no se puede leer con la clave actual. Revísalo en Pagos y cierre."
_DOCUMENT_TO_FIX = "La configuración tiene datos por corregir."
_ALREADY_EXISTS = "Ya existe un negocio con ese identificador."
_CHANGED_ELSEWHERE = "Este negocio cambió desde que lo abriste, quizá en otra pestaña. Recarga para ver lo último antes de guardar."

# Pydantic añade al recorrido las ramas de los tipos compuestos (`int`, `float`, `function-after[...]`...).
_UNION_BRANCHES = {"int", "float", "str", "bool"}
_TECHNICAL_MESSAGES = {
    "model=plans requiere al menos un plan y ningún catálogo": "Agrega al menos un plan o servicio.",
    "model=catalog requiere un catálogo y ningún plan": "Agrega al menos un producto al catálogo.",
}


class ApiError(Exception):
    """Error esperado de la API, con su estado HTTP y los problemas por campo, si los hay."""

    def __init__(self, status_code: int, message: str, *, code: str = "error", issues: list[dict[str, str]] | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.code = code
        self.issues = issues or []

    def payload(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "issues": self.issues}


def _is_branch(part: Any) -> bool:
    return isinstance(part, str) and (part in _UNION_BRANCHES or "[" in part or part.startswith("constrained-"))


def issue_path(location: Iterable[Any]) -> str:
    return ".".join(str(part) for part in location if not _is_branch(part))


def _message(error: dict[str, Any]) -> str:
    kind = error["type"]
    context = error.get("ctx") or {}
    if kind == "value_error":
        text = re.sub(r"^Value error, ", "", error["msg"])
        return _TECHNICAL_MESSAGES.get(text, text[:1].upper() + text[1:] + ("" if text.endswith(".") else "."))
    if kind == "missing":
        return "Este dato es obligatorio."
    if kind == "string_too_long":
        return f"Admite hasta {context.get('max_length')} caracteres."
    if kind == "too_long":
        return f"Admite hasta {context.get('max_length')} elementos."
    if kind == "too_short":
        return f"Necesita al menos {context.get('min_length')} elemento."
    if kind == "string_pattern_mismatch":
        return "El formato no es válido."
    if kind in {"greater_than_equal", "greater_than"}:
        return f"Debe ser {context.get('ge', context.get('gt'))} o más."
    if kind in {"literal_error", "enum"}:
        return "Elige una de las opciones permitidas."
    if kind == "extra_forbidden":
        return "Este dato no forma parte de la configuración."
    if kind.startswith(("date_", "datetime_")):
        return "Escribe una fecha válida."
    return "El valor no tiene el tipo esperado."


def validation_issues(errors: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    """Un problema por campo, con su ruta en el documento. Sin `input`: podría ser un dato de pago."""
    issues: dict[str, str] = {}
    for error in errors:
        issues.setdefault(issue_path(error["loc"]), _message(error))
    return [{"path": path, "message": message} for path, message in issues.items()]


def _reason(request: Request, exc: Exception) -> str:
    """El motivo sin el prefijo con el identificador, que el panel ya conoce."""
    text = str(exc).removeprefix(f"{request.path_params.get('slug', '')}: ")
    return text[:1].upper() + text[1:] + ("" if text.endswith(".") else ".")


def _api_error(request: Request, exc: BusinessConfigError) -> ApiError:
    if isinstance(exc, BusinessNotFoundError):
        return ApiError(status.HTTP_404_NOT_FOUND, "Ese negocio no existe.", code="not_found")
    if isinstance(exc, BusinessAlreadyExistsError):
        return ApiError(status.HTTP_409_CONFLICT, _ALREADY_EXISTS, code="duplicate", issues=[{"path": "slug", "message": _ALREADY_EXISTS}])
    if isinstance(exc, VersionConflictError):
        return ApiError(status.HTTP_409_CONFLICT, _CHANGED_ELSEWHERE, code="conflict")
    if isinstance(exc, PaymentDataUnavailableError):
        return ApiError(status.HTTP_409_CONFLICT, f"No se puede publicar. {PAYMENT_PROBLEM}", code="conflict")
    if isinstance(exc, PublicationError):
        return ApiError(status.HTTP_409_CONFLICT, _reason(request, exc), code="conflict")
    if isinstance(exc, InvalidDocumentError):
        return ApiError(UNPROCESSABLE, _DOCUMENT_TO_FIX, code="invalid", issues=validation_issues(exc.errors))
    if isinstance(exc, InvalidFieldsError):
        message = exc.issues[0].message if len(exc.issues) == 1 else _DOCUMENT_TO_FIX
        return ApiError(UNPROCESSABLE, message, code="invalid", issues=[asdict(issue) for issue in exc.issues])
    return ApiError(UNPROCESSABLE, _reason(request, exc), code="invalid")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _expected(_request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(exc.payload(), exc.status_code)

    @app.exception_handler(BusinessConfigError)
    async def _business_config(request: Request, exc: BusinessConfigError) -> JSONResponse:
        error = _api_error(request, exc)
        return JSONResponse(error.payload(), error.status_code)

    @app.exception_handler(RequestValidationError)
    async def _invalid_request(_request: Request, exc: RequestValidationError) -> JSONResponse:
        # El manejador por defecto repite la entrada, que puede traer datos de pago.
        issues = validation_issues(error for error in exc.errors())
        return JSONResponse({"code": "invalid", "message": "La petición no es válida.", "issues": issues}, UNPROCESSABLE)

    @app.exception_handler(SecretResolutionError)
    async def _payment_key(_request: Request, exc: SecretResolutionError) -> JSONResponse:
        return JSONResponse({"code": "payment_key", "message": str(exc), "issues": []}, status.HTTP_503_SERVICE_UNAVAILABLE)

    @app.exception_handler(Exception)
    async def _unexpected(_request: Request, exc: Exception) -> JSONResponse:
        # Sin el mensaje de la excepción: las respuestas no deben llevar detalles internos.
        logger.error("error_inesperado", extra={"error_type": type(exc).__name__})
        return JSONResponse({"code": "unexpected", "message": "Ocurrió un error inesperado en el servidor local.", "issues": []}, status.HTTP_500_INTERNAL_SERVER_ERROR)
