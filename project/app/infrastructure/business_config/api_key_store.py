"""Las claves de API en `api_keys` y `api_key_businesses` (migraciones 0012 y 0013). Implementa `ApiKeyStorage`.

Solo se guarda la huella de cada clave (`key_hash`, SHA-256) y su comienzo visible. Reconocer una clave es buscar su huella: no
hay forma de obtener la clave desde la base.

Una clave es de un negocio (`reach = 'one'`) o de una cuenta: entra a todos los negocios de su dueño (`all`) o a algunos (`some`).
Desde un negocio se ven las claves que llegan a él: las suyas y las de la cuenta de quien pregunta que lo incluyen.
"""
from __future__ import annotations

import uuid
from collections.abc import Iterable
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, false, func, insert, or_, select, update
from sqlalchemy.engine import Connection, Engine

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
from app.domain.business_config.key_permissions import KeyReach, is_expired
from app.infrastructure.business_config.tables import api_key_businesses, api_keys, tenants
from app.infrastructure.business_config.tenancy import tenant_of

# «Usada por última vez» se anota como mucho una vez por minuto por clave: una escritura por minuto, no una por mensaje.
LAST_USED_EVERY = timedelta(minutes=1)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _reach(row: Any, slugs: frozenset[str]) -> KeyReach:
    kind = row.reach or "one"
    return KeyReach(kind, slugs if kind != "all" else frozenset())


def _key(row: Any, slugs: frozenset[str], business_slug: str | None) -> ApiKey:
    return ApiKey(
        id=str(row.id), business_slug=business_slug, name=row.name, prefix=row.prefix, scopes=tuple(row.scopes or ()),
        created_at=_utc(row.created_at), created_by=row.created_by, last_used_at=_utc(row.last_used_at), revoked_at=_utc(row.revoked_at),
        reach=_reach(row, slugs), expires_at=_utc(row.expires_at),
    )


class ApiKeyStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # ------------------------------------------------------------------ crear

    def create(
        self,
        *,
        name: str,
        scopes: tuple[str, ...],
        reach: KeyReach,
        created_by: str | None,
        owner_user_id: str | None,
        expires_at: datetime | None = None,
    ) -> CreatedApiKey:
        """Una clave nueva. `reach.businesses` son los identificadores de su negocio (uno) o de los elegidos (algunos)."""
        secret, now = new_secret(), _now()
        key_id = uuid.uuid4()
        with self._engine.begin() as conn:
            tenant_ids = {slug: tenant_of(conn, slug).id for slug in sorted(reach.businesses)}
            self._require_room(conn, owner_user_id, tenant_ids.values() if reach.kind == "one" else ())
            conn.execute(
                insert(api_keys).values(
                    id=key_id, tenant_id=next(iter(tenant_ids.values())) if reach.kind == "one" else None, name=name,
                    prefix=visible_prefix(secret), key_hash=fingerprint(secret), scopes=list(scopes), created_by=created_by,
                    created_at=now, owner_user_id=owner_user_id, reach=reach.kind, expires_at=expires_at,
                )
            )
            if reach.kind == "some":
                conn.execute(insert(api_key_businesses), [{"key_id": key_id, "tenant_id": tenant_id} for tenant_id in tenant_ids.values()])
        business = next(iter(reach.businesses)) if reach.kind == "one" else None
        key = ApiKey(
            id=str(key_id), business_slug=business, name=name, prefix=visible_prefix(secret), scopes=scopes, created_at=now,
            created_by=created_by, reach=reach, expires_at=expires_at,
        )
        return CreatedApiKey(key, secret)

    def _require_room(self, conn: Connection, owner_user_id: str | None, tenant_ids: Iterable[Any]) -> None:
        """Hasta `MAX_ACTIVE_KEYS` activas por negocio (las de un negocio) y por cuenta (las de la cuenta)."""
        owned = api_keys.c.owner_user_id == owner_user_id if owner_user_id is not None else api_keys.c.owner_user_id.is_(None)
        scope = or_(api_keys.c.tenant_id.in_(list(tenant_ids)), and_(api_keys.c.tenant_id.is_(None), owned))
        active = conn.execute(select(func.count()).select_from(api_keys).where(scope, api_keys.c.revoked_at.is_(None))).scalar_one()
        if active >= MAX_ACTIVE_KEYS:
            raise InvalidFieldsError("Ya tienes muchas claves.", [FieldIssue("name", f"Máximo {MAX_ACTIVE_KEYS} activas: revoca las que no uses.")])

    # ------------------------------------------------------------------ ver

    def _slugs_of(self, conn: Connection, key_ids: list[Any]) -> dict[str, frozenset[str]]:
        if not key_ids:
            return {}
        rows = conn.execute(
            select(api_key_businesses.c.key_id, tenants.c.slug)
            .join(tenants, tenants.c.id == api_key_businesses.c.tenant_id)
            .where(api_key_businesses.c.key_id.in_(key_ids))
        ).all()
        found: dict[str, set[str]] = {}
        for row in rows:
            found.setdefault(str(row.key_id), set()).add(row.slug)
        return {key: frozenset(slugs) for key, slugs in found.items()}

    def list_keys(self, tenant_slug: str, *, owner_user_id: str | None = None, local: bool = False) -> list[ApiKey]:
        """Las claves que llegan a este negocio: las suyas y las de la cuenta de quien pregunta que lo incluyen (todas las de la
        cuenta en este equipo, `local`). Las activas primero, las más nuevas arriba."""
        with self._engine.connect() as conn:
            tenant = tenant_of(conn, tenant_slug)
            owned = api_keys.c.owner_user_id.is_(None) if local else api_keys.c.owner_user_id == owner_user_id
            included = select(api_key_businesses.c.key_id).where(api_key_businesses.c.tenant_id == tenant.id)
            account = and_(api_keys.c.tenant_id.is_(None), owned, or_(api_keys.c.reach == "all", api_keys.c.id.in_(included)))
            rows = conn.execute(
                select(api_keys, tenants.c.slug.label("tenant_slug"))
                .select_from(api_keys.outerjoin(tenants, tenants.c.id == api_keys.c.tenant_id))
                .where(or_(api_keys.c.tenant_id == tenant.id, account if (local or owner_user_id) else false()))
                .order_by(api_keys.c.revoked_at.is_not(None), api_keys.c.created_at.desc())
            ).all()
            slugs = self._slugs_of(conn, [row.id for row in rows if row.reach == "some"])
        return [
            _key(row, slugs.get(str(row.id), frozenset({row.tenant_slug}) if row.tenant_slug else frozenset()), row.tenant_slug)
            for row in rows
        ]

    # ------------------------------------------------------------------ revocar

    def revoke(self, tenant_slug: str, key_id: str, *, owner_user_id: str | None = None, local: bool = False) -> ApiKey:
        """Revoca una clave que llega a este negocio. Una de la cuenta solo la revoca su dueño."""
        try:
            wanted = str(uuid.UUID(str(key_id)))
        except ValueError as exc:
            raise BusinessNotFoundError("esa clave no existe") from exc
        key = next((item for item in self.list_keys(tenant_slug, owner_user_id=owner_user_id, local=local) if item.id == wanted), None)
        if key is None:
            raise BusinessNotFoundError("esa clave no existe")
        if key.revoked_at is not None:
            return key
        now = _now()
        with self._engine.begin() as conn:
            conn.execute(update(api_keys).where(api_keys.c.id == uuid.UUID(wanted), api_keys.c.revoked_at.is_(None)).values(revoked_at=now))
        return replace(key, revoked_at=now)

    # ------------------------------------------------------------------ reconocer

    def authenticate(self, secret: str) -> ApiKeyIdentity | None:
        """Quién llama con una clave activa y sin vencer, o None. Anota que se usó (como mucho una vez por minuto)."""
        if not looks_like_key(secret):
            return None
        now = _now()
        with self._engine.connect() as conn:
            row = conn.execute(
                select(api_keys, tenants.c.slug.label("tenant_slug"))
                .select_from(api_keys.outerjoin(tenants, tenants.c.id == api_keys.c.tenant_id))
                .where(api_keys.c.key_hash == fingerprint(secret), api_keys.c.revoked_at.is_(None))
            ).first()
            if row is None or is_expired(_utc(row.expires_at), now):
                return None
            slugs = self._slugs_of(conn, [row.id]).get(str(row.id), frozenset()) if row.reach == "some" else frozenset()
        if row.last_used_at is None or now - _utc(row.last_used_at) >= LAST_USED_EVERY:
            with self._engine.begin() as conn:
                conn.execute(
                    update(api_keys)
                    .where(api_keys.c.id == row.id, or_(api_keys.c.last_used_at.is_(None), api_keys.c.last_used_at < now - LAST_USED_EVERY))
                    .values(last_used_at=now)
                )
        reach = KeyReach("one", frozenset({row.tenant_slug})) if (row.reach or "one") == "one" else _reach(row, slugs)
        return ApiKeyIdentity(
            key_id=str(row.id), business_slug=row.tenant_slug, name=row.name, scopes=tuple(row.scopes or ()), reach=reach,
            owner_user_id=row.owner_user_id, owner_label=row.created_by,
        )
