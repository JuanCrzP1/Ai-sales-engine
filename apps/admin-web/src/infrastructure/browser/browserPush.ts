import type { DevicePush, PushPermission, PushSupport } from "../../repositories/attention";
import { PersistenceError } from "../../repositories/persistenceError";
import type { HttpClient } from "../api/httpClient";

/** El service worker del panel (`public/sw.js`): muestra las notificaciones y abre el chat al tocarlas. */
export const SERVICE_WORKER_PATH = "/sw.js";

interface PushStatusPayload {
  public_key: string;
  subscribed: boolean;
}

function problem(message: string): PersistenceError {
  return new PersistenceError("unknown", { message });
}

/** La clave pública de la plataforma, como la pide el navegador. */
export function applicationServerKey(base64url: string): Uint8Array<ArrayBuffer> {
  const padded = `${base64url}${"=".repeat((4 - (base64url.length % 4)) % 4)}`.replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(padded);
  const bytes = new Uint8Array(new ArrayBuffer(raw.length));
  for (let index = 0; index < raw.length; index += 1) bytes[index] = raw.charCodeAt(index);
  return bytes;
}

function isAppleMobile(): boolean {
  return /iphone|ipad|ipod/i.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
}

function isInstalled(): boolean {
  return window.matchMedia?.("(display-mode: standalone)").matches === true || (navigator as Navigator & { standalone?: boolean }).standalone === true;
}

/** «Chrome en Android», «Safari en iPhone»: para reconocer el dispositivo (no se usa para nada más). */
export function deviceLabel(userAgent: string = navigator.userAgent): string {
  const browser = /edg\//i.test(userAgent)
    ? "Edge"
    : /firefox|fxios/i.test(userAgent)
      ? "Firefox"
      : /chrome|crios/i.test(userAgent)
        ? "Chrome"
        : /safari/i.test(userAgent)
          ? "Safari"
          : "Navegador";
  const system = /iphone/i.test(userAgent)
    ? "iPhone"
    : /ipad/i.test(userAgent)
      ? "iPad"
      : /android/i.test(userAgent)
        ? "Android"
        : /mac os/i.test(userAgent)
          ? "Mac"
          : /windows/i.test(userAgent)
            ? "Windows"
            : "computador";
  return `${browser} en ${system}`;
}

/** `DevicePush` con las API del navegador (Service Worker, Push y Notification) y la API del panel (`/api/notifications/push`). */
export function createBrowserPush(http: HttpClient): DevicePush {
  const support = (): PushSupport => {
    const capable = typeof window !== "undefined" && "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
    if (capable) return "supported";
    // En iPhone y iPad las notificaciones solo funcionan con el panel instalado en la pantalla de inicio.
    return typeof window !== "undefined" && isAppleMobile() && !isInstalled() ? "install" : "unsupported";
  };

  const registration = async (): Promise<ServiceWorkerRegistration> => {
    await navigator.serviceWorker.register(SERVICE_WORKER_PATH);
    return navigator.serviceWorker.ready;
  };

  const current = async (): Promise<PushSubscription | null> => {
    if (support() !== "supported") return null;
    const existing = await navigator.serviceWorker.getRegistration(SERVICE_WORKER_PATH);
    return existing ? existing.pushManager.getSubscription() : null;
  };

  return {
    support,
    permission: (): PushPermission => (support() === "supported" ? (Notification.permission as PushPermission) : "default"),

    async subscribed() {
      if (support() !== "supported" || Notification.permission !== "granted") return false;
      const subscription = await current();
      if (!subscription) return false;
      const status = await http.get<PushStatusPayload>(`/notifications/push?endpoint=${encodeURIComponent(subscription.endpoint)}`);
      return status.subscribed;
    },

    async enable() {
      if (support() !== "supported") throw problem("Este navegador no puede recibir notificaciones.");
      // El permiso se pide primero, mientras dura el toque en el botón (Safari lo exige).
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        throw problem(
          permission === "denied"
            ? "Bloqueaste las notificaciones para este sitio. Permítelas en la configuración del navegador y vuelve a intentarlo."
            : "No diste el permiso para las notificaciones.",
        );
      }
      const [worker, status] = await Promise.all([registration(), http.get<PushStatusPayload>("/notifications/push")]);
      const key = applicationServerKey(status.public_key);
      let subscription = await worker.pushManager.getSubscription();
      if (subscription) {
        // Si se suscribió con otra clave (otro servidor), se rehace.
        const used = subscription.options.applicationServerKey;
        const same = used ? new Uint8Array(used).every((byte, index) => byte === key[index]) : false;
        if (!same) {
          await subscription.unsubscribe();
          subscription = null;
        }
      }
      subscription ??= await worker.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: key });
      const json = subscription.toJSON();
      await http.post<void>("/notifications/push", { endpoint: json.endpoint, keys: json.keys, device: deviceLabel() });
    },

    async disable() {
      const subscription = await current();
      if (!subscription) return;
      await http.post<void>("/notifications/push/remove", { endpoint: subscription.endpoint });
      await subscription.unsubscribe();
    },

    async test() {
      const subscription = await current();
      if (!subscription) throw problem("Activa primero las notificaciones en este navegador.");
      await http.post<void>("/notifications/push/test", { endpoint: subscription.endpoint });
    },
  };
}
