"""El equipo de cada negocio y sus invitaciones en la base (`business_members` y `team_invitations`, migración 0016).

Cambiar un rol, quitar a alguien y aceptar una invitación leen y escriben en la misma transacción, con las filas bloqueadas en
PostgreSQL (`FOR UPDATE`): dos cambios a la vez nunca dejan el negocio sin dueño ni usan dos veces la misma invitación.
"""
from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy import and_, delete, func, insert, select, update
from sqlalchemy.engine import Connection, Engine, Row

from app.domain.business_config.errors import FieldIssue, InvalidFieldsError
from app.domain.business_config.team import MAX_PENDING_INVITATIONS, OWNER, Invitation, InvitationError, Member, TeamRuleError
from app.infrastructure.business_config.tables import business_members, team_invitations, tenants
from app.infrastructure.business_config.tenancy import tenant_of

_MISSING_MEMBER = "Esa persona ya no está en el equipo."
_MISSING_INVITATION = "Esa invitación ya no existe."


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _key(invitation_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(invitation_id))
    except ValueError as exc:
        raise InvitationError(_MISSING_INVITATION) from exc


def _member(row: Row) -> Member:
    return Member(user_id=row.user_id, email=row.email, role=row.role, joined_at=_utc(row.created_at))


def _invitation(row: Row) -> Invitation:
    return Invitation(
        id=str(row.id),
        tenant_slug=row.slug,
        business_name=row.name,
        email=row.email,
        role=row.role,
        invited_by=row.invited_by,
        created_at=_utc(row.created_at),
        expires_at=_utc(row.expires_at),
        accepted_at=_utc(row.accepted_at),
        revoked_at=_utc(row.revoked_at),
    )


_INVITATION_COLUMNS = (team_invitations, tenants.c.slug, tenants.c.name)


class TeamStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._locks = engine.dialect.name == "postgresql"

    def _locked(self, query, of=None):
        if not self._locks:
            return query
        return query.with_for_update(of=of) if of is not None else query.with_for_update()

    # ------------------------------------------------------------------------------------------------------------- miembros

    def members(self, tenant_slug: str) -> list[Member]:
        query = (
            select(business_members)
            .join(tenants, tenants.c.id == business_members.c.tenant_id)
            .where(tenants.c.slug == tenant_slug)
            .order_by(business_members.c.created_at, business_members.c.user_id)
        )
        with self._engine.connect() as conn:
            return [_member(row) for row in conn.execute(query)]

    def _team(self, conn: Connection, tenant_id: uuid.UUID) -> dict[str, Row]:
        rows = conn.execute(self._locked(select(business_members).where(business_members.c.tenant_id == tenant_id)))
        return {row.user_id: row for row in rows}

    def change_role(self, tenant_slug: str, user_id: str, decide: Callable[[str, int], str]) -> Member:
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            team = self._team(conn, tenant.id)
            target = team.get(user_id)
            if target is None:
                raise TeamRuleError(_MISSING_MEMBER)
            owners = sum(1 for row in team.values() if row.role == OWNER)
            role = decide(target.role, owners)
            conn.execute(update(business_members).where(and_(business_members.c.tenant_id == tenant.id, business_members.c.user_id == user_id)).values(role=role))
            return Member(user_id=user_id, email=target.email, role=role, joined_at=_utc(target.created_at))

    def remove(self, tenant_slug: str, user_id: str, decide: Callable[[str, int], None]) -> None:
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            team = self._team(conn, tenant.id)
            target = team.get(user_id)
            if target is None:
                raise TeamRuleError(_MISSING_MEMBER)
            decide(target.role, sum(1 for row in team.values() if row.role == OWNER))
            conn.execute(delete(business_members).where(and_(business_members.c.tenant_id == tenant.id, business_members.c.user_id == user_id)))

    # -------------------------------------------------------------------------------------------------------- invitaciones

    def _invitation_query(self):
        return select(*_INVITATION_COLUMNS).join(tenants, tenants.c.id == team_invitations.c.tenant_id)

    def invitations(self, tenant_slug: str) -> list[Invitation]:
        query = (
            self._invitation_query()
            .where(tenants.c.slug == tenant_slug, team_invitations.c.accepted_at.is_(None), team_invitations.c.revoked_at.is_(None))
            .order_by(team_invitations.c.created_at.desc())
        )
        with self._engine.connect() as conn:
            return [_invitation(row) for row in conn.execute(query)]

    def _one(self, conn: Connection, condition) -> Invitation:
        row = conn.execute(self._invitation_query().where(condition)).first()
        if row is None:
            raise InvitationError(_MISSING_INVITATION)
        return _invitation(row)

    def invite(self, tenant_slug: str, *, email: str, role: str, token_hash: str, invited_by: str, now: datetime, expires_at: datetime) -> Invitation:
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            members = conn.execute(select(business_members.c.email).where(business_members.c.tenant_id == tenant.id))
            if any((row.email or "").strip().lower() == email for row in members):
                raise InvalidFieldsError("Esa persona ya está en el equipo.", [FieldIssue("email", "Esa persona ya está en el equipo.")])
            pending = and_(team_invitations.c.tenant_id == tenant.id, team_invitations.c.accepted_at.is_(None), team_invitations.c.revoked_at.is_(None))
            # Una invitación nueva al mismo correo reemplaza la anterior: el enlace viejo deja de servir.
            conn.execute(update(team_invitations).where(pending, team_invitations.c.email == email).values(revoked_at=now))
            count = conn.execute(select(func.count()).select_from(team_invitations).where(pending)).scalar_one()
            if count >= MAX_PENDING_INVITATIONS:
                message = f"Tienes {MAX_PENDING_INVITATIONS} invitaciones sin usar. Retira las que ya no sirven antes de invitar a alguien más."
                raise InvalidFieldsError(message, [FieldIssue("invitations", message)])
            new_id = uuid.uuid4()
            conn.execute(
                insert(team_invitations).values(
                    id=new_id, tenant_id=tenant.id, email=email, role=role, token_hash=token_hash, invited_by=invited_by, created_at=now, expires_at=expires_at
                )
            )
            return self._one(conn, team_invitations.c.id == new_id)

    def renew(self, tenant_slug: str, invitation_id: str, *, token_hash: str, now: datetime, expires_at: datetime) -> Invitation:
        key = _key(invitation_id)
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            mine = and_(team_invitations.c.id == key, team_invitations.c.tenant_id == tenant.id, team_invitations.c.accepted_at.is_(None), team_invitations.c.revoked_at.is_(None))
            changed = conn.execute(update(team_invitations).where(mine).values(token_hash=token_hash, created_at=now, expires_at=expires_at)).rowcount
            if not changed:
                raise InvitationError(_MISSING_INVITATION)
            return self._one(conn, team_invitations.c.id == key)

    def revoke(self, tenant_slug: str, invitation_id: str, *, now: datetime) -> None:
        key = _key(invitation_id)
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            mine = and_(team_invitations.c.id == key, team_invitations.c.tenant_id == tenant.id, team_invitations.c.accepted_at.is_(None), team_invitations.c.revoked_at.is_(None))
            if not conn.execute(update(team_invitations).where(mine).values(revoked_at=now)).rowcount:
                raise InvitationError(_MISSING_INVITATION)

    def invitation_by_token(self, token_hash: str) -> Invitation | None:
        with self._engine.connect() as conn:
            row = conn.execute(self._invitation_query().where(team_invitations.c.token_hash == token_hash)).first()
        return _invitation(row) if row is not None else None

    def accept(self, token_hash: str, *, user_id: str, email: str | None, now: datetime, check: Callable[[Invitation | None], Invitation]) -> str:
        with self._engine.begin() as conn:
            row = conn.execute(self._locked(self._invitation_query().where(team_invitations.c.token_hash == token_hash), of=team_invitations)).first()
            invitation = check(_invitation(row) if row is not None else None)
            tenant_id = row.tenant_id
            already = conn.execute(
                select(business_members.c.user_id).where(and_(business_members.c.tenant_id == tenant_id, business_members.c.user_id == user_id))
            ).first()
            if already is None:
                conn.execute(insert(business_members).values(tenant_id=tenant_id, user_id=user_id, role=invitation.role, created_at=now, email=email))
            conn.execute(update(team_invitations).where(team_invitations.c.id == row.id).values(accepted_at=now, accepted_by=user_id))
            return invitation.tenant_slug
