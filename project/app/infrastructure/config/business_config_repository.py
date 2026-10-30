"""Configuración de cada negocio guardada por versiones en la base de datos (Neon/PostgreSQL).

Ciclo de vida de una configuración:
- guardar: cada guardado crea una versión inmutable en borrador, validada contra el contrato y con el
  `tenant_slug` del negocio dueño; un documento inválido no se guarda;
- publicar: archiva la versión publicada y publica la elegida en una sola transacción; antes ejecuta
  la comprobación que reciba (p. ej. compilarla con sus datos de pago) y no publica si falla;
- revertir: vuelve a publicar la versión publicada anterior (número de versión menor);
- usar: el runtime solo lee la versión publicada y la valida de nuevo antes de usarla.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError
from sqlalchemy import func, insert, select, update
from sqlalchemy.engine import Connection, Engine

from app.domain.business_config.contract import BusinessConfig
from app.infrastructure.config.business_config_store import BusinessConfigError
from app.infrastructure.config.business_config_tables import business_configs, tenants

PublishCheck = Callable[[BusinessConfig], None]


@dataclass(frozen=True)
class ConfigVersion:
    version: int
    status: str
    content_hash: str
    published_at: datetime | None


def content_hash(document: dict[str, Any]) -> str:
    canonical = json.dumps(document, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_document(tenant_slug: str, document: Any) -> BusinessConfig:
    try:
        config = BusinessConfig.model_validate(document)
    except ValidationError as exc:
        raise BusinessConfigError(f"{tenant_slug}: la configuración no cumple el contrato ({exc.error_count()} errores)") from exc
    if config.tenant_slug != tenant_slug:
        raise BusinessConfigError(f"{tenant_slug}: el documento declara el tenant '{config.tenant_slug}'")
    return config


class BusinessConfigRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @staticmethod
    def _tenant_id(conn: Connection, tenant_slug: str):
        tenant_id = conn.execute(select(tenants.c.id).where(tenants.c.slug == tenant_slug)).scalar_one_or_none()
        if tenant_id is None:
            raise BusinessConfigError(f"{tenant_slug}: el negocio no existe en la base de datos")
        return tenant_id

    @staticmethod
    def _row(conn: Connection, tenant_id, *conditions):
        return conn.execute(select(business_configs).where(business_configs.c.tenant_id == tenant_id, *conditions)).first()

    def save_draft(self, tenant_slug: str, document: dict[str, Any], *, created_by: str | None = None) -> ConfigVersion:
        payload = validate_document(tenant_slug, document).model_dump(mode="json", exclude_none=True)
        digest = content_hash(payload)
        with self._engine.begin() as conn:
            tenant_id = self._tenant_id(conn, tenant_slug)
            current = conn.execute(select(func.max(business_configs.c.version)).where(business_configs.c.tenant_id == tenant_id)).scalar()
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
        return ConfigVersion(version=version, status="draft", content_hash=digest, published_at=None)

    def publish(self, tenant_slug: str, version: int, *, check: PublishCheck | None = None) -> None:
        with self._engine.begin() as conn:
            tenant_id = self._tenant_id(conn, tenant_slug)
            row = self._row(conn, tenant_id, business_configs.c.version == version)
            if row is None:
                raise BusinessConfigError(f"{tenant_slug}: no existe la versión {version}")
            if row.status == "published":
                return
            config = validate_document(tenant_slug, row.document)
            if check is not None:
                check(config)
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

    def rollback(self, tenant_slug: str, *, check: PublishCheck | None = None) -> int:
        """Vuelve a publicar la versión publicada anterior a la vigente y devuelve su número."""
        with self._engine.connect() as conn:
            tenant_id = self._tenant_id(conn, tenant_slug)
            current = self._row(conn, tenant_id, business_configs.c.status == "published")
            if current is None:
                raise BusinessConfigError(f"{tenant_slug}: no hay una versión publicada que revertir")
            previous = conn.execute(
                select(func.max(business_configs.c.version)).where(
                    business_configs.c.tenant_id == tenant_id,
                    business_configs.c.status == "archived",
                    business_configs.c.published_at.is_not(None),
                    business_configs.c.version < current.version,
                )
            ).scalar()
        if previous is None:
            raise BusinessConfigError(f"{tenant_slug}: no hay una versión publicada anterior")
        self.publish(tenant_slug, previous, check=check)
        return previous

    def published(self, tenant_slug: str) -> BusinessConfig:
        with self._engine.connect() as conn:
            tenant_id = self._tenant_id(conn, tenant_slug)
            row = self._row(conn, tenant_id, business_configs.c.status == "published")
        if row is None:
            raise BusinessConfigError(f"{tenant_slug}: no hay una versión publicada")
        # Lo almacenado se valida siempre antes de usarse: la base de datos no es una fuente confiable.
        return validate_document(tenant_slug, row.document)

    def history(self, tenant_slug: str) -> list[ConfigVersion]:
        with self._engine.connect() as conn:
            tenant_id = self._tenant_id(conn, tenant_slug)
            rows = conn.execute(
                select(business_configs).where(business_configs.c.tenant_id == tenant_id).order_by(business_configs.c.version)
            ).all()
        return [ConfigVersion(row.version, row.status, row.content_hash, row.published_at) for row in rows]
