import { useState, type FormEvent } from "react";
import { Button } from "../../components/ui/Button";
import { Dialog } from "../../components/ui/Dialog";
import { Alert } from "../../components/ui/Feedback";
import { SelectField, TextField } from "../../components/ui/FormFields";
import type { Sale } from "../../domain/commerce/types";
import { PersistenceError, persistenceErrorMessage } from "../../state/directoryContext";
import { useCommerce } from "../../state/commerceContext";

const CURRENCIES = [
  { value: "COP", label: "Pesos colombianos (COP)" },
  { value: "USD", label: "Dólares (USD)" },
];

type Problems = Partial<Record<"customer_name" | "description" | "amount" | "currency" | "general", string>>;

/**
 * Registrar una venta: lo que compró el cliente y cuánto pagó. Desde un cliente o un pago por verificar llega con su conversación:
 * el cliente pasa a «Cliente» y la conversación deja de esperar la verificación.
 */
export function RecordSaleDialog({
  customerName = "",
  conversationId = null,
  onClose,
  onSaved,
}: {
  customerName?: string;
  conversationId?: string | null;
  onClose: () => void;
  onSaved: (sale: Sale) => void;
}) {
  const commerce = useCommerce();
  const [name, setName] = useState(customerName);
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("COP");
  const [problems, setProblems] = useState<Problems>({});
  const [saving, setSaving] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const local: Problems = {};
    if (!name.trim()) local.customer_name = "Escribe el nombre del cliente.";
    if (!description.trim()) local.description = "Escribe qué compró.";
    const value = amount.replace(/[^\d,.-]/g, "").replace(/\./g, "").replace(",", ".");
    if (!(Number(value) > 0)) local.amount = "Escribe el valor de la venta.";
    setProblems(local);
    if (Object.keys(local).length > 0) return;
    setSaving(true);
    try {
      onSaved(await commerce.recordSale({ customerName: name, description, amount: value, currency, conversationId }));
    } catch (error) {
      const found: Problems = {};
      if (error instanceof PersistenceError) for (const problem of error.problems) found[problem.path.split(".").at(-1) as keyof Problems] = problem.message;
      setProblems(Object.keys(found).length ? found : { general: persistenceErrorMessage(error) });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      title="Registrar venta"
      description={conversationId ? "Queda en Ventas y el cliente pasa a «Cliente»." : "Queda en Ventas y suma en los reportes."}
      onClose={onClose}
    >
      <form className="sale-form" aria-label="Registrar venta" noValidate onSubmit={submit}>
        {problems.general && <Alert tone="danger">{problems.general}</Alert>}
        <TextField label="Cliente" required value={name} onChange={setName} maxLength={120} error={problems.customer_name} />
        <TextField label="Qué compró" required value={description} onChange={setDescription} maxLength={200} placeholder="Ej.: Plan Básico" error={problems.description} />
        <div className="grid-2">
          <TextField label="Valor" required value={amount} onChange={setAmount} inputMode="numeric" placeholder="Ej.: 210000" error={problems.amount} />
          <SelectField label="Moneda" value={currency} options={CURRENCIES} onChange={setCurrency} error={problems.currency} />
        </div>
        <div className="button-row button-row--end">
          <Button variant="ghost" onClick={onClose} disabled={saving}>
            Cancelar
          </Button>
          <Button type="submit" disabled={saving}>
            {saving ? "Guardando…" : "Registrar venta"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
