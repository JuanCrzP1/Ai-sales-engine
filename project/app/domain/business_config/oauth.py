"""OAuth 2.1 del servidor MCP: lo que hace que Claude (en la web y en la app) y ChatGPT se conecten pegando solo la dirección.

El agente se registra solo (registro dinámico, RFC 7591), la persona entra al panel y autoriza con los permisos que elija, y el
agente cambia el código por tokens (código de autorización con PKCE S256 obligatorio). Lo que la persona autoriza es una
**conexión**: una clave de la cuenta de tipo `oauth`, con permisos por área y alcance como cualquier otra, pero sin valor fijo. Los
tokens son de esa conexión: revocarla en «Claves de API» los corta todos.

- El código de autorización sirve una vez y por 10 minutos.
- El token de acceso dura 1 hora; el de renovación, 30 días, y cambia cada vez que se usa (el anterior deja de servir).
- De todos se guarda solo la huella (SHA-256), como de las claves.

Descubrimiento (lo primero que consulta un agente al recibir 401):
- recurso protegido (RFC 9728): qué servidor de autorización usar;
- servidor de autorización (RFC 8414): dónde registrarse, autorizar y pedir tokens.

Todo aquí es puro: sin base de datos ni red.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

CODE_TTL = timedelta(minutes=10)
ACCESS_TTL = timedelta(hours=1)
REFRESH_TTL = timedelta(days=30)

ACCESS_TOKEN_PREFIX = "ase_at_"
REFRESH_TOKEN_PREFIX = "ase_rt_"
MAX_REDIRECT_URIS = 5
MAX_CLIENT_NAME_CHARS = 60
MAX_PARAM_CHARS = 2048
DEFAULT_CLIENT_NAME = "Agente de IA"
LOOPBACK_HOSTS = ("localhost", "127.0.0.1", "[::1]", "::1")

PROTECTED_RESOURCE_PATH = "/.well-known/oauth-protected-resource"
AUTHORIZATION_SERVER_PATH = "/.well-known/oauth-authorization-server"
AUTHORIZE_PAGE_PATH = "/oauth/authorize"
REGISTER_PATH = "/api/oauth/register"
TOKEN_PATH = "/api/oauth/token"

_PKCE_VERIFIER = re.compile(r"^[A-Za-z0-9\-._~]{43,128}$")
_PKCE_CHALLENGE = re.compile(r"^[A-Za-z0-9\-_]{43}$")


class OAuthError(ValueError):
    """Un error de OAuth con su código estándar (`invalid_request`, `invalid_grant`...). `redirectable`: se le puede devolver al
    agente por su dirección de regreso (no si esa dirección es la que no sirve: entonces se muestra en el panel)."""

    def __init__(self, code: str, message: str, *, redirectable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.redirectable = redirectable


@dataclass(frozen=True)
class OAuthAddresses:
    """Las direcciones públicas: el panel (emisor y pantalla de autorización) y el servidor MCP (el único recurso)."""

    issuer: str
    resource: str


@dataclass(frozen=True)
class OAuthClient:
    client_id: str
    name: str
    redirect_uris: tuple[str, ...]
    created_at: datetime


@dataclass(frozen=True)
class AuthorizationRequest:
    """Lo que pide el agente en la pantalla de autorización, ya revisado contra su registro."""

    client_id: str
    redirect_uri: str
    code_challenge: str
    state: str | None
    resource: str | None


@dataclass(frozen=True)
class AuthorizationCode:
    """Un código emitido: se guarda su huella y se usa una sola vez."""

    code_hash: str
    client_id: str
    key_id: str
    redirect_uri: str
    code_challenge: str
    resource: str | None
    expires_at: datetime


@dataclass(frozen=True)
class TokenGrant:
    """Los tokens vigentes de una conexión: de acceso y de renovación (sus huellas)."""

    key_id: str
    client_id: str
    access_hash: str
    access_expires_at: datetime
    refresh_hash: str
    refresh_expires_at: datetime


def token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def is_access_token(token: str) -> bool:
    return token.startswith(ACCESS_TOKEN_PREFIX)


def is_allowed_redirect_uri(value: str) -> bool:
    """https en cualquier dominio; http solo en el propio equipo (agentes locales como Claude Code); nunca con fragmento."""
    try:
        url = urlsplit(value)
    except ValueError:
        return False
    if url.fragment or not url.hostname or len(value) > MAX_PARAM_CHARS:
        return False
    if url.scheme == "https":
        return True
    return url.scheme == "http" and url.hostname in LOOPBACK_HOSTS


def read_client_registration(raw: object) -> tuple[str, tuple[str, ...]]:
    """El nombre y las direcciones de regreso de un registro dinámico (RFC 7591). Solo agentes públicos con PKCE."""
    value = raw if isinstance(raw, dict) else {}
    uris = value.get("redirect_uris")
    uris = [uri for uri in uris if isinstance(uri, str)] if isinstance(uris, list) else []
    if not uris or len(uris) > MAX_REDIRECT_URIS:
        raise OAuthError("invalid_redirect_uri", f"Envía entre 1 y {MAX_REDIRECT_URIS} redirect_uris.")
    invalid = next((uri for uri in uris if not is_allowed_redirect_uri(uri)), None)
    if invalid is not None:
        raise OAuthError("invalid_redirect_uri", f"redirect_uri no permitida (usa https, o http solo en este equipo): {invalid[:200]}")
    method = value.get("token_endpoint_auth_method")
    if method is not None and method != "none":
        raise OAuthError("invalid_client_metadata", "Solo se admiten agentes públicos (token_endpoint_auth_method: none) con PKCE.")
    for field, allowed in (("grant_types", {"authorization_code", "refresh_token"}), ("response_types", {"code"})):
        asked = value.get(field)
        if isinstance(asked, list) and not set(asked) <= allowed:
            raise OAuthError("invalid_client_metadata", f"{field} admite solo: {', '.join(sorted(allowed))}.")
    name = " ".join(str(value.get("client_name") or "").split())[:MAX_CLIENT_NAME_CHARS] or DEFAULT_CLIENT_NAME
    return name, tuple(dict.fromkeys(uris))


def authorization_params(raw: object) -> dict[str, str]:
    """Los parámetros de autorización tal como los puso el agente: solo textos de largo razonable."""
    if not isinstance(raw, dict):
        return {}
    return {str(key): value for key, value in raw.items() if isinstance(value, str) and len(value) <= MAX_PARAM_CHARS}


def same_resource(asked: str, resource: str) -> bool:
    return asked.rstrip("/") == resource.rstrip("/")


def read_authorization_request(params: dict[str, str], client: OAuthClient | None, resource: str) -> AuthorizationRequest:
    """Revisa la solicitud contra el agente registrado. La dirección de regreso debe ser EXACTAMENTE una de las registradas: si
    no, el error no se le devuelve a ella (se muestra en el panel)."""
    if client is None:
        raise OAuthError("invalid_client", "El agente no está registrado. Vuelve a conectarlo desde su programa.")
    redirect_uri = params.get("redirect_uri") or ""
    if redirect_uri not in client.redirect_uris:
        raise OAuthError("invalid_request", "La dirección de regreso no es la que registró el agente.")
    if params.get("response_type") != "code":
        raise OAuthError("unsupported_response_type", "Solo se admite response_type=code.", redirectable=True)
    challenge = params.get("code_challenge") or ""
    if params.get("code_challenge_method") != "S256" or not _PKCE_CHALLENGE.match(challenge):
        raise OAuthError("invalid_request", "Falta PKCE (code_challenge con S256).", redirectable=True)
    asked = params.get("resource") or None
    if asked is not None and not same_resource(asked, resource):
        raise OAuthError("invalid_target", "Ese recurso no es el servidor MCP de AI Sales Engine.", redirectable=True)
    return AuthorizationRequest(client.client_id, redirect_uri, challenge, params.get("state") or None, asked)


def pkce_matches(verifier: str, challenge: str) -> bool:
    """PKCE S256: base64url(SHA-256(verifier)) sin relleno es el challenge, comparado en tiempo constante."""
    if not _PKCE_VERIFIER.match(verifier or ""):
        return False
    computed = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
    return hmac.compare_digest(computed, challenge)


def redirect_with(redirect_uri: str, params: dict[str, str | None]) -> str:
    """La dirección de regreso con sus parámetros (el código o el error, y el `state` del agente), conservando los que ya traía."""
    url = urlsplit(redirect_uri)
    query = parse_qsl(url.query, keep_blank_values=True)
    query.extend((key, value) for key, value in params.items() if value is not None)
    return urlunsplit((url.scheme, url.netloc, url.path, urlencode(query), ""))


def oauth_addresses(mcp_url: str) -> OAuthAddresses:
    """El emisor es el origen del panel donde vive el servidor MCP (`https://panel/api/mcp` → `https://panel`)."""
    url = urlsplit(mcp_url)
    return OAuthAddresses(issuer=f"{url.scheme}://{url.netloc}", resource=mcp_url.rstrip("/"))


def resource_metadata_url(resource: str) -> str:
    """Dónde publica el recurso sus metadatos (RFC 9728 §3.1): el origen, la ruta conocida y la ruta del recurso."""
    url = urlsplit(resource)
    path = "" if url.path in ("", "/") else url.path
    return f"{url.scheme}://{url.netloc}{PROTECTED_RESOURCE_PATH}{path}"


def protected_resource_metadata(addresses: OAuthAddresses) -> dict[str, Any]:
    return {
        "resource": addresses.resource,
        "authorization_servers": [addresses.issuer],
        "bearer_methods_supported": ["header"],
        "resource_name": "AI Sales Engine",
    }


def authorization_server_metadata(addresses: OAuthAddresses) -> dict[str, Any]:
    return {
        "issuer": addresses.issuer,
        "authorization_endpoint": f"{addresses.issuer}{AUTHORIZE_PAGE_PATH}",
        "token_endpoint": f"{addresses.issuer}{TOKEN_PATH}",
        "registration_endpoint": f"{addresses.issuer}{REGISTER_PATH}",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
    }
