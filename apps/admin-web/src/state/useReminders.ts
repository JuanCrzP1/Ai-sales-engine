import { useEffect, useState } from "react";
import type { Reminder } from "../domain/commerce/reminders";
import { persistenceErrorMessage } from "../repositories/persistenceError";
import type { Loadable } from "./useConversations";
import { useCommerce } from "./commerceContext";

/**
 * Los recordatorios del negocio: los pendientes (o los hechos, con `done`), y con `mine` solo los de quien mira. `version` cambia
 * cuando algo se creó, se marcó o se borró, y se vuelven a pedir; mientras llegan, se siguen viendo los anteriores.
 */
export function useReminders(version: number, { done = false, mine = false, enabled = true }: { done?: boolean; mine?: boolean; enabled?: boolean } = {}): Loadable<Reminder[]> {
  const commerce = useCommerce();
  const [state, setState] = useState<Loadable<Reminder[]>>({ status: "loading" });
  useEffect(() => {
    if (!enabled) return;
    let active = true;
    commerce.reminders({ done, mine }).then(
      (data) => active && setState({ status: "ready", data }),
      (error: unknown) => active && setState({ status: "error", message: persistenceErrorMessage(error) }),
    );
    return () => {
      active = false;
    };
  }, [commerce, version, done, mine, enabled]);
  return state;
}
