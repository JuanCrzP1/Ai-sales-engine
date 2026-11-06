import { useCallback } from "react";
import { useParams } from "react-router-dom";
import { workspacePath } from "./navItems";

/** Convierte una ruta del recorrido en la ruta completa del negocio que está abierto. */
export function useWorkspacePath(): (path?: string) => string {
  const { slug = "" } = useParams();
  return useCallback((path = "") => workspacePath(slug, path), [slug]);
}
