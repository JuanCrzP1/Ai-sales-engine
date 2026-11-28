import { TextAreaField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { optionalText } from "../../domain/config/document";
import { phraseFor, type Phrase } from "../../domain/config/formality";
import { useConfig, useFieldIssue, useSection } from "../../state/useConfig";

// Los ejemplos van con el trato del negocio (Asistente IA → Estilo): un negocio que trata de usted ve ejemplos de usted.
const FIELDS: { key: "data_request" | "human_handoff" | "after_hours" | "ai_resumed" | "after_sale"; label: string; placeholder: Phrase; hint?: string }[] = [
  {
    key: "data_request",
    label: "Al pedir los datos del cliente",
    placeholder: { tu: "Ej.: Para continuar, ¿me compartes tu nombre y teléfono?", usted: "Ej.: Para continuar, ¿me comparte su nombre y teléfono?" },
  },
  {
    key: "human_handoff",
    label: "Al pasar la conversación a una persona",
    placeholder: { tu: "Ej.: Te comunico con alguien de nuestro equipo.", usted: "Ej.: Le comunico con alguien de nuestro equipo." },
  },
  {
    key: "after_hours",
    label: "Fuera del horario del equipo",
    placeholder: {
      tu: "Ej.: Nuestro equipo atiende de lunes a viernes de 8 a 6. Te escribimos apenas abramos.",
      usted: "Ej.: Nuestro equipo atiende de lunes a viernes de 8 a 6. Le escribimos apenas abramos.",
    },
    hint: "Cuando un chat pasa a una persona fuera del horario de Configuración → Atención humana. Si lo dejas vacío, el asistente dice tu horario y cuándo lo atienden.",
  },
  {
    key: "ai_resumed",
    label: "Cuando la IA retoma el chat",
    placeholder: {
      tu: "Ej.: Disculpa la espera. Mientras alguien del equipo se libera, sigo ayudándote yo.",
      usted: "Ej.: Disculpe la espera. Mientras alguien del equipo se libera, sigo ayudándole yo.",
    },
    hint: "Si nadie de tu equipo responde a tiempo, la IA vuelve a atender y envía este mensaje primero.",
  },
  {
    key: "after_sale",
    label: "Después de una compra",
    placeholder: { tu: "Ej.: ¡Gracias por tu compra!", usted: "Ej.: ¡Gracias por su compra!" },
    hint: "El asistente lo usa cuando el cliente vuelve a escribir después de pagar.",
  },
];

/** Mensajes opcionales del negocio: si no se escriben, el asistente responde con sus propias palabras. */
export function OtherMessagesForm() {
  const { document } = useConfig();
  const formality = document.response_style?.formality;
  const [messages, update] = useSection("messages");
  return (
    <Card icon="chat" tone="sky" wide title="Otros mensajes" description="Opcionales. Si no los escribes, el asistente responde con sus propias palabras.">
      <div className="grid-2">
        {FIELDS.map(({ key, label, placeholder, hint }) => (
          <MessageField
            key={key}
            path={`messages.${key}`}
            label={label}
            placeholder={phraseFor(placeholder, formality)}
            hint={hint}
            value={messages[key] ?? ""}
            onChange={(text) => update({ [key]: optionalText(text) })}
          />
        ))}
      </div>
    </Card>
  );
}

interface MessageFieldProps {
  path: string;
  label: string;
  placeholder: string;
  hint?: string;
  value: string;
  onChange: (text: string) => void;
}

function MessageField({ path, label, placeholder, hint, value, onChange }: MessageFieldProps) {
  const issue = useFieldIssue(path);
  return <TextAreaField label={label} value={value} onChange={onChange} placeholder={placeholder} rows={2} hint={hint} issue={issue} />;
}
