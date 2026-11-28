import { useEffect, useState } from "react";
import type { Label } from "../domain/commerce/labels";
import { useCommerce } from "./commerceContext";

/**
 * El catálogo de etiquetas del negocio. `version` cambia cuando algo se creó, se renombró, se borró o se le puso a un cliente, y el
 * catálogo (con sus conteos) se vuelve a pedir. Si no se puede cargar queda vacío: Clientes funciona igual, sin etiquetas.
 */
export function useLabels(version: number): { list: Label[]; loaded: boolean } {
  const commerce = useCommerce();
  const [state, setState] = useState<{ list: Label[]; loaded: boolean }>({ list: [], loaded: false });
  useEffect(() => {
    let active = true;
    commerce.labels().then(
      (list) => active && setState({ list, loaded: true }),
      () => active && setState({ list: [], loaded: false }),
    );
    return () => {
      active = false;
    };
  }, [commerce, version]);
  return state;
}
