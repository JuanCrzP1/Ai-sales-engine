import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { Button, LinkButton } from "../../components/ui/Button";
import { RadioGroup } from "../../components/ui/ChoiceGroup";
import { Alert } from "../../components/ui/Feedback";
import { Card, PageHeader } from "../../components/ui/Layout";
import { AI_ITEM } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useConfig } from "../../state/useConfig";
import { usePlayground, type ChatTurn, type ConfigSource } from "../../state/usePlayground";

const SOURCES = [
  { value: "draft" as ConfigSource, label: "Lo que estoy editando", hint: "Lo último guardado, aunque todavía no esté publicado." },
  { value: "published" as ConfigSource, label: "Lo publicado", hint: "Lo que hoy reciben tus clientes." },
];

/** Lo que la IA entendió de cada mensaje, en palabras del negocio. */
const INTENTS: Record<string, string> = {
  info: "Pide información",
  price: "Pregunta el precio",
  buy: "Quiere comprar",
  objection: "Tiene una objeción",
  greeting: "Saluda",
  support: "Pide ayuda",
};

const MAX_MESSAGE_CHARS = 1000;

/** Conversación de prueba con el asistente de este negocio: responde la IA real con su configuración y su clave. */
export function PlaygroundPage() {
  const playground = usePlayground();
  const { dirty } = useConfig();
  const pathTo = useWorkspacePath();
  const [message, setMessage] = useState("");
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView?.({ block: "end" });
  }, [playground.turns.length, playground.sending]);

  const submit = (event?: FormEvent) => {
    event?.preventDefault();
    const text = message.trim();
    if (!text || playground.sending) return;
    setMessage("");
    void playground.send(text);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  };

  return (
    <>
      <PageHeader
        eyebrow="Asistente"
        title="Probar asistente"
        description="Conversa con tu asistente como si fueras un cliente. Responde la IA real, con la configuración de este negocio y su clave de OpenRouter."
        actions={
          <Button variant="secondary" onClick={() => void playground.restart()} disabled={playground.turns.length === 0 || playground.sending}>
            Nueva conversación
          </Button>
        }
      />

      {playground.missingKey && (
        <Alert tone="warning" title="Este negocio todavía no tiene su clave de IA">
          <p>Agrégala para que su asistente pueda responder, aquí y con tus clientes.</p>
          <LinkButton to={pathTo(AI_ITEM.path)}>Agregar la clave</LinkButton>
        </Alert>
      )}
      {dirty && playground.source === "draft" && (
        <Alert tone="info" title="Tienes cambios sin guardar">
          <p>El asistente responde con lo último que guardaste. Guarda para probar tus cambios.</p>
        </Alert>
      )}

      <Card>
        <RadioGroup legend="¿Con qué versión responde?" name="version-de-prueba" options={SOURCES} value={playground.source} onChange={playground.setSource} />

        <div className="playground__transcript" role="log" aria-live="polite" aria-label="Conversación de prueba">
          {playground.turns.length === 0 && !playground.sending && (
            <p className="playground__empty">Escribe el primer mensaje como lo haría un cliente.</p>
          )}
          {playground.turns.map((turn) => (
            <Bubble key={turn.id} turn={turn} />
          ))}
          {playground.sending && <p className="playground__typing">El asistente está escribiendo…</p>}
          <div ref={end} />
        </div>

        {playground.error && <Alert tone="danger" title={playground.error} />}

        <form className="playground__composer" onSubmit={submit}>
          <label className="visually-hidden" htmlFor="playground-message">
            Mensaje de prueba
          </label>
          <textarea
            id="playground-message"
            className="playground__input"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Escribe como si fueras un cliente…"
            rows={2}
            maxLength={MAX_MESSAGE_CHARS}
            disabled={playground.sending}
          />
          <Button type="submit" disabled={playground.sending || !message.trim()}>
            Enviar
          </Button>
        </form>
        <p className="playground__note">
          Estas conversaciones no llegan a tus clientes ni se guardan.
          {playground.version !== null && ` Respondió con la versión ${playground.version}.`}
        </p>
      </Card>
    </>
  );
}

function Bubble({ turn }: { turn: ChatTurn }) {
  const customer = turn.from === "customer";
  return (
    <div className={`playground__bubble playground__bubble--${turn.from}`}>
      <span className="visually-hidden">{customer ? "Tú: " : "Asistente: "}</span>
      {turn.text}
      {!customer && (turn.intent || turn.aiAnswered === false) && (
        <span className="playground__meta">
          {turn.aiAnswered === false ? "Respondió sin la IA: revisa la clave o el modelo en Inteligencia artificial." : INTENTS[turn.intent ?? ""] ?? turn.intent}
        </span>
      )}
    </div>
  );
}
