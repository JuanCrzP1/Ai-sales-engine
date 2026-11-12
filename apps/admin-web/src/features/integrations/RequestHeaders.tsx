import { CopyButton } from "../../components/ui/CopyButton";
import { REQUEST_HEADERS } from "../../domain/integrations/types";

/**
 * Las cabeceras de la petición como las piden las plataformas: un nombre y un valor por fila, cada uno con su botón de copiar.
 * «TU_CLAVE» se cambia por la clave creada.
 */
export function RequestHeaders() {
  return (
    <div className="request-headers">
      <span className="field__label">Cabeceras de la petición (encabezados)</span>
      <table className="request-headers__table">
        <thead>
          <tr>
            <th scope="col">Nombre</th>
            <th scope="col">Valor</th>
          </tr>
        </thead>
        <tbody>
          {REQUEST_HEADERS.map((header) => (
            <tr key={header.name}>
              <td>
                <span className="request-headers__cell">
                  <code>{header.name}</code>
                  <CopyButton text={header.name} />
                </span>
              </td>
              <td>
                <span className="request-headers__cell">
                  <code>{header.value}</code>
                  <CopyButton text={header.value} />
                </span>
                {header.hint && <span className="request-headers__hint">{header.hint}</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
