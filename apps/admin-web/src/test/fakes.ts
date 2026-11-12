import contractSchema from "../../../../project/config/contracts/v1/business-config.schema.json";
import type { ApplicationServices } from "../app/compositionRoot";
import { AuthError, type Session, type UserProfile } from "../domain/auth/types";
import { normalizeEmail } from "../domain/auth/validation";
import type { ContractSchema } from "../domain/config/contractSchema";
import { paymentHolders } from "../domain/config/document";
import type { BusinessDocument, BusinessSummary, BusinessTemplate, Diagnostic, PaymentFields, PaymentFieldState, PaymentValues, VersionInfo, VersionStatus } from "../domain/config/types";
import { createLocalOperatorAuthService } from "../infrastructure/local/localOperatorAuthService";
import type { AIModelOption, AISettings, AIUsage, AssistantLab, ConfigSource, ModelCatalog } from "../repositories/assistantLab";
import type { Attention, AttentionSettings, AttentionView, DevicePush, PushPermission, PushSupport } from "../repositories/attention";
import type { AuthService } from "../repositories/authService";
import type { BusinessDirectory } from "../repositories/businessDirectory";
import type { Channels, WhatsAppChannel } from "../repositories/channels";
import type { Commerce } from "../repositories/commerce";
import type { Customer, Report, Sale } from "../domain/commerce/types";
import type { ConfigRepository, StoredConfig } from "../repositories/configRepository";
import type { ChatMessage, ConversationSummary, ConversationThread, InboxFilter, Notification } from "../domain/inbox/types";
import type { Inbox } from "../repositories/inbox";
import type { AgentAuthorization, AuthorizationDecision } from "../repositories/agentAuthorization";
import type { ApiKey, Integrations, NewKeyRequest } from "../repositories/integrations";
import { SCOPE_ASSISTANT_CHAT, type KeyArea } from "../domain/integrations/types";
import { PersistenceError } from "../repositories/persistenceError";
import { SAMPLE_DOCUMENT } from "./fixtures/sampleDocument";

export const TEST_ACCOUNT = { name: "Laura Gómez", email: "laura@empresa.com", password: "clave1234" };

interface MemoryVersion {
  version: number;
  status: VersionStatus;
  document: BusinessDocument;
  createdAt: string;
  publishedAt: string | null;
}

interface MemoryBusiness {
  slug: string;
  name: string;
  versions: MemoryVersion[];
  /** Versiones publicadas, de la más antigua a la vigente. */
  published: number[];
}

type FailingOperation = "list" | "create" | "templates" | "remove" | "importExisting" | "contractSchema" | "load" | "save" | "review" | "history" | "versionDocument" | "publish" | "rollback" | "restore";

export interface MemoryBackend {
  directory: BusinessDirectory;
  createConfigRepository: (slug: string) => ConfigRepository;
  /** La versión más reciente guardada de un negocio. */
  stored: (slug: string) => BusinessDocument | null;
  /** Los valores de pago que recibió cada guardado. */
  paymentValuesReceived: PaymentValues[];
  /** Hace fallar la próxima llamada a una operación. */
  failNext: (operation: FailingOperation, error: PersistenceError) => void;
  /** Lo que responde la revisión del servidor. */
  review: { diagnostics: Diagnostic[]; compileError: string | null };
  /** Fuerza el estado que el servidor informa de un dato de pago, por su referencia guardada. */
  paymentFieldStates: Map<string, PaymentFieldState>;
}

/** Las referencias de un documento ya guardado llevan `~versión`, como las que devuelve el servidor. */
const storedRef = (ref: string) => (ref.includes("~") ? ref : `${ref}~guardado`);

/** Plantillas del servidor falso: las mismas formas que publica la API (`GET /business-templates`). */
export const TEMPLATES: BusinessTemplate[] = [
  { id: "restaurante", title: "Restaurante o comida a domicilio", description: "Menú con precios, domicilio y recogida en el local.", icon: "utensils" },
  { id: "software", title: "Software o servicio por suscripción", description: "Planes mensuales para otros negocios.", icon: "bolt" },
];

/** El documento que deja una plantilla en el servidor falso: el de ejemplo, sin datos de pago. */
const templateDocument: BusinessDocument = (() => {
  const document = structuredClone(SAMPLE_DOCUMENT);
  document.payments = [];
  if (document.offer.catalog) document.offer.catalog.payment_profile = null;
  for (const plan of document.offer.plans ?? []) plan.payment_profile = null;
  return document;
})();

function withStoredRefs(document: BusinessDocument): BusinessDocument {
  return JSON.parse(JSON.stringify(document), (key, value: unknown) => (key === "secret_ref" && typeof value === "string" ? storedRef(value) : value)) as BusinessDocument;
}

/**
 * Sustituto en memoria de la API para probar la interfaz. Reproduce lo que la interfaz necesita del servidor (versiones,
 * conflictos, referencias de pago), pero no valida el contrato: eso se comprueba contra la API real en `test/integration`.
 */
export function createMemoryBackend(seed: BusinessDocument[] = []): MemoryBackend {
  const businesses = new Map<string, MemoryBusiness>();
  const failures = new Map<FailingOperation, PersistenceError>();
  const paymentValuesReceived: PaymentValues[] = [];
  const review: MemoryBackend["review"] = { diagnostics: [], compileError: null };
  const paymentFieldStates: MemoryBackend["paymentFieldStates"] = new Map();
  /** La parte visible de cada dato recibido; lo que viene sembrado se muestra con una máscara fija. */
  const masks = new Map<string, string>();
  let clock = Date.UTC(2026, 0, 1, 9, 0, 0);
  const now = () => new Date((clock += 60_000)).toISOString();

  const check = (operation: FailingOperation) => {
    const failure = failures.get(operation);
    if (failure) {
      failures.delete(operation);
      throw failure;
    }
  };

  const find = (slug: string): MemoryBusiness => {
    const business = businesses.get(slug);
    if (!business) throw new PersistenceError("not_found", { message: "Ese negocio no existe." });
    return business;
  };

  const latest = (business: MemoryBusiness) => business.versions.at(-1) ?? null;
  const draftOf = (business: MemoryBusiness) => [...business.versions].reverse().find((version) => version.status === "draft") ?? null;
  const publishedVersion = (business: MemoryBusiness) => business.published.at(-1) ?? null;

  const summary = (business: MemoryBusiness): BusinessSummary => ({
    slug: business.slug,
    name: business.name,
    latestVersion: latest(business)?.version ?? null,
    draftVersion: draftOf(business)?.version ?? null,
    publishedVersion: publishedVersion(business),
  });

  const toInfo = ({ version, status, createdAt, publishedAt }: MemoryVersion): VersionInfo => ({ version, status, createdAt, publishedAt });

  /** Lo que se edita: el borrador en curso; si no hay, lo publicado. */
  const current = (business: MemoryBusiness) => draftOf(business) ?? business.versions.find((version) => version.version === publishedVersion(business)) ?? latest(business);

  const fieldsOf = (document: BusinessDocument): PaymentFields =>
    Object.fromEntries(
      paymentHolders(document.payments).map(({ ref }) => [ref.secret_ref, paymentFieldStates.get(ref.secret_ref) ?? { status: "configured" as const, masked: masks.get(ref.secret_ref) ?? "••••0000" }]),
    );

  const stored = (business: MemoryBusiness): StoredConfig => {
    const version = current(business);
    return {
      slug: business.slug,
      name: business.name,
      document: version ? structuredClone(version.document) : null,
      version: version ? toInfo(version) : null,
      latestVersion: latest(business)?.version ?? null,
      publishedVersion: publishedVersion(business),
      paymentFields: version ? fieldsOf(version.document) : {},
    };
  };

  const addVersion = (business: MemoryBusiness, document: BusinessDocument) => {
    for (const version of business.versions) if (version.status === "draft") version.status = "archived";
    business.versions.push({ version: business.versions.length + 1, status: "draft", document, createdAt: now(), publishedAt: null });
  };

  const setPublished = (business: MemoryBusiness, target: MemoryVersion) => {
    for (const version of business.versions) if (version.status === "published") version.status = "archived";
    target.status = "published";
    target.publishedAt = now();
  };

  for (const document of seed) {
    const business: MemoryBusiness = { slug: document.tenant_slug, name: document.identity.name, versions: [], published: [] };
    addVersion(business, withStoredRefs(document));
    businesses.set(business.slug, business);
  }

  const directory: BusinessDirectory = {
    list: async () => {
      check("list");
      return [...businesses.values()].map(summary);
    },
    canImportExisting: true,
    canRemove: true,
    create: async ({ slug, name, template }) => {
      check("create");
      if (businesses.has(slug)) throw new PersistenceError("duplicate", { message: "Ya existe un negocio con ese identificador.", problems: [{ path: "slug", message: "Ya existe un negocio con ese identificador." }] });
      if (template && !TEMPLATES.some((item) => item.id === template)) {
        throw new PersistenceError("invalid", { message: "Esa plantilla no existe.", problems: [{ path: "template", message: "Elige otra plantilla." }] });
      }
      const business: MemoryBusiness = { slug, name, versions: [], published: [] };
      businesses.set(slug, business);
      // Como el servidor: la plantilla queda como primer borrador, con el nombre y el identificador del negocio y sin datos de pago.
      if (template) addVersion(business, { ...structuredClone(templateDocument), tenant_slug: slug, identity: { ...templateDocument.identity, name } });
      return summary(business);
    },
    templates: async () => {
      check("templates");
      return structuredClone(TEMPLATES);
    },
    remove: async (slug) => {
      check("remove");
      find(slug);
      businesses.delete(slug);
    },
    importExisting: async () => {
      check("importExisting");
      return { created: [], skipped: [...businesses.keys()] };
    },
    contractSchema: async () => {
      check("contractSchema");
      return contractSchema as unknown as ContractSchema;
    },
  };

  const createConfigRepository = (slug: string): ConfigRepository => ({
    load: async () => {
      check("load");
      return stored(find(slug));
    },
    save: async ({ document, paymentValues, baseVersion }) => {
      check("save");
      const business = find(slug);
      if (baseVersion !== (latest(business)?.version ?? null)) throw new PersistenceError("conflict", { message: "Este negocio cambió desde que lo abriste, quizá en otra pestaña." });
      paymentValuesReceived.push(paymentValues);
      for (const [ref, value] of Object.entries(paymentValues)) masks.set(storedRef(ref), `••••${value.slice(-4)}`);
      addVersion(business, withStoredRefs(document));
      return stored(business);
    },
    review: async () => {
      check("review");
      const version = current(find(slug));
      return { version: version?.version ?? null, diagnostics: review.diagnostics, compiles: review.compileError === null, compileError: review.compileError };
    },
    history: async () => {
      check("history");
      return find(slug).versions.map(toInfo);
    },
    versionDocument: async (version) => {
      check("versionDocument");
      const target = find(slug).versions.find((item) => item.version === version);
      if (!target) throw new PersistenceError("not_found", { message: "Esa versión no existe." });
      return { version: toInfo(target), document: structuredClone(target.document) };
    },
    publish: async (version) => {
      check("publish");
      const business = find(slug);
      const target = business.versions.find((item) => item.version === version);
      if (!target) throw new PersistenceError("conflict", { message: "Esa versión no existe." });
      setPublished(business, target);
      business.published.push(version);
      return stored(business);
    },
    rollback: async () => {
      check("rollback");
      const business = find(slug);
      const previous = business.published.at(-2);
      const target = business.versions.find((item) => item.version === previous);
      if (!target) throw new PersistenceError("conflict", { message: "No hay una versión publicada anterior." });
      setPublished(business, target);
      business.published.pop();
      return stored(business);
    },
    restore: async (version) => {
      check("restore");
      const business = find(slug);
      const target = business.versions.find((item) => item.version === version);
      if (!target) throw new PersistenceError("conflict", { message: "Esa versión no existe." });
      addVersion(business, structuredClone(target.document));
      return stored(business);
    },
  });

  return {
    directory,
    createConfigRepository,
    stored: (slug) => {
      const business = businesses.get(slug);
      return business ? (structuredClone(latest(business)?.document) ?? null) : null;
    },
    paymentValuesReceived,
    failNext: (operation, error) => failures.set(operation, error),
    review,
    paymentFieldStates,
  };
}

export interface MemoryAssistantLabs {
  create: (slug: string) => AssistantLab;
  /** La clave guardada de cada negocio: comprueba que la interfaz la envía y nunca la recibe de vuelta. */
  keys: Map<string, string>;
  messages: { slug: string; message: string; source: ConfigSource; sessionId: string | null }[];
  resets: string[];
  /** El consumo de IA de cada negocio; sin entrada, cero. */
  usage: Map<string, AIUsage>;
  /** La lista de OpenRouter; null simula que no se pudo cargar. */
  catalog: { current: ModelCatalog | null };
}

const model = (id: string, name: string, provider: string, prompt: number, completion: number, extra: Partial<AIModelOption> = {}): AIModelOption => ({
  id, name, provider, promptUsdPerMillion: prompt, completionUsdPerMillion: completion, contextLength: 128000, recommended: false, free: false, ...extra,
});

/** Una muestra de la lista de OpenRouter, con recomendados, uno gratis y uno más caro. */
export const SAMPLE_MODEL_CATALOG: ModelCatalog = {
  defaultModel: "openai/gpt-4o-mini",
  models: [
    model("openai/gpt-4o-mini", "GPT-4o-mini", "OpenAI", 0.15, 0.6, { recommended: true }),
    model("google/gemini-2.5-flash", "Gemini 2.5 Flash", "Google", 0.3, 2.5, { recommended: true }),
    model("anthropic/claude-sonnet-4.5", "Claude Sonnet 4.5", "Anthropic", 3, 15),
    model("meta-llama/llama-3.3-70b-instruct:free", "Llama 3.3 70B Instruct (free)", "Meta", 0, 0, { free: true }),
  ],
};

/** Sustituto en memoria de la inteligencia artificial y del área de pruebas: responde «Respuesta a: …» sin red. */
export function createMemoryAssistantLabs(): MemoryAssistantLabs {
  const keys = new Map<string, string>();
  const models = new Map<string, string | null>();
  const messages: MemoryAssistantLabs["messages"] = [];
  const resets: string[] = [];
  const usage = new Map<string, AIUsage>();
  const catalog: MemoryAssistantLabs["catalog"] = { current: SAMPLE_MODEL_CATALOG };
  let sessions = 0;
  const settingsOf = (slug: string): AISettings => {
    const key = keys.get(slug);
    return { provider: "openrouter", model: models.get(slug) ?? null, key: { configured: Boolean(key), hint: key ? `••••${key.slice(-4)}` : null } };
  };
  const missingKey = () => new PersistenceError("ai_key_missing", { message: "Este negocio no tiene clave de IA; agrégala en Inteligencia artificial." });

  return {
    keys,
    messages,
    resets,
    usage,
    catalog,
    create: (slug) => ({
      getAISettings: async () => settingsOf(slug),
      async saveAISettings({ model, apiKey, clearKey }) {
        if (apiKey !== undefined && (apiKey.length < 20 || /\s/.test(apiKey))) {
          const message = "Pega la clave completa de OpenRouter, sin espacios.";
          throw new PersistenceError("invalid", { message, problems: [{ path: "api_key", message }] });
        }
        models.set(slug, model);
        if (apiKey) keys.set(slug, apiKey);
        else if (clearKey) keys.delete(slug);
        return settingsOf(slug);
      },
      async verifyAIKey() {
        if (!keys.has(slug)) throw missingKey();
        return { valid: true, message: "La clave funciona." };
      },
      async getAIModels() {
        if (!catalog.current) throw new PersistenceError("unavailable", { message: "No se pudo cargar la lista de modelos de OpenRouter." });
        return catalog.current;
      },
      getAIUsage: async () => usage.get(slug) ?? { since: "2026-10-12", replies: 0, promptTokens: 0, completionTokens: 0, costUsd: null, days: [] },
      async sendMessage({ message, source, sessionId }) {
        if (!keys.has(slug)) throw missingKey();
        messages.push({ slug, message, source, sessionId });
        const session = sessionId ?? (++sessions).toString(16).padStart(32, "0");
        return { sessionId: session, source, version: source === "published" ? 1 : 2, reply: `Respuesta a: ${message}`, intent: "info", aiAnswered: true };
      },
      async resetConversation(sessionId) {
        resets.push(sessionId);
      },
    }),
  };
}

/** Token que el WhatsApp en memoria acepta como el de una instancia (cualquier otro se rechaza en su campo). */
export const TEST_QR = "data:image/png;base64,iVBORw0KGgo=";

export interface MemoryWhatsApp {
  channels: Channels;
  /** Simula que el negocio escaneó el código desde su teléfono. */
  scan(): void;
  /** Cuántas veces se pidió un código nuevo. */
  newCodes: () => number;
}

/** WhatsApp por código QR en memoria. `available: false` simula una plataforma sin el servidor configurado. */
export function createMemoryWhatsApp({ available = true }: { available?: boolean } = {}): MemoryWhatsApp {
  const empty: WhatsAppChannel = { available, status: "disconnected", phone: null, profileName: null, qrcode: null, paircode: null };
  let state: WhatsAppChannel = { ...empty };
  let scanned = false;
  let codes = 0;
  const view = (extra: Partial<WhatsAppChannel> = {}) => ({ ...state, ...extra });
  const connect = async () => {
    if (!available) throw new PersistenceError("unavailable", { message: "La conexión de WhatsApp por código QR todavía no está activa. Intenta más tarde." });
    state = { ...state, status: "connecting" };
    return view({ qrcode: TEST_QR });
  };
  const channels: Channels = {
    whatsapp: async () => view(),
    connectWhatsApp: connect,
    newWhatsAppCode: async () => {
      codes += 1;
      return connect();
    },
    whatsAppStatus: async () => {
      if (scanned) state = { ...state, status: "connected", phone: "573001112233", profileName: "Café Aroma" };
      return view(state.status === "connecting" ? { qrcode: TEST_QR } : {});
    },
    disconnectWhatsApp: async () => {
      scanned = false;
      state = { ...empty };
      return view();
    },
  };
  return { channels, scan: () => (scanned = true), newCodes: () => codes };
}

/** Un reporte vacío de `days` días que terminan hoy, para sembrar lo que la prueba necesite. */
export function emptyReport(days = 30): Report {
  const today = new Date();
  const list = Array.from({ length: days }, (_, index) => {
    const day = new Date(today.getTime() - (days - 1 - index) * 86_400_000).toISOString().slice(0, 10);
    return { day, newConversations: 0, customerMessages: 0, assistantMessages: 0, agentMessages: 0, sales: 0 };
  });
  const totals = { conversations: 0, customerMessages: 0, assistantMessages: 0, agentMessages: 0, handoffs: 0, sales: 0, revenue: {} };
  return {
    since: list[0]?.day ?? "",
    until: list.at(-1)?.day ?? "",
    days: list,
    totals,
    previous: { ...totals },
    funnel: { new: 0, interested: 0, ready: 0, payment: 0, customer: 0 },
    handoffsByReason: {},
    aiCostUsd: null,
    aiReplies: 0,
  };
}

/** Clientes, ventas y reportes en memoria: registrar una venta convierte al cliente, como el servidor. */
export function createMemoryCommerce(seed: { customers?: Customer[]; sales?: Sale[]; report?: Report } = {}): Commerce & { customerList: Customer[]; saleList: Sale[]; reportDays: number[] } {
  const customerList = (seed.customers ?? []).map((item) => ({ ...item }));
  const saleList = (seed.sales ?? []).map((item) => ({ ...item }));
  const reportDays: number[] = [];
  return {
    customerList,
    saleList,
    reportDays,
    customers: async (filter = {}) => {
      const text = (filter.query ?? "").trim().toLowerCase();
      return customerList
        .filter((item) => (!filter.stage || item.stage === filter.stage) && (!text || `${item.name ?? ""} ${item.contact}`.toLowerCase().includes(text)))
        .map((item) => ({ ...item }));
    },
    sales: async () => saleList.map((item) => ({ ...item })),
    recordSale: async (sale) => {
      if (!sale.customerName.trim()) throw new PersistenceError("invalid", { message: "Escribe el nombre del cliente.", problems: [{ path: "customer_name", message: "Escribe el nombre del cliente." }] });
      if (!(Number(sale.amount) > 0)) throw new PersistenceError("invalid", { message: "El valor debe ser mayor que cero.", problems: [{ path: "amount", message: "El valor debe ser mayor que cero." }] });
      const created: Sale = {
        id: `venta-${saleList.length + 1}`,
        customerName: sale.customerName.trim(),
        description: sale.description.trim(),
        amount: Number(sale.amount).toFixed(2),
        currency: sale.currency,
        status: "confirmed",
        createdAt: new Date().toISOString(),
        createdBy: "operador@ejemplo.com",
        conversationId: sale.conversationId ?? null,
      };
      saleList.unshift(created);
      const customer = customerList.find((item) => item.conversationId === sale.conversationId);
      if (customer) Object.assign(customer, { stage: "customer", needsHuman: false, purchases: customer.purchases + 1 });
      return { ...created };
    },
    cancelSale: async (saleId) => {
      const sale = saleList.find((item) => item.id === saleId);
      if (!sale) throw new PersistenceError("not_found", { message: "Esa venta no existe." });
      sale.status = "cancelled";
      return { ...sale };
    },
    report: async (days) => {
      reportDays.push(days);
      return seed.report ?? emptyReport(days);
    },
  };
}

/** La atención humana en memoria: guarda lo que se envía, valida como el servidor lo esencial y registra los correos de prueba. */
export function createMemoryAttention(seed: Partial<AttentionView> = {}): Attention & { view: AttentionView; testEmails: number; failEmail: boolean } {
  const state = {
    view: {
      hoursMode: "business",
      teamHours: [],
      timezone: "America/Bogota",
      replyMinutes: 10,
      resumeAfterMinutes: 30,
      emailEnabled: true,
      emailTo: null,
      updatedAt: null,
      businessHours: [{ days: ["lunes", "martes", "miercoles", "jueves", "viernes"], opens: "08:00", closes: "18:00" }],
      accountEmails: ["laura@empresa.com"],
      emailAvailable: true,
      teamAvailableNow: true,
      nextOpening: null,
      options: {
        timezones: [
          { id: "America/Bogota", label: "Colombia" },
          { id: "America/Mexico_City", label: "México (Ciudad de México)" },
        ],
        replyMinutes: [0, 5, 10, 15, 30, 60, 120, 240],
        resumeAfterMinutes: [10, 15, 30, 45, 60, 120, 240],
      },
      ...seed,
    } as AttentionView,
    testEmails: 0,
    failEmail: false,
  };
  return Object.assign(state, {
    get: async () => structuredClone(state.view),
    save: async (settings: AttentionSettings) => {
      if (settings.hoursMode === "custom" && settings.teamHours.length === 0) {
        throw new PersistenceError("invalid", { message: "Revisa la atención humana.", problems: [{ path: "team_hours", message: "Agrega al menos una franja, o elige otro horario." }] });
      }
      state.view = { ...state.view, ...settings, emailTo: settings.emailTo?.trim() || null, updatedAt: new Date().toISOString() };
      return structuredClone(state.view);
    },
    sendTestEmail: async () => {
      if (state.failEmail) throw new PersistenceError("unknown", { message: "El correo de avisos aún no está activado en la plataforma." });
      state.testEmails += 1;
      return state.view.emailTo ? [state.view.emailTo] : state.view.accountEmails;
    },
  });
}

/** Las notificaciones de un navegador en memoria: soportadas, con permiso por dar. */
export function createMemoryDevicePush(initial: { support?: PushSupport; permission?: PushPermission; subscribed?: boolean } = {}) {
  const state = { support: initial.support ?? "supported", permission: initial.permission ?? "default", subscribed: initial.subscribed ?? false, tests: 0, denyNext: false };
  const push: DevicePush & { state: typeof state } = {
    state,
    support: () => state.support as PushSupport,
    permission: () => state.permission as PushPermission,
    subscribed: async () => state.subscribed,
    enable: async () => {
      if (state.denyNext) {
        state.permission = "denied";
        throw new PersistenceError("unknown", { message: "Bloqueaste las notificaciones para este sitio. Permítelas en la configuración del navegador y vuelve a intentarlo." });
      }
      state.permission = "granted";
      state.subscribed = true;
    },
    disable: async () => {
      state.subscribed = false;
    },
    test: async () => {
      state.tests += 1;
    },
  };
  return push;
}

/** Las integraciones en memoria: claves con su valor (solo al crearlas) y la prueba de la API. */
/** Las áreas que define el motor (`key_permissions.py`), para las pruebas del panel. */
export const KEY_AREAS: KeyArea[] = [
  { id: "chat", label: "Conversar con el asistente", read: null, write: "Mandarle mensajes de clientes y recibir sus respuestas.", oneBusinessOnly: true },
  { id: "businesses", label: "Negocios", read: "Ver tus negocios y las plantillas.", write: "Crear negocios nuevos desde una plantilla.", oneBusinessOnly: false },
  { id: "assistant", label: "Asistente IA", read: "Ver la configuración.", write: "Editar, probar y publicar.", oneBusinessOnly: false },
  { id: "payments", label: "Datos de pago", read: null, write: "Escribir tus datos de pago. Nunca leerlos.", oneBusinessOnly: false },
  { id: "conversations", label: "Conversaciones", read: "Leer los chats con tus clientes.", write: "Responderles a tus clientes.", oneBusinessOnly: false },
  { id: "sales", label: "Clientes y ventas", read: "Ver clientes, ventas y reportes.", write: "Registrar y anular ventas.", oneBusinessOnly: false },
  { id: "attention", label: "Atención humana", read: "Ver la atención humana.", write: "Cambiarla.", oneBusinessOnly: false },
];

export function createMemoryIntegrations(options: { url?: string | null; mcpUrl?: string | null; business?: string; signIn?: boolean } = {}) {
  const state = { keys: [] as ApiKey[], secrets: new Map<string, string>(), tried: [] as string[], counter: 0, requests: [] as NewKeyRequest[] };
  const business = options.business ?? "cafe_aroma";
  const integrations: Integrations & { state: typeof state } = {
    state,
    overview: async () => {
      const active = state.keys.filter((key) => key.active);
      return {
        assistantApiUrl: options.url === undefined ? "https://motor.example.com/api/v1/assistant/messages" : options.url,
        mcpUrl: options.mcpUrl === undefined ? "https://panel.example.com/api/mcp" : options.mcpUrl,
        mcpSignIn: options.signIn ?? true,
        chatKeys: active.filter((key) => key.scopes.includes(SCOPE_ASSISTANT_CHAT)).length,
        activeKeys: active.length,
        areas: KEY_AREAS,
      };
    },
    keys: async () => structuredClone([...state.keys].sort((a, b) => Number(b.active) - Number(a.active))),
    createKey: async (request) => {
      state.requests.push(structuredClone(request));
      const problems = [
        ...(request.name.trim() ? [] : [{ path: "name", message: "Ponle un nombre." }]),
        ...(Object.keys(request.permissions).length > 0 ? [] : [{ path: "permissions", message: "Dale acceso al menos a un área." }]),
        ...(request.permissions.chat && request.reach !== "one" ? [{ path: "permissions.chat", message: "Es de un solo negocio." }] : []),
      ];
      if (problems.length > 0) throw new PersistenceError("invalid", { message: "Revisa la clave.", problems });
      state.counter += 1;
      const secret = `ase_live_${"Ab12Cd".padEnd(40, String(state.counter))}`;
      const scopes = Object.entries(request.permissions).flatMap(([area, level]) => (area === "chat" ? [SCOPE_ASSISTANT_CHAT] : [`${area}:${level}`]));
      const key: ApiKey = {
        id: `clave-${state.counter}`, name: request.name.trim(), prefix: secret.slice(0, 15), scopes, permissions: request.permissions, reach: request.reach,
        businesses: request.reach === "one" ? [business] : request.reach === "some" ? (request.businesses ?? []) : [], createdAt: new Date().toISOString(),
        createdBy: "laura@empresa.com", lastUsedAt: null, revokedAt: null,
        expiresAt: request.expiresInDays === null ? null : new Date(Date.now() + request.expiresInDays * 86_400_000).toISOString(), active: true, expired: false,
        kind: "key",
      };
      state.keys.push(key);
      state.secrets.set(key.id, secret);
      return { key: structuredClone(key), secret };
    },
    revokeKey: async (id) => {
      const key = state.keys.find((item) => item.id === id)!;
      key.active = false;
      key.revokedAt = new Date().toISOString();
      return structuredClone(key);
    },
    tryAssistantApi: async (message) => {
      state.tried.push(message);
      return {
        conversation_id: "prueba", reply: `Respuesta a: ${message}`, parts: [`Respuesta a: ${message}`], handoff: false, handoff_reason: null,
        attended_by: "assistant", intent: "info", stage: "new", fallback: false, duplicate: false,
      };
    },
  };
  return integrations;
}

/** La autorización de agentes en memoria: «claude» es un agente registrado; cualquier otro, no. Guarda lo que se decide. */
export function createMemoryAgentAuthorization() {
  const decisions: AuthorizationDecision[] = [];
  const service: AgentAuthorization & { decisions: AuthorizationDecision[] } = {
    decisions,
    describe: async (params) =>
      params.client_id === "claude"
        ? { ready: true, clientName: "Claude", redirectHost: "claude.ai", areas: KEY_AREAS.filter((area) => area.id !== "chat") }
        : { ready: false, message: "El agente no está registrado. Vuelve a conectarlo desde su programa.", redirectTo: null },
    decide: async (decision) => {
      if (decision.approve && decision.reach === "some" && (decision.businesses ?? []).length === 0) {
        throw new PersistenceError("invalid", { message: "Revisa la clave.", problems: [{ path: "businesses", message: "Elige al menos un negocio." }] });
      }
      decisions.push(structuredClone(decision));
      const back = new URL(decision.params.redirect_uri ?? "https://claude.ai/api/mcp/auth_callback");
      if (decision.approve) back.searchParams.set("code", "codigo-de-prueba");
      else back.searchParams.set("error", "access_denied");
      if (decision.params.state) back.searchParams.set("state", decision.params.state);
      return back.toString();
    },
  };
  return service;
}

/** Servicios como los de la aplicación, sobre el backend en memoria. */
export function createTestServices(backend: MemoryBackend = createMemoryBackend(), overrides: Partial<ApplicationServices> = {}): ApplicationServices {
  const whatsapp = createMemoryWhatsApp();
  const commerce = createMemoryCommerce();
  const attention = createMemoryAttention();
  const integrations = createMemoryIntegrations();
  return {
    auth: createLocalOperatorAuthService(),
    directory: backend.directory,
    createConfigRepository: backend.createConfigRepository,
    createAssistantLab: createMemoryAssistantLabs().create,
    inbox: createMemoryInbox(),
    createChannels: () => whatsapp.channels,
    createCommerce: () => commerce,
    createAttention: () => attention,
    devicePush: createMemoryDevicePush(),
    createIntegrations: () => integrations,
    agentAuthorization: createMemoryAgentAuthorization(),
    ...overrides,
  };
}

/**
 * Servicio en memoria que SÍ verifica credenciales (contraseñas en claro: solo para pruebas).
 * Permite probar la interfaz que tendrá la futura autenticación real en servidor.
 */
export function createVerifyingAuthService(): AuthService {
  const accounts = new Map<string, { profile: UserProfile; password: string }>();
  let session: Session | null = null;
  let otherDevicesSignedOut = 0;
  const start = (profile: UserProfile): Session => (session = { user: profile, startedAt: new Date().toISOString() });

  return {
    verifiesCredentials: true,
    getSession: async () => session,
    async signIn({ email, password }) {
      const account = accounts.get(normalizeEmail(email));
      if (!account || account.password !== password) throw new AuthError("invalid_credentials");
      return start(account.profile);
    },
    async signUp({ name, email, password }) {
      const key = normalizeEmail(email);
      if (accounts.has(key)) throw new AuthError("email_taken");
      const profile: UserProfile = { id: `cuenta_${accounts.size + 1}`, name, email: key, avatarUrl: null, createdAt: new Date().toISOString() };
      accounts.set(key, { profile, password: password ?? "" });
      return start(profile);
    },
    async signOut() {
      session = null;
    },
    async updateProfile(update) {
      if (!session) throw new AuthError("not_signed_in");
      const profile = { ...session.user, ...update };
      const account = accounts.get(profile.email);
      if (account) account.profile = profile;
      session = { ...session, user: profile };
      return profile;
    },
    async changePassword({ currentPassword, newPassword, signOutOtherDevices }) {
      if (!session) throw new AuthError("not_signed_in");
      const account = accounts.get(session.user.email);
      if (!account || account.password !== currentPassword) throw new AuthError("wrong_password");
      account.password = newPassword;
      if (signOutOtherDevices) otherDevicesSignedOut += 1;
    },
    async signOutOtherDevices() {
      if (!session) throw new AuthError("not_signed_in");
      otherDevicesSignedOut += 1;
    },
    get otherDevicesSignedOut() {
      return otherDevicesSignedOut;
    },
  } as AuthService & { readonly otherDevicesSignedOut: number };
}


/** Lo que la prueba hace del otro lado: llega un mensaje del cliente, el asistente escribe, la respuesta no sale. */
export interface MemoryInboxControls {
  requests: InboxFilter[];
  resolved: string[];
  /** Los chats eliminados, en orden. */
  removed: string[];
  notificationList: Notification[];
  replies: { conversationId: string; text: string }[];
  readMarks: string[];
  /** Un mensaje nuevo en un hilo (como si llegara por el canal): aparece en vivo. */
  receive(conversationId: string, message: ChatMessage, conversation?: Partial<ConversationSummary>): void;
  /** Cambia la conversación (por ejemplo, el asistente está «escribiendo…»). */
  update(conversationId: string, conversation: Partial<ConversationSummary>): void;
  /** La próxima respuesta del equipo no sale por el canal. */
  failNextReply(message: string): void;
  /** Los archivos que devuelve `media`, por su id. */
  files: Map<string, Blob>;
}

/** Bandeja en memoria: hilos y avisos sembrados por la prueba; filtra, marca y responde como el servidor, en vivo. */
export function createMemoryInbox(seededThreads: ConversationThread[] = [], seededNotifications: Notification[] = []): Inbox & MemoryInboxControls {
  // Copias: lo que cambia una prueba (marcar como atendida) no toca los datos sembrados de las demás.
  const threads = seededThreads.map((thread) => ({ conversation: { ...thread.conversation }, messages: [...thread.messages] }));
  const requests: InboxFilter[] = [];
  const resolved: string[] = [];
  const removed: string[] = [];
  const replies: { conversationId: string; text: string }[] = [];
  const readMarks: string[] = [];
  const files = new Map<string, Blob>();
  let replyFailure: string | null = null;
  let clock = 0;
  // Cuándo cambió cada mensaje (un reloj de la prueba): `live` devuelve solo lo que cambió desde la marca.
  const changedAt = new Map<string, number>();
  for (const thread of threads) for (const message of thread.messages) changedAt.set(message.id, 0);
  const notificationList = seededNotifications.map((item) => ({ ...item }));
  const newestFirst = (a: ConversationSummary, b: ConversationSummary) => b.lastMessageAt.localeCompare(a.lastMessageAt);
  const find = (id: string) => {
    const found = threads.find((thread) => thread.conversation.id === id);
    if (!found) throw new PersistenceError("not_found", { message: "Esa conversación no existe." });
    return found;
  };
  const touch = (message: ChatMessage) => {
    clock += 1;
    changedAt.set(message.id, clock);
  };
  return {
    requests,
    resolved,
    removed,
    notificationList,
    replies,
    readMarks,
    files,
    receive: (conversationId, message, conversation = {}) => {
      const thread = find(conversationId);
      thread.messages = [...thread.messages, message];
      touch(message);
      thread.conversation = {
        ...thread.conversation,
        lastMessageAt: message.createdAt,
        lastMessagePreview: message.body,
        messageCount: thread.messages.length,
        unreadCount: (thread.conversation.unreadCount ?? 0) + (message.author === "customer" ? 1 : 0),
        ...conversation,
      };
    },
    update: (conversationId, conversation) => {
      const thread = find(conversationId);
      thread.conversation = { ...thread.conversation, ...conversation };
    },
    failNextReply: (message) => {
      replyFailure = message;
    },
    live: async (id, since) => {
      const thread = find(id);
      const mark = since === undefined ? -1 : Number(since);
      return {
        conversation: { ...thread.conversation },
        messages: thread.messages.filter((message) => (changedAt.get(message.id) ?? 0) > mark),
        cursor: String(clock),
      };
    },
    reply: async (id, text) => {
      const thread = find(id);
      if (replyFailure) {
        const message = replyFailure;
        replyFailure = null;
        throw new PersistenceError("unknown", { message });
      }
      replies.push({ conversationId: id, text });
      const sent: ChatMessage = { id: `agente-${replies.length}`, author: "agent", body: text, intent: null, createdAt: new Date().toISOString(), kind: "text", status: "sent" };
      thread.messages = [...thread.messages, sent];
      touch(sent);
      thread.conversation = { ...thread.conversation, aiPaused: true, needsHuman: false, lastMessagePreview: text, messageCount: thread.messages.length };
      return sent;
    },
    setAssistant: async (id, active) => {
      const thread = find(id);
      thread.conversation = { ...thread.conversation, aiPaused: !active, ...(active ? { needsHuman: false, handoffReason: null } : {}) };
      return { ...thread.conversation };
    },
    markRead: async (id) => {
      readMarks.push(id);
      find(id).conversation.unreadCount = 0;
    },
    media: async (_id, mediaId) => {
      const file = files.get(mediaId);
      if (!file) throw new PersistenceError("not_found", { message: "Ese archivo no existe." });
      return file;
    },
    list: async (filter = {}) => {
      requests.push({ ...filter });
      return threads
        .map((thread) => thread.conversation)
        .filter((item) => (!filter.business || item.business.slug === filter.business) && (!filter.channel || item.channel === filter.channel) && (!filter.waitingHuman || item.needsHuman))
        .sort(newestFirst);
    },
    thread: async (id) => ({ conversation: { ...find(id).conversation }, messages: [...find(id).messages] }),
    activity: async (slug) => {
      const mine = threads.filter((thread) => thread.conversation.business.slug === slug);
      return {
        conversations: mine.length,
        conversationsToday: mine.length,
        messagesToday: mine.reduce((total, thread) => total + thread.messages.length, 0),
        testConversations: mine.filter((thread) => thread.conversation.channel === "prueba").length,
        waitingHuman: mine.filter((thread) => thread.conversation.needsHuman).length,
      };
    },
    resolveHandoff: async (id) => {
      const thread = find(id);
      resolved.push(id);
      thread.conversation = { ...thread.conversation, needsHuman: false };
      return thread.conversation;
    },
    remove: async (id) => {
      find(id);
      removed.push(id);
      threads.splice(threads.findIndex((thread) => thread.conversation.id === id), 1);
    },
    removeTestChats: async (slug) => {
      for (let index = threads.length - 1; index >= 0; index -= 1) {
        const conversation = threads[index]!.conversation;
        if (conversation.business.slug === slug && conversation.channel === "prueba") {
          removed.push(conversation.id);
          threads.splice(index, 1);
        }
      }
    },
    notifications: async () => ({ items: notificationList.map((item) => ({ ...item })), unread: notificationList.filter((item) => !item.read).length }),
    markNotificationsRead: async (ids) => {
      for (const item of notificationList) if (!ids || ids.includes(item.id)) item.read = true;
    },
  };
}
