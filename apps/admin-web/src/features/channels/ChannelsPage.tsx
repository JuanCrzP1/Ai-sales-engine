import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Feedback";
import { PageHeader } from "../../components/ui/Layout";

const CHANNELS = [
  { id: "whatsapp", name: "WhatsApp", description: "Responde los mensajes de tu número de WhatsApp Business.", letter: "W" },
  { id: "instagram", name: "Instagram", description: "Atiende los mensajes directos de tu cuenta de Instagram.", letter: "I" },
  { id: "telegram", name: "Telegram", description: "Conecta un bot de Telegram para tu negocio.", letter: "T" },
  { id: "web", name: "Chat web", description: "Un chat para tu página web, con tu asistente detrás.", letter: "W" },
] as const;

/** Por dónde le escriben los clientes al negocio. Cada canal se conecta aparte y sus chats llegan a Conversaciones. */
export function ChannelsPage() {
  return (
    <>
      <PageHeader eyebrow="Configuración" title="Canales" description="Conecta los lugares donde te escriben tus clientes. Todos sus chats llegan a Conversaciones." />
      <div className="channel-grid">
        {CHANNELS.map((channel) => (
          <article key={channel.id} className="channel-card">
            <div className="channel-card__top">
              <span className={`channel-card__logo channel-color--${channel.id}`} aria-hidden="true">
                {channel.letter}
              </span>
              <Badge tone="neutral">No conectado</Badge>
            </div>
            <h2 className="channel-card__name">{channel.name}</h2>
            <p className="channel-card__text">{channel.description}</p>
            <Button variant="secondary" disabled>
              Conectar · muy pronto
            </Button>
          </article>
        ))}
      </div>
    </>
  );
}
