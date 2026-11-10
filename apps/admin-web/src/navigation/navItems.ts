import { CONFIG_SECTIONS, type ConfigSectionId } from "../domain/sections";

export type NavKey =
  | "home"
  | ConfigSectionId
  | "review"
  | "ai"
  | "playground"
  | "conversations"
  | "customers"
  | "sales"
  | "reports"
  | "assistantHub"
  | "channels"
  | "settings";

export interface NavItem {
  key: NavKey;
  /** Ruta dentro del espacio de trabajo del negocio. */
  path: string;
  title: string;
  section?: ConfigSectionId;
}

const SECTION_PATHS: Record<ConfigSectionId, string> = {
  business: "negocio",
  catalog: "productos",
  payments: "pagos",
  assistant: "atencion",
  messages: "mensajes",
};

/** Entrada del panel: lleva al negocio del usuario o, si no tiene, a crear el primero. */
export const ENTRY_PATH = "/";
/** Administración de negocios (importar y eliminar): solo en este equipo. */
export const BUSINESSES_PATH = "/negocios";
/** Crear un negocio: la bienvenida de quien aún no tiene uno. */
export const NEW_BUSINESS_PATH = "/nuevo-negocio";

export const HOME_ITEM: NavItem = { key: "home", path: "", title: "Inicio" };
export const REVIEW_ITEM: NavItem = { key: "review", path: "revision", title: "Revisión y publicación" };
/** Herramientas del asistente: fuera del recorrido guiado de configuración. */
export const AI_ITEM: NavItem = { key: "ai", path: "ia", title: "Inteligencia artificial" };
export const PLAYGROUND_ITEM: NavItem = { key: "playground", path: "probar", title: "Probar asistente" };

/** Menú principal: atender y vender. */
export const CONVERSATIONS_ITEM: NavItem = { key: "conversations", path: "conversaciones", title: "Conversaciones" };
export const CUSTOMERS_ITEM: NavItem = { key: "customers", path: "clientes", title: "Clientes" };
export const SALES_ITEM: NavItem = { key: "sales", path: "ventas", title: "Ventas" };
export const REPORTS_ITEM: NavItem = { key: "reports", path: "reportes", title: "Reportes" };
export const CHANNELS_ITEM: NavItem = { key: "channels", path: "canales", title: "Canales" };
/** Ajustes del negocio: hoy, su inteligencia artificial. */
export const SETTINGS_ITEM: NavItem = { key: "settings", path: AI_ITEM.path, title: "Ajustes" };

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

/** Ruta completa dentro del espacio de trabajo de un negocio. */
export function workspacePath(slug: string, path = ""): string {
  const base = `/negocios/${encodeURIComponent(slug)}`;
  return path ? `${base}/${path}` : base;
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

export const MAIN_ITEMS: NavItem[] = [HOME_ITEM, CONVERSATIONS_ITEM, CUSTOMERS_ITEM, SALES_ITEM, REPORTS_ITEM];

/** Pestañas del Asistente IA: su entrenamiento, probarlo y publicarlo. */
export const ASSISTANT_TABS: { item: NavItem; label: string }[] = [
  ...SECTION_ITEMS.map((item) => ({ item, label: item.title })),
  { item: PLAYGROUND_ITEM, label: "Probar" },
  { item: REVIEW_ITEM, label: "Publicar" },
];

/** Entrada del menú hacia el Asistente IA: abre su primera pestaña. */
export const ASSISTANT_HUB_ITEM: NavItem = { key: "assistantHub", path: sectionPath("business"), title: "Asistente IA" };

/** Si la ruta es una pestaña del Asistente IA (`/negocios/x/pagos`). */
export function isAssistantPath(pathname: string): boolean {
  const last = pathname.replace(/\/+$/, "").split("/").pop() ?? "";
  return ASSISTANT_TABS.some(({ item }) => item.path === last);
}
