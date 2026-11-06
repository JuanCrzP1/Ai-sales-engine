import type { BusinessConfig, Offer, TransferMethod } from "../../contracts/businessConfig.v1";

/**
 * El panel edita directamente el documento del contrato global (BusinessConfig v1): no tiene un modelo propio.
 * Así lo que no tiene pantalla se conserva al guardar y los errores del servidor señalan el mismo campo que se edita.
 */

export type {
  CatalogItem,
  CustomerProblem,
  Faq,
  Identity,
  ItemPrice,
  Location,
  PaymentProfile,
  Plan,
  PlanPrice,
  Policies,
  Promotion,
  RecommendationRule,
  TransferMethod,
} from "../../contracts/businessConfig.v1";

/** El documento con sus secciones presentes: la API siempre las devuelve así. */
export type BusinessDocument = BusinessConfig &
  Required<Pick<BusinessConfig, "terms" | "payments" | "sales" | "response_style" | "knowledge" | "inventory">>;

/** Secciones que se editan como un único objeto. */
export type EditableSection = "identity" | "terms" | "sales" | "capabilities" | "messages" | "response_style" | "knowledge" | "inventory";

export type OfferModel = Offer["model"];

export type TransferMethodType = TransferMethod["type"];

/**
 * Datos de pago escritos en esta sesión, por su referencia en el documento. Solo viajan al guardar: el servidor los
 * cifra y nunca los devuelve completos. Un valor presente significa que se está escribiendo uno nuevo; vacío, en un dato ya
 * guardado, no se envía y se conserva el que hay.
 */
export type PaymentValues = Record<string, string>;

/** Lo que el servidor informa de un dato de pago guardado: si se puede usar y una versión enmascarada. Nunca el valor. */
export interface PaymentFieldState {
  status: "configured" | "missing" | "unreadable";
  masked: string | null;
}

/** El estado de cada dato de pago del documento guardado, por su referencia. */
export type PaymentFields = Record<string, PaymentFieldState>;

/** Lo que se está editando y aún no se ha guardado. */
export interface WorkingCopy {
  document: BusinessDocument;
  paymentValues: PaymentValues;
}

export interface BusinessSummary {
  slug: string;
  name: string;
  latestVersion: number | null;
  draftVersion: number | null;
  publishedVersion: number | null;
}

export type VersionStatus = "draft" | "published" | "archived";

export interface VersionInfo {
  version: number;
  status: VersionStatus;
  createdAt: string | null;
  publishedAt: string | null;
}

/** Hallazgo del diagnóstico del servidor: un dato que conviene revisar, aunque el documento sea válido. */
export interface Diagnostic {
  code: string;
  kind: string;
  path: string;
  message: string;
}
