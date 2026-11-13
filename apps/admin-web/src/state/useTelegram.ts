import { useCallback, useEffect, useState } from "react";
import type { TelegramChannel } from "../domain/channels/types";
import { useChannels } from "./channelsContext";
import { PersistenceError, persistenceErrorMessage } from "./directoryContext";

export interface TelegramState {
  channel: TelegramChannel | null;
  /** Un error general (no del campo del código). */
  error: string | null;
  /** El problema con el código pegado, en su campo. */
  tokenError: string | null;
  busy: boolean;
  /** Conecta con el código de @BotFather. Devuelve si quedó conectado. */
  connect(token: string): Promise<boolean>;
  reconnect(): Promise<void>;
  check(): Promise<void>;
  disconnect(): Promise<void>;
  clearErrors(): void;
}

/** El bot de Telegram del negocio abierto: Canales → Telegram. */
export function useTelegram(): TelegramState {
  const channels = useChannels();
  const [channel, setChannel] = useState<TelegramChannel | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tokenError, setTokenError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    channels.telegram().then(
      (loaded) => active && setChannel(loaded),
      (reason: unknown) => active && setError(persistenceErrorMessage(reason)),
    );
    return () => {
      active = false;
    };
  }, [channels]);

  const run = useCallback(async (action: () => Promise<TelegramChannel>): Promise<boolean> => {
    setBusy(true);
    setError(null);
    setTokenError(null);
    try {
      setChannel(await action());
      return true;
    } catch (reason) {
      const onToken = reason instanceof PersistenceError ? reason.problems.find((problem) => problem.path === "token") : undefined;
      if (onToken) setTokenError(onToken.message);
      else setError(persistenceErrorMessage(reason));
      return false;
    } finally {
      setBusy(false);
    }
  }, []);

  return {
    channel,
    error,
    tokenError,
    busy,
    connect: async (token) => {
      if (!token.trim()) {
        setTokenError("Pega el código que te dio @BotFather.");
        return false;
      }
      return run(() => channels.connectTelegram(token.trim()));
    },
    reconnect: async () => void (await run(() => channels.reconnectTelegram())),
    check: async () => void (await run(() => channels.checkTelegram())),
    disconnect: async () => void (await run(() => channels.disconnectTelegram())),
    clearErrors: () => {
      setError(null);
      setTokenError(null);
    },
  };
}
