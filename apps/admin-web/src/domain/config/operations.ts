import { createTransferMethod } from "./factories";
import type { AssistantConfig, Offering, TransferMethod, TransferMethodType } from "./types";

/**
 * Operaciones puras sobre la configuración: reciben una configuración y devuelven
 * una nueva, sin mutar la original. Son la única forma de modificarla desde la interfaz
 * (a través de `useConfigActions`).
 */

/** Secciones que se editan como un único objeto. */
export type EditableSection = "business" | "payments" | "closing" | "behavior" | "messages";

export function updateSection<K extends EditableSection>(
  config: AssistantConfig,
  section: K,
  patch: Partial<AssistantConfig[K]>,
): AssistantConfig {
  const next = { ...config };
  next[section] = { ...config[section], ...patch };
  return next;
}

/** Agrega el producto o servicio, o lo reemplaza si ya existe uno con el mismo id. */
export function saveOffering(config: AssistantConfig, offering: Offering): AssistantConfig {
  const exists = config.offerings.some((item) => item.id === offering.id);
  return {
    ...config,
    offerings: exists ? config.offerings.map((item) => (item.id === offering.id ? offering : item)) : [...config.offerings, offering],
  };
}

export function removeOffering(config: AssistantConfig, id: string): AssistantConfig {
  return { ...config, offerings: config.offerings.filter((item) => item.id !== id) };
}

export function setOfferingAvailability(config: AssistantConfig, id: string, available: boolean): AssistantConfig {
  return { ...config, offerings: config.offerings.map((item) => (item.id === id ? { ...item, available } : item)) };
}

export function addTransferMethod(config: AssistantConfig, method: TransferMethod = createTransferMethod()): AssistantConfig {
  return updateSection(config, "payments", { transferMethods: [...config.payments.transferMethods, method] });
}

export function removeTransferMethod(config: AssistantConfig, id: string): AssistantConfig {
  return updateSection(config, "payments", { transferMethods: config.payments.transferMethods.filter((item) => item.id !== id) });
}

/** Datos editables de una cuenta; el tipo se cambia solo con `changeTransferMethodType`. */
export type TransferMethodDetails = Partial<Omit<TransferMethod, "id" | "type">>;

export function updateTransferMethod(config: AssistantConfig, id: string, details: TransferMethodDetails): AssistantConfig {
  return mapTransferMethod(config, id, (method) => ({ ...method, ...details }));
}

/**
 * Cambia el tipo de una cuenta y borra los datos del tipo anterior (celular, banco,
 * número o llave), para no dejar información residual que ya no corresponde.
 * Cambiar al mismo tipo no modifica nada.
 */
export function changeTransferMethodType(config: AssistantConfig, id: string, type: TransferMethodType): AssistantConfig {
  return mapTransferMethod(config, id, (method) => (method.type === type ? method : createTransferMethod({ id: method.id, type })));
}

function mapTransferMethod(config: AssistantConfig, id: string, change: (method: TransferMethod) => TransferMethod): AssistantConfig {
  return updateSection(config, "payments", {
    transferMethods: config.payments.transferMethods.map((method) => (method.id === id ? change(method) : method)),
  });
}
