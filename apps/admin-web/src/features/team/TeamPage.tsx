import { useState } from "react";
import { useParams } from "react-router-dom";
import { Avatar } from "../../components/ui/Avatar";
import { Button } from "../../components/ui/Button";
import { Dialog } from "../../components/ui/Dialog";
import { Alert, Badge } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { PageHeader } from "../../components/ui/Layout";
import {
  ROLE_DESCRIPTIONS,
  ROLE_LABELS,
  ROLES,
  assignableRoles,
  expiryText,
  memberActions,
  type Invitation,
  type IssuedInvitation,
  type Role,
  type TeamMember,
} from "../../domain/team/team";
import { LoadingScreen } from "../../layout/StatusScreen";
import { useConfig } from "../../state/useConfig";
import { teamProblems, useTeam } from "../../state/useTeam";
import { InviteDialog, InvitationLinkDialog } from "./InviteDialog";

type Pending = { kind: "invite" } | { kind: "link"; issued: IssuedInvitation; renewed: boolean } | { kind: "remove"; member: TeamMember } | { kind: "revoke"; invitation: Invitation } | null;

function joined(value: string): string {
  return new Date(value).toLocaleDateString("es-CO", { day: "numeric", month: "long", year: "numeric" });
}

/**
 * Configuración → Equipo: quién está en el negocio y con qué rol, y las invitaciones que aún no se usan. El dueño y los
 * administradores invitan con un enlace (se muestra una sola vez), cambian roles y quitan personas; las reglas («siempre queda un
 * dueño», «solo un dueño toca a otro dueño») las decide el servidor y aquí se explican antes de intentarlo.
 */
export function TeamPage() {
  const { slug = "" } = useParams();
  const { document } = useConfig();
  const team = useTeam(slug);
  const [pending, setPending] = useState<Pending>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const businessName = document.identity.name.trim() || "tu negocio";

  const header = (
    <PageHeader
      title="Equipo"
      description="Las personas que atienden o administran este negocio, cada una con su rol. Invítalas con un enlace."
      actions={
        team.status === "ready" ? (
          <Button onClick={() => setPending({ kind: "invite" })}>
            <Icon name="plus" size={16} /> Invitar
          </Button>
        ) : undefined
      }
    />
  );

  if (team.status === "loading") return <LoadingScreen label="Cargando el equipo…" />;
  if (team.status === "error" || !team.team) {
    return (
      <>
        {header}
        <Alert tone="danger" title={team.error ?? "No se pudo cargar el equipo."}>
          <Button variant="secondary" size="small" onClick={team.reload}>
            Reintentar
          </Button>
        </Alert>
      </>
    );
  }

  const { members, invitations, myRole } = team.team;
  const owners = members.filter((member) => member.role === "owner").length;

  const run = async (key: string, action: () => Promise<unknown>) => {
    setBusy(key);
    setProblem(null);
    try {
      await action();
    } catch (reason) {
      setProblem(teamProblems(reason).message);
    } finally {
      setBusy(null);
    }
  };

  const renew = (invitation: Invitation) =>
    run(`renovar-${invitation.id}`, async () => setPending({ kind: "link", issued: await team.renew(invitation.id), renewed: true }));

  return (
    <>
      {header}
      {problem && <Alert tone="danger">{problem}</Alert>}

      <section className="team-section" aria-labelledby="miembros">
        <h2 id="miembros" className="team-section__title">
          Personas <span>{members.length}</span>
        </h2>
        <ul className="team-list">
          {members.map((member) => {
            const actions = memberActions(myRole, member, owners);
            const name = member.email ?? "Cuenta sin correo";
            return (
              <li key={member.userId} className="team-row">
                <Avatar name={name} />
                <div className="team-row__main">
                  <span className="team-row__name">
                    {name}
                    {member.me && <Badge tone="accent">Tú</Badge>}
                  </span>
                  <span className="team-row__meta">Desde el {joined(member.joinedAt)}</span>
                </div>
                {actions.changeRole ? (
                  <label className="team-row__role">
                    <span className="visually-hidden">Rol de {name}</span>
                    <select
                      className="select select--compact"
                      value={member.role}
                      disabled={busy !== null}
                      onChange={(event) => void run(`rol-${member.userId}`, () => team.changeRole(member.userId, event.target.value as Role))}
                    >
                      {(member.role === "owner" ? ROLES : assignableRoles(myRole)).map((role) => (
                        <option key={role} value={role}>
                          {ROLE_LABELS[role]}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : (
                  <span className="team-row__fixed" title={actions.reason}>
                    {ROLE_LABELS[member.role]}
                  </span>
                )}
                {actions.remove ? (
                  <Button variant="ghost" size="small" aria-label={`Quitar a ${name}`} disabled={busy !== null} onClick={() => setPending({ kind: "remove", member })}>
                    <Icon name="trash" size={14} />
                  </Button>
                ) : (
                  <span className="team-row__spacer" aria-hidden="true" />
                )}
              </li>
            );
          })}
        </ul>
      </section>

      <section className="team-section" aria-labelledby="invitaciones">
        <h2 id="invitaciones" className="team-section__title">
          Invitaciones sin usar <span>{invitations.length}</span>
        </h2>
        {invitations.length === 0 ? (
          <p className="team-section__empty">No hay invitaciones pendientes. Cuando invites a alguien, aparece aquí hasta que entre.</p>
        ) : (
          <ul className="team-list">
            {invitations.map((invitation) => (
              <li key={invitation.id} className="team-row">
                <span className="team-row__icon" aria-hidden="true">
                  <Icon name="mail" size={16} />
                </span>
                <div className="team-row__main">
                  <span className="team-row__name">{invitation.email}</span>
                  <span className={`team-row__meta${invitation.status === "expired" ? " team-row__meta--late" : ""}`}>
                    {ROLE_LABELS[invitation.role]} · {expiryText(invitation.expiresAt)} · invitó {invitation.invitedBy}
                  </span>
                </div>
                <Button variant="secondary" size="small" disabled={busy !== null} onClick={() => void renew(invitation)}>
                  {invitation.status === "expired" ? "Renovar" : "Nuevo enlace"}
                </Button>
                <Button variant="ghost" size="small" aria-label={`Retirar la invitación de ${invitation.email}`} disabled={busy !== null} onClick={() => setPending({ kind: "revoke", invitation })}>
                  <Icon name="trash" size={14} />
                </Button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="team-section" aria-labelledby="roles">
        <h2 id="roles" className="team-section__title">
          Qué puede cada rol
        </h2>
        <dl className="team-roles">
          {ROLES.map((role) => (
            <div key={role} className="team-roles__item">
              <dt>{ROLE_LABELS[role]}</dt>
              <dd>{ROLE_DESCRIPTIONS[role]}</dd>
            </div>
          ))}
        </dl>
      </section>

      {pending?.kind === "invite" && (
        <InviteDialog
          roles={assignableRoles(myRole)}
          onInvite={team.invite}
          onDone={(issued) => setPending({ kind: "link", issued, renewed: false })}
          onClose={() => setPending(null)}
        />
      )}
      {pending?.kind === "link" && <InvitationLinkDialog issued={pending.issued} businessName={businessName} renewed={pending.renewed} onClose={() => setPending(null)} />}
      {pending?.kind === "remove" && (
        <ConfirmDialog
          title={`¿Quitar a ${pending.member.email ?? "esta persona"} del equipo?`}
          text="Deja de entrar a este negocio al instante. Lo que hizo (respuestas, ventas registradas) se conserva. Puedes invitarla de nuevo cuando quieras."
          confirm="Sí, quitar"
          onConfirm={() => team.remove(pending.member.userId)}
          onClose={() => setPending(null)}
        />
      )}
      {pending?.kind === "revoke" && (
        <ConfirmDialog
          title={`¿Retirar la invitación de ${pending.invitation.email}?`}
          text="El enlace deja de servir. Si ya se lo enviaste, al abrirlo verá que se retiró."
          confirm="Sí, retirar"
          onConfirm={() => team.revoke(pending.invitation.id)}
          onClose={() => setPending(null)}
        />
      )}
    </>
  );
}

function ConfirmDialog({ title, text, confirm, onConfirm, onClose }: { title: string; text: string; confirm: string; onConfirm: () => Promise<unknown>; onClose: () => void }) {
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const go = async () => {
    setBusy(true);
    setProblem(null);
    try {
      await onConfirm();
      onClose();
    } catch (reason) {
      setProblem(teamProblems(reason).message);
      setBusy(false);
    }
  };
  return (
    <Dialog
      title={title}
      description={text}
      onClose={busy ? () => undefined : onClose}
      footer={
        <>
          <Button variant="ghost" disabled={busy} onClick={onClose}>
            Cancelar
          </Button>
          <Button variant="danger" className="button--danger-solid" disabled={busy} onClick={() => void go()}>
            {busy ? "Un momento…" : confirm}
          </Button>
        </>
      }
    >
      {problem && <Alert tone="danger">{problem}</Alert>}
    </Dialog>
  );
}
