import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Icon } from "../components/ui/Icon";
import { relativeTime } from "../domain/inbox/format";
import type { Notification } from "../domain/inbox/types";
import { CONVERSATIONS_ITEM, workspacePath } from "../navigation/navItems";
import { useDevicePush } from "../state/useDevicePush";
import { useNotifications } from "../state/useNotifications";

/** Campana de avisos: cuántos faltan por leer y la lista. Abrir uno lleva a su conversación y lo marca como leído. */
export function NotificationBell() {
  const { feed, markRead } = useNotifications();
  const push = useDevicePush();
  // Se ofrece activarlas en este dispositivo mientras no se hayan activado ni bloqueado.
  const offerPush = push.support === "supported" && push.subscribed === false && push.permission === "default";
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const root = useRef<HTMLDivElement>(null);
  const { unread, items } = feed;

  useEffect(() => {
    if (!open) return;
    const close = (event: MouseEvent | KeyboardEvent) => {
      if (event instanceof KeyboardEvent ? event.key === "Escape" : !root.current?.contains(event.target as Node)) setOpen(false);
    };
    window.addEventListener("mousedown", close);
    window.addEventListener("keydown", close);
    return () => {
      window.removeEventListener("mousedown", close);
      window.removeEventListener("keydown", close);
    };
  }, [open]);

  const openNotification = (item: Notification) => {
    setOpen(false);
    if (!item.read) void markRead([item.id]);
    const conversations = workspacePath(item.business.slug, CONVERSATIONS_ITEM.path);
    navigate(item.conversationId ? `${conversations}?c=${encodeURIComponent(item.conversationId)}` : conversations);
  };

  return (
    <div className="bell" ref={root}>
      <button
        type="button"
        className="bell__button"
        aria-label={unread > 0 ? `Notificaciones: ${unread} sin leer` : "Notificaciones"}
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <Icon name="bell" size={18} />
        {unread > 0 && (
          <span className="bell__badge" aria-hidden="true">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>
      {open && (
        <div className="bell__panel" role="dialog" aria-label="Notificaciones">
          <div className="bell__head">
            <strong>Notificaciones</strong>
            {unread > 0 && (
              <button type="button" className="bell__mark" onClick={() => void markRead()}>
                Marcar todo como leído
              </button>
            )}
          </div>
          {offerPush && (
            <div className="bell__push">
              <span>Recibe estos avisos aunque el panel esté cerrado.</span>
              <button type="button" className="bell__mark" onClick={() => void push.enable()} disabled={push.busy}>
                {push.busy ? "Activando…" : "Activar notificaciones"}
              </button>
            </div>
          )}
          {push.notice && !push.notice.ok && <p className="bell__push bell__push--error">{push.notice.message}</p>}
          {items.length === 0 ? (
            <p className="bell__empty">No tienes avisos. Cuando el asistente pase un chat a una persona de tu equipo, te avisamos aquí.</p>
          ) : (
            <ul className="bell__list">
              {items.map((item) => (
                <li key={item.id}>
                  <button type="button" className={`bell__item${item.read ? "" : " bell__item--unread"}`} onClick={() => openNotification(item)}>
                    <span className="bell__icon" aria-hidden="true">
                      <Icon name={item.kind === "ai_resumed" ? "robot" : "headset"} size={16} />
                    </span>
                    <span className="bell__text">
                      <span className="bell__title">{item.title}</span>
                      {item.body && <span className="bell__body">{item.kind === "handoff" ? `«${item.body}»` : item.body}</span>}
                      <span className="bell__meta">
                        {item.business.name} · {relativeTime(item.createdAt)}
                      </span>
                    </span>
                    {!item.read && <span className="visually-hidden">Sin leer</span>}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
