import { useCallback, useEffect, useRef, useState } from "react";
import { hasNews, liveTiming, mergeMessages, pollDelay } from "../domain/inbox/live";
import type { BusinessActivity, ChatMessage, ConversationSummary, ConversationThread, InboxFilter, MediaInfo } from "../domain/inbox/types";
import { persistenceErrorMessage } from "../repositories/persistenceError";
import { useInbox } from "./inboxContext";
import { attachmentKind } from "../domain/inbox/attachments";

export type Loadable<T> = { status: "loading" } | { status: "error"; message: string } | { status: "ready"; data: T };

const hidden = () => typeof document !== "undefined" && document.visibilityState === "hidden";

/**
 * La bandeja en vivo: la lista de conversaciones con su filtro y el chat abierto, que se actualizan solos (sin recargar la página).
 * La lista pregunta cada pocos segundos; el chat abierto pide solo lo que cambió, más seguido si hay movimiento, y nada con la
 * pestaña oculta. Desde aquí el equipo responde, pausa o reanuda la IA y marca lo leído.
 */
export function useConversations(initialFilter: InboxFilter, initialSelected: string | null = null) {
  const inbox = useInbox();
  const [filter, setFilter] = useState<InboxFilter>(initialFilter);
  const [list, setList] = useState<Loadable<ConversationSummary[]>>({ status: "loading" });
  const [selectedId, setSelectedId] = useState<string | null>(initialSelected);
  const [thread, setThread] = useState<Loadable<ConversationThread> | null>(null);
  const [attempt, setAttempt] = useState(0);

  // La lista: la primera vez con «cargando»; después se refresca sola, sin parpadeos.
  useEffect(() => {
    let active = true;
    let timer: number | undefined;
    setList({ status: "loading" });
    const load = async (first: boolean) => {
      if (!first && hidden()) {
        timer = window.setTimeout(() => void load(false), liveTiming.listMs);
        return;
      }
      try {
        const items = await inbox.list(filter);
        if (active) setList({ status: "ready", data: items });
      } catch (error) {
        if (active && first) setList({ status: "error", message: persistenceErrorMessage(error) });
      }
      if (active) timer = window.setTimeout(() => void load(false), liveTiming.listMs);
    };
    void load(true);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [inbox, filter, attempt]);

  // El chat abierto: primero todo; después solo lo nuevo o lo que cambió desde la marca del servidor.
  useEffect(() => {
    if (!selectedId) {
      setThread(null);
      return;
    }
    let active = true;
    let timer: number | undefined;
    let cursor: string | undefined;
    let busy = false;
    let lastChange = Date.now();
    setThread({ status: "loading" });

    const tick = async () => {
      if (!active || busy) return;
      if (hidden()) {
        timer = window.setTimeout(() => void tick(), liveTiming.calmMs);
        return;
      }
      busy = true;
      try {
        const changes = await inbox.live(selectedId, cursor);
        if (!active) return;
        cursor = changes.cursor;
        setThread((previous) => {
          if (!previous || previous.status !== "ready") return { status: "ready", data: { conversation: changes.conversation, messages: changes.messages } };
          if (hasNews(previous.data.messages, changes.messages) || previous.data.conversation.assistantTyping !== changes.conversation.assistantTyping) {
            lastChange = Date.now();
          }
          return { status: "ready", data: { conversation: changes.conversation, messages: mergeMessages(previous.data.messages, changes.messages) } };
        });
        setList((previous) => (previous.status === "ready" ? { status: "ready", data: previous.data.map((item) => (item.id === changes.conversation.id ? changes.conversation : item)) } : previous));
      } catch (error) {
        // Si falla la primera vez se informa; después se sigue mostrando lo último y se vuelve a intentar.
        if (active && cursor === undefined) setThread({ status: "error", message: persistenceErrorMessage(error) });
      } finally {
        busy = false;
      }
      if (active) timer = window.setTimeout(() => void tick(), pollDelay(lastChange, Date.now()));
    };

    const onVisible = () => {
      if (!hidden()) {
        window.clearTimeout(timer);
        void tick();
      }
    };
    void tick();
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      active = false;
      window.clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [inbox, selectedId, attempt]);

  const patchConversation = useCallback((conversation: ConversationSummary) => {
    setThread((previous) => (previous?.status === "ready" && previous.data.conversation.id === conversation.id ? { status: "ready", data: { ...previous.data, conversation } } : previous));
    setList((previous) => (previous.status === "ready" ? { status: "ready", data: previous.data.map((item) => (item.id === conversation.id ? conversation : item)) } : previous));
  }, []);

  const patchMessages = useCallback((change: (messages: ChatMessage[]) => ChatMessage[], conversation?: Partial<ConversationSummary>) => {
    setThread((previous) =>
      previous?.status === "ready"
        ? { status: "ready", data: { conversation: { ...previous.data.conversation, ...conversation }, messages: change(previous.data.messages) } }
        : previous,
    );
  }, []);

  // Abrir un chat con mensajes sin leer los marca como leídos (también los que llegan mientras está abierto).
  const unread = thread?.status === "ready" ? (thread.data.conversation.unreadCount ?? 0) : 0;
  const readingId = thread?.status === "ready" ? thread.data.conversation.id : null;
  useEffect(() => {
    if (!readingId || unread === 0 || hidden()) return;
    inbox.markRead(readingId).then(
      () => {
        setThread((previous) =>
          previous?.status === "ready" && previous.data.conversation.id === readingId
            ? { status: "ready", data: { ...previous.data, conversation: { ...previous.data.conversation, unreadCount: 0 } } }
            : previous,
        );
        setList((previous) => (previous.status === "ready" ? { status: "ready", data: previous.data.map((item) => (item.id === readingId ? { ...item, unreadCount: 0 } : item)) } : previous));
      },
      () => undefined,
    );
  }, [inbox, readingId, unread]);

  const reload = useCallback(() => setAttempt((count) => count + 1), []);

  /** Alguien del equipo ya atendió a quien pidió una persona: deja de esperar. */
  const resolveHandoff = useCallback(
    async (conversationId: string) => {
      patchConversation(await inbox.resolveHandoff(conversationId));
    },
    [inbox, patchConversation],
  );

  /** Reanuda (`true`) o pausa (`false`) la IA en el chat. */
  const setAssistant = useCallback(
    async (conversationId: string, active: boolean) => {
      patchConversation(await inbox.setAssistant(conversationId, active));
    },
    [inbox, patchConversation],
  );

  /**
   * El equipo responde: el mensaje aparece enseguida («enviando») y la IA queda pausada en el chat. Si no sale, se quita de la
   * vista y se informa (el texto queda en la caja para intentar de nuevo; si el servidor lo guardó como no enviado, llega así).
   */
  const reply = useCallback(
    async (conversationId: string, text: string) => {
      const localId = `local-${Date.now()}`;
      const pending: ChatMessage = { id: localId, author: "agent", body: text, intent: null, createdAt: new Date().toISOString(), kind: "text", status: "sending" };
      patchMessages((messages) => [...messages, pending], { aiPaused: true, needsHuman: false });
      try {
        const saved = await inbox.reply(conversationId, text);
        patchMessages((messages) => mergeMessages(messages.filter((message) => message.id !== localId), [saved]));
      } catch (error) {
        patchMessages((messages) => messages.filter((message) => message.id !== localId));
        throw error;
      }
    },
    [inbox, patchMessages],
  );

  /** El equipo envía un archivo: aparece enseguida («enviando») con su texto, y la IA queda pausada. Si no sale, se quita y se informa. */
  const sendAttachment = useCallback(
    async (conversationId: string, file: File, caption: string) => {
      const localId = `local-archivo-${Date.now()}`;
      const kind = attachmentKind(file.type) ?? "document";
      const pending: ChatMessage = { id: localId, author: "agent", body: caption, intent: null, createdAt: new Date().toISOString(), kind, status: "sending" };
      patchMessages((messages) => [...messages, pending], { aiPaused: true, needsHuman: false });
      try {
        const saved = await inbox.sendAttachment(conversationId, file, caption);
        patchMessages((messages) => mergeMessages(messages.filter((message) => message.id !== localId), [saved]));
      } catch (error) {
        patchMessages((messages) => messages.filter((message) => message.id !== localId));
        throw error;
      }
    },
    [inbox, patchMessages],
  );

  /** El archivo de una respuesta rápida sale desde el servidor: aparece enseguida («enviando») con su texto, como un archivo adjunto. */
  const sendQuickReplyFile = useCallback(
    async (conversationId: string, fileId: string, caption: string, label: string) => {
      const localId = `local-rapida-${Date.now()}`;
      const pending: ChatMessage = { id: localId, author: "agent", body: [label, caption].filter(Boolean).join(" "), intent: null, createdAt: new Date().toISOString(), kind: "text", status: "sending" };
      patchMessages((messages) => [...messages, pending], { aiPaused: true, needsHuman: false });
      try {
        const saved = await inbox.sendQuickReplyFile(conversationId, fileId, caption);
        patchMessages((messages) => mergeMessages(messages.filter((message) => message.id !== localId), [saved]));
      } catch (error) {
        patchMessages((messages) => messages.filter((message) => message.id !== localId));
        throw error;
      }
    },
    [inbox, patchMessages],
  );

  /** Un chat ya eliminado en el servidor: sale de la lista y, si estaba abierto, se cierra. */
  const forget = useCallback((conversationId: string) => {
    setList((previous) => (previous.status === "ready" ? { status: "ready", data: previous.data.filter((item) => item.id !== conversationId) } : previous));
    setSelectedId((current) => (current === conversationId ? null : current));
  }, []);

  /** Borra de una vez los chats de «Probar asistente» del negocio. */
  const removeTestChats = useCallback(
    async (business: string) => {
      await inbox.removeTestChats(business);
      const isGone = (item: ConversationSummary) => item.channel === "prueba" && item.business.slug === business;
      setList((previous) => {
        if (previous.status !== "ready") return previous;
        const open = previous.data.find((item) => item.id === selectedId);
        if (open && isGone(open)) setSelectedId(null);
        return { status: "ready", data: previous.data.filter((item) => !isGone(item)) };
      });
    },
    [inbox, selectedId],
  );

  return { filter, setFilter, list, selectedId, select: setSelectedId, thread, reload, resolveHandoff, setAssistant, reply, sendAttachment, sendQuickReplyFile, forget, removeTestChats };
}

/** Una URL local para mostrar un archivo de la conversación (se descarga con la sesión del usuario y se libera al salir). */
export function useMediaUrl(conversationId: string, media: MediaInfo | null | undefined): Loadable<string> | null {
  const inbox = useInbox();
  const [state, setState] = useState<Loadable<string> | null>(null);
  const mediaId = media?.id ?? null;
  const url = useRef<string | null>(null);
  useEffect(() => {
    if (!mediaId) {
      setState(null);
      return;
    }
    let active = true;
    setState({ status: "loading" });
    inbox.media(conversationId, mediaId).then(
      (blob) => {
        if (!active) return;
        url.current = URL.createObjectURL(blob);
        setState({ status: "ready", data: url.current });
      },
      (error: unknown) => active && setState({ status: "error", message: persistenceErrorMessage(error) }),
    );
    return () => {
      active = false;
      if (url.current) URL.revokeObjectURL(url.current);
      url.current = null;
    };
  }, [inbox, conversationId, mediaId]);
  return state;
}

/** La actividad de hoy de un negocio, para su inicio. */
export function useBusinessActivity(slug: string): Loadable<BusinessActivity> {
  const inbox = useInbox();
  const [state, setState] = useState<Loadable<BusinessActivity>>({ status: "loading" });
  useEffect(() => {
    let active = true;
    setState({ status: "loading" });
    inbox.activity(slug).then(
      (data) => active && setState({ status: "ready", data }),
      (error: unknown) => active && setState({ status: "error", message: persistenceErrorMessage(error) }),
    );
    return () => {
      active = false;
    };
  }, [inbox, slug]);
  return state;
}
