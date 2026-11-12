import { createContext, useContext } from "react";
import type { Help } from "../repositories/help";

/** El Centro de ayuda. Lo entrega la aplicación: es el mismo en todos los negocios. */
export const HelpContext = createContext<Help | null>(null);

export function useHelpService(): Help {
  const help = useContext(HelpContext);
  if (!help) throw new Error("useHelpService debe usarse dentro de <App>.");
  return help;
}
