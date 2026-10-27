import { CONFIG_SECTIONS, type ConfigSectionId } from "../domain/sections";

export interface NavItem {
  key: "home" | ConfigSectionId | "review";
  path: string;
  title: string;
  section?: ConfigSectionId;
}

const SECTION_PATHS: Record<ConfigSectionId, string> = {
  business: "/negocio",
  catalog: "/productos",
  payments: "/pagos",
  assistant: "/atencion",
  messages: "/mensajes",
};

export const HOME_ITEM: NavItem = { key: "home", path: "/", title: "Inicio" };
export const REVIEW_ITEM: NavItem = { key: "review", path: "/revision", title: "Revisión" };

export const SECTION_ITEMS: NavItem[] = CONFIG_SECTIONS.map((section) => ({
  key: section.id,
  path: SECTION_PATHS[section.id],
  title: section.title,
  section: section.id,
}));

/** Orden del recorrido guiado: inicio, secciones y revisión. */
export const FLOW_ITEMS: NavItem[] = [HOME_ITEM, ...SECTION_ITEMS, REVIEW_ITEM];

export function sectionPath(id: ConfigSectionId): string {
  return SECTION_PATHS[id];
}

/** Etiqueta del paso en el recorrido: "Paso N" para las secciones y "Último paso" para la revisión. */
export function stepLabel(key: NavItem["key"]): string {
  if (key === REVIEW_ITEM.key) return "Último paso";
  const index = SECTION_ITEMS.findIndex((item) => item.key === key);
  return index >= 0 ? `Paso ${index + 1}` : "";
}

export function neighbours(key: NavItem["key"]): { previous?: NavItem; next?: NavItem } {
  const index = FLOW_ITEMS.findIndex((item) => item.key === key);
  return { previous: FLOW_ITEMS[index - 1], next: FLOW_ITEMS[index + 1] };
}
