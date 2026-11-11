import { useCallback, useEffect, useState } from "react";
import type { Commerce } from "../repositories/commerce";
import { persistenceErrorMessage } from "../repositories/persistenceError";
import { useCommerce } from "./commerceContext";
import type { Loadable } from "./useConversations";

/** Carga algo de clientes, ventas o reportes; `reload` lo vuelve a pedir (después de registrar o anular una venta). */
export function useCommerceData<T>(load: (commerce: Commerce) => Promise<T>, deps: unknown[]): { state: Loadable<T>; reload: () => void; commerce: Commerce } {
  const commerce = useCommerce();
  const [state, setState] = useState<Loadable<T>>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(load, deps);
  useEffect(() => {
    let active = true;
    run(commerce).then(
      (data) => active && setState({ status: "ready", data }),
      (error: unknown) => active && setState({ status: "error", message: persistenceErrorMessage(error) }),
    );
    return () => {
      active = false;
    };
  }, [commerce, run, attempt]);
  return { state, reload: useCallback(() => setAttempt((count) => count + 1), []), commerce };
}
