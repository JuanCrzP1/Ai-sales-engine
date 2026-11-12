import type { QuickReplies, QuickReply, QuickReplyInput } from "../../repositories/quickReplies";
import type { HttpClient } from "./httpClient";

interface QuickReplyPayload {
  id: string;
  shortcut: string;
  category: string | null;
  pieces: { kind: "text"; text: string }[];
  use_count: number;
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
}

function toReply(payload: QuickReplyPayload): QuickReply {
  return {
    id: payload.id,
    shortcut: payload.shortcut,
    category: payload.category,
    pieces: payload.pieces.filter((piece) => piece.kind === "text").map((piece) => ({ kind: "text", text: piece.text })),
    useCount: payload.use_count,
    lastUsedAt: payload.last_used_at,
    createdAt: payload.created_at,
    updatedAt: payload.updated_at,
  };
}

/** Lo que se envía al guardar, con los nombres de la API (los problemas por campo vuelven con estas rutas). */
export function quickReplyBody(input: QuickReplyInput) {
  return { shortcut: input.shortcut, category: input.category?.trim() || null, pieces: input.pieces.map((piece) => ({ kind: "text", text: piece.text })) };
}

/** `QuickReplies` sobre la API del panel: `/api/businesses/{slug}/quick-replies`. */
export function createApiQuickReplies(http: HttpClient, slug: string): QuickReplies {
  const base = `/businesses/${encodeURIComponent(slug)}/quick-replies`;
  const one = (id: string) => `${base}/${encodeURIComponent(id)}`;
  return {
    list: async () => {
      const payload = await http.get<{ quick_replies: QuickReplyPayload[]; can_manage: boolean }>(base);
      return { replies: payload.quick_replies.map(toReply), canManage: payload.can_manage };
    },
    create: async (input) => toReply(await http.post<QuickReplyPayload>(base, quickReplyBody(input))),
    update: async (id, input) => toReply(await http.put<QuickReplyPayload>(one(id), quickReplyBody(input))),
    remove: (id) => http.delete(one(id)),
    markUsed: async (id) => toReply(await http.post<QuickReplyPayload>(`${one(id)}/use`)),
  };
}
