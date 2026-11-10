"""Configuración de cada negocio guardada por versiones en una base de datos (SQLite o PostgreSQL).

Ciclo de vida de una configuración:
- guardar: cada guardado crea una versión inmutable en borrador, validada contra el contrato y con el
  `tenant_slug` del negocio dueño; un documento inválido no se guarda. La versión y sus datos de pago se
  escriben en una sola transacción: o queda todo o no queda nada;
- publicar: archiva la versión publicada y publica la elegida en una sola transacción; antes ejecuta
  la comprobación que reciba (p. ej. compilarla con sus datos de pago) y no publica si falla;
- revertir: vuelve a publicar la versión publicada anterior (número de versión menor), también en una transacción;
- usar: el runtime solo lee la versión publicada y la valida de nuevo antes de usarla.

Los ajustes técnicos no se versionan con el documento comercial: hay uno vigente por negocio, y se
adjunta a la versión publicada al leerla.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, delete, func, insert, select, update
from sqlalchemy.engine import Connection, Engine, Row
from sqlalchemy.exc import IntegrityError

from app.business_config_application.ports import ANY_VERSION, ExpectedVersion, PublishCheck
from app.domain.business_config.access import OWNER
from app.domain.business_config.contract import BusinessConfig
from app.domain.business_config.engine_settings import EngineSettings
from app.domain.business_config.errors import (
    BusinessAlreadyExistsError,
    BusinessConfigError,
    PublicationError,
    VersionConflictError,
    VersionNotFoundError,
)
from app.domain.business_config.records import BusinessSummary, ConfigVersion, StoredConfig
from app.domain.business_config.validation import validate_document, validate_engine_settings
from app.infrastructure.business_config.payment_secret_store import PaymentSecretStore
from app.infrastructure.business_config.tables import business_configs, business_engine_settings, business_members, tenants
from app.infrastructure.business_config.tenancy import tenant_of

SAVE_ATTEMPTS = 50
_VERSION_STATE = (business_configs.c.version, business_configs.c.status, business_configs.c.published_at)


def content_hash(document: dict[str, Any]) -> str:
    canonical = json.dumps(document, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _utc(value: datetime | None) -> datetime | None:
    # SQLite devuelve las fechas sin zona; siempre se guardan en UTC.
    return value.replace(tzinfo=timezone.utc) if value is not None and value.tzinfo is None else value


def _version(row) -> ConfigVersion:
    return ConfigVersion(row.version, row.status, row.content_hash, _utc(row.published_at), _utc(row.created_at), row.created_by)


def _current_draft(rows) -> int | None:
    """El borrador en curso: el más reciente posterior a lo último que se publicó."""
    last_published = max((row.version for row in rows if row.published_at is not None), default=0)
    return max((row.version for row in rows if row.status == "draft" and row.version > last_published), default=None)


def _summary(tenant: Row, rows, latest_document: Any) -> BusinessSummary:
    """El nombre es el de la versión más reciente, o el del registro si no tiene ninguna."""
    # Una versión dañada no impide listar: se detecta al leerla, porque ahí sí se valida.
    identity = latest_document.get("identity") if isinstance(latest_document, dict) else None
    name = (identity.get("name") if isinstance(identity, dict) else None) or tenant.name
    latest = max((row.version for row in rows), default=None)
    published = next((row.version for row in rows if row.status == "published"), None)
    return BusinessSummary(tenant.slug, name, latest, _current_draft(rows), published)


class BusinessConfigRepository:
    def __init__(self, engine: Engine, secrets: PaymentSecretStore | None = None) -> None:
        self._engine = engine
        self._secrets = secrets or PaymentSecretStore(engine)

    @staticmethod
    def _row(conn: Connection, tenant_id, *conditions):
        return conn.execute(select(business_configs).where(business_configs.c.tenant_id == tenant_id, *conditions)).first()

    @staticmethod
    def _engine_settings(conn: Connection, tenant_id, tenant_slug: str) -> EngineSettings | None:
        document = conn.execute(
            select(business_engine_settings.c.document).where(business_engine_settings.c.tenant_id == tenant_id)
        ).scalar_one_or_none()
        return None if document is None else validate_engine_settings(tenant_slug, document)

    # ------------------------------------------------------------------ negocios

    def create_business(self, tenant_slug: str, name: str, *, owner_id: str | None = None) -> BusinessSummary:
        tenant_id = uuid.uuid4()
        try:
            with self._engine.begin() as conn:
                conn.execute(insert(tenants).values(id=tenant_id, name=name, slug=tenant_slug))
                if owner_id is not None:
                    conn.execute(insert(business_members).values(tenant_id=tenant_id, user_id=owner_id, role=OWNER))
        except IntegrityError as exc:
            raise BusinessAlreadyExistsError(f"{tenant_slug}: el negocio ya existe") from exc
        return BusinessSummary(tenant_slug, name, None, None, None)

    def business(self, tenant_slug: str) -> BusinessSummary:
        with self._engine.connect() as conn:
            tenant = tenant_of(conn, tenant_slug)
            rows = conn.execute(select(*_VERSION_STATE).where(business_configs.c.tenant_id == tenant.id)).all()
            latest = self._row(conn, tenant.id, business_configs.c.version == max(row.version for row in rows)) if rows else None
        return _summary(tenant, rows, latest.document if latest else None)

    def list_businesses(self) -> list[BusinessSummary]:
        """Negocios por identificador, con dos consultas de versiones sea cual sea su número."""
        newest = (
            select(business_configs.c.tenant_id, func.max(business_configs.c.version).label("version"))
            .group_by(business_configs.c.tenant_id)
            .subquery()
        )
        states = defaultdict(list)
        with self._engine.connect() as conn:
            registered = conn.execute(select(tenants).order_by(tenants.c.slug)).all()
            for row in conn.execute(select(business_configs.c.tenant_id, *_VERSION_STATE)).all():
                states[row.tenant_id].append(row)
            documents = dict(
                conn.execute(
                    select(business_configs.c.tenant_id, business_configs.c.document).join(
                        newest, and_(business_configs.c.tenant_id == newest.c.tenant_id, business_configs.c.version == newest.c.version)
                    )
                )
                .tuples()
                .all()
            )
        return [_summary(tenant, states[tenant.id], documents.get(tenant.id)) for tenant in registered]

    def delete_business(self, tenant_slug: str) -> None:
        """Borra el negocio; sus versiones, datos de pago y ajustes caen en cascada. Solo en la base local."""
        if self._engine.dialect.name != "sqlite":
            # En PostgreSQL `tenants` es la tabla del motor: borrar aquí arrastraría sus datos.
            raise BusinessConfigError(f"{tenant_slug}: eliminar negocios solo está disponible en la base local")
        with self._engine.begin() as conn:
            conn.execute(delete(tenants).where(tenants.c.id == tenant_of(conn, tenant_slug).id))

    # ------------------------------------------------------------------ guardar

    def save_draft(
        self,
        tenant_slug: str,
        document: dict[str, Any],
        *,
        created_by: str | None = None,
        expected_version: ExpectedVersion = ANY_VERSION,
        payment_secrets: dict[str, str] | None = None,
    ) -> ConfigVersion:
        payload = validate_document(tenant_slug, document).model_dump(mode="json", exclude_none=True)
        digest = content_hash(payload)
        for _attempt in range(SAVE_ATTEMPTS):
            try:
                with self._engine.begin() as conn:
                    tenant_id = tenant_of(conn, tenant_slug).id
                    current = conn.execute(select(func.max(business_configs.c.version)).where(business_configs.c.tenant_id == tenant_id)).scalar()
                    if expected_version is not ANY_VERSION and current != expected_version:
                        raise VersionConflictError(f"{tenant_slug}: el negocio cambió desde la versión {expected_version}")
                    version = (current or 0) + 1
                    conn.execute(
                        insert(business_configs).values(
                            tenant_id=tenant_id,
                            version=version,
                            schema_version=payload["schema_version"],
                            status="draft",
                            document=payload,
                            content_hash=digest,
                            created_by=created_by,
                        )
                    )
                    if payment_secrets:
                        self._secrets.write(conn, tenant_id, payment_secrets)
            except IntegrityError as exc:
                # Otro guardado simultáneo tomó ese número de versión: quien sabía qué versión editaba debe recargar; el resto reintenta.
                if expected_version is not ANY_VERSION:
                    raise VersionConflictError(f"{tenant_slug}: el negocio cambió desde la versión {expected_version}") from exc
                continue
            return ConfigVersion(version=version, status="draft", content_hash=digest, published_at=None)
        raise VersionConflictError(f"{tenant_slug}: no se pudo guardar por demasiados guardados simultáneos")

    def save_engine_settings(self, tenant_slug: str, document: dict[str, Any]) -> None:
        """Guarda los ajustes técnicos vigentes del negocio; no crean una versión del documento comercial."""
        payload = validate_engine_settings(tenant_slug, document).model_dump(mode="json", exclude_none=True)
        with self._engine.begin() as conn:
            tenant_id = tenant_of(conn, tenant_slug).id
            conn.execute(delete(business_engine_settings).where(business_engine_settings.c.tenant_id == tenant_id))
            conn.execute(insert(business_engine_settings).values(tenant_id=tenant_id, document=payload))

    # ------------------------------------------------------------------ publicar

    def _publish_row(self, conn: Connection, tenant_slug: str, tenant_id, row: Row, check: PublishCheck | None) -> None:
        if row.status == "published":
            return
        config = validate_document(tenant_slug, row.document)
        if check is not None:
            check(config.with_engine_settings(self._engine_settings(conn, tenant_id, tenant_slug)))
        conn.execute(
            update(business_configs)
            .where(business_configs.c.tenant_id == tenant_id, business_configs.c.status == "published")
            .values(status="archived")
        )
        conn.execute(
            update(business_configs)
            .where(business_configs.c.id == row.id)
            .values(status="published", published_at=datetime.now(timezone.utc))
        )

    def publish(self, tenant_slug: str, version: int, *, check: PublishCheck | None = None) -> None:
        with self._engine.begin() as conn:
            tenant_id = tenant_of(conn, tenant_slug).id
            row = self._row(conn, tenant_id, business_configs.c.version == version)
            if row is None:
                raise VersionNotFoundError(f"{tenant_slug}: no existe la versión {version}")
            self._publish_row(conn, tenant_slug, tenant_id, row, check)

    def rollback(self, tenant_slug: str, *, check: PublishCheck | None = None) -> int:
        """Vuelve a publicar la versión publicada anterior a la vigente y devuelve su número."""
        with self._engine.begin() as conn:
            tenant_id = tenant_of(conn, tenant_slug).id
            current = self._row(conn, tenant_id, business_configs.c.status == "published")
            if current is None:
                raise PublicationError(f"{tenant_slug}: no hay una versión publicada que revertir")
            previous = conn.execute(
                select(business_configs)
                .where(
                    business_configs.c.tenant_id == tenant_id,
                    business_configs.c.status == "archived",
                    business_configs.c.published_at.is_not(None),
                    business_configs.c.version < current.version,
                )
                .order_by(business_configs.c.version.desc())
                .limit(1)
            ).first()
            if previous is None:
                raise PublicationError(f"{tenant_slug}: no hay una versión publicada anterior")
            self._publish_row(conn, tenant_slug, tenant_id, previous, check)
        return previous.version

    # ------------------------------------------------------------------ consultar

    def published(self, tenant_slug: str) -> BusinessConfig:
        with self._engine.connect() as conn:
            tenant_id = tenant_of(conn, tenant_slug).id
            row = self._row(conn, tenant_id, business_configs.c.status == "published")
            if row is None:
                raise BusinessConfigError(f"{tenant_slug}: no hay una versión publicada")
            # Lo almacenado se valida siempre antes de usarse: la base de datos no es una fuente confiable.
            return validate_document(tenant_slug, row.document).with_engine_settings(self._engine_settings(conn, tenant_id, tenant_slug))

    def version(self, tenant_slug: str, version: int) -> StoredConfig:
        with self._engine.connect() as conn:
            tenant_id = tenant_of(conn, tenant_slug).id
            row = self._row(conn, tenant_id, business_configs.c.version == version)
            if row is None:
                raise VersionNotFoundError(f"{tenant_slug}: no existe la versión {version}")
            config = validate_document(tenant_slug, row.document).with_engine_settings(self._engine_settings(conn, tenant_id, tenant_slug))
        return StoredConfig(_version(row), config)

    def latest_draft(self, tenant_slug: str) -> StoredConfig | None:
        with self._engine.connect() as conn:
            tenant_id = tenant_of(conn, tenant_slug).id
            rows = conn.execute(select(*_VERSION_STATE).where(business_configs.c.tenant_id == tenant_id)).all()
        draft = _current_draft(rows)
        return None if draft is None else self.version(tenant_slug, draft)

    def history(self, tenant_slug: str) -> list[ConfigVersion]:
        with self._engine.connect() as conn:
            tenant_id = tenant_of(conn, tenant_slug).id
            rows = conn.execute(
                select(business_configs).where(business_configs.c.tenant_id == tenant_id).order_by(business_configs.c.version)
            ).all()
        return [_version(row) for row in rows]
