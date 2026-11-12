import { useCallback, useEffect, useState } from "react";
import type { PushPermission, PushSupport } from "../repositories/attention";
import { persistenceErrorMessage } from "../repositories/persistenceError";
import { useDevicePushService } from "./attentionContext";

export interface DevicePushState {
  support: PushSupport;
  permission: PushPermission;
  /** null mientras se averigua. */
  subscribed: boolean | null;
  busy: boolean;
  /** Lo último que pasó, para decírselo a la persona. */
  notice: { ok: boolean; message: string } | null;
  enable: () => Promise<void>;
  disable: () => Promise<void>;
  test: () => Promise<void>;
}

/** Las notificaciones en este navegador o celular: si se pueden, si están activadas, y activarlas, quitarlas o probarlas. */
export function useDevicePush(): DevicePushState {
  const push = useDevicePushService();
  const support: PushSupport = push ? push.support() : "unsupported";
  const [permission, setPermission] = useState<PushPermission>(() => (push ? push.permission() : "default"));
  const [subscribed, setSubscribed] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<DevicePushState["notice"]>(null);

  useEffect(() => {
    let active = true;
    if (!push || support !== "supported") {
      setSubscribed(false);
      return;
    }
    push.subscribed().then(
      (value) => active && setSubscribed(value),
      () => active && setSubscribed(false),
    );
    return () => {
      active = false;
    };
  }, [push, support]);

  const run = useCallback(
    async (action: () => Promise<void>, done: string) => {
      if (!push) return;
      setBusy(true);
      setNotice(null);
      try {
        await action();
        setNotice({ ok: true, message: done });
      } catch (reason) {
        setNotice({ ok: false, message: persistenceErrorMessage(reason) });
      } finally {
        setPermission(push.permission());
        setBusy(false);
      }
    },
    [push],
  );

  const enable = useCallback(
    () =>
      run(async () => {
        await push!.enable();
        setSubscribed(true);
      }, "Listo: este dispositivo te avisará cuando un cliente necesite a una persona."),
    [push, run],
  );
  const disable = useCallback(
    () =>
      run(async () => {
        await push!.disable();
        setSubscribed(false);
      }, "Este dispositivo ya no recibirá notificaciones."),
    [push, run],
  );
  const test = useCallback(() => run(() => push!.test(), "Te enviamos una notificación de prueba. Debería aparecer en unos segundos."), [push, run]);

  return { support, permission, subscribed, busy, notice, enable, disable, test };
}
