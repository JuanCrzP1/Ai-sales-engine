import { createContext } from "react";
import type { EditableSection, TransferMethodDetails } from "../domain/config/operations";
import type { AssistantConfig, Offering, TransferMethodType } from "../domain/config/types";
import type { ConfigProgress } from "../domain/validation/progress";
import type { ValidationIssue } from "../domain/validation/types";

/**
 * Estado del último guardado. `saved` solo se alcanza cuando el repositorio confirmó la
 * operación; `savedAt` es la fecha del último guardado confirmado (también el de una sesión anterior).
 */
export interface SaveState {
  status: "idle" | "saving" | "saved" | "error";
  savedAt: string | null;
  error: string | null;
}

/** Operaciones con nombre sobre la configuración. Las pantallas no conocen cómo se aplican. */
export interface ConfigActions {
  updateSection: <K extends EditableSection>(section: K, patch: Partial<AssistantConfig[K]>) => void;
  saveOffering: (offering: Offering) => void;
  removeOffering: (id: string) => void;
  setOfferingAvailability: (id: string, available: boolean) => void;
  addTransferMethod: () => void;
  updateTransferMethod: (id: string, details: TransferMethodDetails) => void;
  changeTransferMethodType: (id: string, type: TransferMethodType) => void;
  removeTransferMethod: (id: string) => void;
  /** Borra toda la configuración del asistente (la cuenta no se toca). */
  resetConfig: () => void;
  /** Vuelve a intentar guardar la configuración actual tras un fallo. */
  retrySave: () => void;
}

export interface ConfigContextValue {
  config: AssistantConfig;
  issues: ValidationIssue[];
  progress: ConfigProgress;
  save: SaveState;
  actions: ConfigActions;
}

export const ConfigContext = createContext<ConfigContextValue | null>(null);
