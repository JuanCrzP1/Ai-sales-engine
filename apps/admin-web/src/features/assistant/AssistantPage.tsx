import { PageHeader } from "../../components/ui/Layout";
import { SectionPager } from "../../layout/SectionPager";
import { stepLabel } from "../../navigation/navItems";
import { FaqForm } from "./FaqForm";
import { SalesKnowledgeForm } from "./SalesKnowledgeForm";
import { StyleForm } from "./StyleForm";

export function AssistantPage() {
  return (
    <>
      <PageHeader
        eyebrow={stepLabel("assistant")}
        title="Cómo atiende el asistente"
        description="Define el largo de sus respuestas, qué debe tener en cuenta para recomendar y las respuestas a preguntas frecuentes."
      />
      <StyleForm />
      <SalesKnowledgeForm />
      <FaqForm />
      <SectionPager current="assistant" />
    </>
  );
}
