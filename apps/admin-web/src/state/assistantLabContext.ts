import { createContext, useContext } from "react";
import type { AssistantLab } from "../repositories/assistantLab";

/** La inteligencia artificial y el área de pruebas del negocio abierto. La entrega el espacio de trabajo del negocio. */
export const AssistantLabContext = createContext<AssistantLab | null>(null);

export function useAssistantLab(): AssistantLab {
  const lab = useContext(AssistantLabContext);
  if (!lab) throw new Error("useAssistantLab debe usarse dentro del espacio de trabajo de un negocio.");
  return lab;
}
