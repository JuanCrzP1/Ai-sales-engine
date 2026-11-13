/**
 * Los archivos que el equipo envía desde el chat: los mismos tipos y el mismo tope que el servidor
 * (`domain/business_config/conversations.py`, que es quien decide). Aquí sirven para avisar antes de subir algo que no va a salir.
 */
import type { MessageKind } from "./types";

/** El tope del servidor (en Vercel, una petición no puede pasar de 4,5 MB). */
export const MAX_ATTACHMENT_BYTES = 4 * 1024 * 1024;
export const MAX_CAPTION = 1024;

const KINDS: Record<string, MessageKind> = {
  "image/jpeg": "image",
  "image/png": "image",
  "image/webp": "image",
  "video/mp4": "video",
  "audio/mpeg": "audio",
  "audio/ogg": "audio",
  "audio/mp4": "audio",
  "application/pdf": "document",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "document",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "document",
  "application/vnd.openxmlformats-officedocument.presentationml.presentation": "document",
  "application/msword": "document",
  "application/vnd.ms-excel": "document",
  "text/plain": "document",
  "text/csv": "document",
};

/** Para el selector de archivos: los tipos que se pueden enviar. */
export const ATTACHMENT_ACCEPT = Object.keys(KINDS).join(",");

export const ATTACHMENT_HINT = "Fotos (JPG, PNG, WebP), PDF, Word, Excel, PowerPoint, texto, videos MP4 y audios (MP3, OGG, M4A), de hasta 4 MB.";

export function attachmentKind(mimeType: string): MessageKind | null {
  return KINDS[mimeType.split(";")[0]!.trim().toLowerCase()] ?? null;
}

/** Por qué no se puede enviar este archivo, o null si se puede. */
export function attachmentProblem(file: { size: number; type: string }): string | null {
  if (file.size === 0) return "El archivo está vacío.";
  if (!attachmentKind(file.type)) return `Ese tipo de archivo no se puede enviar. Se pueden: ${ATTACHMENT_HINT}`;
  if (file.size > MAX_ATTACHMENT_BYTES) return "El archivo pesa más de 4 MB. Envía uno más liviano (o comprime la foto).";
  return null;
}

/** «2,3 MB», «512 KB». */
export function formatBytes(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toLocaleString("es-CO", { maximumFractionDigits: 1 })} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}
