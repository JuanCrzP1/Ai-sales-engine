/**
 * Inteligencia artificial y área de pruebas de UN negocio. La clave de IA solo viaja hacia el servidor: de vuelta llega si está
 * configurada y sus últimos caracteres, nunca la clave.
 */
export interface AISettings {
  provider: "openrouter";
  /** Modelo de OpenRouter (`proveedor/modelo`), o null para usar el del motor. */
  model: string | null;
  key: { configured: boolean; hint: string | null };
}

export interface SaveAISettings {
  model: string | null;
  /** Solo cuando cambia. Sin ella, se conserva la guardada. */
  apiKey?: string;
  clearKey?: boolean;
}

export interface KeyCheck {
  valid: boolean;
  message: string;
}

/** Qué versión responde: la que se está editando (para probar antes de publicar) o la publicada. */
export type ConfigSource = "draft" | "published";

export interface AssistantReply {
  sessionId: string;
  source: ConfigSource;
  version: number;
  reply: string;
  intent: string | null;
  /** Falso si respondió el motor sin la IA, por ejemplo porque el proveedor rechazó la clave o el modelo. */
  aiAnswered: boolean;
}

export interface AssistantLab {
  getAISettings(): Promise<AISettings>;
  saveAISettings(input: SaveAISettings): Promise<AISettings>;
  verifyAIKey(): Promise<KeyCheck>;
  sendMessage(input: { message: string; source: ConfigSource; sessionId: string | null }): Promise<AssistantReply>;
  resetConversation(sessionId: string): Promise<void>;
}
