import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { Alert, EmptyState } from "../../components/ui/Feedback";
import { Icon, type IconName } from "../../components/ui/Icon";
import { contactLabel, fullDate, messageTime, relativeTime } from "../../domain/inbox/format";
import { DELIVERY_LABELS, fileSize } from "../../domain/inbox/live";
import { CHANNEL_LABELS, CHANNELS, HANDOFF_LABELS, type Channel, type ChatMessage, type ConversationSummary, type ConversationThread } from "../../domain/inbox/types";
import { ContactAvatar } from "../../layout/ContactAvatar";
import { DeleteChatDialog } from "../../layout/DeleteChatDialog";
import { persistenceErrorMessage } from "../../state/directoryContext";
import { useConversations, useMediaUrl } from "../../state/useConversations";

const AUTHOR_LABELS: Record<ChatMessage["author"], string> = { customer: "Cliente", assistant: "Asistente IA", agent: "Equipo" };
const MAX_REPLY = 4000;

/** Bandeja de conversaciones en vivo: los chats de tus clientes, quién los atiende y la respuesta del equipo, sin recargar. */
export function ConversationsPage() {
  const { slug = "" } = useParams();
  // Desde un aviso se llega con `?c=` y la conversación se abre directo.
  const [params] = useSearchParams();
  const { filter, setFilter, list, selectedId, select, thread, reload, resolveHandoff, setAssistant, reply, forget, removeTestChats } = useConversations(
    { business: slug },
    params.get("c"),
  );
  const allBusinesses = filter.business === undefined;
  // Las pruebas de «Probar asistente» de este negocio se acumulan: se pueden borrar de una vez.
  const testChats = list.status === "ready" ? list.data.filter((item) => item.channel === "prueba" && item.business.slug === slug).length : 0;
  const [cleaning, setCleaning] = useState<string | null>(null);

  // Como WhatsApp Web: una barra de título compacta y la bandeja ocupando todo el alto y el ancho disponibles.
  return (
    <div className="inbox-page">
      <div className={`inbox${selectedId ? " inbox--reading" : ""}`}>
        <section className="inbox__list" aria-label="Lista de conversaciones">
          {/* Como «Chats» en WhatsApp Web: el título va en la cabecera de la lista, sin una barra que le quite alto al chat. */}
          <header className="inbox__list-head">
            <h1 className="inbox-page__title">Conversaciones</h1>
            <span className="live-indicator" role="status">
              <span className="live-indicator__dot" aria-hidden="true" /> En vivo
            </span>
          </header>
          <div className="inbox__filters">
            <div className="segmented" role="group" aria-label="Negocios">
              <button type="button" className="segmented__option" aria-pressed={!allBusinesses} onClick={() => setFilter({ ...filter, business: slug })}>
                Este negocio
              </button>
              <button type="button" className="segmented__option" aria-pressed={allBusinesses} onClick={() => setFilter({ channel: filter.channel })}>
                Todos mis negocios
              </button>
            </div>
            <div className="inbox__filter-row">
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
            {testChats > 0 && (
              <div className="inbox__cleanup">
                <span>
                  {testChats === 1 ? "1 chat de prueba" : `${testChats} chats de prueba`} de «Probar asistente»
                </span>
                <ConfirmButton
                  variant="ghost"
                  confirmLabel={testChats === 1 ? "Sí, borrarlo" : "Sí, borrarlos"}
                  onConfirm={() =>
                    void removeTestChats(slug).then(
                      () => setCleaning(null),
                      () => setCleaning("No se pudieron borrar las pruebas. Vuelve a intentarlo."),
                    )
                  }
                >
                  <Icon name="trash" size={14} /> Borrar pruebas
                </ConfirmButton>
              </div>
            )}
            {cleaning && <p className="field__error" role="alert">{cleaning}</p>}
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
                  <ConversationItem conversation={conversation} showBusiness={allBusinesses} selected={conversation.id === selectedId} onSelect={() => select(conversation.id)} />
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
          {selectedId && thread?.status === "ready" && (
            <ThreadView
              key={thread.data.conversation.id}
              thread={thread.data}
              onBack={() => select(null)}
              onDeleted={forget}
              onResolve={resolveHandoff}
              onAssistant={setAssistant}
              onReply={reply}
            />
          )}
        </section>
      </div>
    </div>
  );
}

function ConversationItem({ conversation, selected, showBusiness, onSelect }: { conversation: ConversationSummary; selected: boolean; showBusiness: boolean; onSelect: () => void }) {
  const name = contactLabel(conversation);
  const unread = conversation.unreadCount ?? 0;
  return (
    <button
      type="button"
      className={`inbox-item${selected ? " inbox-item--active" : ""}${unread > 0 ? " inbox-item--unread" : ""}`}
      aria-current={selected ? "true" : undefined}
      onClick={onSelect}
    >
      <ContactAvatar name={name} channel={conversation.channel} />
      <span className="inbox-item__body">
        <span className="inbox-item__top">
          <span className="inbox-item__name">{name}</span>
          <time className="inbox-item__time" dateTime={conversation.lastMessageAt}>
            {relativeTime(conversation.lastMessageAt)}
          </time>
        </span>
        <span className="inbox-item__line">
          {conversation.assistantTyping ? (
            <span className="inbox-item__typing">Escribiendo…</span>
          ) : (
            conversation.lastMessagePreview && <span className="inbox-item__preview">{conversation.lastMessagePreview}</span>
          )}
          {unread > 0 && (
            <span className="unread-badge" aria-label={`${unread} sin leer`}>
              {unread}
            </span>
          )}
        </span>
        <span className="inbox-item__tags">
          {conversation.needsHuman && <span className="handoff-badge">{conversation.handoffReason ? HANDOFF_LABELS[conversation.handoffReason] : "Pide una persona"}</span>}
          {conversation.aiPaused && !conversation.needsHuman && <span className="paused-badge">Atiende tu equipo</span>}
          {/* El negocio solo hace falta al ver los chats de todos tus negocios. */}
          {showBusiness && (
            <span className="business-badge" title="Negocio">
              {conversation.business.name}
            </span>
          )}
        </span>
      </span>
    </button>
  );
}

function ThreadView({
  thread,
  onBack,
  onDeleted,
  onResolve,
  onAssistant,
  onReply,
}: {
  thread: ConversationThread;
  onBack: () => void;
  onDeleted: (id: string) => void;
  onResolve: (id: string) => Promise<void>;
  onAssistant: (id: string, active: boolean) => Promise<void>;
  onReply: (id: string, text: string) => Promise<void>;
}) {
  const { conversation, messages } = thread;
  const name = contactLabel(conversation);
  const log = useRef<HTMLDivElement>(null);
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const isTest = conversation.channel === "prueba";
  const canReply = Boolean(conversation.canReply);
  const [deleting, setDeleting] = useState(false);

  // Baja al último mensaje al abrir y cuando llega uno nuevo, salvo que la persona esté leyendo más arriba.
  const lastId = messages.at(-1)?.id;
  const nearBottom = useRef(true);
  useEffect(() => {
    const element = log.current;
    if (element && nearBottom.current) element.scrollTop = element.scrollHeight;
  }, [lastId, conversation.assistantTyping]);

  const act = async (action: () => Promise<void>, failure: string) => {
    setBusy(true);
    setProblem(null);
    try {
      await action();
    } catch {
      setProblem(failure);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="thread">
      {deleting && (
        <DeleteChatDialog
          conversationId={conversation.id}
          contactName={name}
          isTest={isTest}
          onClose={() => setDeleting(false)}
          onDeleted={() => onDeleted(conversation.id)}
        />
      )}
      <header className="thread__header">
        <button type="button" className="thread__back" aria-label="Volver a las conversaciones" onClick={onBack}>
          <Icon name="arrowLeft" size={20} />
        </button>
        <ContactAvatar name={name} channel={conversation.channel} />
        <div className="thread__who">
          <h2 className="thread__name">{name}</h2>
          <p className="thread__meta">
            {CHANNEL_LABELS[conversation.channel]} · {conversation.business.name} · desde el {fullDate(conversation.startedAt)}
          </p>
        </div>
        <button type="button" className="thread__delete" aria-label="Eliminar chat" title="Eliminar chat" onClick={() => setDeleting(true)}>
          <Icon name="trash" size={18} />
        </button>
        {canReply && (
          <div className="thread__actions">
            <span className={`attendant attendant--${conversation.aiPaused ? "team" : "ai"}`}>
              <Icon name={conversation.aiPaused ? "headset" : "robot"} size={14} /> {conversation.aiPaused ? "Atiende tu equipo" : "Atiende la IA"}
            </span>
            <Button
              size="small"
              variant="secondary"
              disabled={busy}
              onClick={() => void act(() => onAssistant(conversation.id, Boolean(conversation.aiPaused)), "No se pudo cambiar quién atiende. Vuelve a intentarlo.")}
            >
              <Icon name={conversation.aiPaused ? "play" : "pause"} size={14} /> {conversation.aiPaused ? "Reanudar IA" : "Pausar IA"}
            </Button>
          </div>
        )}
      </header>

      {conversation.needsHuman && (
        <div className="handoff-banner" role="status">
          <span className="handoff-banner__icon" aria-hidden="true">
            <Icon name="headset" size={18} />
          </span>
          <div className="handoff-banner__text">
            <strong>
              {isTest ? "Prueba: " : ""}
              {conversation.handoffReason ? HANDOFF_LABELS[conversation.handoffReason] : "Este cliente pidió hablar con una persona"}
            </strong>
            <span>
              {conversation.handoffRequestedAt ? `Desde ${relativeTime(conversation.handoffRequestedAt)}. ` : ""}
              {isTest
                ? "Así te avisaremos cuando un cliente real lo pida."
                : canReply
                  ? "La IA está pausada en este chat: respóndele desde aquí."
                  : `Atiéndelo por ${CHANNEL_LABELS[conversation.channel]} y márcalo cuando esté listo.`}
            </span>
          </div>
          <Button size="small" onClick={() => void act(() => onResolve(conversation.id), "No se pudo marcar como atendida. Vuelve a intentarlo.")} disabled={busy}>
            Ya lo atendí
          </Button>
        </div>
      )}

      <div
        ref={log}
        className="thread__messages"
        role="log"
        aria-label={`Mensajes con ${name}`}
        aria-live="polite"
        onScroll={(event) => {
          const element = event.currentTarget;
          nearBottom.current = element.scrollHeight - element.scrollTop - element.clientHeight < 120;
        }}
      >
        {messages.map((message) => (
          <MessageBubble key={message.id} conversationId={conversation.id} message={message} />
        ))}
        {conversation.assistantTyping && (
          <div className="chat-bubble chat-bubble--assistant chat-bubble--typing" role="status" aria-label="El asistente está escribiendo">
            <span className="typing-dots" aria-hidden="true">
              <span />
              <span />
              <span />
            </span>
            <span className="chat-bubble__meta">
              <Icon name="robot" size={12} /> Escribiendo…
            </span>
          </div>
        )}
      </div>

      {problem && (
        <div className="thread__problem">
          <Alert tone="danger">{problem}</Alert>
        </div>
      )}

      {canReply ? (
        <Composer aiActive={!conversation.aiPaused} onSend={(text) => onReply(conversation.id, text)} />
      ) : (
        <footer className="thread__footer">
          {isTest
            ? "Conversación de prueba hecha desde «Probar asistente». No llegó a ningún cliente."
            : `Los datos de pago se muestran ocultos. Por ${CHANNEL_LABELS[conversation.channel]} todavía no se puede responder desde aquí.`}
        </footer>
      )}
    </div>
  );
}

function Composer({ aiActive, onSend }: { aiActive: boolean; onSend: (text: string) => Promise<void> }) {
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const trimmed = text.trim();

  const send = async () => {
    if (!trimmed || sending) return;
    setSending(true);
    setProblem(null);
    const sent = trimmed;
    setText("");
    try {
      await onSend(sent);
    } catch (error) {
      setText(sent);
      setProblem(persistenceErrorMessage(error));
    } finally {
      setSending(false);
    }
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      void send();
    }
  };

  return (
    <form
      className="composer"
      aria-label="Responder al cliente"
      onSubmit={(event) => {
        event.preventDefault();
        void send();
      }}
    >
      {problem && <p className="composer__problem" role="alert">{problem}</p>}
      <div className="composer__row">
        <label className="visually-hidden" htmlFor="composer-text">
          Tu respuesta
        </label>
        <textarea
          id="composer-text"
          className="composer__input"
          rows={1}
          maxLength={MAX_REPLY}
          value={text}
          placeholder={aiActive ? "Escribe para tomar la conversación…" : "Escribe tu respuesta…"}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={onKeyDown}
        />
        <Button type="submit" disabled={!trimmed || sending} aria-label="Enviar respuesta">
          <Icon name="send" size={16} /> {sending ? "Enviando…" : "Enviar"}
        </Button>
      </div>
      <p className="composer__hint">
        {aiActive ? "Al responder tú, la IA se pausa en este chat hasta que la reanudes." : "La IA está pausada: este chat lo atiende tu equipo."} Enter envía · Mayús+Enter
        hace un salto de línea.
      </p>
    </form>
  );
}

const KIND_ICONS: Partial<Record<NonNullable<ChatMessage["kind"]>, IconName>> = { audio: "mic", document: "file", video: "camera", image: "image", location: "mapPin", contact: "user" };
const KIND_LABELS: Partial<Record<NonNullable<ChatMessage["kind"]>, string>> = {
  image: "Foto",
  audio: "Nota de voz",
  video: "Video",
  document: "Documento",
  sticker: "Sticker",
  location: "Ubicación",
  contact: "Contacto",
};

function MessageBubble({ conversationId, message }: { conversationId: string; message: ChatMessage }) {
  const kind = message.kind ?? "text";
  const outgoing = message.author !== "customer";
  return (
    <div className={`chat-bubble chat-bubble--${message.author}${message.status === "failed" ? " chat-bubble--failed" : ""}`}>
      <span className="visually-hidden">{AUTHOR_LABELS[message.author]}: </span>
      {kind !== "text" && <MediaContent conversationId={conversationId} message={message} />}
      {message.body && <p className="chat-bubble__text">{message.body}</p>}
      <span className="chat-bubble__meta">
        {message.author === "assistant" && (
          <>
            <Icon name="robot" size={12} /> IA ·{" "}
          </>
        )}
        {message.author === "agent" && <>Equipo · </>}
        <time dateTime={message.createdAt}>{messageTime(message.createdAt)}</time>
        {outgoing && message.status && <DeliveryMark status={message.status} />}
      </span>
    </div>
  );
}

function DeliveryMark({ status }: { status: NonNullable<ChatMessage["status"]> }) {
  if (status === "received") return null;
  const label = DELIVERY_LABELS[status];
  if (status === "failed") {
    return (
      <span className="delivery delivery--failed" title={label}>
        <Icon name="alert" size={12} /> {label}
      </span>
    );
  }
  const icon: IconName = status === "sending" ? "clock" : status === "sent" ? "tick" : "ticks";
  return (
    <span className={`delivery delivery--${status}`} role="img" aria-label={label} title={label}>
      <Icon name={icon} size={14} />
    </span>
  );
}

function MediaContent({ conversationId, message }: { conversationId: string; message: ChatMessage }) {
  const kind = message.kind ?? "other";
  const url = useMediaUrl(conversationId, message.media);
  const label = KIND_LABELS[kind] ?? "Archivo";
  const note = message.mediaNote;

  if (!message.media) {
    return (
      <div className="media-placeholder">
        <Icon name={KIND_ICONS[kind] ?? "file"} size={16} /> {label}
        {note && <span className="media-note">{note}</span>}
      </div>
    );
  }
  const ready = url?.status === "ready" ? url.data : null;
  return (
    <div className={`media media--${kind}`}>
      {(kind === "image" || kind === "sticker") &&
        (ready ? (
          <a href={ready} target="_blank" rel="noreferrer" className="media__image-link">
            <img className={kind === "sticker" ? "media__sticker" : "media__image"} src={ready} alt={note ? `${label}: ${note}` : label} />
          </a>
        ) : (
          <span className="media__loading">{url?.status === "error" ? "No se pudo mostrar la foto." : "Cargando la foto…"}</span>
        ))}
      {kind === "audio" && (ready ? <audio className="media__audio" controls src={ready} aria-label={label} /> : <span className="media__loading">Cargando el audio…</span>)}
      {kind === "video" && (ready ? <video className="media__video" controls src={ready} aria-label={label} /> : <span className="media__loading">Cargando el video…</span>)}
      {kind === "document" && (
        <a className="media__document" href={ready ?? undefined} download={message.media.fileName ?? "documento"} aria-disabled={!ready}>
          <Icon name="file" size={18} />
          <span>
            <strong>{message.media.fileName ?? "Documento"}</strong>
            <span>{fileSize(message.media.sizeBytes)}</span>
          </span>
        </a>
      )}
      {note && (
        <p className="media-note">
          <Icon name={kind === "audio" ? "mic" : "sparkles"} size={12} /> {kind === "audio" ? "Transcripción: " : "La IA vio: "}
          {note}
        </p>
      )}
    </div>
  );
}
