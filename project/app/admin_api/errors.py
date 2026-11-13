"""Errores de la API: traduce los del dominio a respuestas HTTP, con mensajes en español que nunca repiten los valores recibidos."""
from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.business_config.errors import (
    AIKeyMissingError,
    AssistantUnavailableError,
    BusinessAlreadyExistsError,
    BusinessConfigError,
    BusinessDeletionBlockedError,
    BusinessNotFoundError,
    ConversationNotFoundError,
    InvalidDocumentError,
    InvalidFieldsError,
    NotAllowedError,
    QuickReplyNotFoundError,
    PaymentDataUnavailableError,
    PublicationError,
    SecretResolutionError,
    UsageLimitExceededError,
    VersionConflictError,
)
from app.domain.business_config.validation_messages import validation_issues
from app.domain.business_config.help import HelpArticleNotFoundError
from app.domain.business_config.team import InvitationError, TeamRuleError

logger = logging.getLogger("admin-api")

UNPROCESSABLE = 422
# Sin detalles técnicos: quien administra el negocio lo corrige reemplazando el dato, y la referencia interna no le sirve.
PAYMENT_PROBLEM = "Falta un dato de pago o no se puede leer con la clave actual. Revísalo en Pagos y cierre."
_DOCUMENT_TO_FIX = "La configuración tiene datos por corregir."
_ALREADY_EXISTS = "Ya existe un negocio con ese identificador."
_CHANGED_ELSEWHERE = "Este negocio cambió desde que lo abriste, quizá en otra pestaña. Recarga para ver lo último antes de guardar."
_TOO_MANY = "Hiciste muchas solicitudes seguidas. Espera {wait} y vuelve a intentarlo."


def _wait(seconds: int) -> str:
    if seconds < 60:
        return "unos segundos" if seconds < 10 else f"{seconds} segundos"
    minutes = -(-seconds // 60)
    return "1 minuto" if minutes == 1 else f"{minutes} minutos"

class ApiError(Exception):
    """Error esperado de la API, con su estado HTTP y los problemas por campo, si los hay."""

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        code: str = "error",
        issues: list[dict[str, str]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.code = code
        self.issues = issues or []
        self.headers = headers

    def payload(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "issues": self.issues}


def _reason(request: Request, exc: Exception) -> str:
    """El motivo sin el prefijo con el identificador, que el panel ya conoce."""
    text = str(exc).removeprefix(f"{request.path_params.get('slug', '')}: ")
    return text[:1].upper() + text[1:] + ("" if text.endswith(".") else ".")


def _api_error(request: Request, exc: BusinessConfigError) -> ApiError:
    if isinstance(exc, UsageLimitExceededError):
        wait = exc.retry_after_seconds
        return ApiError(status.HTTP_429_TOO_MANY_REQUESTS, _TOO_MANY.format(wait=_wait(wait)), code="rate_limited", headers={"Retry-After": str(wait)})
    if isinstance(exc, AIKeyMissingError):
        return ApiError(status.HTTP_409_CONFLICT, _reason(request, exc), code="ai_key_missing")
    if isinstance(exc, AssistantUnavailableError):
        return ApiError(status.HTTP_503_SERVICE_UNAVAILABLE, _reason(request, exc), code="unavailable")
    if isinstance(exc, ConversationNotFoundError):
        return ApiError(status.HTTP_404_NOT_FOUND, "Esa conversación no existe.", code="not_found")
    if isinstance(exc, InvitationError):
        return ApiError(status.HTTP_404_NOT_FOUND, str(exc), code="invitation")
    if isinstance(exc, TeamRuleError):
        return ApiError(status.HTTP_409_CONFLICT, str(exc), code="conflict")
    if isinstance(exc, HelpArticleNotFoundError):
        return ApiError(status.HTTP_404_NOT_FOUND, "Ese artículo de ayuda no existe.", code="not_found")
    if isinstance(exc, QuickReplyNotFoundError):
        return ApiError(status.HTTP_404_NOT_FOUND, "Esa respuesta rápida no existe.", code="not_found")
    if isinstance(exc, NotAllowedError):
        return ApiError(status.HTTP_403_FORBIDDEN, str(exc), code="forbidden")
    if isinstance(exc, BusinessDeletionBlockedError):
        return ApiError(status.HTTP_409_CONFLICT, str(exc), code="conflict")
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
        return JSONResponse(exc.payload(), exc.status_code, headers=exc.headers)

    @app.exception_handler(BusinessConfigError)
    async def _business_config(request: Request, exc: BusinessConfigError) -> JSONResponse:
        error = _api_error(request, exc)
        return JSONResponse(error.payload(), error.status_code, headers=error.headers)

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
        return JSONResponse({"code": "unexpected", "message": "Ocurrió un error inesperado en el servidor. Intenta de nuevo en un momento.", "issues": []}, status.HTTP_500_INTERNAL_SERVER_ERROR)
