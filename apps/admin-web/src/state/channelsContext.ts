import { createContext, useContext } from "react";
import type { Channels } from "../repositories/channels";

/** Los canales del negocio abierto (por ahora, WhatsApp por código QR). Los entrega el espacio de trabajo del negocio. */
export const ChannelsContext = createContext<Channels | null>(null);

export function useChannels(): Channels {
  const channels = useContext(ChannelsContext);
  if (!channels) throw new Error("useChannels debe usarse dentro del espacio de trabajo de un negocio.");
  return channels;
}
