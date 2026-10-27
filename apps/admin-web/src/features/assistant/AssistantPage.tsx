import { PageHeader } from "../../components/ui/Layout";
import { SectionPager } from "../../layout/SectionPager";
import { stepLabel } from "../../navigation/navItems";
import { SalesInstructionsForm } from "./SalesInstructionsForm";
import { SalesKnowledgeForm } from "./SalesKnowledgeForm";
import { StyleForm } from "./StyleForm";

export function AssistantPage() {
  return (
    <>
      <PageHeader
        eyebrow={stepLabel("assistant")}
        title="Cómo atiende el asistente"
        description="Define cómo habla y qué debe tener en cuenta para recomendar y vender."
      />
      <StyleForm />
      <SalesKnowledgeForm />
      <SalesInstructionsForm />
      <SectionPager current="assistant" />
    </>
  );
}
