/**
 * El catálogo de Integraciones: qué se puede conectar, en qué categoría va y en qué estado está para este negocio. Puro: recibe lo
 * que ya se sabe (las claves de API y si la IA tiene su clave) y devuelve las tarjetas; la pantalla solo las dibuja.
 *
 * Solo aparece como disponible lo que de verdad funciona hoy; lo demás va en «Próximamente».
 */
import { connectionState, type ApiKey } from "./types";

export type IntegrationCategory = "ai" | "platforms" | "agents" | "security";

export const INTEGRATION_CATEGORIES: { id: IntegrationCategory; label: string }[] = [
  { id: "ai", label: "Inteligencia artificial" },
  { id: "platforms", label: "Plataformas" },
  { id: "agents", label: "Agentes de IA" },
  { id: "security", label: "Seguridad" },
];

export type CategoryFilter = IntegrationCategory | "all";

/** El logo de cada integración (lo dibuja `components/brand/IntegrationMark`). */
export type IntegrationMarkId = "openrouter" | "openai" | "anthropic" | "gemini" | "mcp" | "api" | "keys";

/** Adónde lleva su tarjeta: la pantalla lo traduce a una dirección del panel. */
export type IntegrationTarget = "ai-settings" | "assistant-api" | "api-keys";

export type IntegrationStatus =
  /** Conectada: `detail` dice cómo va (cuándo se usó, cuántas claves). */
  | { kind: "active"; detail: string; lastUsedAt?: string | null }
  | { kind: "available" }
  | { kind: "soon" };

export interface CatalogEntry {
  id: string;
  mark: IntegrationMarkId;
  name: string;
  category: IntegrationCategory;
  tagline: string;
  status: IntegrationStatus;
  target: IntegrationTarget | null;
}

export interface CatalogInput {
  keys: ApiKey[];
  /** Si la IA del negocio tiene su clave; null mientras no se sabe. */
  aiConfigured: boolean | null;
}

export function categoryLabel(category: IntegrationCategory): string {
  return INTEGRATION_CATEGORIES.find((item) => item.id === category)?.label ?? category;
}

export function buildCatalog({ keys, aiConfigured }: CatalogInput): CatalogEntry[] {
  const api = connectionState(keys);
  const activeKeys = keys.filter((key) => key.active).length;
  return [
    {
      id: "openrouter",
      mark: "openrouter",
      name: "OpenRouter",
      category: "ai",
      tagline: "La IA con la que responde tu asistente: modelos de OpenAI, Google, Anthropic y más con una sola clave.",
      status: aiConfigured ? { kind: "active", detail: "Conectada" } : { kind: "available" },
      target: "ai-settings",
    },
    {
      id: "assistant-api",
      mark: "api",
      name: "API del asistente",
      category: "platforms",
      tagline: "Conecta tu asistente a cualquier plataforma que haga peticiones HTTP: ella le manda el mensaje y envía la respuesta.",
      status:
        api.kind === "connected" ? { kind: "active", detail: "En uso", lastUsedAt: api.lastUsedAt }
        : api.kind === "ready" ? { kind: "active", detail: "Lista · todavía sin usar", lastUsedAt: null }
        : { kind: "available" },
      target: "assistant-api",
    },
    {
      id: "api-keys",
      mark: "keys",
      name: "Claves de API",
      category: "security",
      tagline: "Todas las claves de este negocio en un lugar: para qué es cada una, cuándo se usó y revocarla en un clic.",
      status: activeKeys > 0 ? { kind: "active", detail: activeKeys === 1 ? "1 clave activa" : `${activeKeys} claves activas` } : { kind: "available" },
      target: "api-keys",
    },
    {
      id: "mcp",
      mark: "mcp",
      name: "Agentes de IA (MCP)",
      category: "agents",
      tagline: "Que Claude, ChatGPT, Cursor, Gemini o n8n configuren y consulten tu plataforma, con los mismos permisos del panel.",
      status: { kind: "soon" },
      target: null,
    },
    {
      id: "openai",
      mark: "openai",
      name: "OpenAI",
      category: "ai",
      tagline: "GPT con tu propia clave de OpenAI, sin pasar por OpenRouter.",
      status: { kind: "soon" },
      target: null,
    },
    {
      id: "anthropic",
      mark: "anthropic",
      name: "Anthropic",
      category: "ai",
      tagline: "Claude con tu propia clave de Anthropic.",
      status: { kind: "soon" },
      target: null,
    },
    {
      id: "gemini",
      mark: "gemini",
      name: "Google Gemini",
      category: "ai",
      tagline: "Gemini con tu clave de Google AI Studio.",
      status: { kind: "soon" },
      target: null,
    },
  ];
}

function normalized(text: string): string {
  return text.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

/** Las de una categoría que coinciden con lo buscado (nombre, descripción o categoría; sin importar tildes). */
export function filterCatalog(entries: CatalogEntry[], category: CategoryFilter, query: string): CatalogEntry[] {
  const words = normalized(query).split(/\s+/).filter(Boolean);
  return entries.filter((entry) => {
    if (category !== "all" && entry.category !== category) return false;
    const haystack = normalized(`${entry.name} ${entry.tagline} ${categoryLabel(entry.category)}`);
    return words.every((word) => haystack.includes(word));
  });
}

/** Activas arriba, luego las disponibles y al final las que llegan pronto. */
export function groupCatalog(entries: CatalogEntry[]): { active: CatalogEntry[]; available: CatalogEntry[]; soon: CatalogEntry[] } {
  return {
    active: entries.filter((entry) => entry.status.kind === "active"),
    available: entries.filter((entry) => entry.status.kind === "available"),
    soon: entries.filter((entry) => entry.status.kind === "soon"),
  };
}

export function isCategory(value: string | null): value is IntegrationCategory {
  return INTEGRATION_CATEGORIES.some((category) => category.id === value);
}
