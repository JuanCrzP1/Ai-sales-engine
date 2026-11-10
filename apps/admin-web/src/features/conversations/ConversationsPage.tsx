import { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { Alert, EmptyState } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { PageHeader } from "../../components/ui/Layout";
import { contactLabel, fullDate, initials, messageTime, relativeTime } from "../../domain/inbox/format";
import { CHANNEL_LABELS, CHANNELS, type Channel, type ChatMessage, type ConversationSummary, type ConversationThread } from "../../domain/inbox/types";
import { useConversations } from "../../state/useConversations";

const AUTHOR_LABELS: Record<ChatMessage["author"], string> = { customer: "Cliente", assistant: "Asistente IA", agent: "Tú" };

/** Bandeja de conversaciones: los chats de tus clientes con su historial, y de qué negocio y canal viene cada uno. */
export function ConversationsPage() {
  const { slug = "" } = useParams();
  // Desde un aviso se llega con `?c=` y la conversación se abre directo.
  const [params] = useSearchParams();
  const { filter, setFilter, list, selectedId, select, thread, reload, resolveHandoff } = useConversations({ business: slug }, params.get("c"));
  const allBusinesses = filter.business === undefined;

  return (
    <>
      <PageHeader
        eyebrow="Atención"
        title="Conversaciones"
        description="Los chats de tus clientes, de todos tus canales, con su historial completo."
        actions={
          <Button variant="secondary" onClick={reload}>
            Actualizar
          </Button>
        }
      />

      <div className={`inbox${selectedId ? " inbox--reading" : ""}`}>
        <section className="inbox__list" aria-label="Lista de conversaciones">
          <div className="inbox__filters">
            <div className="segmented" role="group" aria-label="Negocios">
              <button type="button" className="segmented__option" aria-pressed={!allBusinesses} onClick={() => setFilter({ ...filter, business: slug })}>
                Este negocio
              </button>
              <button type="button" className="segmented__option" aria-pressed={allBusinesses} onClick={() => setFilter({ channel: filter.channel })}>
                Todos mis negocios
              </button>
            </div>
            <button
              type="button"
              className="filter-chip"
              aria-pressed={Boolean(filter.waitingHuman)}
              onClick={() => setFilter({ ...filter, waitingHuman: filter.waitingHuman ? undefined : true })}
            >
              <Icon name="headset" size={14} /> Esperan a una persona
            </button>
            <label className="inbox__channel">
              <span className="visually-hidden">Canal</span>
              <select
                className="input"
                value={filter.channel ?? ""}
                onChange={(event) => setFilter({ ...filter, channel: (event.target.value || undefined) as Channel | undefined })}
              >
                <option value="">Todos los canales</option>
                {CHANNELS.map((channel) => (
                  <option key={channel} value={channel}>
                    {CHANNEL_LABELS[channel]}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {list.status === "loading" && (
            <p className="inbox__status" role="status">
              Cargando conversaciones…
            </p>
          )}
          {list.status === "error" && (
            <Alert tone="danger" title="No se pudieron cargar las conversaciones">
              <p>{list.message}</p>
              <Button size="small" variant="secondary" onClick={reload}>
                Reintentar
              </Button>
            </Alert>
          )}
          {list.status === "ready" && list.data.length === 0 && (
            <EmptyState
              title="Aún no hay conversaciones"
              description="Cuando conectes un canal, aquí verás cada chat con su historial. Las pruebas que hagas en «Probar asistente» también aparecen, marcadas como Prueba."
            />
          )}
          {list.status === "ready" && list.data.length > 0 && (
            <ul className="inbox__items">
              {list.data.map((conversation) => (
                <li key={conversation.id}>
                  <ConversationItem conversation={conversation} selected={conversation.id === selectedId} onSelect={() => select(conversation.id)} />
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="inbox__thread" aria-label="Conversación abierta">
          {!selectedId && (
            <div className="inbox__placeholder">
              <span className="inbox__placeholder-icon">
                <Icon name="inbox" size={28} />
              </span>
              <p>Elige una conversación para leerla.</p>
            </div>
          )}
          {selectedId && thread?.status === "loading" && (
            <p className="inbox__status" role="status">
              Abriendo la conversación…
            </p>
          )}
          {selectedId && thread?.status === "error" && <Alert tone="danger" title={thread.message} />}
          {selectedId && thread?.status === "ready" && <ThreadView thread={thread.data} onBack={() => select(null)} onResolve={resolveHandoff} />}
        </section>
      </div>
    </>
  );
}

function ConversationItem({ conversation, selected, onSelect }: { conversation: ConversationSummary; selected: boolean; onSelect: () => void }) {
  const name = contactLabel(conversation);
  return (
    <button type="button" className={`inbox-item${selected ? " inbox-item--active" : ""}`} aria-current={selected ? "true" : undefined} onClick={onSelect}>
      <span className={`inbox-item__avatar channel-color--${conversation.channel}`} aria-hidden="true">
        {initials(name)}
      </span>
      <span className="inbox-item__body">
        <span className="inbox-item__top">
          <span className="inbox-item__name">{name}</span>
          <time className="inbox-item__time" dateTime={conversation.lastMessageAt}>
            {relativeTime(conversation.lastMessageAt)}
          </time>
        </span>
        {conversation.lastMessagePreview && <span className="inbox-item__preview">{conversation.lastMessagePreview}</span>}
        <span className="inbox-item__tags">
          {conversation.needsHuman && <span className="handoff-badge">Pide una persona</span>}
          <span className={`channel-badge channel-color--${conversation.channel}`}>{CHANNEL_LABELS[conversation.channel]}</span>
          <span className="business-badge" title="Negocio">
            {conversation.business.name}
          </span>
        </span>
      </span>
    </button>
  );
}

function ThreadView({ thread, onBack, onResolve }: { thread: ConversationThread; onBack: () => void; onResolve: (id: string) => Promise<void> }) {
  const { conversation, messages } = thread;
  const end = useRef<HTMLDivElement>(null);
  const name = contactLabel(conversation);
  const [resolving, setResolving] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  const resolve = async () => {
    setResolving(true);
    setProblem(null);
    try {
      await onResolve(conversation.id);
    } catch {
      setProblem("No se pudo marcar como atendida. Vuelve a intentarlo.");
    } finally {
      setResolving(false);
    }
  };

  useEffect(() => {
    end.current?.scrollIntoView?.({ block: "end" });
  }, [conversation.id]);

  return (
    <div className="thread">
      <header className="thread__header">
        <button type="button" className="thread__back" onClick={onBack}>
          ← Conversaciones
        </button>
        <span className={`inbox-item__avatar channel-color--${conversation.channel}`} aria-hidden="true">
          {initials(name)}
        </span>
        <div className="thread__who">
          <h2 className="thread__name">{name}</h2>
          <p className="thread__meta">
            {CHANNEL_LABELS[conversation.channel]} · {conversation.business.name} · desde el {fullDate(conversation.startedAt)}
          </p>
        </div>
        <span className="thread__count">{conversation.messageCount} mensajes</span>
      </header>

      {conversation.needsHuman && (
        <div className="handoff-banner" role="status">
          <span className="handoff-banner__icon" aria-hidden="true">
            <Icon name="headset" size={18} />
          </span>
          <div className="handoff-banner__text">
            <strong>{conversation.channel === "prueba" ? "Prueba: el cliente pidió hablar con una persona" : "Este cliente pidió hablar con una persona"}</strong>
            <span>
              {conversation.handoffRequestedAt ? `Lo pidió ${relativeTime(conversation.handoffRequestedAt)}. ` : ""}
              {conversation.channel === "prueba"
                ? "Así te avisaremos cuando un cliente real lo pida."
                : `Atiéndelo por ${CHANNEL_LABELS[conversation.channel]} y márcalo cuando esté listo.`}
            </span>
            {problem && <span className="handoff-banner__problem">{problem}</span>}
          </div>
          <Button size="small" onClick={() => void resolve()} disabled={resolving}>
            {resolving ? "Guardando…" : "Ya lo atendí"}
          </Button>
        </div>
      )}

      <div className="thread__messages" role="log" aria-label={`Mensajes con ${name}`}>
        {messages.map((message) => (
          <div key={message.id} className={`chat-bubble chat-bubble--${message.author}`}>
            <span className="visually-hidden">{AUTHOR_LABELS[message.author]}: </span>
            <p className="chat-bubble__text">{message.body}</p>
            <span className="chat-bubble__meta">
              {message.author === "assistant" && (
                <>
                  <Icon name="robot" size={12} /> IA ·{" "}
                </>
              )}
              <time dateTime={message.createdAt}>{messageTime(message.createdAt)}</time>
            </span>
          </div>
        ))}
        <div ref={end} />
      </div>

      <footer className="thread__footer">
        {conversation.channel === "prueba"
          ? "Conversación de prueba hecha desde «Probar asistente». No llegó a ningún cliente."
          : "Los datos de pago se muestran ocultos. Pronto podrás responder tú desde aquí y pausar la IA."}
      </footer>
    </div>
  );
}
