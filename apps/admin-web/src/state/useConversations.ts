import { useCallback, useEffect, useState } from "react";
import type { BusinessActivity, ConversationSummary, ConversationThread, InboxFilter } from "../domain/inbox/types";
import { persistenceErrorMessage } from "../repositories/persistenceError";
import { useInbox } from "./inboxContext";

export type Loadable<T> = { status: "loading" } | { status: "error"; message: string } | { status: "ready"; data: T };

/** La lista de conversaciones con su filtro, y el hilo abierto. Se recarga al cambiar el filtro o al pedirlo. */
export function useConversations(initialFilter: InboxFilter) {
  const inbox = useInbox();
  const [filter, setFilter] = useState<InboxFilter>(initialFilter);
  const [list, setList] = useState<Loadable<ConversationSummary[]>>({ status: "loading" });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [thread, setThread] = useState<Loadable<ConversationThread> | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    setList({ status: "loading" });
    inbox.list(filter).then(
      (items) => active && setList({ status: "ready", data: items }),
      (error: unknown) => active && setList({ status: "error", message: persistenceErrorMessage(error) }),
    );
    return () => {
      active = false;
    };
  }, [inbox, filter, attempt]);

  useEffect(() => {
    if (!selectedId) {
      setThread(null);
      return;
    }
    let active = true;
    setThread({ status: "loading" });
    inbox.thread(selectedId).then(
      (loaded) => active && setThread({ status: "ready", data: loaded }),
      (error: unknown) => active && setThread({ status: "error", message: persistenceErrorMessage(error) }),
    );
    return () => {
      active = false;
    };
  }, [inbox, selectedId, attempt]);

  const reload = useCallback(() => setAttempt((count) => count + 1), []);
  return { filter, setFilter, list, selectedId, select: setSelectedId, thread, reload };
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
