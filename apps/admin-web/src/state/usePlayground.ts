import { useCallback, useRef, useState } from "react";
import type { ConfigSource } from "../repositories/assistantLab";
import { PersistenceError, persistenceErrorMessage } from "../repositories/persistenceError";
import { useAssistantLab } from "./assistantLabContext";

export type { ConfigSource } from "../repositories/assistantLab";

export interface ChatTurn {
  id: number;
  from: "customer" | "assistant";
  text: string;
  intent?: string | null;
  /** Falso si respondió el motor sin la IA. */
  aiAnswered?: boolean;
}

export interface PlaygroundState {
  source: ConfigSource;
  /** Cambiar la versión empieza una conversación nueva: mezclar dos configuraciones confundiría la prueba. */
  setSource: (source: ConfigSource) => void;
  turns: ChatTurn[];
  sending: boolean;
  error: string | null;
  /** El negocio no tiene clave de IA: hay que agregarla antes de probar. */
  missingKey: boolean;
  /** La versión con la que respondió el último mensaje. */
  version: number | null;
  send: (message: string) => Promise<void>;
  restart: () => Promise<void>;
}

/** Una conversación de prueba con el asistente del negocio abierto. Vive solo en esta pantalla: no se guarda en el navegador. */
export function usePlayground(): PlaygroundState {
  const lab = useAssistantLab();
  const [source, setSourceState] = useState<ConfigSource>("draft");
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [missingKey, setMissingKey] = useState(false);
  const [version, setVersion] = useState<number | null>(null);
  const sessionId = useRef<string | null>(null);
  const nextId = useRef(1);

  const forget = useCallback(async () => {
    const previous = sessionId.current;
    sessionId.current = null;
    setTurns([]);
    setVersion(null);
    setError(null);
    if (previous) await lab.resetConversation(previous).catch(() => undefined);
  }, [lab]);

  const send = useCallback(
    async (message: string) => {
      const text = message.trim();
      if (!text || sending) return;
      setSending(true);
      setError(null);
      setTurns((current) => [...current, { id: nextId.current++, from: "customer", text }]);
      try {
        const answer = await lab.sendMessage({ message: text, source, sessionId: sessionId.current });
        sessionId.current = answer.sessionId;
        setVersion(answer.version);
        setMissingKey(false);
        setTurns((current) => [...current, { id: nextId.current++, from: "assistant", text: answer.reply, intent: answer.intent, aiAnswered: answer.aiAnswered }]);
      } catch (reason) {
        const keyMissing = reason instanceof PersistenceError && reason.code === "ai_key_missing";
        setMissingKey(keyMissing);
        setError(keyMissing ? null : persistenceErrorMessage(reason));
      } finally {
        setSending(false);
      }
    },
    [lab, sending, source],
  );

  const setSource = useCallback(
    (next: ConfigSource) => {
      setSourceState(next);
      void forget();
    },
    [forget],
  );

  return { source, setSource, turns, sending, error, missingKey, version, send, restart: forget };
}
