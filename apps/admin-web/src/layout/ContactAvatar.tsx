import { WhatsAppLogo } from "../components/brand/WhatsAppLogo";
import { Icon, type IconName } from "../components/ui/Icon";
import { CHANNEL_LABELS, type Channel } from "../domain/inbox/types";
import { initials } from "../domain/inbox/format";

const CHANNEL_ICONS: Record<Exclude<Channel, "whatsapp">, IconName> = {
  instagram: "camera",
  telegram: "send",
  web: "chat",
  api: "link",
  prueba: "flask",
};

// Colores de las iniciales, ninguno verde: el verde queda para lo que hay que mirar (sin leer, el canal de WhatsApp).
const FACE_TONES = 6;

function faceTone(name: string): number {
  let hash = 0;
  for (const char of name) hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  return hash % FACE_TONES;
}

/**
 * Un contacto: sus iniciales, siempre del mismo color para la misma persona, y el canal como un ícono pequeño sobre la foto (como
 * en las bandejas de Intercom o WhatsApp Business). Así el canal no ocupa una etiqueta en cada chat.
 */
export function ContactAvatar({ name, channel, size = "md" }: { name: string; channel: Channel; size?: "sm" | "md" }) {
  const face = channel === "prueba" ? "test" : String(faceTone(name));
  return (
    <span className={`contact-avatar contact-avatar--${size}`}>
      <span className={`contact-avatar__face contact-avatar__face--${face}`} aria-hidden="true">
        {initials(name)}
      </span>
      <span className={`contact-avatar__channel channel-color--${channel}`} role="img" aria-label={CHANNEL_LABELS[channel]} title={CHANNEL_LABELS[channel]}>
        {channel === "whatsapp" ? <WhatsAppLogo size={10} /> : <Icon name={CHANNEL_ICONS[channel]} size={9} />}
      </span>
    </span>
  );
}
