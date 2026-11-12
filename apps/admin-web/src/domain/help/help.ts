/**
 * El Centro de ayuda: los artículos vienen del servidor (`project/content/help`, los mismos que leen los agentes por MCP). Aquí
 * está lo que el panel decide solo: qué ayuda corresponde a cada pantalla, a dónde lleva cada enlace y los pasos de «Empieza aquí».
 */

export interface HelpArticleSummary {
  slug: string;
  module: string;
  title: string;
  summary: string;
  minutes: number;
  /** Fecha `AAAA-MM-DD` de la última revisión. */
  updated: string;
}

export interface HelpModule {
  id: string;
  name: string;
  description: string;
  articles: HelpArticleSummary[];
}

export interface HelpSection {
  id: string;
  title: string;
}

export interface HelpArticle extends HelpArticleSummary {
  moduleName: string;
  /** Markdown, sin el encabezado de metadatos. */
  body: string;
  sections: HelpSection[];
  related: HelpArticleSummary[];
}

/** La ayuda de una pantalla: su tema y, si hay uno que la explica justo a ella, ese artículo primero. */
export interface ScreenHelp {
  module: string;
  article?: string;
}

/** Las pantallas (ruta dentro del negocio) y su ayuda, de la más específica a la más general. */
const SCREENS: [prefix: string, help: ScreenHelp][] = [
  ["configuracion/respuestas-rapidas", { module: "respuestas-rapidas", article: "crear-respuestas-rapidas" }],
  ["configuracion/atencion-humana", { module: "atencion-humana", article: "cuando-pasa-a-una-persona" }],
  ["configuracion/inteligencia-artificial", { module: "inteligencia-artificial", article: "clave-de-openrouter" }],
  ["configuracion/eliminar-negocio", { module: "cuenta", article: "eliminar-un-negocio" }],
  ["configuracion", { module: "cuenta", article: "configuracion-y-mi-cuenta" }],
  ["cuenta/seguridad", { module: "cuenta", article: "seguridad-y-sesiones" }],
  ["cuenta/notificaciones", { module: "cuenta", article: "activar-notificaciones" }],
  ["cuenta", { module: "cuenta", article: "configuracion-y-mi-cuenta" }],
  ["integraciones/api", { module: "integraciones", article: "api-del-asistente" }],
  ["integraciones/claves", { module: "integraciones", article: "claves-de-api" }],
  ["integraciones/agentes", { module: "integraciones", article: "agentes-de-ia" }],
  ["integraciones", { module: "integraciones", article: "catalogo-de-integraciones" }],
  ["conversaciones", { module: "conversaciones", article: "bandeja-en-vivo" }],
  ["clientes", { module: "clientes-y-ventas", article: "etapas-de-clientes" }],
  ["ventas", { module: "clientes-y-ventas", article: "registrar-una-venta" }],
  ["reportes", { module: "clientes-y-ventas", article: "reportes" }],
  ["canales", { module: "canales", article: "conectar-whatsapp" }],
  ["asistente", { module: "asistente", article: "como-aprende-tu-asistente" }],
  ["negocio", { module: "asistente", article: "mi-negocio" }],
  ["productos", { module: "asistente", article: "productos-y-servicios" }],
  ["pagos", { module: "asistente", article: "pagos-y-cierre" }],
  ["atencion", { module: "asistente", article: "como-atiende" }],
  ["mensajes", { module: "asistente", article: "mensajes-del-asistente" }],
  ["probar", { module: "asistente", article: "probar-el-asistente" }],
  ["revision", { module: "asistente", article: "guardar-y-publicar" }],
];

/** Los artículos que el panel nombra (cada pantalla y «Empieza aquí»): una prueba revisa que existan. */
export const REFERENCED_ARTICLES: string[] = [...new Set([...SCREENS.flatMap(([, help]) => (help.article ? [help.article] : [])), "empieza-aqui"])];

/** La ruta dentro del negocio: `/negocios/panaderia/canales/` → `canales`. */
export function screenOf(pathname: string): string {
  return pathname.replace(/^\/negocios\/[^/]+\/?/, "").replace(/\/+$/, "");
}

/** La ayuda de la pantalla abierta; en el inicio (o una pantalla sin ayuda propia), los primeros pasos. */
export function helpForPath(pathname: string): ScreenHelp {
  const screen = screenOf(pathname);
  const match = SCREENS.find(([prefix]) => screen === prefix || screen.startsWith(`${prefix}/`));
  return match ? match[1] : { module: "primeros-pasos", article: "empieza-aqui" };
}

/** Los artículos de un tema para una pantalla: el que la explica primero y luego el resto en su orden. */
export function articlesForScreen(module: HelpModule | undefined, help: ScreenHelp): HelpArticleSummary[] {
  if (!module) return [];
  const first = module.articles.find((article) => article.slug === help.article);
  return first ? [first, ...module.articles.filter((article) => article !== first)] : module.articles;
}

export type HelpLink = { kind: "article"; slug: string } | { kind: "screen"; path: string } | { kind: "external"; href: string } | { kind: "text" };

/** A dónde lleva un enlace del texto: otro artículo (`slug`), una pantalla del panel (`panel:ruta`) o una dirección `https://`. */
export function helpLink(href: string): HelpLink {
  if (/^https:\/\//.test(href)) return { kind: "external", href };
  if (/^panel:[a-z0-9/-]*$/.test(href)) return { kind: "screen", path: href.slice("panel:".length) };
  if (/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(href)) return { kind: "article", slug: href };
  return { kind: "text" };
}

/** «Si algo falla» → «si-algo-falla»: el ancla de cada sección (la misma que calcula el servidor). */
export function anchorOf(title: string): string {
  return title
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/** «2026-11-12» → «12 de noviembre de 2026». */
export function formatUpdated(value: string): string {
  const [year, month, day] = value.split("-").map(Number);
  if (!year || !month || !day) return value;
  const months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
  return `${day} de ${months[month - 1]} de ${year}`;
}

/** Lo que el panel sabe del negocio abierto para marcar «Empieza aquí». `null`: todavía no se sabe (no se marca ni se desmarca). */
export interface StartFacts {
  sectionsReady: boolean;
  aiKey: boolean | null;
  published: boolean;
  whatsapp: boolean | null;
  quickReplies: boolean | null;
}

export interface StartStep {
  id: "sections" | "ai" | "publish" | "whatsapp" | "quickReplies";
  title: string;
  detail: string;
  /** La pantalla donde se hace, dentro del negocio. */
  path: string;
  /** El artículo que lo explica. */
  article: string;
  done: boolean | null;
}

/** Los cinco pasos de «Empieza aquí», en el orden del artículo `empieza-aqui`. */
export function startSteps(facts: StartFacts): StartStep[] {
  return [
    { id: "sections", title: "Enséñale lo que vendes", detail: "Completa las cinco secciones de Asistente IA.", path: "asistente", article: "como-aprende-tu-asistente", done: facts.sectionsReady },
    { id: "ai", title: "Pon tu clave de IA", detail: "Sin ella, tu asistente no puede responder.", path: "configuracion/inteligencia-artificial", article: "clave-de-openrouter", done: facts.aiKey },
    { id: "publish", title: "Pruébalo y publícalo", detail: "Escríbele como un cliente y publica cuando te guste.", path: "revision", article: "guardar-y-publicar", done: facts.published },
    { id: "whatsapp", title: "Conecta tu WhatsApp", detail: "Escanea el código QR con el celular del negocio.", path: "canales", article: "conectar-whatsapp", done: facts.whatsapp },
    { id: "quickReplies", title: "Guarda tus respuestas rápidas", detail: "Lo que tu equipo responde todos los días, a un «/».", path: "configuracion/respuestas-rapidas", article: "crear-respuestas-rapidas", done: facts.quickReplies },
  ];
}
