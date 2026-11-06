import { PageHeader } from "../../components/ui/Layout";
import { ContractSection } from "../../layout/ContractSection";
import { SectionPager } from "../../layout/SectionPager";
import { stepLabel } from "../../navigation/navItems";
import { ChannelsForm } from "./ChannelsForm";
import { OtherMessagesForm } from "./OtherMessagesForm";
import { PaymentMessagesForm } from "./PaymentMessagesForm";
import { WelcomeMessageForm } from "./WelcomeMessageForm";

export function MessagesPage() {
  return (
    <>
      <PageHeader eyebrow={stepLabel("messages")} title="Mensajes y canales" description="Los mensajes que el asistente envía tal cual y los canales por los que atiendes." />
      <WelcomeMessageForm />
      <PaymentMessagesForm />
      <OtherMessagesForm />
      <ChannelsForm />
      <ContractSection title="Otros canales y restricciones" description="Por dónde funciona lo que vendes y lo que tu negocio no hace." section="capabilities" fields={["product_channels", "restrictions"]} />
      <SectionPager current="messages" />
    </>
  );
}
