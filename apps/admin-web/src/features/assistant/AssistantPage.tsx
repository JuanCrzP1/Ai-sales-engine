import { PageHeader } from "../../components/ui/Layout";
import { ContractSection } from "../../layout/ContractSection";
import { SectionPager } from "../../layout/SectionPager";
import { stepLabel } from "../../navigation/navItems";
import { FaqForm } from "./FaqForm";
import { RecommendationsForm } from "./RecommendationsForm";
import { SalesKnowledgeForm } from "./SalesKnowledgeForm";
import { StyleForm } from "./StyleForm";

export function AssistantPage() {
  return (
    <>
      <PageHeader
        eyebrow={stepLabel("assistant")}
        title="Cómo atiende el asistente"
        description="Define su personalidad, cómo debe vender y las respuestas a preguntas frecuentes. Aquí se configura el negocio: las instrucciones internas del asistente no cambian."
      />
      <StyleForm />
      <SalesKnowledgeForm />
      <RecommendationsForm />
      <FaqForm />
      <ContractSection
        title="Estrategia comercial avanzada"
        description="Opcional: motivos de compra, objeciones, flujo de la conversación y reglas de cierre."
        section="sales"
        fields={["motivations", "customer_problems", "pain_points", "use_cases", "solution", "offer_mix", "offer_presentation", "qualification", "support", "conversation_flow", "objections", "closing"]}
      />
      <ContractSection
        title="Cómo vende el negocio"
        description="Opcional: interruptores comerciales. Si no se indican, se deducen de tu oferta."
        section="features"
      />
      <SectionPager current="assistant" />
    </>
  );
}
