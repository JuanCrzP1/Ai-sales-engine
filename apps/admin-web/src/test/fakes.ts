import contractSchema from "../../../../project/config/contracts/v1/business-config.schema.json";
import type { ApplicationServices } from "../app/compositionRoot";
import { AuthError, type Session, type UserProfile } from "../domain/auth/types";
import { normalizeEmail } from "../domain/auth/validation";
import type { ContractSchema } from "../domain/config/contractSchema";
import { paymentHolders } from "../domain/config/document";
import type { BusinessDocument, BusinessSummary, Diagnostic, PaymentFields, PaymentFieldState, PaymentValues, VersionInfo, VersionStatus } from "../domain/config/types";
import { createLocalOperatorAuthService } from "../infrastructure/local/localOperatorAuthService";
import type { AISettings, AssistantLab, ConfigSource } from "../repositories/assistantLab";
import type { AuthService } from "../repositories/authService";
import type { BusinessDirectory } from "../repositories/businessDirectory";
import type { ConfigRepository, StoredConfig } from "../repositories/configRepository";
import { PersistenceError } from "../repositories/persistenceError";

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

type FailingOperation = "list" | "create" | "remove" | "importExisting" | "contractSchema" | "load" | "save" | "review" | "history" | "publish" | "rollback" | "restore";

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
    create: async ({ slug, name }) => {
      check("create");
      if (businesses.has(slug)) throw new PersistenceError("duplicate", { message: "Ya existe un negocio con ese identificador.", problems: [{ path: "slug", message: "Ya existe un negocio con ese identificador." }] });
      const business: MemoryBusiness = { slug, name, versions: [], published: [] };
      businesses.set(slug, business);
      return summary(business);
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
}

/** Sustituto en memoria de la inteligencia artificial y del área de pruebas: responde «Respuesta a: …» sin red. */
export function createMemoryAssistantLabs(): MemoryAssistantLabs {
  const keys = new Map<string, string>();
  const models = new Map<string, string | null>();
  const messages: MemoryAssistantLabs["messages"] = [];
  const resets: string[] = [];
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

/** Servicios como los de la aplicación, sobre el backend en memoria. */
export function createTestServices(backend: MemoryBackend = createMemoryBackend(), overrides: Partial<ApplicationServices> = {}): ApplicationServices {
  return {
    auth: createLocalOperatorAuthService(),
    directory: backend.directory,
    createConfigRepository: backend.createConfigRepository,
    createAssistantLab: createMemoryAssistantLabs().create,
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
  };
}
