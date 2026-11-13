import { toRole, type Invitation, type InvitationStatus, type IssuedInvitation } from "../../domain/team/team";
import type { Team } from "../../repositories/team";
import type { HttpClient } from "./httpClient";

interface InvitationPayload {
  id: string;
  business: string;
  business_name: string;
  email: string;
  role: string;
  invited_by: string;
  created_at: string;
  expires_at: string;
  status: InvitationStatus;
  token?: string;
}

interface MemberPayload {
  user_id: string;
  email: string | null;
  role: string;
  joined_at: string;
  me: boolean;
}

const toInvitation = (payload: InvitationPayload): Invitation => ({
  id: payload.id,
  business: payload.business,
  businessName: payload.business_name,
  email: payload.email,
  role: toRole(payload.role),
  invitedBy: payload.invited_by,
  createdAt: payload.created_at,
  expiresAt: payload.expires_at,
  status: payload.status,
});

const toIssued = (payload: InvitationPayload): IssuedInvitation => ({ ...toInvitation(payload), token: payload.token ?? "" });

const toMember = (payload: MemberPayload) => ({ userId: payload.user_id, email: payload.email, role: toRole(payload.role), joinedAt: payload.joined_at, me: payload.me });

/** `Team` sobre la API del panel: `/api/businesses/{slug}/team` y `/api/invitations/{token}`. */
export function createApiTeam(http: HttpClient): Team {
  const base = (slug: string) => `/businesses/${encodeURIComponent(slug)}/team`;
  return {
    view: async (slug) => {
      const payload = await http.get<{ members: MemberPayload[]; invitations: InvitationPayload[]; my_role: string }>(base(slug));
      return { members: payload.members.map(toMember), invitations: payload.invitations.map(toInvitation), myRole: toRole(payload.my_role) };
    },
    invite: async (slug, input) => toIssued(await http.post<InvitationPayload>(`${base(slug)}/invitations`, { email: input.email, role: input.role })),
    renew: async (slug, id) => toIssued(await http.post<InvitationPayload>(`${base(slug)}/invitations/${encodeURIComponent(id)}/renew`)),
    revoke: (slug, id) => http.delete(`${base(slug)}/invitations/${encodeURIComponent(id)}`),
    changeRole: async (slug, userId, role) => toMember(await http.put<MemberPayload>(`${base(slug)}/members/${encodeURIComponent(userId)}`, { role })),
    remove: (slug, userId) => http.delete(`${base(slug)}/members/${encodeURIComponent(userId)}`),
    preview: async (token) => toInvitation(await http.get<InvitationPayload>(`/invitations/${encodeURIComponent(token)}`)),
    accept: async (token) => (await http.post<{ business: string }>(`/invitations/${encodeURIComponent(token)}/accept`)).business,
  };
}
