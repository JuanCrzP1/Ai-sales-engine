"""El equipo de cada negocio: los roles, lo que puede hacer cada uno, quién puede tocar a quién y las invitaciones por enlace.

| | Dueño | Administrador | Asesor |
|---|---|---|---|
| Atender: chats, clientes, registrar ventas, usar respuestas rápidas | ✓ | ✓ | ✓ |
| Reportes y anular ventas | ✓ | ✓ | — |
| Configurar: asistente, publicar, IA, canales, integraciones, atención humana, respuestas rápidas | ✓ | ✓ | — |
| Equipo: invitar, cambiar roles, quitar | ✓ | ✓ (menos a los dueños) | — |
| Eliminar el negocio | ✓ | — | — |

Reglas que nunca se rompen: siempre queda al menos un dueño, nadie cambia su propio rol ni se quita a sí mismo desde el equipo, y
solo un dueño nombra o toca a otro dueño. Todo aquí es puro: lo usan el servicio, las pruebas y el panel (que repite la tabla).
"""
from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.domain.business_config.errors import BusinessConfigError, FieldIssue, InvalidFieldsError, NotAllowedError, NotOwnerError

OWNER = "owner"
ADMIN = "admin"
AGENT = "agent"
ROLES: tuple[str, ...] = (OWNER, ADMIN, AGENT)
ROLE_LABELS = {OWNER: "Dueño", ADMIN: "Administrador", AGENT: "Asesor"}

# Lo que se puede hacer en un negocio. Cada ruta y cada herramienta pide uno.
ATTEND = "attend"
REPORTS = "reports"
CONFIGURE = "configure"
TEAM = "team"
DELETE_BUSINESS = "delete_business"
CAPABILITIES: dict[str, frozenset[str]] = {
    OWNER: frozenset({ATTEND, REPORTS, CONFIGURE, TEAM, DELETE_BUSINESS}),
    ADMIN: frozenset({ATTEND, REPORTS, CONFIGURE, TEAM}),
    AGENT: frozenset({ATTEND}),
}
# Por qué no puede, en palabras del negocio.
REFUSALS = {
    ATTEND: "No tienes acceso a este negocio.",
    REPORTS: "Los reportes y anular ventas son del dueño o de un administrador.",
    CONFIGURE: "Configurar el negocio es del dueño o de un administrador. Pídeselo a uno de ellos.",
    TEAM: "Administrar el equipo es del dueño o de un administrador.",
    DELETE_BUSINESS: "Solo el dueño del negocio puede hacer esto.",
}

INVITATION_DAYS = 7
MAX_PENDING_INVITATIONS = 50
INVITATION_TOKEN_PREFIX = "inv_"
_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class TeamRuleError(BusinessConfigError):
    """Un cambio del equipo que rompe una regla (quitar al último dueño, tocarse a sí mismo…). El mensaje es para la persona."""


class InvitationError(BusinessConfigError):
    """La invitación no sirve: no existe, venció, ya se usó o se retiró, o es para otro correo. El mensaje es para la persona."""


def can(role: str | None, capability: str) -> bool:
    return role is not None and capability in CAPABILITIES.get(role, frozenset())


def refusal(capability: str) -> NotAllowedError:
    """El error para quien no puede: eliminar el negocio sigue siendo «solo el dueño» (`NotOwnerError`)."""
    message = REFUSALS.get(capability, REFUSALS[CONFIGURE])
    return NotOwnerError(message) if capability == DELETE_BUSINESS else NotAllowedError(message)


def role_label(role: str) -> str:
    return ROLE_LABELS.get(role, role)


def normalize_email(value: object) -> str:
    return str(value or "").strip().lower()


def validated_invitation(*, email: object, role: object, actor_role: str) -> tuple[str, str]:
    """El correo y el rol de una invitación nueva, o los problemas por campo (`email`, `role`)."""
    clean = normalize_email(email)
    problems: list[FieldIssue] = []
    if not _EMAIL.match(clean) or len(clean) > 200:
        problems.append(FieldIssue("email", "Escribe el correo de la persona, por ejemplo ana@tunegocio.com."))
    if role not in ROLES:
        problems.append(FieldIssue("role", "Elige su rol: Administrador o Asesor."))
    elif role == OWNER and actor_role != OWNER:
        problems.append(FieldIssue("role", "Solo un dueño puede invitar a otro dueño."))
    if problems:
        raise InvalidFieldsError(problems[0].message if len(problems) == 1 else "Revisa la invitación.", problems)
    return clean, str(role)


def check_role_change(*, actor_id: str, actor_role: str, target_id: str, target_role: str, new_role: object, owners: int) -> str:
    """El rol nuevo si el cambio se puede hacer; si no, `TeamRuleError` con el motivo."""
    if new_role not in ROLES:
        raise InvalidFieldsError("Elige un rol: Dueño, Administrador o Asesor.", [FieldIssue("role", "Elige un rol válido.")])
    if actor_id == target_id:
        raise TeamRuleError("No puedes cambiar tu propio rol. Pídeselo a otro dueño.")
    if OWNER in (target_role, new_role) and actor_role != OWNER:
        raise TeamRuleError("Solo un dueño puede nombrar dueños o cambiarles el rol.")
    if target_role == OWNER and new_role != OWNER and owners <= 1:
        raise TeamRuleError("El negocio debe tener al menos un dueño. Nombra otro dueño antes de cambiar este.")
    return str(new_role)


def check_removal(*, actor_id: str, actor_role: str, target_id: str, target_role: str, owners: int) -> None:
    if actor_id == target_id:
        raise TeamRuleError("No puedes quitarte a ti mismo del equipo.")
    if target_role == OWNER and actor_role != OWNER:
        raise TeamRuleError("Solo un dueño puede quitar a otro dueño.")
    if target_role == OWNER and owners <= 1:
        raise TeamRuleError("El negocio debe tener al menos un dueño.")


def new_invitation_token() -> str:
    """El secreto del enlace: solo se muestra al crearlo; se guarda su huella."""
    return INVITATION_TOKEN_PREFIX + secrets.token_urlsafe(32)


def token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Member:
    user_id: str
    email: str | None
    role: str
    joined_at: datetime


@dataclass(frozen=True)
class Invitation:
    id: str
    tenant_slug: str
    business_name: str
    email: str
    role: str
    invited_by: str
    created_at: datetime
    expires_at: datetime
    accepted_at: datetime | None = None
    revoked_at: datetime | None = None

    def status(self, now: datetime) -> str:
        """pending, accepted, revoked o expired."""
        if self.accepted_at is not None:
            return "accepted"
        if self.revoked_at is not None:
            return "revoked"
        return "expired" if now >= self.expires_at else "pending"


def invitation_expiry(now: datetime) -> datetime:
    return now + timedelta(days=INVITATION_DAYS)


def check_acceptance(invitation: Invitation | None, *, email: str | None, now: datetime) -> Invitation:
    """La invitación si quien entró puede aceptarla; si no, `InvitationError` con lo que debe hacer."""
    if invitation is None:
        raise InvitationError("Este enlace de invitación no existe. Pídele a quien te invitó uno nuevo.")
    state = invitation.status(now)
    if state == "accepted":
        raise InvitationError("Esta invitación ya se usó. Si eres tú, entra con tu cuenta y busca el negocio en tus negocios.")
    if state == "revoked":
        raise InvitationError("Esta invitación se retiró. Pídele a quien te invitó una nueva.")
    if state == "expired":
        raise InvitationError("Esta invitación venció. Pídele a quien te invitó que la renueve.")
    if email is not None and normalize_email(email) != invitation.email:
        raise InvitationError(f"Esta invitación es para {invitation.email}. Entra con esa cuenta para aceptarla.")
    return invitation
