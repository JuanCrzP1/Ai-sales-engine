import type { BusinessDocument, Diagnostic, PaymentFields, PaymentValues, VersionInfo } from "../domain/config/types";

export interface StoredConfig {
  slug: string;
  name: string;
  /** El documento guardado, o null si el negocio aún no tiene ninguna versión. */
  document: BusinessDocument | null;
  /** La versión del documento: el borrador en curso o, si no hay, lo publicado. */
  version: VersionInfo | null;
  latestVersion: number | null;
  publishedVersion: number | null;
  /** Estado de cada dato de pago del documento, por su referencia: nunca el valor completo. */
  paymentFields: PaymentFields;
}

export interface SaveRequest {
  document: BusinessDocument;
  paymentValues: PaymentValues;
  /** La versión más reciente que se conocía al empezar a editar: detecta cambios hechos en otra pestaña. */
  baseVersion: number | null;
}

/** Una versión guardada con su documento (los datos de pago, solo como referencias). */
export interface VersionDocument {
  version: VersionInfo;
  document: BusinessDocument;
}

/** Lo que el servidor opina de la versión que se está editando. */
export interface ReviewReport {
  version: number | null;
  diagnostics: Diagnostic[];
  compiles: boolean;
  compileError: string | null;
}

/**
 * Persistencia de la configuración de UN negocio. El servidor valida con el contrato: cada guardado crea una versión y
 * los datos de pago entran por aquí, pero solo vuelven enmascarados. Los fallos se rechazan con `PersistenceError`.
 */
export interface ConfigRepository {
  load(): Promise<StoredConfig>;
  /** Resuelve solo cuando el servidor aceptó y guardó el documento. */
  save(request: SaveRequest): Promise<StoredConfig>;
  review(): Promise<ReviewReport>;
  history(): Promise<VersionInfo[]>;
  /** Una versión concreta con su documento: sirve para comparar lo que se edita con lo publicado. */
  versionDocument(version: number): Promise<VersionDocument>;
  publish(version: number): Promise<StoredConfig>;
  rollback(): Promise<StoredConfig>;
  restore(version: number): Promise<StoredConfig>;
}
