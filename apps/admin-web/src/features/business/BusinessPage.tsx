import { PageHeader } from "../../components/ui/Layout";
import { ContractSection } from "../../layout/ContractSection";
import { SectionPager } from "../../layout/SectionPager";
import { stepLabel } from "../../navigation/navItems";
import { BusinessDetailsForm } from "./BusinessDetailsForm";
import { BusinessIdentityForm } from "./BusinessIdentityForm";
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
      <BusinessIdentityForm />
      <BusinessDetailsForm />
      <ContractSection title="Horarios y cliente ideal" description="Cuándo atiendes y a quién te diriges." section="identity" fields={["opening_hours", "target_customer"]} />
      <SalesModeForm />
      <OfferingsOverview />
      <SectionPager current="business" />
    </>
  );
}
