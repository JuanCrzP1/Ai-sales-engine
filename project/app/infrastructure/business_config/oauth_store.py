"""El OAuth del servidor MCP en `mcp_oauth_clients`, `mcp_oauth_codes` y `mcp_oauth_tokens` (migración 0014). Implementa
`OAuthStorage`.

Solo huellas (SHA-256) de códigos y tokens. Tomar un código o un token de renovación lo borra en la misma operación: si dos
peticiones llegan a la vez con el mismo, solo una lo consigue (la que borra la fila).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from app.domain.business_config.oauth import AuthorizationCode, OAuthClient, TokenGrant
from app.infrastructure.business_config.tables import api_keys, mcp_oauth_clients, mcp_oauth_codes, mcp_oauth_tokens


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _grant(row: Any) -> TokenGrant:
    return TokenGrant(
        key_id=str(row.key_id), client_id=row.client_id, access_hash=row.access_hash, access_expires_at=_utc(row.access_expires_at),
        refresh_hash=row.refresh_hash, refresh_expires_at=_utc(row.refresh_expires_at),
    )


class OAuthStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # ------------------------------------------------------------------ agentes

    def create_client(self, client: OAuthClient) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                insert(mcp_oauth_clients).values(
                    client_id=client.client_id, name=client.name, redirect_uris=list(client.redirect_uris), created_at=client.created_at,
                )
            )

    def find_client(self, client_id: str) -> OAuthClient | None:
        with self._engine.connect() as conn:
            row = conn.execute(select(mcp_oauth_clients).where(mcp_oauth_clients.c.client_id == client_id)).first()
        if row is None:
            return None
        return OAuthClient(row.client_id, row.name, tuple(row.redirect_uris or ()), _utc(row.created_at))

    # ------------------------------------------------------------------ códigos

    def save_code(self, code: AuthorizationCode) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                insert(mcp_oauth_codes).values(
                    code_hash=code.code_hash, client_id=code.client_id, key_id=uuid.UUID(code.key_id), redirect_uri=code.redirect_uri,
                    code_challenge=code.code_challenge, resource=code.resource, expires_at=code.expires_at,
                )
            )

    def take_code(self, code_hash: str) -> AuthorizationCode | None:
        with self._engine.begin() as conn:
            row = conn.execute(select(mcp_oauth_codes).where(mcp_oauth_codes.c.code_hash == code_hash)).first()
            if row is None or conn.execute(delete(mcp_oauth_codes).where(mcp_oauth_codes.c.code_hash == code_hash)).rowcount != 1:
                return None
        return AuthorizationCode(
            code_hash=row.code_hash, client_id=row.client_id, key_id=str(row.key_id), redirect_uri=row.redirect_uri,
            code_challenge=row.code_challenge, resource=row.resource, expires_at=_utc(row.expires_at),
        )

    # ------------------------------------------------------------------ tokens

    def save_grant(self, grant: TokenGrant, *, now: datetime) -> None:
        with self._engine.begin() as conn:
            conn.execute(delete(mcp_oauth_tokens).where(mcp_oauth_tokens.c.refresh_expires_at < now))
            conn.execute(delete(mcp_oauth_codes).where(mcp_oauth_codes.c.expires_at < now))
            conn.execute(
                insert(mcp_oauth_tokens).values(
                    id=uuid.uuid4(), key_id=uuid.UUID(grant.key_id), client_id=grant.client_id, access_hash=grant.access_hash,
                    access_expires_at=grant.access_expires_at, refresh_hash=grant.refresh_hash, refresh_expires_at=grant.refresh_expires_at,
                    created_at=now,
                )
            )

    def take_refresh(self, refresh_hash: str) -> TokenGrant | None:
        with self._engine.begin() as conn:
            row = conn.execute(select(mcp_oauth_tokens).where(mcp_oauth_tokens.c.refresh_hash == refresh_hash)).first()
            if row is None or conn.execute(delete(mcp_oauth_tokens).where(mcp_oauth_tokens.c.id == row.id)).rowcount != 1:
                return None
        return _grant(row)

    def key_for_access(self, access_hash: str, now: datetime) -> str | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                select(mcp_oauth_tokens.c.key_id, mcp_oauth_tokens.c.access_expires_at)
                .join(api_keys, api_keys.c.id == mcp_oauth_tokens.c.key_id)
                .where(mcp_oauth_tokens.c.access_hash == access_hash, api_keys.c.revoked_at.is_(None))
            ).first()
        if row is None or _utc(row.access_expires_at) <= now:
            return None
        return str(row.key_id)
