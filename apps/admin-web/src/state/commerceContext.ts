import { createContext, useContext } from "react";
import type { Commerce } from "../repositories/commerce";

/** Clientes, ventas y reportes del negocio abierto. */
export const CommerceContext = createContext<Commerce | null>(null);

export function useCommerce(): Commerce {
  const commerce = useContext(CommerceContext);
  if (!commerce) throw new Error("useCommerce debe usarse dentro del espacio de trabajo de un negocio.");
  return commerce;
}
