"""Las claves de API de cada negocio en `api_keys` (migración 0012). Implementa `ApiKeyStorage`.

Solo se guarda la huella de cada clave (`key_hash`, SHA-256) y su comienzo visible. Reconocer una clave es buscar su huella: no
hay forma de obtener la clave desde la base. Cada operación del panel recibe el negocio y solo alcanza sus claves.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, insert, or_, select, update
from sqlalchemy.engine import Engine

from app.domain.business_config.api_keys import (
    MAX_ACTIVE_KEYS,
    ApiKey,
    ApiKeyIdentity,
    CreatedApiKey,
    fingerprint,
    looks_like_key,
    new_secret,
    visible_prefix,
)
from app.domain.business_config.errors import BusinessNotFoundError, FieldIssue, InvalidFieldsError
from app.infrastructure.business_config.tables import api_keys, tenants
from app.infrastructure.business_config.tenancy import tenant_of

# «Usada por última vez» se anota como mucho una vez por minuto por clave: una escritura por minuto, no una por mensaje.
LAST_USED_EVERY = timedelta(minutes=1)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _key(row: Any, slug: str) -> ApiKey:
    return ApiKey(
        id=str(row.id), business_slug=slug, name=row.name, prefix=row.prefix, scopes=tuple(row.scopes or ()),
        created_at=_utc(row.created_at), created_by=row.created_by, last_used_at=_utc(row.last_used_at), revoked_at=_utc(row.revoked_at),
    )


class ApiKeyStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create(self, tenant_slug: str, *, name: str, scopes: tuple[str, ...], created_by: str | None) -> CreatedApiKey:
        secret, now = new_secret(), _now()
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            active = conn.execute(
                select(func.count()).select_from(api_keys).where(api_keys.c.tenant_id == tenant.id, api_keys.c.revoked_at.is_(None))
            ).scalar_one()
            if active >= MAX_ACTIVE_KEYS:
                raise InvalidFieldsError(
                    "Este negocio ya tiene muchas claves.", [FieldIssue("name", f"Máximo {MAX_ACTIVE_KEYS} activas: revoca las que no uses.")]
                )
            key_id = uuid.uuid4()
            conn.execute(
                insert(api_keys).values(
                    id=key_id, tenant_id=tenant.id, name=name, prefix=visible_prefix(secret), key_hash=fingerprint(secret),
                    scopes=list(scopes), created_by=created_by, created_at=now,
                )
            )
        return CreatedApiKey(
            ApiKey(id=str(key_id), business_slug=tenant_slug, name=name, prefix=visible_prefix(secret), scopes=scopes, created_at=now, created_by=created_by),
            secret,
        )

    def list_keys(self, tenant_slug: str) -> list[ApiKey]:
        """Las claves del negocio: las activas primero, las más nuevas arriba."""
        with self._engine.connect() as conn:
            tenant = tenant_of(conn, tenant_slug)
            rows = conn.execute(
                select(api_keys).where(api_keys.c.tenant_id == tenant.id).order_by(api_keys.c.revoked_at.is_not(None), api_keys.c.created_at.desc())
            ).all()
        return [_key(row, tenant_slug) for row in rows]

    def revoke(self, tenant_slug: str, key_id: str) -> ApiKey:
        try:
            key = uuid.UUID(str(key_id))
        except ValueError as exc:
            raise BusinessNotFoundError("esa clave no existe") from exc
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            mine = (api_keys.c.id == key) & (api_keys.c.tenant_id == tenant.id)
            row = conn.execute(select(api_keys).where(mine)).first()
            if row is None:
                raise BusinessNotFoundError("esa clave no existe")
            if row.revoked_at is None:
                conn.execute(update(api_keys).where(mine).values(revoked_at=_now()))
                row = conn.execute(select(api_keys).where(mine)).one()
        return _key(row, tenant_slug)

    def authenticate(self, secret: str) -> ApiKeyIdentity | None:
        """El negocio y los permisos de una clave activa, o None si no existe o está revocada. Anota que se usó."""
        if not looks_like_key(secret):
            return None
        with self._engine.connect() as conn:
            row = conn.execute(
                select(api_keys.c.id, api_keys.c.name, api_keys.c.scopes, api_keys.c.last_used_at, tenants.c.slug)
                .join(tenants, tenants.c.id == api_keys.c.tenant_id)
                .where(api_keys.c.key_hash == fingerprint(secret), api_keys.c.revoked_at.is_(None))
            ).first()
        if row is None:
            return None
        now = _now()
        if row.last_used_at is None or now - _utc(row.last_used_at) >= LAST_USED_EVERY:
            with self._engine.begin() as conn:
                conn.execute(
                    update(api_keys)
                    .where(api_keys.c.id == row.id, or_(api_keys.c.last_used_at.is_(None), api_keys.c.last_used_at < now - LAST_USED_EVERY))
                    .values(last_used_at=now)
                )
        return ApiKeyIdentity(key_id=str(row.id), business_slug=row.slug, name=row.name, scopes=tuple(row.scopes or ()))
