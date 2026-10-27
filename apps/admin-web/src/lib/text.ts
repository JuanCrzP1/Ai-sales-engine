/** Utilidades de texto puras, sin conocimiento del dominio ni de React. */

export function countWords(text: string): number {
  const trimmed = text.trim();
  return trimmed ? trimmed.split(/\s+/).length : 0;
}

/** Elimina vacíos y espacios sobrantes de una lista de textos. */
export function cleanList(items: string[]): string[] {
  return items.map((item) => item.trim()).filter(Boolean);
}

/** Hasta dos iniciales en mayúscula: "Café Aroma" → "CA". */
export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase() ?? "")
    .join("");
}

export function firstName(name: string): string {
  return name.trim().split(/\s+/)[0] ?? "";
}
