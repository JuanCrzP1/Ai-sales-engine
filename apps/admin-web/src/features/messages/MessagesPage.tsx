import { PageHeader } from "../../components/ui/Layout";
import { SectionPager } from "../../layout/SectionPager";
import { stepLabel } from "../../navigation/navItems";
import { ChannelsForm } from "./ChannelsForm";
import { PaymentMessagesForm } from "./PaymentMessagesForm";
import { WelcomeMessageForm } from "./WelcomeMessageForm";

export function MessagesPage() {
  return (
    <>
      <PageHeader
        eyebrow={stepLabel("messages")}
        title="Mensajes y canales"
        description="Los mensajes que el asistente envía tal cual y los canales por los que atiendes."
      />
      <WelcomeMessageForm />
      <PaymentMessagesForm />
      <ChannelsForm />
      <SectionPager current="messages" />
    </>
  );
}
