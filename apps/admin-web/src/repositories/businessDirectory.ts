import type { ContractSchema } from "../domain/config/contractSchema";
import type { BusinessSummary, BusinessTemplate } from "../domain/config/types";

export interface ImportResult {
  created: string[];
  skipped: string[];
}

/** Los negocios que administra el panel. Los fallos se rechazan con `PersistenceError`. */
export interface BusinessDirectory {
  /** Importar los negocios de ejemplo y eliminar negocios: solo en este equipo. En la nube cada cuenta crea los suyos. */
  readonly canImportExisting: boolean;
  readonly canRemove: boolean;
  list(): Promise<BusinessSummary[]>;
  /** Crea el negocio vacío o, con `template`, con su primer borrador ya escrito (sin publicar). */
  create(input: { slug: string; name: string; template?: string | null }): Promise<BusinessSummary>;
  /** Las plantillas para empezar un negocio. «Empezar de cero» no es una plantilla: es no elegir ninguna. */
  templates(): Promise<BusinessTemplate[]>;
  /** Borra el negocio con sus versiones y datos de pago. No se puede deshacer. */
  remove(slug: string): Promise<void>;
  /** Importa los negocios de ejemplo que falten; lo ya guardado no se toca. */
  importExisting(): Promise<ImportResult>;
  /** El esquema del contrato con el que se generan los formularios de los campos sin pantalla propia. */
  contractSchema(): Promise<ContractSchema>;
}
