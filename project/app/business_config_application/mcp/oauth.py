"""OAuth 2.1 del servidor MCP: lo que hace que Claude (web y app) y ChatGPT se conecten pegando solo la dirección.

    register      el agente se registra solo (RFC 7591), sin sesión
    describe      qué agente pide acceso (para la pantalla de autorización del panel, con la sesión de la persona)
    decide        la persona autoriza (una conexión con los permisos y negocios que eligió, y un código) o rechaza
    exchange      el agente cambia el código por tokens (con PKCE), o renueva (el token de renovación cambia en cada uso)
    authenticate  quién llama al servidor MCP con un token de acceso

La conexión es una clave de la cuenta (`ApiKeyStorage.connect`): mismas áreas, mismo alcance, mismas reglas
(`key_permissions.py`), y la misma lista en «Claves de API» para verla y revocarla. Las reglas de OAuth son puras (`oauth.py`).
"""
from __future__ import annotations

import logging
import secrets
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

from app.business_config_application.access import BusinessAccess
from app.business_config_application.ports import ApiKeyStorage, OAuthStorage
from app.domain.business_config.access import Principal
from app.domain.business_config.api_keys import ApiKeyIdentity, validated_key_name
from app.domain.business_config.errors import FieldIssue, InvalidFieldsError
from app.domain.business_config.key_permissions import SCOPE_ASSISTANT_CHAT, validated_permissions, validated_reach
from app.domain.business_config.oauth import (
    ACCESS_TOKEN_PREFIX,
    ACCESS_TTL,
    CODE_TTL,
    REFRESH_TOKEN_PREFIX,
    REFRESH_TTL,
    AuthorizationCode,
    AuthorizationRequest,
    OAuthAddresses,
    OAuthClient,
    OAuthError,
    TokenGrant,
    authorization_params,
    is_access_token,
    pkce_matches,
    read_authorization_request,
    read_client_registration,
    redirect_with,
    same_resource,
    token_fingerprint,
)

logger = logging.getLogger("mcp_oauth")


@dataclass(frozen=True)
class AuthorizationPrompt:
    """Lo que muestra la pantalla de autorización: qué agente pide acceso y a dónde volverá; o por qué no se puede, y si se le
    puede avisar al agente (`redirect_to`)."""

    ready: bool
    client_name: str | None = None
    redirect_host: str | None = None
    message: str | None = None
    redirect_to: str | None = None


def _text(form: dict[str, Any], name: str) -> str:
    value = form.get(name)
    return value if isinstance(value, str) else ""


def _secret() -> str:
    return secrets.token_urlsafe(32)


class McpOAuthService:
    def __init__(
        self,
        storage: OAuthStorage,
        keys: ApiKeyStorage,
        access: BusinessAccess,
        addresses: OAuthAddresses,
        *,
        new_secret: Callable[[], str] = _secret,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._storage = storage
        self._keys = keys
        self._access = access
        self.addresses = addresses
        self._new_secret = new_secret
        self._now = now

    # ------------------------------------------------------------------ registro (sin sesión)

    def register(self, raw: object) -> dict[str, Any]:
        name, redirect_uris = read_client_registration(raw)
        now = self._now()
        client = OAuthClient(client_id=uuid.uuid4().hex, name=name, redirect_uris=redirect_uris, created_at=now)
        self._storage.create_client(client)
        logger.info("oauth_agente_registrado", extra={"client": client.client_id, "client_name": name})
        return {
            "client_id": client.client_id,
            "client_id_issued_at": int(now.timestamp()),
            "client_name": name,
            "redirect_uris": list(redirect_uris),
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
        }

    # ------------------------------------------------------------------ autorizar (con la sesión de la persona)

    def _read(self, raw: object) -> tuple[OAuthClient, AuthorizationRequest]:
        params = authorization_params(raw)
        client_id = params.get("client_id") or ""
        client = self._storage.find_client(client_id) if client_id else None
        return client, read_authorization_request(params, client, self.addresses.resource)  # type: ignore[return-value]

    def describe(self, raw: object) -> AuthorizationPrompt:
        try:
            client, request = self._read(raw)
        except OAuthError as exc:
            params = authorization_params(raw)
            back = redirect_with(params["redirect_uri"], {"error": exc.code, "error_description": str(exc), "state": params.get("state")}) if exc.redirectable else None
            return AuthorizationPrompt(ready=False, message=str(exc), redirect_to=back)
        return AuthorizationPrompt(ready=True, client_name=client.name, redirect_host=urlsplit(request.redirect_uri).netloc)

    def decide(
        self, principal: Principal, raw: object, *, approve: bool, permissions: object = None, reach: object = None, businesses: object = None
    ) -> str:
        """A dónde vuelve el navegador: al agente con el código, o con `access_denied` si la persona no autorizó."""
        try:
            client, request = self._read(raw)
        except OAuthError as exc:
            raise InvalidFieldsError(str(exc), []) from None
        if not approve:
            return redirect_with(request.redirect_uri, {"error": "access_denied", "error_description": "La persona no autorizó el acceso.", "state": request.state})
        chosen = businesses if isinstance(businesses, list) else []
        key_reach = validated_reach(reach, chosen, current=str(chosen[0]) if reach in (None, "one") and chosen else None)
        for slug in key_reach.businesses:
            self._access.require(principal, slug)
        scopes = validated_permissions(permissions, key_reach.kind)
        if SCOPE_ASSISTANT_CHAT in scopes:
            raise InvalidFieldsError("Revisa los permisos.", [FieldIssue("permissions.chat", "Conversar con el asistente se hace con la API del asistente, no con un agente.")])
        connection = self._keys.connect(
            name=validated_key_name(client.name), scopes=scopes, reach=key_reach, created_by=principal.label,
            owner_user_id=None if principal.local_operator else principal.user_id, client_id=client.client_id,
        )
        code = self._new_secret()
        self._storage.save_code(
            AuthorizationCode(
                code_hash=token_fingerprint(code), client_id=client.client_id, key_id=connection.id, redirect_uri=request.redirect_uri,
                code_challenge=request.code_challenge, resource=request.resource, expires_at=self._now() + CODE_TTL,
            )
        )
        logger.info("oauth_conexion_autorizada", extra={"client": client.client_id, "key": connection.id, "reach": key_reach.kind, "scopes": list(scopes)})
        return redirect_with(request.redirect_uri, {"code": code, "state": request.state})

    # ------------------------------------------------------------------ tokens (sin sesión)

    def exchange(self, form: dict[str, Any]) -> dict[str, Any]:
        """El endpoint de tokens. Falla con `OAuthError` y el código estándar si algo no cuadra."""
        resource = _text(form, "resource")
        if resource and not same_resource(resource, self.addresses.resource):
            raise OAuthError("invalid_target", "Ese recurso no es el servidor MCP de AI Sales Engine.")
        grant = _text(form, "grant_type")
        now = self._now()
        if grant == "authorization_code":
            code = self._storage.take_code(token_fingerprint(_text(form, "code")))
            valid = (
                code is not None
                and code.expires_at > now
                and code.client_id == _text(form, "client_id")
                and code.redirect_uri == _text(form, "redirect_uri")
                and pkce_matches(_text(form, "code_verifier"), code.code_challenge)
                and self._keys.identity(code.key_id) is not None
            )
            if not valid:
                raise OAuthError("invalid_grant", "El código no es válido, ya se usó o venció.")
            return self._issue(code.key_id, code.client_id, now)
        if grant == "refresh_token":
            current = self._storage.take_refresh(token_fingerprint(_text(form, "refresh_token")))
            client_id = _text(form, "client_id")
            if current is None or current.refresh_expires_at <= now or (client_id and client_id != current.client_id) or self._keys.identity(current.key_id) is None:
                raise OAuthError("invalid_grant", "El token de renovación no es válido, venció o la conexión se revocó. Vuelve a conectar el agente.")
            return self._issue(current.key_id, current.client_id, now)
        raise OAuthError("unsupported_grant_type", "Solo se admiten authorization_code y refresh_token.")

    def _issue(self, key_id: str, client_id: str, now: datetime) -> dict[str, Any]:
        access, refresh = f"{ACCESS_TOKEN_PREFIX}{self._new_secret()}", f"{REFRESH_TOKEN_PREFIX}{self._new_secret()}"
        self._storage.save_grant(
            TokenGrant(
                key_id=key_id, client_id=client_id, access_hash=token_fingerprint(access), access_expires_at=now + ACCESS_TTL,
                refresh_hash=token_fingerprint(refresh), refresh_expires_at=now + REFRESH_TTL,
            ),
            now=now,
        )
        return {"access_token": access, "token_type": "Bearer", "expires_in": int(ACCESS_TTL.total_seconds()), "refresh_token": refresh}

    # ------------------------------------------------------------------ reconocer

    def authenticate(self, token: str) -> ApiKeyIdentity | None:
        if not is_access_token(token):
            return None
        key_id = self._storage.key_for_access(token_fingerprint(token), self._now())
        return self._keys.identity(key_id) if key_id else None
