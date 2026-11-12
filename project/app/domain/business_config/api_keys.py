"""Claves de API de cada negocio (Integraciones → Claves de API).

Una clave deja que otro sistema use el negocio sin una sesión del panel: Leona, una página web o un servidor propio. Cada clave:
- es de un solo negocio y solo puede lo que dicen sus permisos;
- se muestra una sola vez al crearla. Se guarda solo su huella (SHA-256): como es larga y aleatoria, la huella basta para
  reconocerla y nadie puede reconstruirla desde la base;
- se reconoce a la vista por su comienzo (`ase_live_Ab12…`) y se puede revocar en cualquier momento.

Todo aquí es puro: sin base de datos ni red.
"""
from __future__ import annotations

import hashlib
import re
import secrets
import string
from dataclasses import dataclass
from datetime import datetime

from app.domain.business_config.errors import FieldIssue, InvalidFieldsError

KEY_PREFIX = "ase_live_"
KEY_RANDOM_CHARS = 40
# Lo que se muestra de una clave para reconocerla: su comienzo con los primeros caracteres aleatorios.
VISIBLE_CHARS = len(KEY_PREFIX) + 6
MAX_NAME_CHARS = 60
MAX_ACTIVE_KEYS = 20
_ALPHABET = string.ascii_letters + string.digits
_KEY = re.compile(rf"^{KEY_PREFIX}[A-Za-z0-9]{{{KEY_RANDOM_CHARS}}}$")

# Qué puede hacer una clave. Hoy, conversar con el asistente (la API del asistente). Los de configurar (el servidor MCP) se
# agregan aquí cuando existan.
SCOPE_ASSISTANT_CHAT = "assistant:chat"
SCOPES: dict[str, str] = {SCOPE_ASSISTANT_CHAT: "Conversar con el asistente"}


@dataclass(frozen=True)
class ApiKey:
    id: str
    business_slug: str
    name: str
    # El comienzo visible (`ase_live_Ab12Cd`), para reconocerla.
    prefix: str
    scopes: tuple[str, ...]
    created_at: datetime
    created_by: str | None = None
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None

    @property
    def active(self) -> bool:
        return self.revoked_at is None


@dataclass(frozen=True)
class CreatedApiKey:
    """Una clave recién creada: la única vez que existe `secret` fuera de quien la usa."""

    key: ApiKey
    secret: str


@dataclass(frozen=True)
class ApiKeyIdentity:
    """Quién llama con una clave válida: su negocio, la clave y lo que puede hacer."""

    key_id: str
    business_slug: str
    name: str
    scopes: tuple[str, ...]


def new_secret() -> str:
    return KEY_PREFIX + "".join(secrets.choice(_ALPHABET) for _ in range(KEY_RANDOM_CHARS))


def fingerprint(secret: str) -> str:
    """La huella con la que se guarda y se busca una clave."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def looks_like_key(secret: str) -> bool:
    return bool(_KEY.match(secret or ""))


def visible_prefix(secret: str) -> str:
    return secret[:VISIBLE_CHARS]


def validated_new_key(name: object, scopes: object) -> tuple[str, tuple[str, ...]]:
    """El nombre y los permisos de una clave nueva, revisados."""
    issues: list[FieldIssue] = []
    label = " ".join(str(name or "").split())
    if not label or len(label) > MAX_NAME_CHARS:
        issues.append(FieldIssue("name", f"Ponle un nombre de hasta {MAX_NAME_CHARS} caracteres, por ejemplo «Leona»."))
    chosen = tuple(dict.fromkeys(str(scope) for scope in scopes)) if isinstance(scopes, list) else ()
    if not chosen or any(scope not in SCOPES for scope in chosen):
        issues.append(FieldIssue("scopes", "Elige qué puede hacer la clave."))
    if issues:
        raise InvalidFieldsError("Revisa la clave.", issues)
    return label, chosen
