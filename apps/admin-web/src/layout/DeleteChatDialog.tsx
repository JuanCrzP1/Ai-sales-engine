import { useState } from "react";
import { Button } from "../components/ui/Button";
import { Dialog } from "../components/ui/Dialog";
import { Alert } from "../components/ui/Feedback";
import { persistenceErrorMessage } from "../state/directoryContext";
import { useInbox } from "../state/inboxContext";

interface DeleteChatDialogProps {
  conversationId: string;
  /** Cómo se llama el cliente (o su número), para que quede claro qué chat se borra. */
  contactName: string;
  /** Un chat de «Probar asistente»: no hay un cliente real ni memoria que olvidar. */
  isTest?: boolean;
  onClose: () => void;
  onDeleted: () => void;
}

/**
 * Confirma antes de eliminar un chat, diciendo exactamente qué se borra y qué no. Lo usan Conversaciones y Clientes: un cliente es
 * su chat. Si el servidor no puede borrarlo, lo dice y no se borra nada.
 */
export function DeleteChatDialog({ conversationId, contactName, isTest = false, onClose, onDeleted }: DeleteChatDialogProps) {
  const inbox = useInbox();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const confirm = async () => {
    setBusy(true);
    setError(null);
    try {
      await inbox.remove(conversationId);
      onDeleted();
    } catch (reason) {
      setError(persistenceErrorMessage(reason));
      setBusy(false);
    }
  };

  return (
    <Dialog title={isTest ? "Eliminar esta prueba" : `Eliminar el chat con ${contactName}`} description="Esto no se puede deshacer." onClose={busy ? () => undefined : onClose}>
      <div className="delete-chat">
        {error && <Alert tone="danger">{error}</Alert>}
        <ul className="delete-chat__list">
          <li>Se borran los mensajes, las fotos, los audios y los avisos de este chat.</li>
          {!isTest && <li>El asistente olvida lo que sabía de este cliente: si vuelve a escribir, empieza de cero.</li>}
          {!isTest && <li>Las ventas que registraste se conservan en Ventas y en los reportes.</li>}
        </ul>
        <div className="button-row button-row--end">
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            Cancelar
          </Button>
          <Button variant="danger" className="button--danger-solid" onClick={() => void confirm()} disabled={busy}>
            {busy ? "Eliminando…" : "Eliminar chat"}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
