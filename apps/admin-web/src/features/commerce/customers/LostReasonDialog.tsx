import { useState, type FormEvent } from "react";
import { Button } from "../../../components/ui/Button";
import { Dialog } from "../../../components/ui/Dialog";
import { TextField } from "../../../components/ui/FormFields";
import { LOST_REASONS, MAX_LOST_REASON } from "../../../domain/commerce/pipeline";

/** Al pasar a alguien a «No compró»: por qué (opcional). El motivo queda en su tarjeta y ayuda a ver qué mejorar. */
export function LostReasonDialog({ customerName, saving = false, onConfirm, onClose }: { customerName: string; saving?: boolean; onConfirm: (reason: string) => void; onClose: () => void }) {
  const [reason, setReason] = useState("");
  const submit = (event: FormEvent) => {
    event.preventDefault();
    onConfirm(reason.trim());
  };
  return (
    <Dialog title="¿Por qué no compró?" description={`${customerName} sale del embudo. Si vuelve a escribir con interés, regresa solo.`} onClose={onClose}>
      <form className="lost-form" aria-label="Motivo por el que no compró" noValidate onSubmit={submit}>
        <div className="lost-form__chips" role="group" aria-label="Motivos frecuentes">
          {LOST_REASONS.map((text) => (
            <button key={text} type="button" className="lost-form__chip" aria-pressed={reason === text} onClick={() => setReason(reason === text ? "" : text)}>
              {text}
            </button>
          ))}
        </div>
        <TextField label="Motivo" value={reason} onChange={setReason} maxLength={MAX_LOST_REASON} placeholder="Elige uno o escribe otro (opcional)" />
        <div className="button-row button-row--end">
          <Button variant="ghost" onClick={onClose} disabled={saving}>
            Cancelar
          </Button>
          <Button type="submit" disabled={saving}>
            {saving ? "Guardando…" : "Pasar a «No compró»"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
