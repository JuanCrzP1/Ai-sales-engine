import { Badge } from "../../components/ui/Feedback";
import { PageHeader } from "../../components/ui/Layout";
import { SettingsGroup } from "../../components/ui/SettingsCard";
import { ContractSection } from "../../layout/ContractSection";
import { SectionPager } from "../../layout/SectionPager";
import { stepLabel } from "../../navigation/navItems";
import { ChannelsForm } from "./ChannelsForm";
import { FallbackMessageForm } from "./FallbackMessageForm";
import { OtherMessagesForm } from "./OtherMessagesForm";
import { PaymentMessagesForm } from "./PaymentMessagesForm";
import { WelcomeMessageForm } from "./WelcomeMessageForm";

export function MessagesPage() {
  return (
    <>
      <PageHeader eyebrow={stepLabel("messages")} title="Mensajes y canales" description="Los mensajes que el asistente envía tal cual y los canales por los que atiendes." />
      <SettingsGroup title="Mensajes" description="Los que se envían tal cual en momentos clave de la conversación.">
        <WelcomeMessageForm />
        <PaymentMessagesForm />
        <OtherMessagesForm />
        <FallbackMessageForm />
      </SettingsGroup>
      <SettingsGroup title="Canales" description="Por dónde atiendes y lo que tu negocio no hace.">
        <ChannelsForm />
        <ContractSection
          title="Otros canales y restricciones"
          description="Por dónde funciona lo que vendes y los canales o acciones que tu negocio no ofrece."
          section="capabilities"
          fields={["product_channels", "restrictions"]}
          icon="shield"
          tone="slate"
          badge={<Badge tone="neutral">Opcional</Badge>}
        />
      </SettingsGroup>
      <SectionPager current="messages" />
    </>
  );
}
