import { createContext, useContext } from "react";
import type { ApplicationServices } from "./compositionRoot";

export const ServicesContext = createContext<ApplicationServices | null>(null);

export function useApplicationServices(): ApplicationServices {
  const services = useContext(ServicesContext);
  if (!services) throw new Error("useApplicationServices debe usarse dentro de <App>.");
  return services;
}
