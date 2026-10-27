import type { AssistantConfig } from "../../domain/config/types";
import type { ConfigRepository, StoredConfig } from "../../repositories/configRepository";
import { PersistenceError } from "../../repositories/persistenceError";
import { readJson, removeKey, safeLocalStorage, writeJson, type MaybeStorage } from "../browser/browserStorage";

/**
 * Configuración de una cuenta guardada en el localStorage de este navegador.
 * No está conectada al motor ni a ningún servidor.
 */

export function configStorageKey(accountId: string): string {
  return `ai-sales-engine.admin-web.config.${accountId}.v1`;
}

export function createLocalConfigRepository(
  accountId: string,
  storage: MaybeStorage = safeLocalStorage(),
): ConfigRepository {
  const key = configStorageKey(accountId);
  return {
    async load() {
      const value = readJson(storage, key);
      if (value === undefined) return null;
      // Datos con otra forma: se informa en vez de sobrescribirlos con una configuración vacía.
      if (!isStoredConfig(value)) throw new PersistenceError("corrupted");
      return value;
    },
    async save(config) {
      const stored: StoredConfig = { config, savedAt: new Date().toISOString() };
      writeJson(storage, key, stored);
      return stored;
    },
    async clear() {
      removeKey(storage, key);
    },
  };
}

function isStoredConfig(value: unknown): value is StoredConfig {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Partial<StoredConfig>;
  const config = candidate.config as Partial<AssistantConfig> | undefined;
  return (
    typeof candidate.savedAt === "string" &&
    config?.version === 1 &&
    typeof config.business === "object" &&
    Array.isArray(config.offerings) &&
    typeof config.payments === "object" &&
    typeof config.closing === "object" &&
    typeof config.behavior === "object" &&
    typeof config.messages === "object"
  );
}
