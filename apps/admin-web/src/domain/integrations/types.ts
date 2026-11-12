/**
 * Integraciones: conectar el asistente con otras herramientas.
 * - Claves de API: dejan que otro sistema use la plataforma sin una sesión del panel, con permisos por área y a los negocios
 *   elegidos. Se muestran una sola vez.
 * - Agentes de IA (MCP): Claude, Cursor o n8n trabajan en los negocios con una clave.
 * - API del asistente: otra plataforma (de automatización, una web, un servidor propio) manda el mensaje de un cliente y recibe la
 *   respuesta. Las guías por plataforma solo dicen «Probado» cuando se probó con un flujo real.
 */
import curlSample from "./samples/curl.txt?raw";
import javascriptSample from "./samples/javascript.txt?raw";
import pythonSample from "./samples/python.txt?raw";

/** Conversar con el asistente (la API del asistente): solo con una clave de un negocio. */
export const SCOPE_ASSISTANT_CHAT = "assistant:chat";
/** El área de «Conversar con el asistente»; las demás son de los agentes de IA (MCP). */
export const CHAT_AREA = "chat";

export type AccessLevel = "read" | "write";
/** A qué negocios entra una clave: uno, todos los de la cuenta (también los que se creen después) o algunos. */
export type KeyReach = "one" | "all" | "some";

/** Un área que se puede permitir a una clave y lo que deja cada nivel (null: ese nivel no existe en el área). La define el motor. */
export interface KeyArea {
  id: string;
  label: string;
  read: string | null;
  write: string | null;
  oneBusinessOnly: boolean;
}

export interface ApiKey {
  id: string;
  name: string;
  /** El comienzo visible (`ase_live_Ab12Cd`), para reconocerla. */
  prefix: string;
  scopes: string[];
  /** Lo que puede, por área. */
  permissions: Record<string, AccessLevel>;
  reach: KeyReach;
  /** Los negocios de una clave de uno o de algunos (identificadores). */
  businesses: string[];
  createdAt: string;
  createdBy: string | null;
  lastUsedAt: string | null;
  revokedAt: string | null;
  expiresAt: string | null;
  /** Sirve: no está revocada ni vencida. */
  active: boolean;
  expired: boolean;
  /** `key`: un valor fijo que se mostró una vez. `oauth`: una conexión que autorizaste desde el agente (Claude, ChatGPT) iniciando sesión. */
  kind: KeyKind;
}

export type KeyKind = "key" | "oauth";

/** Qué agente pide conectarse con inicio de sesión (la pantalla de autorización), o por qué no se puede. */
export type AuthorizationPrompt =
  | { ready: true; clientName: string; redirectHost: string; areas: KeyArea[] }
  | { ready: false; message: string; redirectTo: string | null };

/** Lo que la persona decide en la pantalla de autorización. `params` son los de la dirección, tal como los puso el agente. */
export interface AuthorizationDecision {
  params: Record<string, string>;
  approve: boolean;
  permissions?: Record<string, AccessLevel>;
  reach?: KeyReach;
  businesses?: string[];
}

/** Una clave recién creada: la única vez que se ve completa. */
export interface CreatedApiKey {
  key: ApiKey;
  secret: string;
}

/** Lo que se pide al crear una clave. `expiresInDays` null: no vence. */
export interface NewKeyRequest {
  name: string;
  permissions: Record<string, AccessLevel>;
  reach: KeyReach;
  businesses?: string[];
  expiresInDays: number | null;
}

export const EXPIRY_OPTIONS: { value: number | null; label: string }[] = [
  { value: 30, label: "30 días" },
  { value: 90, label: "90 días" },
  { value: 365, label: "1 año" },
  { value: null, label: "No vence" },
];

export interface IntegrationsOverview {
  /** La dirección pública de la API del asistente, o null si el motor no tiene una (en este equipo sin ngrok). */
  assistantApiUrl: string | null;
  /** La dirección del servidor MCP para pegar en el agente, o null si no está disponible. */
  mcpUrl: string | null;
  /** Claude (web y app) y ChatGPT se conectan pegando la dirección e iniciando sesión, sin clave (en el panel publicado). */
  mcpSignIn: boolean;
  chatKeys: number;
  activeKeys: number;
  areas: KeyArea[];
}

/** Una clave para agentes de IA: puede algo más que conversar con el asistente. */
export function isAgentKey(key: Pick<ApiKey, "permissions">): boolean {
  return Object.keys(key.permissions).some((area) => area !== CHAT_AREA);
}

/** Lo que puede una clave, en palabras: «Asistente IA: ver y editar · Negocios: ver». */
export function permissionSummary(key: Pick<ApiKey, "permissions">, areas: KeyArea[]): string {
  return areas
    .filter((area) => key.permissions[area.id])
    .map((area) => {
      if (area.id === CHAT_AREA) return area.label;
      const level = key.permissions[area.id];
      return `${area.label}: ${level === "write" ? (area.read ? "ver y editar" : "escribir") : "ver"}`;
    })
    .join(" · ");
}

/** A qué negocios entra, en palabras. */
export function reachLabel(key: Pick<ApiKey, "reach" | "businesses">): string {
  if (key.reach === "all") return "Todos tus negocios";
  if (key.reach === "one") return "Solo este negocio";
  return key.businesses.length === 1 ? "1 negocio" : `${key.businesses.length} negocios`;
}

export interface McpSnippet {
  id: "claude-code" | "json" | "n8n";
  label: string;
  hint: string;
  code: string;
}

export const KEY_PLACEHOLDER = "TU_CLAVE";

/** Cómo conectar cada agente al servidor MCP, con la clave real (al crearla) o un marcador. */
export function mcpSnippets(url: string, secret: string = KEY_PLACEHOLDER): McpSnippet[] {
  return [
    {
      id: "claude-code",
      label: "Claude Code",
      hint: "Pégalo en tu terminal.",
      code: `claude mcp add --transport http ai-sales-engine ${url} --header "Authorization: Bearer ${secret}"`,
    },
    {
      id: "json",
      label: "Cursor y otros",
      hint: "En la configuración de servidores MCP del programa (mcp.json). Sirve también para Claude Desktop, Windsurf y Gemini CLI.",
      code: JSON.stringify({ mcpServers: { "ai-sales-engine": { url, headers: { Authorization: `Bearer ${secret}` } } } }, null, 2),
    },
    {
      id: "n8n",
      label: "n8n",
      hint: "Nodo «MCP Client»: transporte HTTP Streamable y autenticación por encabezado.",
      code: `URL: ${url}\nEncabezado: Authorization\nValor: Bearer ${secret}`,
    },
  ];
}

/** Lo que responde la API del asistente (ver docs/api.md). */
export interface AssistantApiReply {
  conversation_id: string;
  reply: string;
  parts: string[];
  handoff: boolean;
  handoff_reason: string | null;
  attended_by: "assistant" | "team";
  intent: string | null;
  stage: string;
  fallback: boolean;
  duplicate: boolean;
}

/** El encabezado que lleva cada petición; «TU_CLAVE» se cambia por la clave creada. */
export const AUTHORIZATION_HEADER = "Authorization: Bearer TU_CLAVE";

/** Las cabeceras de cada petición, como nombre y valor (así las piden las plataformas). */
export const REQUEST_HEADERS: { name: string; value: string; hint?: string }[] = [
  { name: "Authorization", value: "Bearer TU_CLAVE", hint: "Cambia TU_CLAVE por tu clave (empieza por ase_live_). Deja «Bearer» y un espacio antes." },
  { name: "Content-Type", value: "application/json" },
];

/** Un cuerpo de ejemplo con datos de verdad: lo que cualquier plataforma debe mandar. */
export const EXAMPLE_REQUEST_BODY = '{"contact": {"id": "573001112233", "name": "Laura"}, "message": "Hola, ¿qué precios tienen?"}';

/**
 * Leona (probado el 12 de noviembre de 2026 con un flujo real). Sus variables del sistema son `{phone_number}` y `{full_name}`;
 * sus campos personalizados se escriben sin prefijo (`{ase_mensaje}`). Ojo: su botón «Probar petición» no cambia las variables.
 */
export const LEONA = {
  messageField: "ase_mensaje",
  replyField: "ase_respuesta",
  handoffField: "ase_handoff",
  requestBody: '{"contact": {"id": "{phone_number}", "name": "{full_name}"}, "message": "{ase_mensaje}"}',
} as const;

export type CodeLanguage = "curl" | "javascript" | "python";

const CODE_SAMPLES: Record<CodeLanguage, string> = { curl: curlSample, javascript: javascriptSample, python: pythonSample };

export const CODE_LANGUAGES: { value: CodeLanguage; label: string }[] = [
  { value: "curl", label: "cURL" },
  { value: "javascript", label: "JavaScript" },
  { value: "python", label: "Python" },
];

/**
 * El mismo pedido en cada lenguaje, para quien programa su propia integración. Los ejemplos son texto para copiar (`samples/*.txt`),
 * no código del panel: así las pruebas que vigilan las llamadas y las variables de entorno del panel no los confunden con las suyas.
 */
export function codeExample(language: CodeLanguage, url: string): string {
  return CODE_SAMPLES[language].trimEnd().replaceAll("{{URL}}", url);
}

/** Si alguna plataforma ya está usando la API: el último uso de las claves activas para conversar. */
export type ConnectionState = { kind: "connected"; lastUsedAt: string } | { kind: "ready" } | { kind: "no-key" };

/** Si algún agente de IA está conectado: el último uso de las claves de agente que sirven. */
export function agentConnection(keys: ApiKey[]): ConnectionState {
  const agents = keys.filter((key) => key.active && isAgentKey(key));
  if (agents.length === 0) return { kind: "no-key" };
  const lastUsed = agents.map((key) => key.lastUsedAt).filter((value): value is string => value !== null).sort().pop();
  return lastUsed ? { kind: "connected", lastUsedAt: lastUsed } : { kind: "ready" };
}

export function connectionState(keys: ApiKey[]): ConnectionState {
  const chatKeys = keys.filter((key) => key.active && key.scopes.includes(SCOPE_ASSISTANT_CHAT));
  if (chatKeys.length === 0) return { kind: "no-key" };
  const lastUsed = chatKeys.map((key) => key.lastUsedAt).filter((value): value is string => value !== null).sort().pop();
  return lastUsed ? { kind: "connected", lastUsedAt: lastUsed } : { kind: "ready" };
}
