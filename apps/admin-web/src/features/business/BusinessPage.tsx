import { PageHeader } from "../../components/ui/Layout";
import { SectionPager } from "../../layout/SectionPager";
import { stepLabel } from "../../navigation/navItems";
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
      <SalesModeForm />
      <OfferingsOverview />
      <SectionPager current="business" />
    </>
  );
}
