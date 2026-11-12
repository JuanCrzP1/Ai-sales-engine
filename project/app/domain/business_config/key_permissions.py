"""Qué puede hacer una clave de API y a qué negocios entra (Integraciones → Claves de API).

Una sola lista de claves para todo lo que se conecta de fuera: otra plataforma que conversa con el asistente (Leona, una web) y
los agentes de IA por MCP (Claude, Cursor, n8n...). Quien crea la clave elige:

- **Por área**, sin acceso, ver o ver y editar (`KEY_AREAS`). Cada nivel se traduce a permisos internos (`scopes`), que es lo que
  guarda la clave y lo que comprueba cada herramienta.
- **A qué negocios entra**: solo uno, todos los de su cuenta (también los que cree después) o algunos.
- **Cuándo vence**: a los 30, 90 o 365 días, o nunca.

Reglas que no se pueden romper:
- Conversar con el asistente (la API del asistente) es de UN negocio: el mensaje debe saber qué asistente responde.
- Crear negocios exige entrar a todos: un negocio nuevo no está en una lista fija.
- Los datos de pago solo se escriben: ninguna clave puede leer su valor.

Todo aquí es puro: sin base de datos ni red.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from app.domain.business_config.errors import FieldIssue, InvalidFieldsError

AccessLevel = Literal["none", "read", "write"]
BusinessReach = Literal["one", "all", "some"]

SCOPE_ASSISTANT_CHAT = "assistant:chat"
SCOPE_BUSINESSES_READ = "businesses:read"
SCOPE_BUSINESSES_CREATE = "businesses:create"
SCOPE_CONFIG_READ = "assistant:read"
SCOPE_CONFIG_WRITE = "assistant:write"
SCOPE_PAYMENTS_WRITE = "payments:write"


@dataclass(frozen=True)
class KeyArea:
    """Un área que se puede permitir. `read` y `write` dicen, para quien crea la clave, qué deja hacer cada nivel; sin uno de
    ellos, ese nivel no existe en el área."""

    id: str
    label: str
    read: str | None
    write: str | None
    read_scopes: tuple[str, ...] = ()
    write_scopes: tuple[str, ...] = ()
    # Solo con una clave de un negocio.
    one_business_only: bool = False


KEY_AREAS: tuple[KeyArea, ...] = (
    KeyArea(
        "chat",
        "Conversar con el asistente",
        read=None,
        write="Mandarle mensajes de clientes y recibir sus respuestas (API del asistente, por ejemplo desde Leona).",
        write_scopes=(SCOPE_ASSISTANT_CHAT,),
        one_business_only=True,
    ),
    KeyArea(
        "businesses",
        "Negocios",
        read="Ver tus negocios y las plantillas para empezar uno.",
        write="Crear negocios nuevos desde una plantilla.",
        read_scopes=(SCOPE_BUSINESSES_READ,),
        write_scopes=(SCOPE_BUSINESSES_READ, SCOPE_BUSINESSES_CREATE),
    ),
    KeyArea(
        "assistant",
        "Asistente IA",
        read="Ver la configuración de cada sección, lo que falta y lo que cambia al publicar.",
        write="Editar la configuración, probar el asistente (gasta tu clave de IA) y publicar o volver a una versión anterior.",
        read_scopes=(SCOPE_CONFIG_READ,),
        write_scopes=(SCOPE_CONFIG_READ, SCOPE_CONFIG_WRITE),
    ),
    KeyArea(
        "payments",
        "Datos de pago",
        read=None,
        write="Escribir tus números de Nequi o Daviplata, cuentas y enlaces de pago. Nunca puede leerlos: solo ve que están puestos.",
        write_scopes=(SCOPE_PAYMENTS_WRITE,),
    ),
)

KNOWN_SCOPES = frozenset(scope for area in KEY_AREAS for scope in (*area.read_scopes, *area.write_scopes))
EXPIRY_DAYS: tuple[int | None, ...] = (30, 90, 365, None)


@dataclass(frozen=True)
class KeyReach:
    """A qué negocios entra una clave: uno, todos los de su dueño o algunos (por su identificador)."""

    kind: BusinessReach
    businesses: frozenset[str] = frozenset()

    def allows(self, business_slug: str) -> bool:
        return self.kind == "all" or business_slug in self.businesses


def area_by_id(area_id: str) -> KeyArea | None:
    return next((area for area in KEY_AREAS if area.id == area_id), None)


def scopes_for(permissions: dict[str, AccessLevel]) -> tuple[str, ...]:
    chosen: list[str] = []
    for area in KEY_AREAS:
        level = permissions.get(area.id, "none")
        scopes = area.write_scopes if level == "write" else area.read_scopes if level == "read" else ()
        chosen.extend(scope for scope in scopes if scope not in chosen)
    return tuple(chosen)


def permissions_of(scopes: tuple[str, ...] | list[str]) -> dict[str, AccessLevel]:
    """Los niveles por área a partir de los permisos guardados (para mostrar la clave)."""
    held = set(scopes)
    levels: dict[str, AccessLevel] = {}
    for area in KEY_AREAS:
        if area.write_scopes and set(area.write_scopes) <= held:
            levels[area.id] = "write"
        elif area.read_scopes and set(area.read_scopes) <= held:
            levels[area.id] = "read"
    return levels


def validated_permissions(raw: object, reach: BusinessReach) -> tuple[str, ...]:
    """Los permisos de una clave nueva: áreas conocidas, niveles que existen en cada una, al menos un área, y las reglas de alcance."""
    value = raw if isinstance(raw, dict) else {}
    issues: list[FieldIssue] = []
    permissions: dict[str, AccessLevel] = {}
    for area in KEY_AREAS:
        level = value.get(area.id, "none")
        if level in (None, "none"):
            continue
        if level not in ("read", "write") or (level == "read" and area.read is None) or (level == "write" and area.write is None):
            issues.append(FieldIssue(f"permissions.{area.id}", f"Ese nivel no existe en «{area.label}»."))
            continue
        if area.one_business_only and reach != "one":
            issues.append(FieldIssue(f"permissions.{area.id}", f"«{area.label}» es de un solo negocio: crea esa clave para un negocio."))
            continue
        permissions[area.id] = level
    if permissions.get("businesses") == "write" and reach != "all":
        issues.append(FieldIssue("permissions.businesses", "Para crear negocios, la clave debe entrar a todos tus negocios."))
    if not issues and not permissions:
        issues.append(FieldIssue("permissions", "Dale acceso al menos a un área."))
    if issues:
        raise InvalidFieldsError("Revisa los permisos de la clave.", issues)
    return scopes_for(permissions)


def validated_reach(kind: object, businesses: object, *, current: str | None) -> KeyReach:
    """A qué negocios entra: `one` es el negocio desde el que se crea; `some`, una lista de identificadores."""
    if kind in (None, "one"):
        if not current:
            raise InvalidFieldsError("Revisa la clave.", [FieldIssue("reach", "Elige el negocio de la clave.")])
        return KeyReach("one", frozenset({current}))
    if kind == "all":
        return KeyReach("all")
    if kind == "some":
        chosen = frozenset(str(item) for item in businesses) if isinstance(businesses, list) else frozenset()
        if not chosen:
            raise InvalidFieldsError("Revisa la clave.", [FieldIssue("businesses", "Elige al menos un negocio.")])
        return KeyReach("some", chosen)
    raise InvalidFieldsError("Revisa la clave.", [FieldIssue("reach", "Elige a qué negocios entra la clave.")])


def expiry_from(days: object, now: datetime) -> datetime | None:
    if days is not None and (isinstance(days, bool) or not isinstance(days, int)):
        raise InvalidFieldsError("Revisa la clave.", [FieldIssue("expires_in_days", "Elige cuándo vence.")])
    if days not in EXPIRY_DAYS:
        raise InvalidFieldsError("Revisa la clave.", [FieldIssue("expires_in_days", "Elige 30, 90 o 365 días, o que no venza.")])
    return None if days is None else now + timedelta(days=days)


def is_expired(expires_at: datetime | None, now: datetime) -> bool:
    return expires_at is not None and expires_at <= now
