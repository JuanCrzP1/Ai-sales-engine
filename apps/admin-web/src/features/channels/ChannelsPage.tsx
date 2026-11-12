import { Badge } from "../../components/ui/Feedback";
import { Icon, type IconName } from "../../components/ui/Icon";
import { PageHeader } from "../../components/ui/Layout";
import { WhatsAppChannelCard } from "./WhatsAppChannelCard";

/** Los canales que vienen después de WhatsApp. */
const UPCOMING: { id: string; name: string; description: string; icon: IconName }[] = [
  { id: "telegram", name: "Telegram", description: "Conecta el bot de Telegram de tu negocio.", icon: "send" },
  { id: "web", name: "Chat web", description: "Una burbuja de chat para tu página web, con tu asistente detrás. Para conectarlo hoy a otra plataforma, usa Integraciones → API del asistente.", icon: "chat" },
];

/** Por dónde le escriben los clientes al negocio. Cada canal se conecta aparte y sus chats llegan a Conversaciones. */
export function ChannelsPage() {
  return (
    <>
      <PageHeader eyebrow="Configuración" title="Canales" description="Conecta los lugares donde te escriben tus clientes. Todos sus chats llegan a Conversaciones." />
      <WhatsAppChannelCard />
      <section className="settings-group" aria-label="Próximos canales">
        <div className="settings-group__header">
          <h2 className="settings-group__title">Próximamente</h2>
        </div>
        <div className="channel-grid">
          {UPCOMING.map((channel) => (
            <article key={channel.id} className="channel-card channel-card--soon">
              <div className="channel-card__top">
                <span className={`channel-card__logo channel-color--${channel.id}`} aria-hidden="true">
                  <Icon name={channel.icon} size={20} />
                </span>
                <Badge tone="neutral">Próximamente</Badge>
              </div>
              <h3 className="channel-card__name">{channel.name}</h3>
              <p className="channel-card__text">{channel.description}</p>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
