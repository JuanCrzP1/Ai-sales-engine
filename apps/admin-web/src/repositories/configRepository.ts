import type { AssistantConfig } from "../domain/config/types";

export interface StoredConfig {
  config: AssistantConfig;
  /** Momento confirmado por el almacenamiento en que se guardó. */
  savedAt: string;
}

/**
 * Persistencia de la configuración de UNA cuenta. Asíncrono para admitir tanto el
 * almacenamiento del navegador como una API. Los fallos se rechazan con `PersistenceError`.
 */
export interface ConfigRepository {
  /** La configuración guardada, o null si la cuenta aún no tiene ninguna. */
  load(): Promise<StoredConfig | null>;
  /** Resuelve solo cuando el guardado terminó correctamente. */
  save(config: AssistantConfig): Promise<StoredConfig>;
  clear(): Promise<void>;
}
