import { createContext, useContext } from "react";
import type { Team } from "../repositories/team";

/** El equipo de los negocios y las invitaciones. Lo entrega la aplicación: aceptar una invitación ocurre fuera de un negocio. */
export const TeamContext = createContext<Team | null>(null);

export function useTeamService(): Team {
  const team = useContext(TeamContext);
  if (!team) throw new Error("useTeamService debe usarse dentro de <App>.");
  return team;
}
