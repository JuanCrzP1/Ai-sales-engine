import { Badge } from "../../components/ui/Feedback";
import { PageHeader } from "../../components/ui/Layout";
import { SettingsGroup } from "../../components/ui/SettingsCard";
import { ContractSection } from "../../layout/ContractSection";
import { SectionPager } from "../../layout/SectionPager";
import { stepLabel } from "../../navigation/navItems";
import { FaqForm } from "./FaqForm";
import { RecommendationsForm } from "./RecommendationsForm";
import { SalesKnowledgeForm } from "./SalesKnowledgeForm";
import { StyleForm } from "./StyleForm";

const ADVANCED = <Badge tone="neutral">Avanzado</Badge>;

export function AssistantPage() {
  return (
    <>
      <PageHeader
        eyebrow={stepLabel("assistant")}
        title="Cómo atiende el asistente"
        description="Define su personalidad, cómo debe vender y las respuestas a preguntas frecuentes. Aquí se configura el negocio: las instrucciones internas del asistente no cambian."
      />
      <SettingsGroup title="Lo esencial" description="Su forma de hablar, cómo vende y lo que responde siempre igual.">
        <StyleForm />
        <SalesKnowledgeForm />
        <RecommendationsForm />
        <FaqForm />
      </SettingsGroup>
      <SettingsGroup
        title="Estrategia de venta avanzada"
        description="Opcional. Cada tarjeta afina una parte de la venta; todo lo que escribas aquí lo usa el asistente."
      >
        <ContractSection
          title="Motivos de compra"
          description="Por qué te compran, cómo reconocerlo en lo que dice el cliente y cómo hablarle."
          section="sales"
          fields={["motivations"]}
          icon="heart"
          tone="rose"
          badge={ADVANCED}
        />
        <ContractSection
          title="Problemas del cliente"
          description="Los problemas que resuelves: cómo los describe el cliente, cómo notarlos y qué le cuestan."
          section="sales"
          fields={["customer_problems", "pain_points"]}
          icon="alert"
          tone="amber"
          badge={ADVANCED}
        />
        <ContractSection
          title="Casos típicos"
          description="Situaciones frecuentes de tus clientes y cómo enfocar la venta en cada una."
          section="sales"
          fields={["use_cases"]}
          icon="users"
          tone="sky"
          badge={ADVANCED}
        />
        <ContractSection
          title="Cuando el cliente duda"
          description="Cómo responder una objeción (por precio, tiempo, confianza...): reconocerla, replantearla y volver a la venta."
          section="sales"
          fields={["objections"]}
          icon="handshake"
          tone="violet"
          badge={ADVANCED}
        />
        <ContractSection
          title="Orden de la conversación"
          description="Los pasos que sigue la conversación y lo que el asistente no debe hacer."
          section="sales"
          fields={["conversation_flow"]}
          icon="route"
          tone="indigo"
          badge={ADVANCED}
        />
        <ContractSection
          title="Cómo atiende las preguntas"
          description="Si primero aclara o va directo a vender, y si confirma que la opción le sirve antes de cerrar."
          section="sales"
          fields={["support", "qualification"]}
          icon="chat"
          tone="emerald"
          badge={ADVANCED}
        />
        <ContractSection
          title="Cierre de la venta"
          description="Señales de compra, siguientes pasos y reglas para cerrar."
          section="sales"
          fields={["closing"]}
          icon="check"
          tone="emerald"
          badge={ADVANCED}
        />
        <ContractSection
          title="Pasos y requisitos para comprar"
          description="Qué pasos sigue el cliente para comprar o recibir el servicio y qué requisitos debe cumplir."
          section="sales"
          fields={["solution"]}
          icon="route"
          tone="sky"
          badge={ADVANCED}
        />
        <ContractSection
          title="Cómo presenta las opciones"
          description="Cómo mostrar una o varias opciones, y qué mejoras o complementos sugerir."
          section="sales"
          fields={["offer_presentation", "offer_mix"]}
          icon="layers"
          tone="violet"
          badge={ADVANCED}
        />
        <ContractSection
          title="Cómo vende el negocio"
          description="Qué vendes, si da precios, en cuántas monedas y si recomienda un solo plan. Si no los indicas, se deducen de tu oferta."
          section="features"
          icon="toggles"
          tone="slate"
          badge={ADVANCED}
        />
      </SettingsGroup>
      <SectionPager current="assistant" />
    </>
  );
}
