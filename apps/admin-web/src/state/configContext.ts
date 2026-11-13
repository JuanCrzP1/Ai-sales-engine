import { createContext } from "react";
import type { OfferEntry } from "../domain/config/document";
import type { BusinessDocument, CatalogItem, EditableSection, OfferModel, PaymentFields, PaymentValues, Plan, TransferMethod, TransferMethodType, VersionInfo } from "../domain/config/types";
import type { ConfigProgress } from "../domain/validation/progress";
import type { ValidationIssue } from "../domain/validation/types";
import type { ReviewReport } from "../repositories/configRepository";

export type { ReviewReport };

/**
 * Estado del último guardado. `saved` solo se alcanza cuando el servidor aceptó el documento; `savedAt` es la fecha de la
 * versión guardada (también la de una sesión anterior). `problems` son los errores por campo que señaló el servidor.
 */
export interface SaveState {
  status: "idle" | "saving" | "saved" | "error";
  savedAt: string | null;
  error: string | null;
  problems: ValidationIssue[];
}

/** Qué versión se está editando y cuál está publicada. */
export interface ConfigMeta {
  slug: string;
  version: VersionInfo | null;
  latestVersion: number | null;
  publishedVersion: number | null;
}

/**
 * Plan o producto abierto en su formulario, aún sin pasar a la lista. Vive aquí, y no en la pantalla, para que lo escrito no se
 * pierda al cambiar de sección. `touched` indica si ya se escribió algo.
 */
export interface OfferingDraft {
  draft: OfferEntry;
  /** La categoría se escribe por nombre; su identificador se resuelve al aplicar los cambios. */
  categoryName: string;
  isNew: boolean;
  issues: ValidationIssue[];
  touched: boolean;
}

/** Resultado de publicar, revertir o restaurar: `error` es el mensaje del servidor si no se pudo. */
export type ActionResult = { ok: true } | { ok: false; error: string };

/** Operaciones con nombre sobre la configuración. Las pantallas no conocen cómo se aplican. */
export interface ConfigActions {
  updateSection: <K extends EditableSection>(section: K, patch: Partial<BusinessDocument[K]>) => void;
  setRootValue: (key: keyof BusinessDocument, value: unknown) => void;
  savePlan: (plan: Plan) => void;
  saveCatalogItem: (item: CatalogItem, category: string) => void;
  removeEntry: (id: string) => void;
  setEntryAvailability: (id: string, available: boolean) => void;
  switchOfferModel: (model: OfferModel) => void;
  renameCategory: (id: string, name: string) => void;
  removeCategory: (id: string) => void;
  setOfferingDraft: (update: OfferingDraft | null | ((current: OfferingDraft | null) => OfferingDraft | null)) => void;
  addPaymentProfile: () => void;
  removePaymentProfile: (profileId: string) => void;
  setPaymentLinkEnabled: (profileId: string, enabled: boolean) => void;
  removePaymentLink: (profileId: string) => void;
  setPaymentValue: (ref: string, value: string) => void;
  keepStoredPaymentValue: (ref: string) => void;
  setTransferEnabled: (profileId: string, enabled: boolean) => void;
  addTransferMethod: (profileId: string) => void;
  removeTransferMethod: (profileId: string, index: number) => void;
  updateTransferMethod: (profileId: string, index: number, patch: Pick<TransferMethod, "bank" | "account_type" | "label" | "holder">) => void;
  setTransferMethodEnabled: (profileId: string, index: number, enabled: boolean) => void;
  changeTransferMethodType: (profileId: string, index: number, type: TransferMethodType) => void;
  /** Envía los cambios al servidor. Resuelve true solo si los aceptó y guardó. */
  save: () => Promise<boolean>;
  /** Descarta lo que no se ha guardado y vuelve a lo último guardado. */
  discardChanges: () => void;
  loadReview: () => Promise<ReviewReport>;
  loadHistory: () => Promise<VersionInfo[]>;
  publish: (version: number) => Promise<ActionResult>;
  rollback: () => Promise<ActionResult>;
  restore: (version: number) => Promise<ActionResult>;
}

/**
 * Si lo que responde a los clientes está al día con lo guardado. Compara contenido, no números de versión:
 * - `never`: todavía no se ha publicado nada.
 * - `pending`: lo guardado es distinto de lo publicado (hay que publicar para que los clientes lo vean).
 * - `published`: lo guardado es lo publicado.
 * - `checking`: comparando (el primer instante).
 * Los cambios que aún no se guardan los dice `dirty`.
 */
export type PublicationState = "never" | "pending" | "published" | "checking";

export interface ConfigContextValue {
  document: BusinessDocument;
  paymentValues: PaymentValues;
  /** Lo que el servidor informó de los datos de pago guardados. */
  paymentFields: PaymentFields;
  offeringDraft: OfferingDraft | null;
  meta: ConfigMeta;
  /** Hay cambios sin guardar. */
  dirty: boolean;
  /** Lo guardado frente a lo publicado. */
  publication: PublicationState;
  /** El documento publicado (lo que responde hoy), o null si no hay o aún no se cargó. Para «Lo que cambia al publicar». */
  publishedDocument: BusinessDocument | null;
  /** Lo último guardado (sin los cambios que aún no se guardan): lo que se publicaría. */
  savedDocument: BusinessDocument;
  issues: ValidationIssue[];
  progress: ConfigProgress;
  save: SaveState;
  actions: ConfigActions;
}

export const ConfigContext = createContext<ConfigContextValue | null>(null);
