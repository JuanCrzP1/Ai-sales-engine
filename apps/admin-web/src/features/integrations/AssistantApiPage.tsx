import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { Button, LinkButton } from "../../components/ui/Button";
import { ChatPreview } from "../../components/ui/ChatPreview";
import { CopyField } from "../../components/ui/CopyButton";
import { Alert, Badge } from "../../components/ui/Feedback";
import { TextAreaField } from "../../components/ui/FormFields";
import { Icon } from "../../components/ui/Icon";
import { Card, PageHeader } from "../../components/ui/Layout";
import { relativeTime } from "../../domain/inbox/format";
import { connectionState, SCOPE_ASSISTANT_CHAT, type ApiKey, type CreatedApiKey } from "../../domain/integrations/types";
import { LoadingScreen } from "../../layout/StatusScreen";
import { API_KEYS_ITEM, INTEGRATIONS_ITEM } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useAssistantApiTry } from "../../state/useAssistantApiTry";
import { useIntegrationsData } from "../../state/useIntegrationsData";
import { CreateKeyDialog, NewSecretDialog } from "./KeyDialogs";
import { PlatformGuides } from "./PlatformGuides";

const DOCS_URL = "https://github.com/JuanCrzP1/Ai-sales-engine/blob/main/docs/api.md";

const REQUEST_FIELDS: [string, string][] = [
  ["contact.id", "Quién escribe: su teléfono o su id. El asistente recuerda a cada cliente por este dato."],
  ["contact.name", "Su nombre (opcional), para verlo en Conversaciones."],
  ["message", "Lo que escribió el cliente."],
];

const RESPONSE_FIELDS: [string, string][] = [
  ["reply", "Lo que hay que enviarle al cliente (vacío si lo atiende tu equipo)."],
  ["handoff", "true si el chat necesita a una persona: pásalo a tu equipo."],
  ["parts", "Lo mismo que reply en mensajes separados, por si prefieres enviarlos uno por uno."],
  ["attended_by", "Quién atiende ahora: «assistant» o «team»."],
  ["fallback", "true si respondió con tu mensaje de respaldo porque la IA no pudo."],
  ["intent / stage", "Lo que quiere el cliente y en qué etapa va, por si tu plataforma los usa."],
];

/** Integraciones → API del asistente: cualquier plataforma le manda el mensaje de un cliente y recibe la respuesta para enviársela. */
export function AssistantApiPage() {
  const data = useIntegrationsData();
  const tryout = useAssistantApiTry();
  const pathTo = useWorkspacePath();
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState<CreatedApiKey | null>(null);
  const [message, setMessage] = useState("Hola, ¿qué precios tienen?");

  if (data.status === "loading") return <LoadingScreen label="Cargando la API del asistente…" />;
  const overview = data.overview;
  const url = overview?.assistantApiUrl ?? null;
  const chatKeys = data.keys.filter((key) => key.active && key.scopes.includes(SCOPE_ASSISTANT_CHAT));

  const tryIt = async (event: FormEvent) => {
    event.preventDefault();
    await tryout.send(message);
  };
  const { trying, result, error: tryError } = tryout;

  return (
    <>
      <PageHeader
        eyebrow="Integraciones"
        title="API del asistente"
        description="Conecta tu asistente a cualquier plataforma: ella le manda el mensaje del cliente y le envía la respuesta. Es el mismo asistente de WhatsApp, con lo que tienes publicado."
        actions={
          <div className="page-header__side">
            <ConnectionBadge keys={data.keys} />
            <Link className="back-link" to={pathTo(INTEGRATIONS_ITEM.path)}>
              <Icon name="arrowLeft" size={16} /> Integraciones
            </Link>
          </div>
        }
      />
      {data.status === "error" && <Alert tone="danger" title={data.error ?? "No se pudo cargar."} />}

      <div className="settings-stack">
        <Card icon="route" tone="indigo" title="Cómo funciona">
          <ol className="api-flow" aria-label="El recorrido de cada mensaje">
            <li className="api-flow__step">
              <Icon name="plug" size={18} />
              <span>
                <strong>Tu plataforma</strong> recibe el mensaje del cliente y se lo manda al asistente
              </span>
            </li>
            <li className="api-flow__step api-flow__step--accent">
              <Icon name="robot" size={18} />
              <span>
                <strong>Tu asistente</strong> responde con tu información y recuerda a cada cliente
              </span>
            </li>
            <li className="api-flow__step">
              <Icon name="send" size={18} />
              <span>
                <strong>Tu plataforma</strong> le envía la respuesta al cliente
              </span>
            </li>
          </ol>
          <p className="field__hint">
            Los chats aparecen en Conversaciones con el canal «API». Si el cliente pide una persona, la respuesta lo dice y tu equipo recibe el aviso.
          </p>
        </Card>

        <Card icon="shield" tone="emerald" title="1. Tus datos de conexión" description="Los mismos para cualquier plataforma.">
          <div className="form-stack">
            {url ? (
              <CopyField label="Dirección (POST)" value={url} />
            ) : (
              <Alert tone="info" title="La dirección aparece cuando el motor está publicado en internet.">
                En la nube ya la tiene. En este equipo, arráncalo con ./run_local.sh, que la toma de ngrok.
              </Alert>
            )}
            <KeySummary keys={chatKeys} keysPath={pathTo(API_KEYS_ITEM.path)} onCreate={() => setCreating(true)} />
          </div>
        </Card>

        <Card icon="layers" tone="violet" title="2. Conéctala a tu plataforma" description="Elige la tuya y sigue los pasos.">
          <PlatformGuides url={url} docsUrl={DOCS_URL} />
        </Card>

        <Card icon="file" tone="slate" title="3. Qué envías y qué recibes">
          <div className="api-fields">
            <FieldTable title="Envías" fields={REQUEST_FIELDS} />
            <FieldTable title="Recibes" fields={RESPONSE_FIELDS} />
          </div>
        </Card>

        <Card icon="flask" tone="sky" title="4. Pruébala" description="Así respondería la API con lo que tienes publicado. Gasta tu clave de IA, como «Probar asistente», y queda como prueba.">
          <form className="form-stack" onSubmit={tryIt} noValidate>
            <TextAreaField label="Mensaje del cliente" value={message} onChange={setMessage} rows={2} />
            <div>
              <Button type="submit" disabled={trying || !message.trim()}>
                {trying ? "Enviando…" : "Enviar"}
              </Button>
            </div>
          </form>
          {tryError && <Alert tone="danger" title={tryError} />}
          {result && (
            <div className="api-result">
              <ChatPreview lines={[{ from: "customer", text: message }, ...result.parts.map((text) => ({ from: "assistant" as const, text }))]} />
              <div className="api-result__flags">
                {result.handoff && <Badge tone="warning">Pasa a una persona</Badge>}
                {result.fallback && <Badge tone="warning">Respondió con tu mensaje de respaldo</Badge>}
                {result.intent && <Badge tone="neutral">Intención: {result.intent}</Badge>}
              </div>
              <CopyField label="Respuesta JSON" value={JSON.stringify(result, null, 2)} multiline />
            </div>
          )}
        </Card>

        <p className="field__hint api-docs-link">
          <a href={DOCS_URL} target="_blank" rel="noreferrer">
            Ver la documentación completa de la API →
          </a>
        </p>
      </div>

      {creating && overview && (
        <CreateKeyDialog
          scopes={overview.scopes}
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

/** Si una plataforma ya está llamando: el último uso de las claves para conversar. */
function ConnectionBadge({ keys }: { keys: ApiKey[] }) {
  const state = connectionState(keys);
  if (state.kind === "connected") {
    return (
      <Badge tone="success">
        <span className="live-dot live-dot--on" aria-hidden="true" />
        Conectada · usada {relativeTime(state.lastUsedAt)}
      </Badge>
    );
  }
  return state.kind === "ready" ? <Badge tone="neutral">Lista · todavía sin usar</Badge> : <Badge tone="neutral">Sin clave</Badge>;
}

function KeySummary({ keys, keysPath, onCreate }: { keys: ApiKey[]; keysPath: string; onCreate: () => void }) {
  return (
    <div className="key-summary">
      <span className="field__label">Clave</span>
      {keys.length > 0 ? (
        <ul className="key-summary__list">
          {keys.map((key) => (
            <li key={key.id}>
              <code>{key.prefix}…</code> <span>{key.name}</span>
              <span className="key-summary__used">{key.lastUsedAt ? `usada ${relativeTime(key.lastUsedAt)}` : "sin usar"}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="field__hint">Todavía no tienes una clave. Crea una por cada plataforma que vayas a conectar.</p>
      )}
      <p className="field__hint">
        La clave completa solo se ve al crearla. En tu plataforma va en el encabezado <code>Authorization: Bearer</code> + la clave.
      </p>
      <div className="key-summary__actions">
        <Button onClick={onCreate}>{keys.length > 0 ? "Crear otra clave" : "Crear clave"}</Button>
        {keys.length > 0 && (
          <LinkButton variant="secondary" to={keysPath}>
            Ver claves
          </LinkButton>
        )}
      </div>
    </div>
  );
}

function FieldTable({ title, fields }: { title: string; fields: [string, string][] }) {
  return (
    <div>
      <h3 className="api-fields__title">{title}</h3>
      <dl className="field-list">
        {fields.map(([name, meaning]) => (
          <div key={name} className="field-list__row">
            <dt>
              <code>{name}</code>
            </dt>
            <dd>{meaning}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
