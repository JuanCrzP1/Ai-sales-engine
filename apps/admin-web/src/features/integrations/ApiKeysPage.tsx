import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { Alert, EmptyState } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { Card, PageHeader } from "../../components/ui/Layout";
import type { CreatedApiKey } from "../../domain/integrations/types";
import { LoadingScreen } from "../../layout/StatusScreen";
import { INTEGRATIONS_ITEM } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useIntegrationsData } from "../../state/useIntegrationsData";
import { CreateKeyDialog, NewSecretDialog } from "./KeyDialogs";
import { KeysTable } from "./KeysTable";

/**
 * Integraciones → Claves de API: todas las claves que llegan a este negocio (las suyas y las de tu cuenta), qué puede cada una, a
 * qué negocios entra, cuándo se usó y cuándo vence, y revocarla.
 */
export function ApiKeysPage() {
  const data = useIntegrationsData();
  const pathTo = useWorkspacePath();
  const business = useParams().slug ?? "";
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState<CreatedApiKey | null>(null);
  const [revokeError, setRevokeError] = useState<string | null>(null);

  if (data.status === "loading") return <LoadingScreen label="Cargando las claves…" />;
  const areas = data.overview?.areas ?? [];

  return (
    <>
      <PageHeader
        eyebrow="Integraciones"
        title="Claves de API"
        description="Cada clave deja que otra plataforma o un agente de IA trabaje con tus negocios, solo con lo que le permitas. Se muestra una sola vez al crearla; si una se filtra o ya no la usas, revócala."
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
        description="Las de este negocio y las de tu cuenta que entran a él."
        actions={
          <Button size="small" onClick={() => setCreating(true)} disabled={!data.overview}>
            Crear clave
          </Button>
        }
      >
        {data.keys.length === 0 ? (
          <EmptyState title="Todavía no tienes claves" description="Crea una para cada plataforma o agente que vayas a conectar, con su nombre para reconocerla." />
        ) : (
          <KeysTable
            keys={data.keys}
            areas={areas}
            onRevoke={(key) => {
              setRevokeError(null);
              void data.revokeKey(key.id).then(setRevokeError);
            }}
          />
        )}
      </Card>

      {creating && data.overview && (
        <CreateKeyDialog
          purpose="any"
          areas={areas}
          business={business}
          create={data.createKey}
          onClose={() => setCreating(false)}
          onCreated={(key) => {
            setCreating(false);
            setCreated(key);
          }}
        />
      )}
      {created && <NewSecretDialog created={created} mcpUrl={data.overview?.mcpUrl} onClose={() => setCreated(null)} />}
    </>
  );
}
