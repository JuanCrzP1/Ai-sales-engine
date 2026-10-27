/** Reglas para la foto de perfil. */

export const AVATAR_ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"] as const;
export const AVATAR_MAX_BYTES = 5 * 1024 * 1024;
/** Lado (en píxeles) de la foto cuadrada que se guarda. */
export const AVATAR_OUTPUT_SIZE = 256;

export function validateAvatarFile(file: { type: string; size: number }): string | undefined {
  if (!(AVATAR_ACCEPTED_TYPES as readonly string[]).includes(file.type)) return "Usa una imagen JPG, PNG, WebP o GIF.";
  if (file.size > AVATAR_MAX_BYTES) return "La imagen pesa más de 5 MB. Elige una más liviana.";
  return undefined;
}
