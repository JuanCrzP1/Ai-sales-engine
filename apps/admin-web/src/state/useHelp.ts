import { useEffect, useRef, useState } from "react";
import type { HelpArticle, HelpArticleSummary, HelpModule } from "../repositories/help";
import { PersistenceError, persistenceErrorMessage } from "../repositories/persistenceError";
import { useHelpService } from "./helpContext";

export type HelpLoad<T> = { status: "loading" } | { status: "ready"; value: T } | { status: "error"; message: string; missing: boolean };

/** Cuánto espera la búsqueda a que termines de escribir. */
export const SEARCH_DELAY_MS = 250;

/** Carga lo que `load` trae cada vez que cambia `key` (o al reintentar). Con `key` en null no carga nada. */
function useLoad<T>(key: unknown, load: () => Promise<T>, enabled = true): HelpLoad<T> & { retry: () => void } {
  const [state, setState] = useState<HelpLoad<T>>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const latest = useRef(load);
  latest.current = load;
  useEffect(() => {
    if (!enabled) return;
    let active = true;
    setState({ status: "loading" });
    latest.current().then(
      (value) => active && setState({ status: "ready", value }),
      (reason: unknown) =>
        active && setState({ status: "error", message: persistenceErrorMessage(reason), missing: reason instanceof PersistenceError && reason.code === "not_found" }),
    );
    return () => {
      active = false;
    };
  }, [key, attempt, enabled]);
  return { ...state, retry: () => setAttempt((count) => count + 1) };
}

/** Los temas con sus artículos. `enabled: false` no los pide (el panel de ayuda cerrado). */
export function useHelpIndex({ enabled = true }: { enabled?: boolean } = {}) {
  const help = useHelpService();
  return useLoad<HelpModule[]>(help, () => help.index(), enabled);
}

/** Un artículo completo. */
export function useHelpArticle(slug: string) {
  const help = useHelpService();
  return useLoad<HelpArticle>(`${slug}`, () => help.article(slug));
}

/** Los resultados de buscar, cuando dejas de escribir. `null` sin búsqueda: se muestra lo de siempre. */
export function useHelpSearch(query: string): HelpLoad<HelpArticleSummary[]> | null {
  const help = useHelpService();
  const wanted = query.trim();
  const [state, setState] = useState<HelpLoad<HelpArticleSummary[]> | null>(null);
  useEffect(() => {
    if (!wanted) {
      setState(null);
      return;
    }
    let active = true;
    setState({ status: "loading" });
    const timer = setTimeout(() => {
      help.search(wanted).then(
        (value) => active && setState({ status: "ready", value }),
        (reason: unknown) => active && setState({ status: "error", message: persistenceErrorMessage(reason), missing: false }),
      );
    }, SEARCH_DELAY_MS);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [help, wanted]);
  return state;
}
