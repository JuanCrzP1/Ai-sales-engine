import { useState, type FormEvent } from "react";
import { Button } from "../components/ui/Button";
import { Dialog } from "../components/ui/Dialog";
import { Alert } from "../components/ui/Feedback";
import { TextField } from "../components/ui/FormFields";
import { PersistenceError, persistenceErrorMessage, useBusinessDirectory } from "../state/directoryContext";

interface DeleteBusinessDialogProps {
  business: { slug: string; name: string };
  onClose: () => void;
  onDeleted: () => void;
}

/** Lo que se pierde al eliminar un negocio, en palabras de quien lo administra. */
export const WHAT_IS_DELETED = [
  "La configuración del asistente con todas sus versiones, y los datos de pago.",
  "Las conversaciones con sus fotos y audios, los clientes, las ventas y los reportes.",
  "WhatsApp se desconecta y el asistente deja de responder a tus clientes.",
  "Las claves de API de este negocio y los ajustes de atención humana e inteligencia artificial.",
];

const comparable = (text: string) => text.trim().replace(/\s+/g, " ").toLowerCase();

/**
 * Confirma antes de eliminar un negocio: dice qué se pierde y pide escribir su nombre. Lo usan «Tus negocios» y Configuración →
 * Eliminar negocio. Si el servidor no puede (por ejemplo, no logra desconectar WhatsApp), lo dice y no se borra nada.
 */
export function DeleteBusinessDialog({ business, onClose, onDeleted }: DeleteBusinessDialogProps) {
  const directory = useBusinessDirectory();
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const matches = comparable(typed) !== "" && comparable(typed) === comparable(business.name);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!matches) return;
    setBusy(true);
    setError(null);
    try {
      await directory.remove(business.slug, typed);
      onDeleted();
    } catch (reason) {
      setError(reason instanceof PersistenceError && reason.problems.length > 0 ? reason.problems[0]!.message : persistenceErrorMessage(reason));
      setBusy(false);
    }
  };

  return (
    <Dialog title={`Eliminar «${business.name}»`} description="Esto no se puede deshacer." onClose={busy ? () => undefined : onClose}>
      <form className="form-stack" onSubmit={(event) => void submit(event)} noValidate>
        {error && <Alert tone="danger">{error}</Alert>}
        <ul className="delete-chat__list">
          {WHAT_IS_DELETED.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <TextField label={`Para confirmar, escribe el nombre del negocio: ${business.name}`} value={typed} onChange={setTyped} autoComplete="off" />
        <div className="button-row button-row--end">
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            Cancelar
          </Button>
          <Button type="submit" variant="danger" className="button--danger-solid" disabled={busy || !matches}>
            {busy ? "Eliminando…" : "Eliminar definitivamente"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
