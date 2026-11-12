import { useEffect, useState } from "react";
import type { BusinessSummary } from "../domain/config/types";
import { useBusinessDirectory } from "./directoryContext";

/** Los negocios de quien usa el panel (para elegir a cuáles entra una clave). Vacío mientras carga o si no se pudieron leer. */
export function useMyBusinesses(): BusinessSummary[] {
  const directory = useBusinessDirectory();
  const [businesses, setBusinesses] = useState<BusinessSummary[]>([]);

  useEffect(() => {
    let active = true;
    directory.list().then(
      (list) => {
        if (active) setBusinesses(list);
      },
      () => undefined,
    );
    return () => {
      active = false;
    };
  }, [directory]);

  return businesses;
}
