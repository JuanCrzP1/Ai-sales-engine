import { createContext, useContext } from "react";
import type { ContractSchema } from "../domain/config/contractSchema";
import type { BusinessDirectory } from "../repositories/businessDirectory";

/** Las pantallas no conocen los repositorios: los errores de persistencia les llegan por el estado. */
export { PersistenceError, persistenceErrorMessage } from "../repositories/persistenceError";

export const DirectoryContext = createContext<BusinessDirectory | null>(null);

/** Los negocios que administra el panel. */
export function useBusinessDirectory(): BusinessDirectory {
  const directory = useContext(DirectoryContext);
  if (!directory) throw new Error("useBusinessDirectory debe usarse dentro de <App>.");
  return directory;
}

export const ContractSchemaContext = createContext<ContractSchema | null>(null);

/** El esquema del contrato que publica el servidor, ya cargado por el espacio de trabajo del negocio. */
export function useContractSchema(): ContractSchema {
  const schema = useContext(ContractSchemaContext);
  if (!schema) throw new Error("useContractSchema debe usarse dentro del espacio de trabajo de un negocio.");
  return schema;
}
