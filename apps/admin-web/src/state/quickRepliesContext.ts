import { createContext, useContext } from "react";
import type { QuickReplies } from "../repositories/quickReplies";

/**
 * Las respuestas rápidas de cada negocio. La entrega la aplicación como una fábrica por negocio: la bandeja reúne chats de varios
 * negocios y cada chat usa las de su negocio.
 */
export const QuickRepliesContext = createContext<((slug: string) => QuickReplies) | null>(null);

export function useQuickRepliesService(): (slug: string) => QuickReplies {
  const create = useContext(QuickRepliesContext);
  if (!create) throw new Error("useQuickRepliesService debe usarse dentro de <App>.");
  return create;
}
