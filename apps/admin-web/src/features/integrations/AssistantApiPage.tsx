import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { ChatPreview } from "../../components/ui/ChatPreview";
import { CopyField } from "../../components/ui/CopyButton";
import { Alert, Badge } from "../../components/ui/Feedback";
import { TextAreaField } from "../../components/ui/FormFields";
import { Icon } from "../../components/ui/Icon";
import { Card, PageHeader } from "../../components/ui/Layout";
import { curlExample, LEONA_REQUEST_BODY, type CreatedApiKey } from "../../domain/integrations/types";
import { LoadingScreen } from "../../layout/StatusScreen";
import { API_KEYS_ITEM, INTEGRATIONS_ITEM } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useAssistantApiTry } from "../../state/useAssistantApiTry";
import { useIntegrationsData } from "../../state/useIntegrationsData";
import { CreateKeyDialog, NewSecretDialog } from "./KeyDialogs";

const DOCS_URL = "https://github.com/JuanCrzP1/Ai-sales-engine/blob/main/docs/api.md";

const RESPONSE_FIELDS: [string, string][] = [
  ["reply", "Lo que hay que enviarle al cliente (vacío si lo atiende tu equipo)."],
  ["parts", "Lo mismo en mensajes separados, por si prefieres enviarlos uno por uno."],
  ["handoff", "true si el chat necesita a una persona: pásalo a tu equipo en la otra plataforma."],
  ["attended_by", "«assistant» o «team»: quién atiende ahora el chat."],
  ["intent", "Lo que quiere el cliente: info, pain, objection o buy."],
  ["stage", "La etapa del cliente: new, interested, ready, payment o customer."],
  ["fallback", "true si respondió con tu mensaje de respaldo porque la IA no pudo."],
];

/** Integraciones → API del asistente: crear la clave, la dirección, conectarla a Leona y probarla. */
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
        description="Otra plataforma le manda a tu asistente el mensaje de un cliente y recibe la respuesta para enviársela. Es el mismo asistente de WhatsApp: tu configuración publicada, la memoria de cada cliente y el paso a una persona."
        actions={
          <Link className="back-link" to={pathTo(INTEGRATIONS_ITEM.path)}>
            <Icon name="arrowLeft" size={16} /> Integraciones
          </Link>
        }
      />
      {data.status === "error" && <Alert tone="danger" title={data.error ?? "No se pudo cargar."} />}

      <div className="settings-stack">
        <Card icon="shield" tone="emerald" title="1. Tu clave" description="La plataforma la manda en cada mensaje para demostrar que es tuya.">
          {(overview?.chatKeys ?? 0) > 0 ? (
            <p className="field__hint">
              Tienes {overview!.chatKeys === 1 ? "1 clave activa" : `${overview!.chatKeys} claves activas`} para conversar con el asistente. Puedes{" "}
              <Link to={pathTo(API_KEYS_ITEM.path)}>verlas y revocarlas</Link>, o crear otra para cada plataforma.
            </p>
          ) : (
            <p className="field__hint">Todavía no tienes una clave. Crea una para cada plataforma que vayas a conectar (por ejemplo, «Leona»).</p>
          )}
          <div>
            <Button onClick={() => setCreating(true)}>{(overview?.chatKeys ?? 0) > 0 ? "Crear otra clave" : "Crear clave"}</Button>
          </div>
        </Card>

        <Card icon="link" tone="indigo" title="2. La dirección" description="Adonde la plataforma manda cada mensaje.">
          {url ? (
            <div className="form-stack">
              <CopyField label="Dirección (POST)" value={url} />
              <CopyField label="Encabezado de autorización" value="Authorization: Bearer TU_CLAVE" />
              <CopyField label="Ejemplo desde la terminal" value={curlExample(url)} multiline />
            </div>
          ) : (
            <Alert tone="info" title="La dirección aparece cuando el motor está publicado en internet.">
              En la nube ya la tiene. En este equipo, arráncalo con ./run_local.sh, que la toma de ngrok.
            </Alert>
          )}
        </Card>

        <Card icon="layers" tone="violet" title="3. Conéctala a Leona" description="Con un bloque «Integración HTTP» dentro de tu flujo.">
          <ol className="steps-list">
            <li>
              En tu flujo de Leona, agrega un bloque <strong>Integración HTTP</strong> con el método <strong>POST</strong> y la dirección del paso 2.
            </li>
            <li>
              En <strong>Encabezados</strong>, agrega <code>Authorization</code> con el valor <code>Bearer</code> y tu clave, y <code>Content-Type</code> con{" "}
              <code>application/json</code>.
            </li>
            <li>En <strong>Cuerpo</strong>, pega esto (Leona cambia cada variable por los datos del cliente):</li>
          </ol>
          <CopyField label="Cuerpo de la petición" value={LEONA_REQUEST_BODY} multiline />
          <ol className="steps-list" start={4}>
            <li>
              En <strong>Campos de respuesta</strong>, guarda <code>body.reply</code> en un campo del cliente (por ejemplo, «respuesta_ia») y{" "}
              <code>body.handoff</code> en otro.
            </li>
            <li>
              En la salida de éxito, un bloque <strong>Mensaje</strong> que envíe <code>{"{customer.respuesta_ia}"}</code>. Si <code>handoff</code> es{" "}
              <code>true</code>, pasa el chat a tu equipo dentro de Leona.
            </li>
          </ol>
          <p className="field__hint">
            Los chats que lleguen así aparecen en Conversaciones con el canal «API», y cuentan en Clientes y Reportes.{" "}
            <a href={DOCS_URL} target="_blank" rel="noreferrer">
              Referencia completa de la API
            </a>
            .
          </p>
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

        <Card icon="file" tone="slate" title="Qué responde" description="Los campos de la respuesta, para usarlos en tu plataforma.">
          <dl className="field-list">
            {RESPONSE_FIELDS.map(([name, meaning]) => (
              <div key={name} className="field-list__row">
                <dt>
                  <code>{name}</code>
                </dt>
                <dd>{meaning}</dd>
              </div>
            ))}
          </dl>
        </Card>
      </div>

      {creating && overview && (
        <CreateKeyDialog
          scopes={overview.scopes}
          defaultName="Leona"
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
