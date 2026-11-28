import { useEffect, useState, type FormEvent } from "react";
import { Button } from "../components/ui/Button";
import { Dialog } from "../components/ui/Dialog";
import { Alert } from "../components/ui/Feedback";
import { SelectField, TextField } from "../components/ui/FormFields";
import { CHANNEL_LABELS, type Channel, type PaymentConfirmationPreview, type PaymentConfirmed, type PaymentSale } from "../domain/inbox/types";
import { PersistenceError, persistenceErrorMessage } from "../state/directoryContext";
import { useInbox } from "../state/inboxContext";

const CURRENCIES = [
  { value: "COP", label: "Pesos colombianos (COP)" },
  { value: "USD", label: "Dólares (USD)" },
];

type Problems = Partial<Record<"customer_name" | "description" | "amount" | "currency" | "general", string>>;

/**
 * «Confirmar pago»: el equipo verificó que el dinero llegó. Muestra el mensaje que recibirá el cliente (el de Mensajes → Pagos, o el
 * de la plataforma) y deja anotar la venta. Al confirmar, el cliente recibe ese mensaje una sola vez, el chat queda atendido, la IA
 * sabe que el pago quedó confirmado y, si se anotó lo que compró y el valor, la venta queda en Ventas.
 */
export function ConfirmPaymentDialog({
  conversationId,
  channel,
  customerName,
  onConfirm,
  onClose,
  onDone,
}: {
  conversationId: string;
  channel: Channel;
  customerName: string;
  onConfirm: (sale: PaymentSale | null) => Promise<PaymentConfirmed>;
  onClose: () => void;
  onDone: (done: PaymentConfirmed) => void;
}) {
  const inbox = useInbox();
  const [preview, setPreview] = useState<PaymentConfirmationPreview | null>(null);
  const [loadProblem, setLoadProblem] = useState<string | null>(null);
  const [name, setName] = useState(customerName);
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("COP");
  const [problems, setProblems] = useState<Problems>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let active = true;
    inbox.paymentConfirmation(conversationId).then(
      (found) => active && setPreview(found),
      (error) => active && setLoadProblem(persistenceErrorMessage(error)),
    );
    return () => {
      active = false;
    };
  }, [inbox, conversationId]);

  const test = preview?.test ?? channel === "prueba";

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    // La venta es opcional: sin lo que compró ni el valor, se confirma el pago sin registrarla.
    const value = amount.replace(/[^\d,.-]/g, "").replace(/\./g, "").replace(",", ".");
    const writesSale = !test && (description.trim() !== "" || amount.trim() !== "");
    const local: Problems = {};
    if (writesSale) {
      if (!name.trim()) local.customer_name = "Escribe el nombre del cliente.";
      if (!description.trim()) local.description = "Escribe qué compró, o deja la venta en blanco.";
      if (!(Number(value) > 0)) local.amount = "Escribe el valor, o deja la venta en blanco.";
    }
    setProblems(local);
    if (Object.keys(local).length > 0) return;
    setSaving(true);
    try {
      onDone(await onConfirm(writesSale ? { customerName: name, description, amount: value, currency } : null));
    } catch (error) {
      const found: Problems = {};
      if (error instanceof PersistenceError) for (const problem of error.problems) found[problem.path.split(".").at(-1) as keyof Problems] = problem.message;
      setProblems(Object.keys(found).length && !found.general ? found : { general: persistenceErrorMessage(error) });
    } finally {
      setSaving(false);
    }
  };

  const where = test ? "en la bandeja (es una prueba)" : `por ${CHANNEL_LABELS[channel]}`;
  return (
    <Dialog title="Confirmar pago" description="Hazlo cuando ya verificaste que el dinero llegó." onClose={onClose}>
      <form className="sale-form" aria-label="Confirmar pago" noValidate onSubmit={submit}>
        {loadProblem && <Alert tone="danger">{loadProblem}</Alert>}
        {problems.general && <Alert tone="danger">{problems.general}</Alert>}
        {preview && !preview.pending && <Alert tone="info">Este chat no tiene un pago por confirmar.</Alert>}
        <div className="payment-confirmation">
          <p className="payment-confirmation__label">El cliente recibe este mensaje {where}:</p>
          <p className="payment-confirmation__message">{preview ? preview.message : "Cargando el mensaje…"}</p>
          <p className="payment-confirmation__hint">Lo cambias en Mensajes → Pagos.</p>
        </div>
        <p className="payment-confirmation__after">El chat queda atendido y la IA sigue con el cliente, sabiendo que su pago quedó confirmado.</p>
        {test ? (
          <p className="payment-confirmation__after">En las pruebas no se registran ventas.</p>
        ) : (
          <fieldset className="payment-confirmation__sale">
            <legend>Registrar la venta (opcional)</legend>
            <p className="payment-confirmation__hint">Queda en Ventas y suma en los reportes. Si lo dejas en blanco, no se registra.</p>
            <TextField label="Cliente" value={name} onChange={setName} maxLength={120} error={problems.customer_name} />
            <TextField label="Qué compró" value={description} onChange={setDescription} maxLength={200} placeholder="Ej.: Plan Básico" error={problems.description} />
            <div className="grid-2">
              <TextField label="Valor" value={amount} onChange={setAmount} inputMode="numeric" placeholder="Ej.: 210000" error={problems.amount} />
              <SelectField label="Moneda" value={currency} options={CURRENCIES} onChange={setCurrency} error={problems.currency} />
            </div>
          </fieldset>
        )}
        <div className="button-row button-row--end">
          <Button variant="ghost" onClick={onClose} disabled={saving}>
            Cancelar
          </Button>
          <Button type="submit" disabled={saving || !preview?.pending}>
            {saving ? "Enviando…" : "Confirmar y enviar"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
