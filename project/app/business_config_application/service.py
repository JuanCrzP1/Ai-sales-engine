"""Casos de uso de BusinessConfig: crear, guardar, publicar, revertir, consultar y compilar la configuración de cada negocio.

Solo conoce el dominio y sus puertos (`ports.py`): ni base de datos, ni HTTP, ni YAML, ni motor.

Datos de pago: el documento guarda solo referencias `secret_store:` y el valor se cifra aparte, en la misma operación que
guarda la versión. Cada valor nuevo recibe una referencia propia, de modo que un borrador nunca altera lo publicado y cada
versión conserva los datos con los que se guardó: al revertir o recuperar una versión vuelven también sus datos de pago. Un
documento que dependa de otro origen (como `legacy_yaml:`) o que contenga el valor de un dato de pago del negocio no se guarda.
Quien administra solo recibe el estado de cada dato y una versión enmascarada para reconocerlo, nunca el valor completo.
"""
from __future__ import annotations

import copy
import json
import uuid
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from app.business_config_application.ports import ANY_VERSION, BusinessConfigStorage, ExpectedVersion, PaymentSecretStorage
from app.domain.business_config.compiler import compile_business_config
from app.domain.business_config.contract import BusinessConfig, SecretRef
from app.domain.business_config.diagnostics import Diagnostic, review as diagnose
from app.domain.business_config.errors import (
    BusinessConfigError,
    BusinessNotFoundError,
    FieldIssue,
    InvalidFieldsError,
    PaymentDataUnavailableError,
    PublicationError,
    SecretNotFoundError,
    SecretResolutionError,
    VersionConflictError,
)
from app.domain.business_config.payment_data import (
    MIN_REDACTABLE_CHARS,
    SECRET_STORE_SOURCE,
    iter_payment_fields,
    iter_secret_refs,
    mask_payment_value,
    payment_value_problem,
    redact_values,
)
from app.domain.business_config.records import BusinessSummary, ConfigVersion, PaymentFieldState, StoredConfig
from app.domain.business_config.validation import check_business_identity, validate_document

_VERSION_SEPARATOR = "~"


@dataclass(frozen=True)
class EditableConfig:
    """Un negocio y lo que se edita de él: el borrador en curso; si no hay, lo publicado; si tampoco, la versión más reciente."""

    summary: BusinessSummary
    stored: StoredConfig | None
    # Estado de cada dato de pago del documento, por su referencia.
    payment_fields: dict[str, PaymentFieldState] = field(default_factory=dict)


@dataclass(frozen=True)
class ConfigReview:
    """Diagnóstico de lo que se edita y si se puede compilar. Nunca incluye lo compilado: lleva datos de pago."""

    version: int | None
    diagnostics: list[Diagnostic] = field(default_factory=list)
    payment_data_missing: bool = False
    compile_problem: str | None = None

    @property
    def compiles(self) -> bool:
        return self.version is not None and not self.payment_data_missing and self.compile_problem is None


def _base_ref(ref: str) -> str:
    """La referencia sin el sufijo de su versión."""
    return ref.split(_VERSION_SEPARATOR, 1)[0]


def _reject_payment_values(tenant_slug: str, document: dict[str, Any], values: Iterable[str]) -> None:
    visible = copy.deepcopy(document)
    for holder in iter_secret_refs(visible):
        holder["secret_ref"] = _base_ref(holder["secret_ref"])  # el sufijo aleatorio podría coincidir con un valor corto
    text = json.dumps(visible, ensure_ascii=False)
    if any(len(value) >= MIN_REDACTABLE_CHARS and value in text for value in values):
        raise BusinessConfigError(f"{tenant_slug}: el documento contiene el valor de un dato de pago")


def _reject_malformed_payment_values(tenant_slug: str, document: dict[str, Any], values: dict[str, str]) -> None:
    issues = [
        FieldIssue(item.path, problem)
        for item in iter_payment_fields(document)
        if item.ref in values and (problem := payment_value_problem(item.kind, str(values[item.ref])))
    ]
    if issues:
        raise InvalidFieldsError(f"{tenant_slug}: hay datos de pago con un formato no válido", issues)


@contextmanager
def _publication() -> Iterator[None]:
    """Lo que impide publicar, revertir o restaurar se informa como tal; lo publicado no cambia."""
    try:
        yield
    except (BusinessNotFoundError, PublicationError, VersionConflictError):
        raise
    except SecretResolutionError as exc:
        raise PaymentDataUnavailableError(str(exc)) from exc
    except ValueError as exc:  # no compila o lo guardado ya no cumple el contrato
        raise PublicationError(str(exc)) from exc


class BusinessConfigService:
    def __init__(self, storage: BusinessConfigStorage, secrets: PaymentSecretStorage) -> None:
        self._storage = storage
        self._secrets = secrets

    # ------------------------------------------------------------------ negocios

    def create_business(
        self,
        tenant_slug: str,
        name: str,
        *,
        document: dict[str, Any] | None = None,
        payment_values: dict[str, str] | None = None,
        owner_id: str | None = None,
        created_by: str | None = None,
    ) -> BusinessSummary:
        """Registra un negocio (con su dueño, si se indica) y, si se indica, guarda su primera versión en borrador a nombre de
        `created_by` (quien lo creó: una persona en el panel o un agente de IA)."""
        check_business_identity(tenant_slug, name)
        if document is not None:
            # Antes de registrar nada: un documento rechazado no deja un negocio a medias.
            self._checked_document(tenant_slug, document, payment_values or {}, known_values=())
            if payment_values:
                self._secrets.verify_key()
        self._storage.create_business(tenant_slug, name.strip(), owner_id=owner_id)
        if document is not None:
            self.save_changes(tenant_slug, document, payment_values=payment_values, created_by=created_by)
        return self._storage.business(tenant_slug)

    def get_business(self, tenant_slug: str) -> BusinessSummary:
        return self._storage.business(tenant_slug)

    def list_businesses(self) -> list[BusinessSummary]:
        return self._storage.list_businesses()

    def delete_business(self, tenant_slug: str) -> None:
        """Borra el negocio con sus versiones y datos de pago. No se puede deshacer."""
        self._storage.delete_business(tenant_slug)

    # ------------------------------------------------------------------ consultar

    def get_published(self, tenant_slug: str) -> BusinessConfig:
        return self._storage.published(tenant_slug)

    def get_draft(self, tenant_slug: str) -> StoredConfig | None:
        """El borrador en curso: el más reciente posterior a lo último que se publicó; si no hay, None."""
        return self._storage.latest_draft(tenant_slug)

    def get_version(self, tenant_slug: str, version: int) -> StoredConfig:
        return self._storage.version(tenant_slug, version)

    def _editable_version(self, tenant_slug: str) -> tuple[BusinessSummary, StoredConfig | None]:
        summary = self._storage.business(tenant_slug)
        version = summary.draft_version or summary.published_version or summary.latest_version
        return summary, self._storage.version(tenant_slug, version) if version is not None else None

    def get_editable(self, tenant_slug: str) -> EditableConfig:
        summary, stored = self._editable_version(tenant_slug)
        return EditableConfig(summary, stored, self._payment_field_states(tenant_slug, stored.config) if stored else {})

    def _payment_field_states(self, tenant_slug: str, config: BusinessConfig) -> dict[str, PaymentFieldState]:
        """Con los datos de este negocio: una referencia ajena se informa como inexistente. Sin la clave correcta, como ilegible."""
        resolve = self._secrets.resolver(tenant_slug)
        states: dict[str, PaymentFieldState] = {}
        for item in iter_payment_fields(config.model_dump(mode="json", exclude_none=True)):
            try:
                states[item.ref] = PaymentFieldState("configured", mask_payment_value(item.kind, resolve(SecretRef(secret_ref=item.ref))))
            except SecretNotFoundError:
                states[item.ref] = PaymentFieldState("missing")
            except SecretResolutionError:
                states[item.ref] = PaymentFieldState("unreadable")
        return states

    def history(self, tenant_slug: str) -> list[ConfigVersion]:
        return self._storage.history(tenant_slug)

    def compile_sections(self, tenant_slug: str, version: int | None = None) -> dict[str, dict]:
        """Lo publicado (o una versión concreta) en la forma que consume el motor.

        El resultado contiene los datos de pago descifrados: no debe guardarse ni registrarse.
        """
        config = self.get_published(tenant_slug) if version is None else self.get_version(tenant_slug, version).config
        return compile_business_config(config, self._secrets.resolver(tenant_slug))

    def payment_redactor(self, tenant_slug: str) -> Callable[[str], str]:
        """Oculta en un texto los datos de pago que el negocio tiene guardados (también los de versiones anteriores), para lo que
        se muestra fuera del panel (los mensajes que lee un agente). Si no se pueden descifrar, falla: nunca muestra sin ocultar."""
        values = self._secrets.known_values(tenant_slug)
        return lambda text: redact_values(text, values)

    # ------------------------------------------------------------------ validar

    def validate(self, tenant_slug: str, document: dict[str, Any]) -> list[Diagnostic]:
        """Valida un documento de este negocio sin guardarlo y devuelve sus avisos."""
        self._storage.business(tenant_slug)
        return diagnose(validate_document(tenant_slug, document))

    def review(self, tenant_slug: str) -> ConfigReview:
        _summary, stored = self._editable_version(tenant_slug)
        if stored is None:
            return ConfigReview(version=None)
        payment_data_missing, compile_problem = False, None
        try:
            compile_business_config(stored.config, self._secrets.resolver(tenant_slug))
        except SecretResolutionError:
            payment_data_missing = True
        except ValueError as exc:
            compile_problem = str(exc)
        return ConfigReview(stored.version.version, diagnose(stored.config), payment_data_missing, compile_problem)

    # ------------------------------------------------------------------ guardar

    def save_changes(
        self,
        tenant_slug: str,
        document: dict[str, Any],
        *,
        payment_values: dict[str, str] | None = None,
        created_by: str | None = None,
        expected_version: ExpectedVersion = ANY_VERSION,
    ) -> ConfigVersion:
        """Guarda una versión nueva en borrador, con sus datos de pago en la misma operación.

        `payment_values` son los valores que cambian, por su referencia. `expected_version` es la versión más reciente que
        conocía quien edita: si ya hay otra, no se guarda.
        """
        # Antes de validar, para no pedir que se corrijan campos de algo ya superado. La última palabra la tiene el guardado.
        if expected_version is not ANY_VERSION and self._storage.business(tenant_slug).latest_version != expected_version:
            raise VersionConflictError(f"{tenant_slug}: el negocio cambió desde la versión {expected_version}")
        known_values = self._secrets.known_values(tenant_slug)
        stored_document, secrets = self._checked_document(tenant_slug, document, payment_values or {}, known_values=known_values)
        return self._storage.save_draft(tenant_slug, stored_document, created_by=created_by, expected_version=expected_version, payment_secrets=secrets)

    def restore_version(self, tenant_slug: str, version: int, *, created_by: str | None = None) -> ConfigVersion:
        """Crea un borrador nuevo con el contenido de una versión anterior; no publica nada."""
        with _publication():
            document = self._storage.version(tenant_slug, version).config.model_dump(mode="json", exclude_none=True)
            return self._storage.save_draft(tenant_slug, document, created_by=created_by)

    def save_engine_settings(self, tenant_slug: str, document: dict[str, Any]) -> None:
        _reject_payment_values(tenant_slug, document, self._secrets.known_values(tenant_slug))
        self._storage.save_engine_settings(tenant_slug, document)

    # ------------------------------------------------------------------ publicar

    def publish(self, tenant_slug: str, version: int) -> None:
        """Publica una versión; si no compila o le faltan datos de pago, lo publicado no cambia."""
        with _publication():
            self._storage.publish(tenant_slug, version, check=self._publish_check(tenant_slug))

    def rollback(self, tenant_slug: str) -> int:
        with _publication():
            return self._storage.rollback(tenant_slug, check=self._publish_check(tenant_slug))

    def _publish_check(self, tenant_slug: str):
        resolver = self._secrets.resolver(tenant_slug)

        def _check(config: BusinessConfig) -> None:
            compile_business_config(config, resolver)

        return _check

    # ------------------------------------------------------------------ datos de pago

    def verify_payment_key(self) -> None:
        """Falla si la clave de cifrado falta o no es válida, sin escribir nada."""
        self._secrets.verify_key()

    @staticmethod
    def _checked_document(
        tenant_slug: str, document: dict[str, Any], values: dict[str, str], *, known_values: Iterable[str]
    ) -> tuple[dict[str, Any], dict[str, str]]:
        """El documento listo para guardar (referencias nuevas para los valores que cambian) y esos valores por referencia."""
        validate_document(tenant_slug, document)
        stored = copy.deepcopy(document)
        holders = list(iter_secret_refs(stored))
        unknown = set(values) - {holder["secret_ref"] for holder in holders}
        if unknown:
            raise BusinessConfigError(f"{tenant_slug}: {len(unknown)} datos de pago sin referencia en el documento")
        plain_values = [str(value) for value in values.values()]
        if any(not value.strip() for value in plain_values):
            raise BusinessConfigError(f"{tenant_slug}: hay datos de pago vacíos")
        _reject_malformed_payment_values(tenant_slug, document, values)

        fresh = {ref: f"{_base_ref(ref)}{_VERSION_SEPARATOR}{uuid.uuid4().hex}" for ref in values}
        for holder in holders:
            holder["secret_ref"] = fresh.get(holder["secret_ref"], holder["secret_ref"])

        foreign = sum(1 for holder in holders if not holder["secret_ref"].startswith(f"{SECRET_STORE_SOURCE}:"))
        if foreign:
            raise BusinessConfigError(f"{tenant_slug}: {foreign} datos de pago no están en el almacén cifrado")
        _reject_payment_values(tenant_slug, stored, [*plain_values, *known_values])
        return stored, {fresh[ref]: str(value) for ref, value in values.items()}
