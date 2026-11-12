import { useEffect, useState } from "react";
import type { WhatsAppStatus } from "../repositories/channels";
import { useChannels } from "./channelsContext";

/** El estado real de WhatsApp del negocio abierto, para mostrarlo sin inventar: null mientras se averigua o si no se pudo. */
export function useWhatsAppStatus(): WhatsAppStatus | null {
  const channels = useChannels();
  const [status, setStatus] = useState<WhatsAppStatus | null>(null);
  useEffect(() => {
    let active = true;
    channels.whatsapp().then(
      (channel) => active && setStatus(channel.available ? channel.status : "disconnected"),
      () => active && setStatus(null),
    );
    return () => {
      active = false;
    };
  }, [channels]);
  return status;
}
