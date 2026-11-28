import { useState, type FormEvent } from "react";
import { Button } from "../../../../components/ui/Button";
import { SelectField, TextField } from "../../../../components/ui/FormFields";
import { assigneeLabel, type CardChange, type CustomerCard } from "../../../../domain/commerce/customerCard";
import { formatMoney } from "../../../../domain/commerce/types";
import type { CardResult } from "../../../../state/useCustomerCard";

const CURRENCIES = [
  { value: "COP", label: "Pesos (COP)" },
  { value: "USD", label: "Dólares (USD)" },
];
const NOBODY = "";

/**
 * Cuánto vale lo que el cliente podría comprar y quién del equipo lo atiende. El valor suma en «Por cerrar» mientras no compre. El
 * responsable se elige entre el equipo del negocio; sin equipo todavía, lo dice.
 */
export function DealSection({ card, saving, onUpdate }: { card: CustomerCard; saving: boolean; onUpdate: (change: CardChange) => Promise<CardResult> }) {
  const deal = card.customer.deal;
  const [editing, setEditing] = useState(false);
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("COP");
  const [problem, setProblem] = useState<string | null>(null);
  const [ownerProblem, setOwnerProblem] = useState<string | null>(null);

  const open = () => {
    setAmount(deal ? String(Number(deal.amount)) : "");
    setCurrency(deal?.currency ?? "COP");
    setProblem(null);
    setEditing(true);
  };
  const save = async (change: CardChange) => {
    const result = await onUpdate(change);
    if (result.ok) setEditing(false);
    else setProblem(result.message);
  };
  const submit = (event: FormEvent) => {
    event.preventDefault();
    const value = amount.replace(/[^\d,.-]/g, "").replace(/\./g, "").replace(",", ".");
    if (!(Number(value) > 0)) return setProblem("Escribe cuánto vale, en números.");
    void save({ amount: value, currency });
  };
  const assign = async (userId: string) => {
    const result = await onUpdate({ ownerId: userId === NOBODY ? null : userId });
    setOwnerProblem(result.ok ? null : result.message);
  };

  return (
    <section className="card-section" aria-label="Valor y responsable">
      <div className="deal-grid">
        <div className="deal-box">
          <span className="deal-box__label">Valor</span>
          {!editing && (
            <>
              <span className={`deal-box__value${deal ? "" : " deal-box__value--empty"}`}>{deal ? formatMoney(deal.amount, deal.currency) : "Sin valor"}</span>
              <button type="button" className="link-button" onClick={open}>
                {deal ? "Cambiar" : "Poner valor"}
              </button>
            </>
          )}
          {editing && (
            <form className="deal-form" aria-label="Valor del cliente" noValidate onSubmit={submit}>
              <TextField label="Cuánto vale" required value={amount} onChange={setAmount} inputMode="numeric" placeholder="Ej.: 210000" error={problem ?? undefined} />
              <SelectField label="Moneda" value={currency} options={CURRENCIES} onChange={setCurrency} />
              <div className="button-row">
                <Button type="submit" size="small" disabled={saving}>
                  {saving ? "Guardando…" : "Guardar"}
                </Button>
                <Button size="small" variant="ghost" disabled={saving} onClick={() => setEditing(false)}>
                  Cancelar
                </Button>
                {deal && (
                  <Button size="small" variant="ghost" disabled={saving} onClick={() => void save({ amount: null })}>
                    Quitar valor
                  </Button>
                )}
              </div>
            </form>
          )}
        </div>
        <div className="deal-box">
          {card.assignees.length > 0 ? (
            <SelectField
              label="Responsable"
              value={card.owner?.userId ?? NOBODY}
              options={[{ value: NOBODY, label: "Sin responsable" }, ...card.assignees.map((member) => ({ value: member.userId, label: assigneeLabel(member) }))]}
              onChange={(userId) => void assign(userId)}
              error={ownerProblem ?? undefined}
            />
          ) : (
            <>
              <span className="deal-box__label">Responsable</span>
              <span className="deal-box__value deal-box__value--empty">Sin equipo todavía</span>
              <span className="deal-box__hint">Cuando invites a alguien a tu equipo, podrás asignarle clientes.</span>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
