import { PageHeader } from "../../components/ui/Layout";
import { TelegramChannelCard } from "./TelegramChannelCard";
import { WhatsAppChannelCard } from "./WhatsAppChannelCard";

/** Por dónde le escriben los clientes al negocio. Cada canal se conecta aparte y sus chats llegan a Conversaciones. */
export function ChannelsPage() {
  return (
    <>
      <PageHeader eyebrow="Configuración" title="Canales" description="Conecta los lugares donde te escriben tus clientes. Todos sus chats llegan a Conversaciones." />
      <WhatsAppChannelCard />
      <TelegramChannelCard />
    </>
  );
}
