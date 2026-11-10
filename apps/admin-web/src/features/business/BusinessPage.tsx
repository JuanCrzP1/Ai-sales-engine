import { Badge } from "../../components/ui/Feedback";
import { PageHeader } from "../../components/ui/Layout";
import { SettingsGroup } from "../../components/ui/SettingsCard";
import { ContractSection } from "../../layout/ContractSection";
import { SectionPager } from "../../layout/SectionPager";
import { stepLabel } from "../../navigation/navItems";
import { BusinessDetailsForm, BusinessTrustForm } from "./BusinessDetailsForm";
import { BusinessIdentityForm, BusinessPromiseForm } from "./BusinessIdentityForm";
import { OfferingsOverview } from "./OfferingsOverview";
import { SalesModeForm } from "./SalesModeForm";

export function BusinessPage() {
  return (
    <>
      <PageHeader
        eyebrow={stepLabel("business")}
        title="Mi negocio"
        description="Cuéntale al asistente quién eres y qué ofreces. Escribe como se lo explicarías a un cliente nuevo."
      />
      <SettingsGroup title="Lo esencial" description="Con esto el asistente ya puede presentar tu negocio.">
        <BusinessIdentityForm />
        <SalesModeForm />
        <BusinessPromiseForm />
        <BusinessTrustForm />
        <BusinessDetailsForm />
        <OfferingsOverview />
      </SettingsGroup>
      <SettingsGroup title="Para afinar" description="Opcional. Ábrelas cuando quieras darle más detalle al asistente.">
        <ContractSection
          title="Horario de atención"
          description="Los días y horas en que atiendes. El asistente lo dice si le preguntan."
          section="identity"
          fields={["opening_hours"]}
          icon="clock"
          tone="amber"
          badge={<Badge tone="neutral">Opcional</Badge>}
        />
        <ContractSection
          title="Cliente ideal"
          description="A quién le vendes: así el asistente le habla en su idioma."
          section="identity"
          fields={["target_customer"]}
          icon="target"
          tone="rose"
          badge={<Badge tone="neutral">Opcional</Badge>}
        />
      </SettingsGroup>
      <SectionPager current="business" />
    </>
  );
}
