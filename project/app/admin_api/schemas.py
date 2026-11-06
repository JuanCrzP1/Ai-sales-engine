"""Peticiones y respuestas de la API. El documento comercial se valida con el contrato, no aquí."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.admin_api.errors import PAYMENT_PROBLEM
from app.business_config_application.service import ConfigReview, EditableConfig
from app.domain.business_config.records import BusinessSummary, ConfigVersion


class _Request(BaseModel):
    # Los errores de validación no repiten el valor recibido: podría ser un dato de pago.
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class CreateBusiness(_Request):
    slug: str
    name: str


class SaveConfig(_Request):
    document: dict[str, Any]
    # Valores nuevos de datos de pago, por su referencia en el documento. Nunca se devuelven.
    payment_values: dict[str, str] = Field(default_factory=dict)
    # La versión más reciente que conocía quien edita: detecta cambios hechos en otra pestaña.
    base_version: int | None = None


class ValidateConfig(_Request):
    document: dict[str, Any]


class PublishVersion(_Request):
    version: int


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def summary_payload(summary: BusinessSummary) -> dict[str, Any]:
    return asdict(summary)


def version_payload(version: ConfigVersion) -> dict[str, Any]:
    return {
        "version": version.version,
        "status": version.status,
        "published_at": _iso(version.published_at),
        "created_at": _iso(version.created_at),
        "created_by": version.created_by,
    }


def config_payload(editable: EditableConfig) -> dict[str, Any]:
    """El documento lleva referencias `secret_store:`; de cada dato de pago solo sale su estado y una versión enmascarada."""
    stored = editable.stored
    return {
        **summary_payload(editable.summary),
        "document": stored.config.model_dump(mode="json", exclude_none=True) if stored else None,
        "version": version_payload(stored.version) if stored else None,
        "payment_fields": {ref: asdict(state) for ref, state in editable.payment_fields.items()},
    }


def review_payload(review: ConfigReview) -> dict[str, Any]:
    if review.version is None:
        compile_error = "Todavía no hay una versión guardada."
    else:
        compile_error = PAYMENT_PROBLEM if review.payment_data_missing else review.compile_problem
    return {
        "version": review.version,
        "diagnostics": [asdict(item) for item in review.diagnostics],
        "compiles": review.compiles,
        "compile_error": compile_error,
    }
