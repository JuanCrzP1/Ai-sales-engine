import { createContext, useContext } from "react";
import type { Attention, DevicePush } from "../repositories/attention";

/** La atención humana del negocio abierto. La entrega el espacio de trabajo del negocio. */
export const AttentionContext = createContext<Attention | null>(null);

export function useAttention(): Attention {
  const attention = useContext(AttentionContext);
  if (!attention) throw new Error("useAttention debe usarse dentro del espacio de trabajo de un negocio.");
  return attention;
}

/** Las notificaciones de este navegador. Las entrega la aplicación: son de la persona, no de un negocio. */
export const DevicePushContext = createContext<DevicePush | null>(null);

export function useDevicePushService(): DevicePush | null {
  return useContext(DevicePushContext);
}
