"""Errores de BusinessConfig: qué salió mal, sin saber quién lo va a mostrar.

Cada capa los traduce a su manera; la API del panel los convierte en respuestas HTTP (`app.admin_api.errors`). Ninguno lleva
los valores recibidos, porque podrían ser datos de pago.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FieldIssue:
    """Un problema en un campo: su ruta y un mensaje para quien administra el negocio."""

    path: str
    message: str


class BusinessConfigError(ValueError):
    """La configuración del negocio no existe, no es JSON válido o no cumple el contrato."""


class BusinessNotFoundError(BusinessConfigError):
    """El negocio no existe."""


class BusinessAlreadyExistsError(BusinessConfigError):
    """Ya hay un negocio con ese identificador."""


class InvalidFieldsError(BusinessConfigError):
    """Hay campos concretos por corregir."""

    def __init__(self, message: str, issues: Iterable[FieldIssue]) -> None:
        super().__init__(message)
        self.issues = tuple(issues)


class InvalidDocumentError(BusinessConfigError):
    """El documento no cumple el contrato. `errors` son los de la validación, sin los valores recibidos."""

    def __init__(self, message: str, errors: Iterable[Mapping[str, Any]]) -> None:
        super().__init__(message)
        self.errors = tuple(errors)


class VersionConflictError(BusinessConfigError):
    """El negocio cambió desde que se leyó: guardar pisaría ese cambio."""


class PublicationError(BusinessConfigError):
    """No se pudo publicar, revertir o restaurar. Lo publicado no cambia."""


class VersionNotFoundError(PublicationError):
    """Esa versión no existe en este negocio."""


class SecretResolutionError(LookupError):
    """Un dato de pago no existe, no se puede descifrar o su referencia no es de este almacén."""


class SecretNotFoundError(SecretResolutionError):
    """Ese dato de pago no está guardado en este negocio."""


class PaymentDataUnavailableError(PublicationError, SecretResolutionError):
    """Una versión no se puede publicar porque falta uno de sus datos de pago o no se puede leer."""


class AIKeyMissingError(BusinessConfigError):
    """El negocio no tiene clave de IA: su asistente no puede responder."""


class AssistantUnavailableError(BusinessConfigError):
    """El área de pruebas no puede ejecutar el asistente en este servidor."""


class ConversationNotFoundError(BusinessConfigError):
    """La conversación no existe o es de un negocio al que este usuario no llega."""


class UsageLimitExceededError(BusinessConfigError):
    """Se superó un límite de uso; se puede volver a intentar en `retry_after_seconds`."""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("se alcanzó el límite de uso")
        self.retry_after_seconds = max(1, retry_after_seconds)
