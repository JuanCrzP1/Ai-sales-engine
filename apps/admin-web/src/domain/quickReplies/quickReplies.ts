/**
 * Respuestas rápidas: mensajes guardados del negocio que el equipo pone en un chat sin copiar y pegar. Cada una tiene un atajo
 * («precios», se busca escribiendo «/precios»), una categoría opcional y de uno a diez mensajes que salen en orden: textos o archivos
 * (una foto, un PDF...) con un texto opcional. En los textos, `{nombre}` se cambia por el primer nombre del cliente. Las reglas del
 * servidor están en `domain/business_config/quick_replies.py`.
 */

export interface QuickReplyFile {
  fileId: string;
  fileName: string | null;
  mimeType: string;
  sizeBytes: number;
}

/** Un mensaje: un texto, o un archivo guardado con su texto opcional (`text`). */
export type QuickReplyPiece = { kind: "text"; text: string } | ({ kind: "file"; text: string } & QuickReplyFile);

export interface QuickReply {
  id: string;
  shortcut: string;
  /** «Precios», «Pagos»…; `null`: sin categoría. */
  category: string | null;
  pieces: QuickReplyPiece[];
  /** Veces que el equipo la usó: las más usadas salen primero. */
  useCount: number;
  lastUsedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

/** Lo que se escribe al crearla o editarla. */
export interface QuickReplyInput {
  shortcut: string;
  category: string | null;
  pieces: QuickReplyPiece[];
}

export interface QuickReplyList {
  replies: QuickReply[];
  /** Quien mira puede crearlas, editarlas y borrarlas (hoy, el dueño del negocio). */
  canManage: boolean;
}

export const MAX_PIECES = 10;
export const MAX_TEXT = 4000;
/** El texto que acompaña un archivo (el mismo tope que al enviarlo desde el chat). */
export const MAX_FILE_CAPTION = 1024;
export const MAX_SHORTCUT = 40;
export const MAX_CATEGORY = 40;
export const UNCATEGORIZED = "Sin categoría";
export const NAME_PLACEHOLDER = "{nombre}";
/** Minúsculas sin tildes, números, espacios, guiones y guiones bajos: lo mismo que acepta el servidor. */
export const SHORTCUT_PATTERN = /^[a-z0-9_-][a-z0-9 _-]{0,39}$/;

/** El atajo como se guarda: «/Saludo Inicial » → «saludo inicial»; «Crédito» → «credito». */
export function normalizeShortcut(value: string): string {
  return value
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .toLowerCase()
    .trim()
    .replace(/^[#/]+/, "")
    .replace(/\s+/g, " ")
    .trim();
}

/** Cómo se nombra un archivo en una línea: «📎 Catálogo.pdf». */
export function fileLabel(file: Pick<QuickReplyFile, "fileName" | "mimeType">): string {
  const name = file.fileName ?? (file.mimeType.startsWith("image/") ? "Foto" : file.mimeType.startsWith("video/") ? "Video" : file.mimeType.startsWith("audio/") ? "Audio" : "Documento");
  return `📎 ${name}`;
}

/** Lo que tiene cada respuesta, en una línea: los mensajes separados por «·» (los archivos, con su nombre). */
export function replySummary(reply: Pick<QuickReply, "pieces">): string {
  return reply.pieces
    .map((piece) => {
      const text = piece.text.replace(/\s+/g, " ").trim();
      return piece.kind === "file" ? [fileLabel(piece), text].filter(Boolean).join(" ") : text;
    })
    .join(" · ");
}

/** Si la respuesta lleva algún archivo (en el chat, todo queda en espera y sale en orden). */
export function hasFiles(reply: Pick<QuickReply, "pieces">): boolean {
  return reply.pieces.some((piece) => piece.kind === "file");
}

/** Las que coinciden con lo buscado: primero las que empiezan por el atajo, luego por categoría o texto. Sin tildes ni mayúsculas. */
export function matchQuickReplies(replies: QuickReply[], query: string): QuickReply[] {
  const needle = normalizeShortcut(query);
  if (!needle) return [...replies];
  const starts = replies.filter((reply) => reply.shortcut.startsWith(needle));
  const contains = replies.filter(
    (reply) =>
      !reply.shortcut.startsWith(needle) &&
      (reply.shortcut.includes(needle) || normalizeShortcut(reply.category ?? "").includes(needle) || normalizeShortcut(replySummary(reply)).includes(needle)),
  );
  return [...starts, ...contains];
}

export interface QuickReplyGroup {
  category: string;
  replies: QuickReply[];
}

/** Por categoría, en orden alfabético y con «Sin categoría» al final; dentro de cada una se respeta el orden recibido. */
export function groupByCategory(replies: QuickReply[]): QuickReplyGroup[] {
  const groups = new Map<string, QuickReply[]>();
  for (const reply of replies) {
    const category = reply.category ?? UNCATEGORIZED;
    groups.set(category, [...(groups.get(category) ?? []), reply]);
  }
  return [...groups.entries()]
    .sort(([a], [b]) => (a === UNCATEGORIZED ? 1 : b === UNCATEGORIZED ? -1 : a.localeCompare(b, "es")))
    .map(([category, list]) => ({ category, replies: list }));
}

/** Las categorías que ya usa el negocio, para sugerirlas al escribir. */
export function categoriesOf(replies: QuickReply[]): string[] {
  return [...new Set(replies.map((reply) => reply.category).filter((category): category is string => Boolean(category)))].sort((a, b) => a.localeCompare(b, "es"));
}

/** Un atajo libre para una copia: «saludo» → «saludo-copia», «saludo-copia-2»… */
export function copyShortcut(shortcut: string, taken: string[]): string {
  const base = `${shortcut}-copia`.slice(0, MAX_SHORTCUT - 6);
  if (!taken.includes(base)) return base;
  let index = 2;
  while (taken.includes(`${base}-${index}`)) index += 1;
  return `${base}-${index}`;
}

/** El primer nombre del cliente: «maría fernanda gómez» → «María». Sin nombre, vacío. */
export function firstName(name: string | null | undefined): string {
  const word = (name ?? "").trim().split(/\s+/)[0] ?? "";
  return word ? word.charAt(0).toUpperCase() + word.slice(1).toLowerCase() : "";
}

/** Cambia `{nombre}` por el primer nombre del cliente. Sin nombre, lo quita junto con el espacio de antes («Hola {nombre},» → «Hola,»). */
export function fillName(text: string, name: string | null | undefined): string {
  const value = firstName(name);
  return value ? text.split(NAME_PLACEHOLDER).join(value) : text.replace(/[ \t]*\{nombre\}/g, "");
}

/** La búsqueda que se escribe en el chat: «/prec» → «prec». Solo cuenta si el mensaje empieza por «/» y aún no tiene un salto de línea. */
export function slashQuery(draft: string): string | null {
  const match = /^\/([^\n]*)$/.exec(draft);
  return match ? (match[1] ?? "") : null;
}
