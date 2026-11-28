import { useCallback, useState } from "react";
import { customerName, moveKind } from "../../../domain/commerce/pipeline";
import { STAGE_LABELS, type BoardStage, type Customer } from "../../../domain/commerce/types";
import { useCommerce } from "../../../state/commerceContext";
import { persistenceErrorMessage } from "../../../state/directoryContext";

export interface MoveNotice {
  tone: "success" | "danger";
  text: string;
}

/**
 * Mover a un cliente de etapa, desde el tablero o la lista. Un cambio simple se guarda de una vez; «No compró» pide antes el motivo y
 * «Cliente» abre el registro de la venta (`asking` dice cuál ventana mostrar). `onChanged` avisa para volver a cargar.
 */
export function useCustomerMoves(onChanged: () => void) {
  const commerce = useCommerce();
  const [asking, setAsking] = useState<{ kind: "reason" | "sale"; customer: Customer } | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [notice, setNotice] = useState<MoveNotice | null>(null);

  const moved = useCallback(
    (customer: Customer, stage: BoardStage) => {
      setAsking(null);
      setNotice({ tone: "success", text: `${customerName(customer)} pasó a «${STAGE_LABELS[stage]}».` });
      onChanged();
    },
    [onChanged],
  );

  const move = useCallback(
    async (customer: Customer, stage: BoardStage, reason?: string) => {
      setBusyId(customer.conversationId);
      setNotice(null);
      try {
        await commerce.moveCustomer(customer.conversationId, stage, reason);
        moved(customer, stage);
      } catch (error) {
        setAsking(null);
        setNotice({ tone: "danger", text: persistenceErrorMessage(error) });
      } finally {
        setBusyId(null);
      }
    },
    [commerce, moved],
  );

  const request = useCallback(
    (customer: Customer, stage: BoardStage) => {
      const kind = moveKind(customer.stage, stage);
      if (kind === "direct") void move(customer, stage);
      else if (kind !== "none") setAsking({ kind, customer });
    },
    [move],
  );

  return {
    /** Pide pasar al cliente a esa etapa. */
    request,
    /** La ventana que hay que mostrar antes de terminar el cambio, o null. */
    asking,
    /** El cliente que se está guardando. */
    busyId,
    /** Lo último que pasó, para decirlo en la página. */
    notice,
    cancel: useCallback(() => setAsking(null), []),
    confirmLost: useCallback((reason: string) => (asking ? move(asking.customer, "lost", reason) : Promise.resolve()), [asking, move]),
    /** La venta quedó registrada: el servidor ya lo pasó a «Cliente». */
    sold: useCallback(() => asking && moved(asking.customer, "customer"), [asking, moved]),
    /** Abre el registro de la venta de ese cliente (el botón «Registrar venta» de la lista). */
    sell: useCallback((customer: Customer) => setAsking({ kind: "sale", customer }), []),
  };
}
