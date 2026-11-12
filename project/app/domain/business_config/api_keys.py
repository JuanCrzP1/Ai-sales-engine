"""Claves de API (Integraciones → Claves de API).

Una clave deja que otro sistema use la plataforma sin una sesión del panel: Leona, una página web, un servidor propio o un agente
de IA por MCP. Cada clave:
- es de quien la creó, entra a los negocios que se eligieron y solo puede lo que dicen sus permisos (`key_permissions.py`);
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
from app.domain.business_config.key_permissions import SCOPE_ASSISTANT_CHAT, KeyReach, is_expired

__all__ = ["SCOPE_ASSISTANT_CHAT"]

KEY_PREFIX = "ase_live_"
KEY_RANDOM_CHARS = 40
# Lo que se muestra de una clave para reconocerla: su comienzo con los primeros caracteres aleatorios.
VISIBLE_CHARS = len(KEY_PREFIX) + 6
MAX_NAME_CHARS = 60
MAX_ACTIVE_KEYS = 20
_ALPHABET = string.ascii_letters + string.digits
_KEY = re.compile(rf"^{KEY_PREFIX}[A-Za-z0-9]{{{KEY_RANDOM_CHARS}}}$")



@dataclass(frozen=True)
class ApiKey:
    id: str
    # El negocio de una clave de un solo negocio; None si entra a todos o a algunos.
    business_slug: str | None
    name: str
    # El comienzo visible (`ase_live_Ab12Cd`), para reconocerla.
    prefix: str
    scopes: tuple[str, ...]
    created_at: datetime
    created_by: str | None = None
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
    reach: KeyReach = KeyReach("one")
    expires_at: datetime | None = None
    # `key`: un valor fijo que se mostró una vez. `oauth`: una conexión que la persona autorizó desde el agente (Claude, ChatGPT),
    # sin valor fijo: sus tokens rotan (`oauth.py`).
    kind: str = "key"

    @property
    def active(self) -> bool:
        return self.revoked_at is None

    def usable(self, now: datetime) -> bool:
        return self.active and not is_expired(self.expires_at, now)


@dataclass(frozen=True)
class CreatedApiKey:
    """Una clave recién creada: la única vez que existe `secret` fuera de quien la usa."""

    key: ApiKey
    secret: str


@dataclass(frozen=True)
class ApiKeyIdentity:
    """Quién llama con una clave válida: la clave, lo que puede hacer, a qué negocios entra y de quién es.

    `business_slug` es su negocio cuando es de uno solo (la API del asistente lo necesita); `owner_user_id`, la cuenta que la
    creó (None en este equipo, sin cuentas)."""

    key_id: str
    business_slug: str | None
    name: str
    scopes: tuple[str, ...]
    reach: KeyReach = KeyReach("one")
    owner_user_id: str | None = None
    # Cómo se llama su dueño en el historial (su correo, si se conoce).
    owner_label: str | None = None


def new_secret() -> str:
    return KEY_PREFIX + "".join(secrets.choice(_ALPHABET) for _ in range(KEY_RANDOM_CHARS))


def fingerprint(secret: str) -> str:
    """La huella con la que se guarda y se busca una clave."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def looks_like_key(secret: str) -> bool:
    return bool(_KEY.match(secret or ""))


def visible_prefix(secret: str) -> str:
    return secret[:VISIBLE_CHARS]


def validated_key_name(name: object) -> str:
    """El nombre de una clave nueva, para reconocerla después."""
    label = " ".join(str(name or "").split())
    if not label or len(label) > MAX_NAME_CHARS:
        raise InvalidFieldsError("Revisa la clave.", [FieldIssue("name", f"Ponle un nombre de hasta {MAX_NAME_CHARS} caracteres, por ejemplo «Claude de ventas».")])
    return label
