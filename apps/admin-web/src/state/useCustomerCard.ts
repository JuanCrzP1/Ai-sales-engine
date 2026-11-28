import { useCallback, useEffect, useState } from "react";
import type { CardChange, CustomerCard } from "../domain/commerce/customerCard";
import type { LabelColor } from "../domain/commerce/labels";
import type { Commerce } from "../repositories/commerce";
import { useCommerce } from "./commerceContext";
import { PersistenceError, persistenceErrorMessage } from "../repositories/persistenceError";
import type { Loadable } from "./useConversations";

/** Cómo terminó un cambio: bien, o con el mensaje para mostrar (y el campo que lo causó, si el servidor lo dijo). */
export type CardResult = { ok: true } | { ok: false; message: string; field: string | null };

/**
 * La ficha de un cliente y sus cambios. `version` cambia cuando algo se movió afuera (el tablero) y la ficha se vuelve a pedir, sin
 * parpadear: mientras llega, se sigue viendo la anterior. `onChanged` avisa al tablero cuando la ficha cambió algo que él muestra.
 */
export function useCustomerCard(conversationId: string, version: number, onChanged: () => void) {
  const commerce = useCommerce();
  const [state, setState] = useState<Loadable<CustomerCard>>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [saving, setSaving] = useState(false);

  useEffect(() => setState({ status: "loading" }), [conversationId]);
  useEffect(() => {
    let active = true;
    commerce.customerCard(conversationId).then(
      (data) => active && setState({ status: "ready", data }),
      (error: unknown) => active && setState({ status: "error", message: persistenceErrorMessage(error) }),
    );
    return () => {
      active = false;
    };
  }, [commerce, conversationId, version, attempt]);

  const run = useCallback(
    async (work: (commerce: Commerce) => Promise<CustomerCard | void>, affectsBoard: boolean): Promise<CardResult> => {
      setSaving(true);
      try {
        const card = (await work(commerce)) ?? (await commerce.customerCard(conversationId));
        setState({ status: "ready", data: card });
        if (affectsBoard) onChanged();
        return { ok: true };
      } catch (error) {
        const field = error instanceof PersistenceError ? (error.problems[0]?.path.split(".").at(-1) ?? null) : null;
        return { ok: false, message: persistenceErrorMessage(error), field };
      } finally {
        setSaving(false);
      }
    },
    [commerce, conversationId, onChanged],
  );

  return {
    state,
    saving,
    reload: useCallback(() => setAttempt((count) => count + 1), []),
    /** Cambia el valor y/o el responsable: el tablero también lo muestra. */
    update: useCallback((change: CardChange) => run((api) => api.updateCustomerCard(conversationId, change), true), [run, conversationId]),
    addNote: useCallback((body: string) => run((api) => api.addCustomerNote(conversationId, body).then(() => undefined), false), [run, conversationId]),
    deleteNote: useCallback((noteId: string) => run((api) => api.deleteCustomerNote(conversationId, noteId), false), [run, conversationId]),
    /** Deja al cliente con esas etiquetas: el tablero también las muestra. */
    setLabels: useCallback((labelIds: string[]) => run((api) => api.setCustomerLabels(conversationId, labelIds).then(() => undefined), true), [run, conversationId]),
    /** Crea una etiqueta nueva y se la pone al cliente, además de las que ya tiene (`current`). */
    createLabel: useCallback(
      (name: string, color: LabelColor, current: string[]) =>
        run(async (api) => {
          const created = await api.createLabel(name, color);
          await api.setCustomerLabels(conversationId, [...current, created.id]);
        }, true),
      [run, conversationId],
    ),
  };
}
