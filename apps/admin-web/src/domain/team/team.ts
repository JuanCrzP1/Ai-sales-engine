/**
 * El equipo de un negocio: Dueño, Administrador y Asesor. La misma tabla que el servidor (`domain/business_config/team.py`), que es
 * quien decide de verdad: aquí solo sirve para mostrar a cada persona lo que puede usar y para explicar por qué no.
 */

export type Role = "owner" | "admin" | "agent";
export type Capability = "attend" | "reports" | "configure" | "team" | "deleteBusiness";

export const ROLES: Role[] = ["owner", "admin", "agent"];

export const ROLE_LABELS: Record<Role, string> = { owner: "Dueño", admin: "Administrador", agent: "Asesor" };

export const ROLE_DESCRIPTIONS: Record<Role, string> = {
  owner: "Todo, incluido eliminar el negocio y nombrar otros dueños.",
  admin: "Todo menos eliminar el negocio y tocar a los dueños: configura el asistente, la IA, los canales y el equipo.",
  agent: "Atiende: chats, clientes, registrar ventas y usar las respuestas rápidas. No ve la configuración ni los reportes.",
};

const CAPABILITIES: Record<Role, Capability[]> = {
  owner: ["attend", "reports", "configure", "team", "deleteBusiness"],
  admin: ["attend", "reports", "configure", "team"],
  agent: ["attend"],
};

export function can(role: Role | null | undefined, capability: Capability): boolean {
  return Boolean(role) && CAPABILITIES[role!].includes(capability);
}

/** Lo que el servidor manda; un valor desconocido se trata como el rol con menos permisos. */
export function toRole(value: unknown): Role {
  return value === "owner" || value === "admin" || value === "agent" ? value : "agent";
}

/** Los roles que alguien puede dar al invitar o cambiar un rol: solo un dueño nombra dueños. */
export function assignableRoles(actor: Role): Role[] {
  return actor === "owner" ? ROLES : ROLES.filter((role) => role !== "owner");
}

export interface TeamMember {
  userId: string;
  email: string | null;
  role: Role;
  joinedAt: string;
  /** Es quien mira. */
  me: boolean;
}

export type InvitationStatus = "pending" | "accepted" | "revoked" | "expired";

export interface Invitation {
  id: string;
  business: string;
  businessName: string;
  email: string;
  role: Role;
  invitedBy: string;
  createdAt: string;
  expiresAt: string;
  status: InvitationStatus;
}

/** Una invitación recién creada o renovada: su enlace solo viaja esta vez. */
export interface IssuedInvitation extends Invitation {
  token: string;
}

export interface TeamView {
  members: TeamMember[];
  invitations: Invitation[];
  myRole: Role;
}

export interface InvitationInput {
  email: string;
  role: Role;
}

/** Ruta de la página donde se acepta una invitación (fuera de cualquier negocio: quien la abre aún no está en él). */
export const INVITATION_BASE = "/invitacion";

export function invitationPath(token: string): string {
  return `${INVITATION_BASE}/${encodeURIComponent(token)}`;
}

/** El enlace completo para compartir. */
export function invitationUrl(origin: string, token: string): string {
  return `${origin.replace(/\/+$/, "")}${invitationPath(token)}`;
}

/** Un mensaje listo para mandar por WhatsApp con el enlace. */
export function invitationMessage(businessName: string, role: Role, url: string): string {
  return `Te invito a ${businessName} en AI Sales Engine como ${ROLE_LABELS[role]}. Entra con este enlace (vence en 7 días): ${url}`;
}

/** Lo que el dueño o el administrador puede hacer con alguien del equipo, y por qué no cuando no puede (como el servidor). */
export function memberActions(actor: Role, member: TeamMember, owners: number): { changeRole: boolean; remove: boolean; reason?: string } {
  if (member.me) return { changeRole: false, remove: false, reason: "Eres tú." };
  if (member.role === "owner" && actor !== "owner") return { changeRole: false, remove: false, reason: "Solo un dueño toca a otro dueño." };
  if (member.role === "owner" && owners <= 1) return { changeRole: false, remove: false, reason: "Es el único dueño." };
  return { changeRole: true, remove: true };
}

/** «vence en 3 días», «vence hoy», «venció». */
export function expiryText(expiresAt: string, now: Date = new Date()): string {
  const left = new Date(expiresAt).getTime() - now.getTime();
  if (left <= 0) return "Venció";
  const days = Math.floor(left / 86_400_000);
  if (days === 0) return "Vence hoy";
  return days === 1 ? "Vence mañana" : `Vence en ${days} días`;
}
