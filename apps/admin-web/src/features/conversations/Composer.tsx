import { useCallback, useEffect, useRef, useState, type ClipboardEvent, type KeyboardEvent } from "react";
import { Button } from "../../components/ui/Button";
import { Icon } from "../../components/ui/Icon";
import { ATTACHMENT_ACCEPT, ATTACHMENT_HINT, MAX_CAPTION, attachmentKind, attachmentProblem, formatBytes } from "../../domain/inbox/attachments";
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
  /** Envía un archivo con el texto escrito como leyenda. */
  onSendFile: (file: File, caption: string) => Promise<void>;
}

/**
 * Responder al cliente desde el panel. Con ⚡ o escribiendo «/» se busca una respuesta rápida: si es un solo mensaje va al cuadro de
 * texto para retocarlo; si son varios, quedan en espera y salen en orden al enviar, antes de lo que se escriba. Con el clip (o
 * pegando una imagen) se adjunta un archivo: sale con lo escrito como su texto.
 */
export function Composer({ businessSlug, contactName, aiActive, onSend, onSendFile }: ComposerProps) {
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const picker_ = useRef<HTMLInputElement>(null);
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

  // La miniatura de una foto adjunta: se libera al quitarla o al enviarla.
  useEffect(() => {
    if (!file || attachmentKind(file.type) !== "image" || typeof URL.createObjectURL !== "function") {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const attach = (chosen: File | null | undefined) => {
    if (!chosen) return;
    const reason = attachmentProblem(chosen);
    if (reason) {
      setProblem(reason);
      return;
    }
    setProblem(null);
    setFile(chosen);
    input.current?.focus();
  };

  const onPaste = (event: ClipboardEvent<HTMLTextAreaElement>) => {
    const pasted = [...event.clipboardData.files].find((item) => item.type.startsWith("image/"));
    if (pasted) {
      event.preventDefault();
      attach(pasted);
    }
  };
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
    if ((!trimmed && pending.length === 0 && !file) || sending) return;
    if (file && trimmed.length > MAX_CAPTION) {
      setProblem(`El texto que acompaña el archivo puede tener hasta ${MAX_CAPTION} caracteres.`);
      return;
    }
    setSending(true);
    setProblem(null);
    // Con un archivo, lo escrito es su texto: sale con él, después de los mensajes en espera.
    const queue = [...pending, ...(trimmed && !file ? [trimmed] : [])];
    const attachment = file;
    setPending([]);
    setText("");
    setFile(null);
    let sent = 0;
    try {
      for (const message of queue) {
        await onSend(message);
        sent += 1;
      }
      if (attachment) await onSendFile(attachment, trimmed);
    } catch (error) {
      if (attachment && sent === queue.length) {
        // Lo que falló fue el archivo: vuelve con su texto para intentarlo de nuevo.
        setFile(attachment);
        setText(trimmed);
        setProblem(persistenceErrorMessage(error));
        return;
      }
      if (attachment) {
        setFile(attachment);
        setText(trimmed);
      }
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
      {file && (
        <div className="composer__file" role="group" aria-label="Archivo adjunto">
          {preview ? <img className="composer__file-thumb" src={preview} alt="" /> : <span className="composer__file-icon" aria-hidden="true"><Icon name={attachmentKind(file.type) === "image" ? "image" : "file"} size={18} /></span>}
          <span className="composer__file-text">
            <strong>{file.name}</strong>
            <span>
              {formatBytes(file.size)} · {trimmed ? "lo que escribas sale con el archivo" : "puedes escribir un texto para acompañarlo"}
            </span>
          </span>
          <button type="button" className="composer__pending-remove" aria-label={`Quitar ${file.name}`} onClick={() => setFile(null)}>
            <Icon name="close" size={14} />
          </button>
        </div>
      )}
      <div className="composer__row">
        <input
          ref={picker_}
          type="file"
          className="visually-hidden"
          accept={ATTACHMENT_ACCEPT}
          aria-label="Elegir un archivo para enviar"
          tabIndex={-1}
          onChange={(event) => {
            attach(event.target.files?.[0]);
            event.target.value = "";
          }}
        />
        <button
          type="button"
          className="composer__quick"
          aria-label="Adjuntar un archivo"
          title={`Adjuntar: ${ATTACHMENT_HINT}`}
          disabled={sending}
          onClick={() => picker_.current?.click()}
        >
          <Icon name="paperclip" size={18} />
        </button>
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
          placeholder={
            file
              ? "Escribe un texto para acompañar el archivo (opcional)"
              : aiActive
                ? "Escribe para tomar la conversación… o «/» para una respuesta rápida"
                : "Escribe tu respuesta… o «/» para una respuesta rápida"
          }
          onChange={(event) => setText(event.target.value)}
          onKeyDown={onKeyDown}
          onPaste={onPaste}
        />
        <Button type="submit" disabled={(!trimmed && pending.length === 0 && !file) || sending} aria-label="Enviar respuesta">
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
