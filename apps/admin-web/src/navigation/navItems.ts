import { CONFIG_SECTIONS, type ConfigSectionId } from "../domain/sections";

export type NavKey =
  | "home"
  | "overview"
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
  | "settings"
  | "attention"
  | "accountProfile"
  | "security"
  | "notifications"
  | "quickReplies"
  | "billing"
  | "integrations"
  | "assistantApi"
  | "apiKeys"
  | "agents";

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
/** Lo que recibe el resumen del negocio al abrirse recién creado con una plantilla: para recordar cambiar los ejemplos. */
export interface CreatedFromTemplate {
  template: string;
}

/** Resumen del Asistente IA: cada sección en una tarjeta, con su estado. Es la entrada desde el menú. */
export const OVERVIEW_ITEM: NavItem = { key: "overview", path: "asistente", title: "Resumen" };
/** Herramientas del asistente: fuera del recorrido guiado de configuración. */
export const AI_ITEM: NavItem = { key: "ai", path: "configuracion/inteligencia-artificial", title: "Inteligencia artificial" };
export const PLAYGROUND_ITEM: NavItem = { key: "playground", path: "probar", title: "Probar asistente" };

/** Menú principal: atender y vender. */
export const CONVERSATIONS_ITEM: NavItem = { key: "conversations", path: "conversaciones", title: "Conversaciones" };
export const CUSTOMERS_ITEM: NavItem = { key: "customers", path: "clientes", title: "Clientes" };
export const SALES_ITEM: NavItem = { key: "sales", path: "ventas", title: "Ventas" };
export const REPORTS_ITEM: NavItem = { key: "reports", path: "reportes", title: "Reportes" };
export const CHANNELS_ITEM: NavItem = { key: "channels", path: "canales", title: "Canales" };
/**
 * Configuración: solo lo del NEGOCIO abierto (la IA de su asistente, la atención humana, las respuestas rápidas y la facturación).
 * Se aplica al instante, sin publicar. Lo que aún no existe se muestra con «Próximamente». Lo personal va en «Mi cuenta».
 */
export const SETTINGS_BASE = "configuracion";
export const SETTINGS_ITEM: NavItem = { key: "settings", path: SETTINGS_BASE, title: "Configuración" };

/**
 * Mi cuenta: lo de la PERSONA, igual en todos sus negocios (su perfil, su contraseña y sesiones, y los avisos en sus dispositivos).
 * Se abre desde el menú de su foto.
 */
export const ACCOUNT_BASE = "cuenta";
export const ACCOUNT_PROFILE_ITEM: NavItem = { key: "accountProfile", path: `${ACCOUNT_BASE}/perfil`, title: "Mi perfil" };
export const SECURITY_ITEM: NavItem = { key: "security", path: `${ACCOUNT_BASE}/seguridad`, title: "Seguridad" };
export const NOTIFICATIONS_ITEM: NavItem = { key: "notifications", path: `${ACCOUNT_BASE}/notificaciones`, title: "Notificaciones" };
export const ATTENTION_ITEM: NavItem = { key: "attention", path: `${SETTINGS_BASE}/atencion-humana`, title: "Atención humana" };
export const QUICK_REPLIES_ITEM: NavItem = { key: "quickReplies", path: `${SETTINGS_BASE}/respuestas-rapidas`, title: "Respuestas rápidas" };
export const BILLING_ITEM: NavItem = { key: "billing", path: `${SETTINGS_BASE}/facturacion`, title: "Pagos y suscripciones" };

export interface SettingsEntry {
  item: NavItem;
  description: string;
  /** Todavía no existe: se ve, con «Próximamente», para saber lo que viene. */
  soon?: boolean;
  /** Solo con cuentas (en la nube): el acceso local no tiene perfil ni contraseña. */
  account?: boolean;
}

export interface SettingsGroup {
  title: string;
  entries: SettingsEntry[];
}

/** El menú de Mi cuenta. */
export const ACCOUNT_GROUPS: SettingsGroup[] = [
  {
    title: "Tu cuenta",
    entries: [
      { item: ACCOUNT_PROFILE_ITEM, description: "Tu foto y tus datos", account: true },
      { item: SECURITY_ITEM, description: "Contraseña y sesiones", account: true },
      { item: NOTIFICATIONS_ITEM, description: "Avisos en tu celular y computador" },
    ],
  },
];

/** El menú de Configuración del negocio, por grupos. */
export const SETTINGS_GROUPS: SettingsGroup[] = [
  {
    title: "Asistente",
    entries: [
      { item: AI_ITEM, description: "Proveedor, clave y modelo" },
      { item: ATTENTION_ITEM, description: "Horario del equipo y avisos" },
      { item: QUICK_REPLIES_ITEM, description: "Mensajes guardados para responder rápido", soon: true },
    ],
  },
  { title: "Facturación", entries: [{ item: BILLING_ITEM, description: "Tu plan, pagos y facturas", soon: true }] },
];

/** Integraciones: conectar el asistente con otras herramientas (la API del asistente, sus claves y, pronto, las IAs por MCP). */
export const INTEGRATIONS_ITEM: NavItem = { key: "integrations", path: "integraciones", title: "Integraciones" };
export const ASSISTANT_API_ITEM: NavItem = { key: "assistantApi", path: "integraciones/api", title: "API del asistente" };
export const API_KEYS_ITEM: NavItem = { key: "apiKeys", path: "integraciones/claves", title: "Claves de API" };
export const AGENTS_ITEM: NavItem = { key: "agents", path: "integraciones/agentes", title: "Agentes de IA (MCP)" };

/** Si la ruta es de Integraciones (`/negocios/x/integraciones/...`). */
export function isIntegrationsPath(pathname: string): boolean {
  return /\/integraciones(\/|$)/.test(pathname.replace(/\/+$/, ""));
}

/** Si la ruta es de Mi cuenta (`/negocios/x/cuenta/...`). */
export function isAccountPath(pathname: string): boolean {
  return /\/cuenta(\/|$)/.test(pathname.replace(/\/+$/, ""));
}

/** Si la ruta es de Configuración (`/negocios/x/configuracion/...`). */
export function isSettingsPath(pathname: string): boolean {
  return /\/configuracion(\/|$)/.test(pathname.replace(/\/+$/, ""));
}

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

/** Nombre corto de una sección en la barra de pestañas, para que quepan todas en una fila (el completo sigue siendo su nombre accesible). */
const SHORT_TAB_LABELS: Partial<Record<ConfigSectionId, string>> = { catalog: "Productos", payments: "Pagos", messages: "Mensajes" };

/** Pestañas del Asistente IA: su entrenamiento, probarlo y publicarlo. */
export const ASSISTANT_TABS: { item: NavItem; label: string; short?: string }[] = [
  { item: OVERVIEW_ITEM, label: "Resumen" },
  ...SECTION_ITEMS.map((item) => ({ item, label: item.title, short: item.section ? SHORT_TAB_LABELS[item.section] : undefined })),
  { item: PLAYGROUND_ITEM, label: "Probar" },
  { item: REVIEW_ITEM, label: "Publicar" },
];

/** Entrada del menú hacia el Asistente IA: abre su resumen. */
export const ASSISTANT_HUB_ITEM: NavItem = { key: "assistantHub", path: OVERVIEW_ITEM.path, title: "Asistente IA" };

/** Si la ruta es una pestaña del Asistente IA (`/negocios/x/pagos`). */
export function isAssistantPath(pathname: string): boolean {
  // Configuración, Integraciones y Mi cuenta tienen sus propias secciones: ninguna es una pestaña del asistente aunque se llame parecido.
  if (isSettingsPath(pathname) || isIntegrationsPath(pathname) || isAccountPath(pathname)) return false;
  const last = pathname.replace(/\/+$/, "").split("/").pop() ?? "";
  return ASSISTANT_TABS.some(({ item }) => item.path === last);
}

/** El nombre de la sección abierta, para la barra superior en el celular. */
export function titleForPath(pathname: string): string {
  if (isAssistantPath(pathname)) return ASSISTANT_HUB_ITEM.title;
  if (isSettingsPath(pathname)) return SETTINGS_ITEM.title;
  if (isAccountPath(pathname)) return "Mi cuenta";
  if (isIntegrationsPath(pathname)) return INTEGRATIONS_ITEM.title;
  const last = pathname.replace(/\/+$/, "").split("/").pop() ?? "";
  const item = [CONVERSATIONS_ITEM, CUSTOMERS_ITEM, SALES_ITEM, REPORTS_ITEM, CHANNELS_ITEM, SETTINGS_ITEM].find((entry) => entry.path === last);
  return item?.title ?? HOME_ITEM.title;
}
