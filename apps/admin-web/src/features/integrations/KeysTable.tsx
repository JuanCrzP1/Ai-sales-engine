import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { Badge } from "../../components/ui/Feedback";
import { fullDate, relativeTime } from "../../domain/inbox/format";
import { permissionSummary, reachLabel, type ApiKey, type KeyArea } from "../../domain/integrations/types";

/**
 * Las claves en una tabla: para qué es cada una (sus permisos por área), a qué negocios entra, cuándo se usó, cuándo vence y su
 * estado, con «Revocar». Nunca su valor: solo su comienzo para reconocerla.
 */
export function KeysTable({ keys, areas, onRevoke }: { keys: ApiKey[]; areas: KeyArea[]; onRevoke: (key: ApiKey) => void }) {
  return (
    <div className="table-wrap">
      <table className="data-table api-keys">
        <thead>
          <tr>
            <th scope="col">Nombre</th>
            <th scope="col">Clave</th>
            <th scope="col">Qué puede</th>
            <th scope="col">Negocios</th>
            <th scope="col">Último uso</th>
            <th scope="col">Estado</th>
            <th scope="col">
              <span className="visually-hidden">Acciones</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {keys.map((key) => (
            <tr key={key.id} className={key.active ? undefined : "api-keys__revoked"}>
              <td>
                <strong>{key.name}</strong>
                <span className="api-keys__meta">
                  Creada {fullDate(key.createdAt)}
                  {key.createdBy ? ` por ${key.createdBy}` : ""}
                </span>
              </td>
              <td>
                <code>{key.prefix}…</code>
              </td>
              <td>{permissionSummary(key, areas)}</td>
              <td>{reachLabel(key)}</td>
              <td>{key.lastUsedAt ? relativeTime(key.lastUsedAt) : "Nunca"}</td>
              <td>
                {key.revokedAt ? (
                  <Badge tone="neutral">Revocada</Badge>
                ) : key.expired ? (
                  <Badge tone="warning">Vencida</Badge>
                ) : (
                  <Badge tone="success">Activa</Badge>
                )}
                {key.active && <span className="api-keys__meta">{key.expiresAt ? `Vence ${fullDate(key.expiresAt)}` : "No vence"}</span>}
              </td>
              <td>
                {!key.revokedAt && (
                  <ConfirmButton confirmLabel="Sí, revocarla" onConfirm={() => onRevoke(key)}>
                    Revocar
                  </ConfirmButton>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
