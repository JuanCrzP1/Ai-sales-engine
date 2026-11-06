import type { ContractSchema } from "../domain/config/contractSchema";
import type { BusinessSummary } from "../domain/config/types";

export interface ImportResult {
  created: string[];
  skipped: string[];
}

/** Los negocios que administra el panel. Los fallos se rechazan con `PersistenceError`. */
export interface BusinessDirectory {
  list(): Promise<BusinessSummary[]>;
  create(input: { slug: string; name: string }): Promise<BusinessSummary>;
  /** Borra el negocio con sus versiones y datos de pago. No se puede deshacer. */
  remove(slug: string): Promise<void>;
  /** Importa los negocios existentes que falten; lo ya guardado no se toca. */
  importExisting(): Promise<ImportResult>;
  /** El esquema del contrato con el que se generan los formularios de los campos sin pantalla propia. */
  contractSchema(): Promise<ContractSchema>;
}
