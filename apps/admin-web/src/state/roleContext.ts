import { createContext, useContext } from "react";
import { can, type Capability, type Role } from "../domain/team/team";

/** El rol de quien usa el panel en el negocio abierto. Lo entrega el espacio de trabajo del negocio. */
export const BusinessRoleContext = createContext<Role | null>(null);

/** Fuera de un negocio (o en pruebas que no lo entregan), dueño: el servidor decide de verdad. */
export function useBusinessRole(): Role {
  return useContext(BusinessRoleContext) ?? "owner";
}

export function useCan(capability: Capability): boolean {
  return can(useBusinessRole(), capability);
}
