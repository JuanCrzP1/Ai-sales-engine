import { useEffect, useState } from "react";
import type { CustomerField } from "../domain/commerce/customerFields";
import { useCommerce } from "./commerceContext";

/**
 * Los campos del cliente del negocio. `version` cambia cuando algo se creó, se cambió, se borró o se llenó en una ficha, y el catálogo
 * (con sus conteos) se vuelve a pedir. Si no se puede cargar queda vacío: Clientes funciona igual, sin campos.
 */
export function useCustomerFields(version: number): { list: CustomerField[]; loaded: boolean } {
  const commerce = useCommerce();
  const [state, setState] = useState<{ list: CustomerField[]; loaded: boolean }>({ list: [], loaded: false });
  useEffect(() => {
    let active = true;
    commerce.customerFields().then(
      (list) => active && setState({ list, loaded: true }),
      () => active && setState({ list: [], loaded: false }),
    );
    return () => {
      active = false;
    };
  }, [commerce, version]);
  return state;
}
