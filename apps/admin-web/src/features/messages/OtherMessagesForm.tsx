import { TextAreaField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { optionalText } from "../../domain/config/document";
import { useFieldIssue, useSection } from "../../state/useConfig";

const FIELDS = [
  { key: "data_request", label: "Al pedir los datos del cliente", placeholder: "Ej.: Para continuar, ¿me compartes tu nombre y teléfono?" },
  { key: "human_handoff", label: "Al pasar la conversación a una persona", placeholder: "Ej.: Te comunico con alguien de nuestro equipo." },
  { key: "after_sale", label: "Después de una compra", placeholder: "Ej.: ¡Gracias por tu compra!" },
  { key: "follow_up", label: "Seguimiento a un cliente que no respondió", placeholder: "Ej.: Hola, ¿pudiste revisar la información?" },
] as const;

/** Mensajes opcionales del negocio: si no se escriben, el asistente responde con sus propias palabras. */
export function OtherMessagesForm() {
  const [messages, update] = useSection("messages");
  return (
    <Card title="Otros mensajes" description="Opcionales. Si no los escribes, el asistente responde con sus propias palabras.">
      {FIELDS.map(({ key, label, placeholder }) => (
        <MessageField key={key} path={`messages.${key}`} label={label} placeholder={placeholder} value={messages[key] ?? ""} onChange={(text) => update({ [key]: optionalText(text) })} />
      ))}
    </Card>
  );
}

function MessageField({ path, label, placeholder, value, onChange }: { path: string; label: string; placeholder: string; value: string; onChange: (text: string) => void }) {
  const issue = useFieldIssue(path);
  return <TextAreaField label={label} value={value} onChange={onChange} placeholder={placeholder} rows={2} issue={issue} />;
}
