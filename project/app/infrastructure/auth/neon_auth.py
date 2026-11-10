"""Comprueba los tokens de sesión de Neon Auth (implementa `AccessTokenVerifier`).

El panel envía en cada petición el token de la sesión (`Authorization: Bearer`). Es un JWT firmado por Neon Auth con EdDSA:
se comprueba con sus claves públicas (`<NEON_AUTH_URL>/.well-known/jwks.json`), su emisor y su audiencia (el origen de
`NEON_AUTH_URL`) y su vencimiento. Solo se acepta EdDSA, así un token firmado con otro algoritmo nunca pasa. El usuario es `sub`.
"""
from __future__ import annotations

import logging
from urllib.parse import urlsplit

import jwt
from jwt import PyJWKClient

from app.domain.business_config.access import Principal

logger = logging.getLogger("neon-auth")

ALGORITHMS = ["EdDSA"]
# Un token de Neon Auth ocupa cerca de mil caracteres: uno mucho más largo no se intenta decodificar.
MAX_TOKEN_CHARS = 8192
JWKS_CACHE_SECONDS = 60 * 60


def auth_origin(auth_url: str) -> str:
    """El origen de la dirección de Neon Auth, que es el emisor y la audiencia de sus tokens."""
    parts = urlsplit(str(auth_url or "").strip())
    if parts.scheme != "https" or not parts.netloc:
        raise ValueError("NEON_AUTH_URL debe ser la dirección https de Neon Auth (Neon → la rama → Auth)")
    return f"{parts.scheme}://{parts.netloc}"


class NeonAuthVerifier:
    def __init__(self, auth_url: str, *, jwks_client: PyJWKClient | None = None, leeway_seconds: int = 30) -> None:
        self._origin = auth_origin(auth_url)
        jwks_url = f"{str(auth_url).strip().rstrip('/')}/.well-known/jwks.json"
        self._jwks = jwks_client or PyJWKClient(jwks_url, cache_keys=True, lifespan=JWKS_CACHE_SECONDS, timeout=5)
        self._leeway = leeway_seconds

    def verify(self, token: str) -> Principal | None:
        if not token or len(token) > MAX_TOKEN_CHARS:
            return None
        try:
            key = self._jwks.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                key,
                algorithms=ALGORITHMS,
                issuer=self._origin,
                audience=self._origin,
                leeway=self._leeway,
                options={"require": ["exp", "iat", "sub"]},
            )
        except jwt.PyJWTError as exc:
            # Solo el motivo: el token es una credencial y no se registra.
            logger.info("token_rechazado", extra={"reason": type(exc).__name__})
            return None
        user_id = claims.get("sub")
        if not isinstance(user_id, str) or not user_id.strip():
            return None
        email = claims.get("email")
        return Principal(user_id=user_id, email=email if isinstance(email, str) and email else None)
