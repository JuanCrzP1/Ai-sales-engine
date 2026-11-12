/**
 * Lo que cambia al publicar: la diferencia entre lo publicado (lo que responde hoy a los clientes) y la versión guardada que se
 * va a publicar, en el idioma del negocio. Compara contenido, no números de versión: guardar sin tocar nada no deja cambios.
 *
 * Los datos de pago van en el documento solo como referencias (`secret_ref`), con un sufijo que cambia cuando cambia el valor:
 * se informan como «dato protegido actualizado» y nunca se muestra su valor.
 */
import { sectionForPath, type ConfigSectionId } from "../sections";
import type { BusinessDocument } from "./types";

export type ChangeKind = "added" | "removed" | "changed";

export interface DocumentChange {
  section: ConfigSectionId;
  /** Dónde: «Marca», «Preguntas frecuentes › «¿Hay permanencia?» › Respuesta». */
  label: string;
  kind: ChangeKind;
  /** Cómo estaba y cómo queda, en texto corto. null cuando no aplica o es un dato protegido. */
  before: string | null;
  after: string | null;
  /** Un dato de pago: cambió, pero su valor no se muestra. */
  protectedValue?: boolean;
}

/** El nombre de un campo por su ruta (solo claves, sin índices). Lo da el esquema del contrato. */
export type FieldNamer = (keys: string[]) => string;

const MAX_TEXT = 90;
/** Claves que no son del negocio: no cuentan como cambio. */
const IGNORED_ROOTS = new Set(["schema_version", "tenant_slug"]);

type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

function isObject(value: unknown): value is Record<string, Json> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/** Sin vacíos: null, undefined, "" y listas vacías cuentan como «sin valor», igual que al guardar. */
function present(value: unknown): boolean {
  if (value === null || value === undefined) return false;
  if (typeof value === "string") return value.trim() !== "";
  if (Array.isArray(value)) return value.length > 0;
  if (isObject(value)) return Object.values(value).some(present);
  return true;
}

function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (isObject(value)) {
    const keys = Object.keys(value).filter((key) => present(value[key])).sort();
    return `{${keys.map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(present(value) ? value : null);
}

function same(a: unknown, b: unknown): boolean {
  return canonical(a) === canonical(b);
}

function shorten(text: string): string {
  const clean = text.replace(/\s+/g, " ").trim();
  return clean.length > MAX_TEXT ? `${clean.slice(0, MAX_TEXT - 1)}…` : clean;
}

/** El título de un elemento de una lista: su pregunta, su nombre, su tema... */
function itemTitle(item: unknown): string | null {
  if (!isObject(item)) return null;
  for (const key of ["name", "question", "topic", "title", "label", "motivation", "when", "text", "bank", "type", "id"]) {
    const value = item[key];
    if (typeof value === "string" && value.trim()) return shorten(value);
  }
  return null;
}

function itemKey(item: unknown, index: number): string {
  if (isObject(item)) {
    for (const key of ["id", "question", "name", "topic"]) {
      const value = item[key];
      if (typeof value === "string" && value.trim()) return `${key}:${value.trim().toLowerCase()}`;
    }
  }
  return `#${index}`;
}

function display(value: unknown): string | null {
  if (!present(value)) return null;
  if (typeof value === "boolean") return value ? "Sí" : "No";
  if (typeof value === "number") return value.toLocaleString("es-CO");
  if (typeof value === "string") return shorten(value);
  if (Array.isArray(value) && value.every((item) => typeof item !== "object" || item === null)) return shorten(value.map(String).join(", "));
  if (Array.isArray(value)) return value.length === 1 ? "1 elemento" : `${value.length} elementos`;
  const title = itemTitle(value);
  return title ?? null;
}

function isSecret(value: unknown): boolean {
  return isObject(value) && typeof value.secret_ref === "string";
}

interface Walk {
  /** Ruta del documento con índices (para la sección). */
  path: string[];
  /** Solo claves, para nombrar el campo. */
  keys: string[];
  /** Lo que se lee en pantalla: campo, «elemento», campo. */
  crumbs: string[];
}

/**
 * Los cambios entre lo publicado y la versión que se va a publicar. Sin nada publicado, devuelve [] (todo es nuevo: lo dice la
 * pantalla). `name` da el nombre de cada campo; los elementos de una lista se nombran por su título.
 */
export function documentChanges(published: BusinessDocument | null, draft: BusinessDocument, name: FieldNamer): DocumentChange[] {
  if (!published) return [];
  const changes: DocumentChange[] = [];

  const push = (at: Walk, kind: ChangeKind, before: unknown, after: unknown) => {
    const protectedValue = isSecret(before) || isSecret(after);
    changes.push({
      section: sectionForPath(at.path.join(".")),
      // El primer nivel (identity, knowledge...) ya lo dice la sección en la que se muestra.
      label: (at.crumbs.length > 1 ? at.crumbs.slice(1) : at.crumbs).join(" › "),
      kind,
      before: protectedValue ? null : display(before),
      after: protectedValue ? null : display(after),
      ...(protectedValue ? { protectedValue } : {}),
    });
  };

  const field = (at: Walk, key: string): Walk => {
    const keys = [...at.keys, key];
    return { path: [...at.path, key], keys, crumbs: [...at.crumbs, name(keys)] };
  };

  const walk = (before: unknown, after: unknown, at: Walk) => {
    if (same(before, after)) return;
    const had = present(before);
    const has = present(after);
    if (isSecret(before) || isSecret(after) || (!isObject(before) && !isObject(after) && !Array.isArray(before) && !Array.isArray(after))) {
      push(at, had && has ? "changed" : has ? "added" : "removed", before, after);
      return;
    }
    if ((isObject(before) || !had) && (isObject(after) || !has) && (isObject(before) || isObject(after))) {
      const a = isObject(before) ? before : {};
      const b = isObject(after) ? after : {};
      for (const key of [...new Set([...Object.keys(b), ...Object.keys(a)])]) {
        if (at.path.length === 0 && IGNORED_ROOTS.has(key)) continue;
        walk(a[key], b[key], field(at, key));
      }
      return;
    }
    const listA = Array.isArray(before) ? before : [];
    const listB = Array.isArray(after) ? after : [];
    const objects = [...listA, ...listB].some(isObject);
    if (!objects) {
      push(at, had && has ? "changed" : has ? "added" : "removed", before, after);
      return;
    }
    // Lista de elementos: se emparejan por su id (o su pregunta, su nombre...), para decir qué se agregó, quitó o cambió.
    const keyed = (list: Json[]) => new Map(list.map((item, index) => [itemKey(item, index), item] as const));
    const mapA = keyed(listA as Json[]);
    const mapB = keyed(listB as Json[]);
    for (const [key, item] of mapB) {
      const crumb = itemTitle(item) ?? `Elemento ${[...mapB.keys()].indexOf(key) + 1}`;
      const inside: Walk = { path: [...at.path, "0"], keys: at.keys, crumbs: [...at.crumbs, `«${crumb}»`] };
      if (!mapA.has(key)) push({ ...inside, crumbs: at.crumbs.concat(`«${crumb}»`) }, "added", null, item);
      else walk(mapA.get(key), item, inside);
    }
    for (const [key, item] of mapA) {
      if (mapB.has(key)) continue;
      const crumb = itemTitle(item) ?? "Elemento";
      push({ path: [...at.path, "0"], keys: at.keys, crumbs: [...at.crumbs, `«${crumb}»`] }, "removed", item, null);
    }
  };

  walk(published, draft, { path: [], keys: [], crumbs: [] });
  return changes;
}

/** Si lo guardado es distinto de lo publicado (mismo criterio que `documentChanges`). */
export function differsFromPublished(published: BusinessDocument, draft: BusinessDocument): boolean {
  const strip = (document: BusinessDocument) => Object.fromEntries(Object.entries(document).filter(([key]) => !IGNORED_ROOTS.has(key)));
  return !same(strip(published), strip(draft));
}
