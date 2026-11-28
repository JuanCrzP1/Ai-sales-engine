/**
 * Las etiquetas de los clientes: el catálogo del negocio y las que lleva cada cliente, como las valida el servidor
 * (`project/app/domain/business_config/customer_labels.py`).
 */

export type LabelColor = "slate" | "blue" | "violet" | "pink" | "red" | "amber" | "green" | "teal";
export const LABEL_COLORS: LabelColor[] = ["slate", "blue", "violet", "pink", "red", "amber", "green", "teal"];
export const LABEL_COLOR_NAMES: Record<LabelColor, string> = {
  slate: "Gris",
  blue: "Azul",
  violet: "Morado",
  pink: "Rosa",
  red: "Rojo",
  amber: "Amarillo",
  green: "Verde",
  teal: "Turquesa",
};
export const DEFAULT_LABEL_COLOR: LabelColor = "slate";
export const MAX_LABEL_NAME = 30;
export const MAX_LABELS_PER_CUSTOMER = 10;

/** Una etiqueta, como la lleva un cliente. */
export interface LabelRef {
  id: string;
  name: string;
  color: LabelColor;
}

/** Una etiqueta del catálogo, con cuántos clientes la tienen. */
export interface Label extends LabelRef {
  customers: number;
}

export interface LabelChange {
  name?: string;
  color?: LabelColor;
}

/** Un color que manda el servidor; uno desconocido se pinta gris. */
export function toLabelColor(value: unknown): LabelColor {
  return LABEL_COLORS.includes(value as LabelColor) ? (value as LabelColor) : DEFAULT_LABEL_COLOR;
}

/** Cómo se lee un nombre: sin mayúsculas, acentos, espacios de más ni caracteres invisibles. Dos que se leen igual son la misma. */
export function labelKey(name: string): string {
  return name
    .replace(/[​-‏‪-‮⁠-⁤﻿­]/g, "")
    .normalize("NFKD")
    .replace(/\p{M}/gu, "")
    .trim()
    .replace(/\s+/g, " ")
    .toLowerCase();
}

/** Por qué ese nombre no sirve para una etiqueta, o null. `exceptId`: la etiqueta que se está renombrando. */
export function nameProblem(name: string, existing: LabelRef[], exceptId?: string): string | null {
  const key = labelKey(name);
  if (!key) return "Escribe el nombre de la etiqueta.";
  if (name.trim().length > MAX_LABEL_NAME) return `El nombre es muy largo (máximo ${MAX_LABEL_NAME} caracteres).`;
  if (existing.some((label) => label.id !== exceptId && labelKey(label.name) === key)) return "Ya tienes una etiqueta con ese nombre.";
  return null;
}

/** La selección después de tocar una etiqueta: se quita si estaba y se agrega si no. */
export function toggled(selected: string[], id: string): string[] {
  return selected.includes(id) ? selected.filter((item) => item !== id) : [...selected, id];
}

/** Las que caben en una tarjeta y cuántas quedan por fuera («+2»). */
export function shownLabels<T>(labels: T[], max = 3): { shown: T[]; more: number } {
  return { shown: labels.slice(0, max), more: Math.max(0, labels.length - max) };
}
