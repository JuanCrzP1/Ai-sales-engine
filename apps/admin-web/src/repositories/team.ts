import type { Invitation, InvitationInput, IssuedInvitation, Role, TeamMember, TeamView } from "../domain/team/team";

export type { Invitation, InvitationInput, IssuedInvitation, Role, TeamMember, TeamView } from "../domain/team/team";

/**
 * El equipo de cada negocio y las invitaciones. Los fallos se rechazan con `PersistenceError`: por ejemplo, una regla rota
 * («debe quedar un dueño») llega con su motivo, y un problema de la invitación, en su campo (`email`, `role`).
 */
export interface Team {
  view(slug: string): Promise<TeamView>;
  invite(slug: string, input: InvitationInput): Promise<IssuedInvitation>;
  renew(slug: string, invitationId: string): Promise<IssuedInvitation>;
  revoke(slug: string, invitationId: string): Promise<void>;
  changeRole(slug: string, userId: string, role: Role): Promise<TeamMember>;
  remove(slug: string, userId: string): Promise<void>;
  /** Sin sesión: de qué negocio es. Rechaza con el motivo si el enlace no sirve. */
  preview(token: string): Promise<Invitation>;
  /** Con la cuenta del correo invitado. Devuelve el negocio al que entró. */
  accept(token: string): Promise<string>;
}
