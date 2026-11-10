import { createContext, useContext } from "react";
import type { Inbox } from "../repositories/inbox";

export const InboxContext = createContext<Inbox | null>(null);

/** La bandeja de conversaciones del usuario. */
export function useInbox(): Inbox {
  const inbox = useContext(InboxContext);
  if (!inbox) throw new Error("useInbox debe usarse dentro de <App>.");
  return inbox;
}
