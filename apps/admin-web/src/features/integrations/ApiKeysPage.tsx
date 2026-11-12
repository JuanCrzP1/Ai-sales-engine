import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { Alert, Badge, EmptyState } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { Card, PageHeader } from "../../components/ui/Layout";
import type { CreatedApiKey } from "../../domain/integrations/types";
import { fullDate, relativeTime } from "../../domain/inbox/format";
import { LoadingScreen } from "../../layout/StatusScreen";
import { INTEGRATIONS_ITEM } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useIntegrationsData } from "../../state/useIntegrationsData";
import { CreateKeyDialog, NewSecretDialog } from "./KeyDialogs";

/** Integraciones → Claves de API: todas las claves del negocio, para qué es cada una, cuándo se usó y revocarla. */
export function ApiKeysPage() {
  const data = useIntegrationsData();
  const pathTo = useWorkspacePath();
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState<CreatedApiKey | null>(null);
  const [revokeError, setRevokeError] = useState<string | null>(null);

  if (data.status === "loading") return <LoadingScreen label="Cargando las claves…" />;
  const labels = new Map((data.overview?.scopes ?? []).map((scope) => [scope.id, scope.label]));

  return (
    <>
      <PageHeader
        eyebrow="Integraciones"
        title="Claves de API"
        description="Cada clave deja que otra plataforma use este negocio. Se muestra una sola vez al crearla; si una se filtra o ya no la usas, revócala."
        actions={
          <Link className="back-link" to={pathTo(INTEGRATIONS_ITEM.path)}>
            <Icon name="arrowLeft" size={16} /> Integraciones
          </Link>
        }
      />
      {data.status === "error" && <Alert tone="danger" title={data.error ?? "No se pudieron cargar."} />}
      {revokeError && <Alert tone="danger" title={revokeError} />}

      <Card
        icon="shield"
        tone="emerald"
        title="Tus claves"
        actions={
          <Button size="small" onClick={() => setCreating(true)} disabled={!data.overview}>
            Crear clave
          </Button>
        }
      >
        {data.keys.length === 0 ? (
          <EmptyState title="Todavía no tienes claves" description="Crea una para cada plataforma que vayas a conectar, con su nombre para reconocerla." />
        ) : (
          <div className="table-wrap">
            <table className="data-table api-keys">
              <thead>
                <tr>
                  <th scope="col">Nombre</th>
                  <th scope="col">Clave</th>
                  <th scope="col">Permisos</th>
                  <th scope="col">Último uso</th>
                  <th scope="col">Estado</th>
                  <th scope="col">
                    <span className="visually-hidden">Acciones</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.keys.map((key) => (
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
                    <td>{key.scopes.map((scope) => labels.get(scope) ?? scope).join(", ")}</td>
                    <td>{key.lastUsedAt ? relativeTime(key.lastUsedAt) : "Nunca"}</td>
                    <td>{key.active ? <Badge tone="success">Activa</Badge> : <Badge tone="neutral">Revocada</Badge>}</td>
                    <td>
                      {key.active && (
                        <ConfirmButton
                          confirmLabel="Sí, revocarla"
                          onConfirm={() => {
                            setRevokeError(null);
                            void data.revokeKey(key.id).then(setRevokeError);
                          }}
                        >
                          Revocar
                        </ConfirmButton>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {creating && data.overview && (
        <CreateKeyDialog
          scopes={data.overview.scopes}
          create={data.createKey}
          onClose={() => setCreating(false)}
          onCreated={(key) => {
            setCreating(false);
            setCreated(key);
          }}
        />
      )}
      {created && <NewSecretDialog created={created} onClose={() => setCreated(null)} />}
    </>
  );
}
