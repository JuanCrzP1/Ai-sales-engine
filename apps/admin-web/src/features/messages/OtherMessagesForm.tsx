import { TextAreaField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { optionalText } from "../../domain/config/document";
import { useFieldIssue, useSection } from "../../state/useConfig";

const FIELDS: { key: "data_request" | "human_handoff" | "after_hours" | "ai_resumed" | "after_sale" | "follow_up"; label: string; placeholder: string; hint?: string }[] = [
  { key: "data_request", label: "Al pedir los datos del cliente", placeholder: "Ej.: Para continuar, ¿me compartes tu nombre y teléfono?" },
  { key: "human_handoff", label: "Al pasar la conversación a una persona", placeholder: "Ej.: Te comunico con alguien de nuestro equipo." },
  {
    key: "after_hours",
    label: "Fuera del horario del equipo",
    placeholder: "Ej.: Nuestro equipo atiende de lunes a viernes de 8 a 6. Te escribimos apenas abramos.",
    hint: "Cuando un chat pasa a una persona fuera del horario de Ajustes → Atención humana. Si lo dejas vacío, el asistente dice tu horario y cuándo lo atienden.",
  },
  {
    key: "ai_resumed",
    label: "Cuando la IA retoma el chat",
    placeholder: "Ej.: Disculpa la espera. Mientras alguien del equipo se libera, sigo ayudándote yo.",
    hint: "Si nadie de tu equipo responde a tiempo, la IA vuelve a atender y envía este mensaje primero.",
  },
  {
    key: "after_sale",
    label: "Después de una compra",
    placeholder: "Ej.: ¡Gracias por tu compra!",
    hint: "El asistente lo usa cuando el cliente vuelve a escribir después de pagar.",
  },
  {
    key: "follow_up",
    label: "Seguimiento a un cliente que no respondió",
    placeholder: "Ej.: Hola, ¿pudiste revisar la información?",
    hint: "Se guarda para cuando los canales puedan escribirle primero al cliente: entonces se enviará a quien no respondió.",
  },
];

/** Mensajes opcionales del negocio: si no se escriben, el asistente responde con sus propias palabras. */
export function OtherMessagesForm() {
  const [messages, update] = useSection("messages");
  return (
    <Card icon="chat" tone="sky" wide title="Otros mensajes" description="Opcionales. Si no los escribes, el asistente responde con sus propias palabras.">
      <div className="grid-2">
        {FIELDS.map(({ key, label, placeholder, hint }) => (
          <MessageField
            key={key}
            path={`messages.${key}`}
            label={label}
            placeholder={placeholder}
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
