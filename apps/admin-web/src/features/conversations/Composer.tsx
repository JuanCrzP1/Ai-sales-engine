import { useCallback, useRef, useState, type KeyboardEvent } from "react";
import { Button } from "../../components/ui/Button";
import { Icon } from "../../components/ui/Icon";
import { fillName, slashQuery, type QuickReply } from "../../domain/quickReplies/quickReplies";
import { QUICK_REPLIES_ITEM } from "../../navigation/navItems";
import { persistenceErrorMessage } from "../../state/directoryContext";
import { useQuickReplies } from "../../state/useQuickReplies";
import { QuickReplyPicker, type QuickReplyPickerHandle } from "./QuickReplyPicker";

export const MAX_REPLY = 4000;

interface ComposerProps {
  /** El negocio del chat: sus respuestas rápidas. */
  businessSlug: string;
  /** El nombre del cliente, para `{nombre}`. */
  contactName: string | null;
  aiActive: boolean;
  onSend: (text: string) => Promise<void>;
}

/**
 * Responder al cliente desde el panel. Con ⚡ o escribiendo «/» se busca una respuesta rápida: si es un solo mensaje va al cuadro de
 * texto para retocarlo; si son varios, quedan en espera y salen en orden al enviar, antes de lo que se escriba.
 */
export function Composer({ businessSlug, contactName, aiActive, onSend }: ComposerProps) {
  const [text, setText] = useState("");
  const [pending, setPending] = useState<string[]>([]);
  const [sending, setSending] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  // Abierto con ⚡ (se busca dentro) o con «/» (se busca desde el cuadro de texto). Escape cierra la búsqueda con «/» hasta que cambie.
  const [searching, setSearching] = useState(false);
  const [search, setSearch] = useState("");
  const [dismissed, setDismissed] = useState<string | null>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  const picker = useRef<QuickReplyPickerHandle>(null);
  const catalog = useQuickReplies(businessSlug);
  const trimmed = text.trim();
  const slash = slashQuery(text);
  const slashOpen = slash !== null && dismissed !== text;
  const open = searching || slashOpen;

  const close = useCallback(() => {
    setSearching(false);
    setSearch("");
    setDismissed(slashQuery(input.current?.value ?? "") !== null ? (input.current?.value ?? null) : null);
  }, []);

  const pick = (reply: QuickReply) => {
    const messages = reply.pieces.map((piece) => fillName(piece.text, contactName).trim()).filter(Boolean);
    if (messages.length === 1) {
      setText(messages[0]!);
    } else {
      setPending((current) => [...current, ...messages]);
      if (slash !== null) setText("");
    }
    setSearching(false);
    setSearch("");
    setDismissed(null);
    catalog.markUsed(reply.id);
    input.current?.focus();
  };

  const send = async () => {
    if ((!trimmed && pending.length === 0) || sending) return;
    setSending(true);
    setProblem(null);
    const queue = [...pending, ...(trimmed ? [trimmed] : [])];
    setPending([]);
    setText("");
    let sent = 0;
    try {
      for (const message of queue) {
        await onSend(message);
        sent += 1;
      }
    } catch (error) {
      // Lo que no salió vuelve a su lugar para intentarlo de nuevo, sin repetir lo que ya llegó.
      const rest = queue.slice(sent);
      if (trimmed && rest.at(-1) === trimmed) {
        setPending(rest.slice(0, -1));
        setText(trimmed);
      } else {
        setPending(rest);
      }
      setProblem(persistenceErrorMessage(error));
    } finally {
      setSending(false);
    }
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (slashOpen && picker.current?.handleKey(event)) {
      event.preventDefault();
      return;
    }
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
      {open && (
        <QuickReplyPicker
          ref={picker}
          catalog={catalog}
          managePath={`/negocios/${encodeURIComponent(businessSlug)}/${QUICK_REPLIES_ITEM.path}`}
          query={searching ? search : (slash ?? "")}
          searchable={searching}
          onQuery={setSearch}
          onPick={pick}
          onClose={close}
        />
      )}
      {pending.length > 0 && (
        <div className="composer__pending" role="group" aria-label="Mensajes en espera">
          <p className="composer__pending-title">
            {pending.length === 1 ? "1 mensaje en espera" : `${pending.length} mensajes en espera`}: salen en orden al enviar.
          </p>
          <ol className="composer__pending-list">
            {pending.map((message, index) => (
              <li key={`${index}-${message}`} className="composer__pending-item">
                <span>{message}</span>
                <button
                  type="button"
                  className="composer__pending-remove"
                  aria-label={`Quitar el mensaje en espera ${index + 1}`}
                  onClick={() => setPending((current) => current.filter((_, at) => at !== index))}
                >
                  <Icon name="close" size={14} />
                </button>
              </li>
            ))}
          </ol>
        </div>
      )}
      <div className="composer__row">
        <button
          type="button"
          className={`composer__quick${open ? " composer__quick--open" : ""}`}
          data-quick-toggle
          aria-label="Respuestas rápidas"
          aria-expanded={open}
          title="Respuestas rápidas (/)"
          onClick={() => (open ? close() : setSearching(true))}
        >
          <Icon name="bolt" size={18} />
        </button>
        <label className="visually-hidden" htmlFor="composer-text">
          Tu respuesta
        </label>
        <textarea
          ref={input}
          id="composer-text"
          className="composer__input"
          rows={1}
          maxLength={MAX_REPLY}
          value={text}
          placeholder={aiActive ? "Escribe para tomar la conversación… o «/» para una respuesta rápida" : "Escribe tu respuesta… o «/» para una respuesta rápida"}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={onKeyDown}
        />
        <Button type="submit" disabled={(!trimmed && pending.length === 0) || sending} aria-label="Enviar respuesta">
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
