import { AVATAR_OUTPUT_SIZE, validateAvatarFile } from "../../domain/auth/avatarRules";

export class AvatarImageError extends Error {}

/**
 * Convierte la imagen elegida en una foto cuadrada (recorte centrado) de
 * AVATAR_OUTPUT_SIZE píxeles, como data URL JPEG liviana para guardar.
 */
export async function fileToAvatarDataUrl(file: File, size = AVATAR_OUTPUT_SIZE): Promise<string> {
  const problem = validateAvatarFile(file);
  if (problem) throw new AvatarImageError(problem);

  const image = await loadImage(file);
  const side = Math.min(image.width, image.height);
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext("2d");
  if (!context) throw new AvatarImageError("Tu navegador no pudo procesar la imagen.");

  context.imageSmoothingQuality = "high";
  context.drawImage(image, (image.width - side) / 2, (image.height - side) / 2, side, side, 0, 0, size, size);
  return canvas.toDataURL("image/jpeg", 0.88);
}

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => {
      URL.revokeObjectURL(url);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new AvatarImageError("No se pudo leer la imagen. Prueba con otro archivo."));
    };
    image.src = url;
  });
}
