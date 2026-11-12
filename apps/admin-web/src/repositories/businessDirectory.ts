import type { ContractSchema } from "../domain/config/contractSchema";
import type { BusinessSummary, BusinessTemplate } from "../domain/config/types";

export interface ImportResult {
  created: string[];
  skipped: string[];
}

/** Los negocios que administra el panel. Los fallos se rechazan con `PersistenceError`. */
export interface BusinessDirectory {
  /** Importar los negocios de ejemplo: solo en este equipo. En la nube cada cuenta crea los suyos. */
  readonly canImportExisting: boolean;
  list(): Promise<BusinessSummary[]>;
  /** Crea el negocio vacío o, con `template`, con su primer borrador ya escrito (sin publicar). */
  create(input: { slug: string; name: string; template?: string | null }): Promise<BusinessSummary>;
  /** Las plantillas para empezar un negocio. «Empezar de cero» no es una plantilla: es no elegir ninguna. */
  templates(): Promise<BusinessTemplate[]>;
  /**
   * Elimina el negocio y todo lo suyo (configuración, conversaciones, clientes, ventas, claves, WhatsApp). Solo su dueño, con
   * `confirmation` igual a su nombre. No se puede deshacer; si falla un paso, no se borra nada.
   */
  remove(slug: string, confirmation: string): Promise<void>;
  /** Importa los negocios de ejemplo que falten; lo ya guardado no se toca. */
  importExisting(): Promise<ImportResult>;
  /** El esquema del contrato con el que se generan los formularios de los campos sin pantalla propia. */
  contractSchema(): Promise<ContractSchema>;
}
