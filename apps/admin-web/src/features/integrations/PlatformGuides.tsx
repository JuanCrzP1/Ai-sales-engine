import { useState, type ReactNode } from "react";
import { CopyField } from "../../components/ui/CopyButton";
import { Alert, Badge } from "../../components/ui/Feedback";
import { SegmentedControl } from "../../components/ui/SegmentedControl";
import { Tabs } from "../../components/ui/Tabs";
import { AUTHORIZATION_HEADER, CODE_LANGUAGES, codeExample, EXAMPLE_REQUEST_BODY, LEONA, type CodeLanguage } from "../../domain/integrations/types";

type Platform = "leona" | "other" | "developers";

const URL_PLACEHOLDER = "https://…/api/v1/assistant/messages";

/**
 * «Conéctala a tu plataforma»: una guía por plataforma. Solo dice «Probado» la que se probó con un flujo real; el resto es la guía
 * general, que sirve para cualquier sistema capaz de hacer una petición HTTP.
 */
export function PlatformGuides({ url, docsUrl }: { url: string | null; docsUrl: string }) {
  const [platform, setPlatform] = useState<Platform>("leona");
  const address = url ?? URL_PLACEHOLDER;
  return (
    <Tabs
      label="Plataforma"
      value={platform}
      onChange={(value) => setPlatform(value as Platform)}
      tabs={[
        {
          value: "leona",
          label: (
            <>
              Leona <Badge tone="success">Probado</Badge>
            </>
          ),
        },
        { value: "other", label: "Otra plataforma" },
        { value: "developers", label: "Desarrolladores" },
      ]}
    >
      {platform === "leona" && <LeonaGuide url={address} />}
      {platform === "other" && <OtherPlatformGuide url={address} />}
      {platform === "developers" && <DevelopersGuide url={address} docsUrl={docsUrl} />}
    </Tabs>
  );
}

function Step({ number, title, children }: { number: number; title: string; children: ReactNode }) {
  return (
    <li className="guide-step">
      <span className="guide-step__number" aria-hidden="true">
        {number}
      </span>
      <div className="guide-step__body">
        <h3 className="guide-step__title">{title}</h3>
        {children}
      </div>
    </li>
  );
}

function LeonaFlowSketch() {
  return (
    <figure className="flow-sketch" aria-label="Así queda el flujo en Leona">
      <ol className="flow-sketch__line">
        <li className="flow-sketch__node">Inicio</li>
        <li className="flow-sketch__node">Esperar respuesta</li>
        <li className="flow-sketch__node flow-sketch__node--key">Integración HTTP</li>
        <li className="flow-sketch__node">¿Pidió una persona?</li>
      </ol>
      <div className="flow-sketch__branches">
        <p>
          <strong>Sí:</strong> Mensaje con la respuesta → chat en «Aguardando» para tu equipo
        </p>
        <p>
          <strong>No:</strong> Esperar respuesta (envía la respuesta) → vuelve a la Integración HTTP ↺
        </p>
      </div>
    </figure>
  );
}

function LeonaGuide({ url }: { url: string }) {
  return (
    <div className="guide">
      <p className="field__hint">
        Un flujo de Leona que conversa: cada mensaje del cliente va al asistente y su respuesta vuelve al cliente, hasta que pida una persona.
      </p>
      <LeonaFlowSketch />
      <ol className="guide-steps">
        <Step number={1} title="Bloque «Esperar respuesta»">
          <p>
            Al inicio, con tu saludo. En <strong>Guardar respuesta en</strong>, un campo personalizado llamado <code>{LEONA.messageField}</code>.
          </p>
        </Step>
        <Step number={2} title="Bloque «Integración HTTP»">
          <p>
            Método <strong>POST</strong>. En <strong>Encabezados</strong>, <code>Authorization</code> con <code>Bearer</code> y tu clave, y{" "}
            <code>Content-Type</code> con <code>application/json</code>.
          </p>
          <div className="form-stack">
            <CopyField label="Dirección" value={url} />
            <CopyField label="Cuerpo" value={LEONA.requestBody} multiline />
          </div>
          <p className="field__hint">
            <code>{"{phone_number}"}</code> y <code>{"{full_name}"}</code> son variables de Leona: así cada cliente tiene su propio chat y el asistente lo
            recuerda.
          </p>
          <p>En <strong>Campos de respuesta</strong>:</p>
          <dl className="field-list">
            <div className="field-list__row">
              <dt>
                <code>body.reply</code>
              </dt>
              <dd>
                guárdalo en <code>{LEONA.replyField}</code>: lo que hay que enviarle al cliente.
              </dd>
            </div>
            <div className="field-list__row">
              <dt>
                <code>body.handoff</code>
              </dt>
              <dd>
                guárdalo en <code>{LEONA.handoffField}</code>: dice si el cliente necesita a una persona.
              </dd>
            </div>
          </dl>
        </Step>
        <Step number={3} title="Bloque «Condicional»: ¿pidió una persona?">
          <p>
            Si <code>{LEONA.handoffField}</code> contiene <code>true</code>:
          </p>
          <ul className="guide-list">
            <li>
              <strong>Sí:</strong> un <strong>Mensaje</strong> con <code>{`{${LEONA.replyField}}`}</code> y un <strong>Controlador de chat</strong> en «Aguardando»
              para tu equipo.
            </li>
            <li>
              <strong>No:</strong> otro <strong>Esperar respuesta</strong> que envíe <code>{`{${LEONA.replyField}}`}</code>, guarde en{" "}
              <code>{LEONA.messageField}</code> y vuelva a la Integración HTTP. Así la conversación sigue.
            </li>
            <li>
              En la salida de <strong>fallo</strong> de la Integración HTTP, un mensaje de respaldo («una persona te escribirá pronto»).
            </li>
          </ul>
        </Step>
      </ol>
      <Alert tone="info" title="Pruébalo disparando el flujo a tu número.">
        El botón «Probar petición» de Leona manda las variables sin cambiar, y la API las rechaza para no mezclar clientes.
      </Alert>
    </div>
  );
}

function OtherPlatformGuide({ url }: { url: string }) {
  return (
    <div className="guide">
      <p className="field__hint">
        Sirve cualquier plataforma que pueda hacer una petición HTTP. Según la plataforma se llama «Webhook», «HTTP Request», «Integración» o
        «Llamar a una API».
      </p>
      <ol className="guide-steps">
        <Step number={1} title="Cada vez que el cliente escriba, manda una petición">
          <p>
            Método <strong>POST</strong> a esta dirección, con los encabezados <code>Authorization: Bearer</code> + tu clave y{" "}
            <code>Content-Type: application/json</code>.
          </p>
          <CopyField label="Dirección" value={url} />
        </Step>
        <Step number={2} title="Con este cuerpo">
          <CopyField label="Cuerpo (con datos de ejemplo)" value={EXAMPLE_REQUEST_BODY} multiline />
          <p>Cambia cada dato de ejemplo por la variable de tu plataforma:</p>
          <dl className="field-list">
            <div className="field-list__row">
              <dt>
                <code>contact.id</code>
              </dt>
              <dd>El teléfono o el id del cliente. Siempre el mismo para la misma persona: así el asistente la recuerda.</dd>
            </div>
            <div className="field-list__row">
              <dt>
                <code>contact.name</code>
              </dt>
              <dd>Su nombre (opcional), para verlo en Conversaciones.</dd>
            </div>
            <div className="field-list__row">
              <dt>
                <code>message</code>
              </dt>
              <dd>Lo que escribió el cliente.</dd>
            </div>
          </dl>
        </Step>
        <Step number={3} title="Envíale la respuesta al cliente">
          <p>
            Envíale <code>reply</code>. Si <code>handoff</code> es <code>true</code>, pasa el chat a tu equipo en tu plataforma.
          </p>
        </Step>
        <Step number={4} title="Espera su próximo mensaje y repite">
          <p>Cada mensaje es una petición nueva. El asistente recuerda lo que ya hablaron.</p>
        </Step>
      </ol>
      <Alert tone="warning" title="Usa las variables de tu plataforma con su nombre exacto.">
        Si una llega sin cambiar (por ejemplo, «{"{nombre}"}»), la API la rechaza y te dice cuál fue, para no mezclar a tus clientes en un solo chat.
      </Alert>
    </div>
  );
}

function DevelopersGuide({ url, docsUrl }: { url: string; docsUrl: string }) {
  const [language, setLanguage] = useState<CodeLanguage>("curl");
  return (
    <div className="guide">
      <p className="field__hint">Para quien programa su propia integración: un servidor, una app o una página con su propio backend.</p>
      <SegmentedControl label="Lenguaje" value={language} options={CODE_LANGUAGES} onChange={(value) => setLanguage(value as CodeLanguage)} />
      <CopyField label="Ejemplo" value={codeExample(language, url)} multiline />
      <CopyField label="Encabezado de autorización" value={AUTHORIZATION_HEADER} />
      <ul className="guide-list">
        <li>
          Guarda la clave en una variable de entorno (<code>AI_SALES_ENGINE_KEY</code>). Nunca en el código de una página web: cualquiera podría verla.
        </li>
        <li>
          Si tu sistema puede repetir un pedido, manda <code>Idempotency-Key</code> con un id por mensaje: durante 24 horas devuelve la misma respuesta
          sin gastar la IA otra vez.
        </li>
        <li>
          Los errores siempre llegan como <code>{'{"code", "message", "issues"}'}</code>. Con <code>429</code>, espera los segundos de{" "}
          <code>Retry-After</code>.
        </li>
      </ul>
      <p className="field__hint">
        <a href={docsUrl} target="_blank" rel="noreferrer">
          Referencia completa de la API
        </a>{" "}
        (campos, errores y límites).
      </p>
    </div>
  );
}
