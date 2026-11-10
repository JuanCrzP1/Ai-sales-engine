import { useCallback, useEffect, useState } from "react";
import type { NotificationFeed } from "../domain/inbox/types";
import { useInbox } from "./inboxContext";

/** Cada cuánto se buscan avisos nuevos mientras el panel está abierto. */
export const NOTIFICATIONS_REFRESH_MS = 30_000;

/** Los avisos del usuario: se cargan al abrir el panel, cada 30 segundos y al volver a la pestaña. Un fallo no interrumpe nada. */
export function useNotifications() {
  const inbox = useInbox();
  const [feed, setFeed] = useState<NotificationFeed>({ items: [], unread: 0 });

  const refresh = useCallback(() => {
    inbox.notifications().then(setFeed, () => undefined);
  }, [inbox]);

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, NOTIFICATIONS_REFRESH_MS);
    const onFocus = () => refresh();
    window.addEventListener("focus", onFocus);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("focus", onFocus);
    };
  }, [refresh]);

  const markRead = useCallback(
    async (ids?: string[]) => {
      setFeed((current) => {
        const items = current.items.map((item) => (!ids || ids.includes(item.id) ? { ...item, read: true } : item));
        return { items, unread: items.filter((item) => !item.read).length };
      });
      await inbox.markNotificationsRead(ids).catch(() => undefined);
      refresh();
    },
    [inbox, refresh],
  );

  return { feed, markRead, refresh };
}
