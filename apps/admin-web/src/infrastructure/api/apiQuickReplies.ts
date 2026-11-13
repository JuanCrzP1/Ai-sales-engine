import type { QuickReplies, QuickReply, QuickReplyFile, QuickReplyInput, QuickReplyPiece } from "../../repositories/quickReplies";
import type { HttpClient } from "./httpClient";

interface QuickReplyPayload {
  id: string;
  shortcut: string;
  category: string | null;
  pieces: PiecePayload[];
  use_count: number;
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
}

interface FilePayload {
  file_id: string;
  file_name: string | null;
  mime_type: string;
  size_bytes: number;
}

type PiecePayload = { kind: "text"; text: string } | ({ kind: "file"; text: string } & FilePayload);

const toFile = (payload: FilePayload): QuickReplyFile => ({ fileId: payload.file_id, fileName: payload.file_name, mimeType: payload.mime_type, sizeBytes: payload.size_bytes });

function toPiece(piece: PiecePayload): QuickReplyPiece | null {
  if (piece.kind === "text") return { kind: "text", text: piece.text };
  if (piece.kind === "file") return { kind: "file", text: piece.text ?? "", ...toFile(piece) };
  return null;
}

function toReply(payload: QuickReplyPayload): QuickReply {
  return {
    id: payload.id,
    shortcut: payload.shortcut,
    category: payload.category,
    pieces: payload.pieces.map(toPiece).filter((piece): piece is QuickReplyPiece => piece !== null),
    useCount: payload.use_count,
    lastUsedAt: payload.last_used_at,
    createdAt: payload.created_at,
    updatedAt: payload.updated_at,
  };
}

/** Lo que se envía al guardar, con los nombres de la API (los problemas por campo vuelven con estas rutas). */
export function quickReplyBody(input: QuickReplyInput) {
  return {
    shortcut: input.shortcut,
    category: input.category?.trim() || null,
    pieces: input.pieces.map((piece) => (piece.kind === "file" ? { kind: "file", file_id: piece.fileId, text: piece.text } : { kind: "text", text: piece.text })),
  };
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
    uploadFile: async (file) => toFile(await http.upload<FilePayload>(`${base}/files`, file, { "X-File-Name": encodeURIComponent(file.name) })),
    file: (fileId) => http.blob(`${base}/files/${encodeURIComponent(fileId)}`),
  };
}
