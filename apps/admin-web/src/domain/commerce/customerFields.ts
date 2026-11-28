/**
 * Los campos del cliente: los datos propios que el negocio guarda de cada cliente («Ciudad», «Cumpleaños», «Tipo de cliente»), como
 * los valida el servidor (`project/app/domain/business_config/customer_fields.py`). El valor llega en su forma única: el número sin
 * separadores («1500000»), la fecha como «2026-11-29», el sí o no como `true`/`false` y la opción tal como está en el campo.
 */
import { labelKey } from "./labels";

export type FieldKind = "text" | "number" | "date" | "yes_no" | "choice";
export const FIELD_KINDS: FieldKind[] = ["text", "number", "date", "yes_no", "choice"];
export const FIELD_KIND_LABELS: Record<FieldKind, string> = {
  text: "Texto",
  number: "Número",
  date: "Fecha",
  yes_no: "Sí o no",
  choice: "Lista de opciones",
};
export const FIELD_KIND_HINTS: Record<FieldKind, string> = {
  text: "Una dirección, una referencia, lo que sea.",
  number: "Un presupuesto, una cantidad, una talla.",
  date: "Un cumpleaños, una fecha de entrega.",
  yes_no: "¿Tiene crédito? ¿Ya visitó la tienda?",
  choice: "Una de varias opciones que tú defines.",
};
export const MAX_FIELDS = 30;
export const MAX_FIELD_NAME = 40;
export const MIN_OPTIONS = 2;
export const MAX_OPTIONS = 30;
export const MAX_OPTION = 40;
export const MAX_TEXT_VALUE = 200;

/** Un campo del catálogo, con cuántos clientes lo tienen lleno. */
export interface CustomerField {
  id: string;
  name: string;
  kind: FieldKind;
  options: string[];
  filled: number;
}

export type FieldRawValue = string | boolean | null;

/** Un campo en la ficha de un cliente: su valor (null si está vacío) y quién lo puso y cuándo. */
export interface FieldValue {
  field: CustomerField;
  value: FieldRawValue;
  updatedBy: string | null;
  updatedAt: string | null;
}

export interface NewFieldInput {
  name: string;
  kind: FieldKind;
  options?: string[];
}

export interface FieldChange {
  name?: string;
  options?: string[];
}

/** Un tipo que manda el servidor; uno desconocido se trata como texto. */
export function toFieldKind(value: unknown): FieldKind {
  return FIELD_KINDS.includes(value as FieldKind) ? (value as FieldKind) : "text";
}

/** Por qué ese nombre no sirve para un campo, o null. `exceptId`: el campo que se está renombrando. */
export function fieldNameProblem(name: string, existing: { id: string; name: string }[], exceptId?: string): string | null {
  const key = labelKey(name);
  if (!key) return "Escribe el nombre del campo.";
  if (name.trim().length > MAX_FIELD_NAME) return `El nombre es muy largo (máximo ${MAX_FIELD_NAME} caracteres).`;
  if (existing.some((item) => item.id !== exceptId && labelKey(item.name) === key)) return "Ya tienes un campo con ese nombre.";
  return null;
}

/** Las opciones escritas una por línea, sin vacías. */
export function optionsFromText(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim().replace(/\s+/g, " "))
    .filter(Boolean);
}

/** Por qué esas opciones no sirven para una lista, o null. */
export function optionsProblem(options: string[]): string | null {
  const seen = new Set<string>();
  for (const option of options) {
    if (option.length > MAX_OPTION) return `«${option.slice(0, 20)}…» es muy larga (máximo ${MAX_OPTION} caracteres por opción).`;
    if (seen.has(labelKey(option))) return `«${option}» está repetida.`;
    seen.add(labelKey(option));
  }
  if (options.length < MIN_OPTIONS) return `Una lista necesita al menos ${MIN_OPTIONS} opciones, una por línea.`;
  if (options.length > MAX_OPTIONS) return `Una lista puede tener hasta ${MAX_OPTIONS} opciones.`;
  return null;
}

/** Las opciones que se quitarían al guardar (las que ya no están, ni escritas de otra forma). */
export function removedOptions(before: string[], after: string[]): string[] {
  const kept = new Set(after.map(labelKey));
  return before.filter((option) => !kept.has(labelKey(option)));
}

const numberFormat = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 4 });
const dateFormat = new Intl.DateTimeFormat("es-CO", { day: "numeric", month: "short", year: "numeric" });

/** Una fecha «2026-11-29» como día del calendario (sin correrse por la zona horaria). */
export function calendarDate(value: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  return match ? new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3])) : null;
}

/** El valor como se lee en la ficha: «1.500.000», «29 nov 2026», «Sí». Vacío: null. */
export function valueText(kind: FieldKind, value: FieldRawValue): string | null {
  if (value === null || value === "") return null;
  if (kind === "yes_no") return value === true || value === "true" ? "Sí" : "No";
  const text = String(value);
  if (kind === "number" && Number.isFinite(Number(text))) return numberFormat.format(Number(text));
  if (kind === "date") {
    const day = calendarDate(text);
    return day ? dateFormat.format(day).replace(/\./g, "").replace(/ de /g, " ") : text;
  }
  return text;
}

/** El valor como lo muestra el campo de edición: el número con coma decimal, como se escribe en Colombia. */
export function inputValue(kind: FieldKind, value: FieldRawValue): string {
  if (value === null) return "";
  if (kind === "yes_no") return value === true || value === "true" ? "true" : "false";
  return kind === "number" ? String(value).replace(".", ",") : String(value);
}
