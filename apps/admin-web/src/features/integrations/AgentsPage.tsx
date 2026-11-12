import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { IntegrationMark } from "../../components/brand/IntegrationMark";
import { Button } from "../../components/ui/Button";
import { CopyField } from "../../components/ui/CopyButton";
import { Alert, Badge, EmptyState } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { Card, PageHeader } from "../../components/ui/Layout";
import { Tabs } from "../../components/ui/Tabs";
import { relativeTime } from "../../domain/inbox/format";
import { agentConnection, isAgentKey, mcpSnippets, type ApiKey, type CreatedApiKey } from "../../domain/integrations/types";
import { LoadingScreen } from "../../layout/StatusScreen";
import { INTEGRATIONS_ITEM } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useIntegrationsData } from "../../state/useIntegrationsData";
import { CreateKeyDialog, NewSecretDialog } from "./KeyDialogs";
import { KeysTable } from "./KeysTable";

const CAN_DO = [
  "Crear negocios y montar su configuración completa: negocio, productos y precios, pagos, preguntas frecuentes y mensajes.",
  "Revisar lo que falta y lo que cambia, probar el asistente como si fuera un cliente y publicar cuando tú lo confirmes.",
  "Escribir tus datos de pago sin poder leerlos nunca, si le das ese permiso.",
];
const CANNOT_DO = ["Conectar WhatsApp: hay que escanear el código QR con tu teléfono (en Canales).", "Poner la clave de IA del negocio (en Configuración → Inteligencia artificial)."];

/**
 * Integraciones → Agentes de IA (MCP): que Claude, Cursor, n8n u otro agente trabaje en tus negocios hablándole, con una clave y los
 * permisos que elijas. La dirección del servidor, cómo conectar cada agente y las claves de agente.
 */
export function AgentsPage() {
  const data = useIntegrationsData();
  const pathTo = useWorkspacePath();
  const business = useParams().slug ?? "";
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState<CreatedApiKey | null>(null);
  const [revokeError, setRevokeError] = useState<string | null>(null);
  const [client, setClient] = useState("claude-code");

  if (data.status === "loading") return <LoadingScreen label="Cargando los agentes de IA…" />;
  const overview = data.overview;
  const url = overview?.mcpUrl ?? null;
  const agentKeys = data.keys.filter(isAgentKey);
  const snippets = url ? mcpSnippets(url) : [];
  const shown = snippets.find((snippet) => snippet.id === client);

  return (
    <>
      <PageHeader
        eyebrow="Integraciones"
        title="Agentes de IA (MCP)"
        description="Que Claude, Cursor, n8n u otro agente de IA trabaje en tus negocios cuando se lo pides: por ejemplo, «móntame una panadería en Medellín con estos productos y precios». Solo con los permisos que le des."
        actions={
          <div className="page-header__side">
            <AgentBadge keys={data.keys} />
            <Link className="back-link" to={pathTo(INTEGRATIONS_ITEM.path)}>
              <Icon name="arrowLeft" size={16} /> Integraciones
            </Link>
          </div>
        }
      />
      {data.status === "error" && <Alert tone="danger" title={data.error ?? "No se pudo cargar."} />}
      {revokeError && <Alert tone="danger" title={revokeError} />}

      <div className="settings-stack">
        <Card icon="sparkles" tone="violet" title="Qué puede hacer">
          <div className="agents-scope">
            <IntegrationMark kind="mcp" size="lg" />
            <ul className="guide-list">
              {CAN_DO.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <p className="field__hint">No puede, a propósito: {CANNOT_DO.join(" ")}</p>
        </Card>

        <Card icon="shield" tone="emerald" title="1. Crea una clave para tu agente" description="Una por agente. Eliges qué puede hacer, a qué negocios entra y cuándo vence.">
          {agentKeys.length === 0 ? (
            <EmptyState title="Todavía no tienes claves de agente" description="Crea la primera para conectar tu agente." />
          ) : (
            <KeysTable
              keys={agentKeys}
              areas={overview?.areas ?? []}
              onRevoke={(key) => {
                setRevokeError(null);
                void data.revokeKey(key.id).then(setRevokeError);
              }}
            />
          )}
          <div>
            <Button onClick={() => setCreating(true)} disabled={!overview}>
              Crear clave para un agente
            </Button>
          </div>
        </Card>

        <Card icon="link" tone="indigo" title="2. Conéctalo" description="La dirección del servidor y lo que se pega en cada agente.">
          {url ? (
            <div className="form-stack">
              <CopyField label="Dirección del servidor MCP" value={url} />
              <Tabs
                label="Agente"
                value={client}
                onChange={setClient}
                tabs={[...snippets.map((snippet) => ({ value: snippet.id, label: snippet.label })), { value: "oauth", label: "Claude web y ChatGPT" }]}
              >
                {shown ? (
                  <div className="form-stack">
                    <p className="field__hint">{shown.hint} Cambia TU_CLAVE por tu clave.</p>
                    <CopyField label="Para pegar" value={shown.code} multiline />
                  </div>
                ) : (
                  <Alert tone="info" title="Próximamente">
                    Podrás conectar Claude en la web y en el escritorio, y ChatGPT, pegando solo la dirección e iniciando sesión, sin copiar una clave.
                  </Alert>
                )}
              </Tabs>
            </div>
          ) : (
            <Alert tone="info" title="El servidor MCP no está disponible en este servidor." />
          )}
        </Card>
      </div>

      {creating && overview && (
        <CreateKeyDialog
          purpose="agent"
          areas={overview.areas}
          business={business}
          create={data.createKey}
          onClose={() => setCreating(false)}
          onCreated={(key) => {
            setCreating(false);
            setCreated(key);
          }}
        />
      )}
      {created && <NewSecretDialog created={created} mcpUrl={url} onClose={() => setCreated(null)} />}
    </>
  );
}

function AgentBadge({ keys }: { keys: ApiKey[] }) {
  const state = agentConnection(keys);
  if (state.kind === "connected") {
    return (
      <Badge tone="success">
        <span className="live-dot live-dot--on" aria-hidden="true" />
        Conectado · usado {relativeTime(state.lastUsedAt)}
      </Badge>
    );
  }
  return state.kind === "ready" ? <Badge tone="neutral">Clave lista · todavía sin usar</Badge> : <Badge tone="neutral">Sin conectar</Badge>;
}
