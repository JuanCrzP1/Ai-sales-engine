import { useId, useRef, useState, type FormEvent } from "react";
import { Button } from "../../components/ui/Button";
import { ChatPreview } from "../../components/ui/ChatPreview";
import { Dialog } from "../../components/ui/Dialog";
import { Alert } from "../../components/ui/Feedback";
import { TextAreaField, TextField } from "../../components/ui/FormFields";
import { Icon } from "../../components/ui/Icon";
import { ATTACHMENT_ACCEPT, ATTACHMENT_HINT, attachmentProblem, formatBytes } from "../../domain/inbox/attachments";
import {
  MAX_CATEGORY,
  MAX_FILE_CAPTION,
  MAX_PIECES,
  MAX_SHORTCUT,
  MAX_TEXT,
  NAME_PLACEHOLDER,
  fileLabel,
  fillName,
  normalizeShortcut,
  type QuickReply,
  type QuickReplyFile,
  type QuickReplyInput,
  type QuickReplyPiece,
} from "../../domain/quickReplies/quickReplies";
import { saveFailure } from "../../state/useQuickReplies";

/** Un problema del servidor que se muestra junto a su campo. */
const placed = (path: string) => path === "shortcut" || path === "category" || path.startsWith("pieces");

const toPiece = (item: EditableMessage): QuickReplyPiece => (item.file ? { kind: "file", text: item.text, ...item.file } : { kind: "text", text: item.text });

/** Con qué nombre se muestra la vista previa. */
const SAMPLE_NAME = "María";

interface EditableMessage {
  key: number;
  /** Un texto, o el texto que acompaña al archivo cuando hay `file`. */
  text: string;
  file?: QuickReplyFile;
}

interface QuickReplyEditorProps {
  /** La que se edita; `null`: una nueva (vacía o la copia de `initial`). */
  reply: QuickReply | null;
  initial?: QuickReplyInput;
  /** Las categorías que ya usa el negocio, para sugerirlas. */
  categories: string[];
  onSave: (input: QuickReplyInput) => Promise<unknown>;
  /** Sube un archivo para la respuesta (queda guardado con el negocio). */
  onUpload: (file: File) => Promise<QuickReplyFile>;
  onClose: () => void;
}

/**
 * Crear, editar o duplicar una respuesta rápida: el atajo, la categoría y los mensajes en orden, con la vista previa de cómo le llegan
 * al cliente. Los problemas del servidor se muestran en su campo.
 */
export function QuickReplyEditor({ reply, initial, categories, onSave, onUpload, onClose }: QuickReplyEditorProps) {
  const listId = useId();
  const sequence = useRef(0);
  const nextKey = () => (sequence.current += 1);
  const start = reply ?? initial;
  const [shortcut, setShortcut] = useState(start?.shortcut ?? "");
  const [category, setCategory] = useState(start?.category ?? "");
  const [messages, setMessages] = useState<EditableMessage[]>(() =>
    (start?.pieces.length ? start.pieces : [{ kind: "text" as const, text: "" }]).map((piece) =>
      piece.kind === "file"
        ? { key: nextKey(), text: piece.text, file: { fileId: piece.fileId, fileName: piece.fileName, mimeType: piece.mimeType, sizeBytes: piece.sizeBytes } }
        : { key: nextKey(), text: piece.text },
    ),
  );
  const [uploading, setUploading] = useState(false);
  const [uploadProblem, setUploadProblem] = useState<string | null>(null);
  const filePicker = useRef<HTMLInputElement>(null);

  const addFile = async (chosen: File | undefined) => {
    if (!chosen) return;
    const reason = attachmentProblem(chosen);
    if (reason) {
      setUploadProblem(reason);
      return;
    }
    setUploading(true);
    setUploadProblem(null);
    try {
      const file = await onUpload(chosen);
      // Un mensaje vacío del principio se reemplaza: la respuesta puede ser solo el archivo.
      setMessages((current) => [...current.filter((item) => item.file || item.text.trim() || current.length > 1), { key: nextKey(), text: "", file }]);
    } catch (reason) {
      setUploadProblem(saveFailure(reason).message);
    } finally {
      setUploading(false);
    }
  };
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [problems, setProblems] = useState<Record<string, string>>({});

  const change = (index: number, text: string) => setMessages((current) => current.map((item, at) => (at === index ? { ...item, text } : item)));
  const move = (index: number, delta: -1 | 1) =>
    setMessages((current) => {
      const next = [...current];
      [next[index], next[index + delta]] = [next[index + delta]!, next[index]!];
      return next;
    });
  const remove = (index: number) => setMessages((current) => current.filter((_, at) => at !== index));
  const add = () => setMessages((current) => [...current, { key: nextKey(), text: "" }]);
  const addName = (index: number) => change(index, `${messages[index]?.text.trimEnd() ?? ""} ${NAME_PLACEHOLDER}`.trimStart());

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setProblems({});
    try {
      await onSave({ shortcut: normalizeShortcut(shortcut), category: category.trim() || null, pieces: messages.map(toPiece) });
      onClose();
    } catch (reason) {
      const failure = saveFailure(reason);
      setError(failure.message);
      setProblems(failure.problems);
      setBusy(false);
    }
  };

  const preview = messages
    .filter((item) => item.file || item.text.trim())
    .map((item) => ({ from: "assistant" as const, text: [item.file ? fileLabel(item.file) : "", fillName(item.text.trim(), SAMPLE_NAME)].filter(Boolean).join("\n") }));
  const typed = normalizeShortcut(shortcut);
  const title = reply ? `Editar /${reply.shortcut}` : initial ? "Duplicar respuesta rápida" : "Nueva respuesta rápida";

  return (
    <Dialog
      title={title}
      description="Se envían en orden, un mensaje tras otro, como si los escribieras tú."
      onClose={busy ? () => undefined : onClose}
      footer={
        <>
          <Button variant="ghost" disabled={busy} onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" form="quick-reply-form" disabled={busy || uploading || messages.length === 0}>
            {busy ? "Guardando…" : reply ? "Guardar cambios" : "Crear respuesta"}
          </Button>
        </>
      }
    >
      <form id="quick-reply-form" className="quick-editor" onSubmit={(event) => void submit(event)} noValidate>
        <div className="quick-editor__form">
          <div className="quick-editor__fields">
            <TextField
              label="Atajo"
              value={shortcut}
              maxLength={MAX_SHORTCUT}
              placeholder="precios"
              hint={`En el chat se busca escribiendo /${typed || "atajo"}.`}
              error={problems.shortcut}
              required
              onChange={(value) => setShortcut(value.toLowerCase())}
            />
            <TextField
              label="Categoría"
              value={category}
              maxLength={MAX_CATEGORY}
              placeholder="Saludos, Precios, Pagos…"
              list={listId}
              hint="Opcional. Agrupa las respuestas en el chat."
              error={problems.category}
              onChange={setCategory}
            />
            <datalist id={listId}>
              {categories.map((name) => (
                <option key={name} value={name} />
              ))}
            </datalist>
          </div>

          <ol className="quick-editor__messages">
            {messages.map((item, index) => (
              <li key={item.key} className="quick-editor__message">
                {item.file ? (
                  <>
                    <div className="quick-editor__file" role="group" aria-label={`Archivo del mensaje ${index + 1}`}>
                      <span className="quick-editor__file-icon" aria-hidden="true">
                        <Icon name={item.file.mimeType.startsWith("image/") ? "image" : "file"} size={18} />
                      </span>
                      <span className="quick-editor__file-text">
                        <strong>{item.file.fileName ?? fileLabel(item.file).slice(3)}</strong>
                        <span>{formatBytes(item.file.sizeBytes)}</span>
                      </span>
                    </div>
                    {problems[`pieces[${index}].file`] && <p className="field__message field__message--error" role="alert">{problems[`pieces[${index}].file`]}</p>}
                    <TextAreaField
                      label={`Texto del archivo ${index + 1} (opcional)`}
                      value={item.text}
                      rows={2}
                      maxLength={MAX_FILE_CAPTION}
                      placeholder="Aquí está nuestro catálogo, {nombre} 👇"
                      error={problems[`pieces[${index}].text`]}
                      onChange={(text) => change(index, text)}
                    />
                  </>
                ) : (
                  <TextAreaField
                    label={messages.length > 1 ? `Mensaje ${index + 1}` : "Mensaje"}
                    value={item.text}
                    rows={3}
                    maxLength={MAX_TEXT}
                    placeholder={index === 0 ? "Hola {nombre}, el combo vale $25.000 e incluye bebida." : "Otro mensaje que sale después…"}
                    error={problems[`pieces[${index}].text`]}
                    onChange={(text) => change(index, text)}
                  />
                )}
                <div className="quick-editor__tools" role="group" aria-label={`Acciones del mensaje ${index + 1}`}>
                  <Button variant="ghost" size="small" onClick={() => addName(index)} aria-label={`Agregar el nombre del cliente al mensaje ${index + 1}`}>
                    + {NAME_PLACEHOLDER}
                  </Button>
                  {messages.length > 1 && (
                    <>
                      <Button variant="ghost" size="small" disabled={index === 0} onClick={() => move(index, -1)} aria-label={`Subir el mensaje ${index + 1}`}>
                        ↑
                      </Button>
                      <Button variant="ghost" size="small" disabled={index === messages.length - 1} onClick={() => move(index, 1)} aria-label={`Bajar el mensaje ${index + 1}`}>
                        ↓
                      </Button>
                      <Button variant="ghost" size="small" onClick={() => remove(index)} aria-label={`Quitar el mensaje ${index + 1}`}>
                        <Icon name="trash" size={14} />
                      </Button>
                    </>
                  )}
                </div>
              </li>
            ))}
          </ol>
          {problems.pieces && <p className="field__message field__message--error" role="alert">{problems.pieces}</p>}
          {messages.length < MAX_PIECES && (
            <div className="quick-editor__add">
              <Button variant="secondary" size="small" onClick={add} disabled={uploading}>
                <Icon name="plus" size={14} /> Agregar otro mensaje
              </Button>
              <Button variant="secondary" size="small" onClick={() => filePicker.current?.click()} disabled={uploading}>
                <Icon name="paperclip" size={14} /> {uploading ? "Subiendo…" : "Agregar archivo"}
              </Button>
              <input
                ref={filePicker}
                type="file"
                className="visually-hidden"
                accept={ATTACHMENT_ACCEPT}
                aria-label="Elegir un archivo para la respuesta"
                tabIndex={-1}
                onChange={(event) => {
                  void addFile(event.target.files?.[0]);
                  event.target.value = "";
                }}
              />
            </div>
          )}
          {uploadProblem && <p className="field__message field__message--error" role="alert">{uploadProblem}</p>}
          <p className="quick-editor__tip">Archivos: {ATTACHMENT_HINT}</p>
          <p className="quick-editor__tip">
            <code>{NAME_PLACEHOLDER}</code> se cambia por el primer nombre del cliente. Si no lo sabemos, se quita.
          </p>
        </div>

        <div className="quick-editor__preview">
          <p className="quick-editor__preview-title">Así le llega al cliente</p>
          {preview.length > 0 ? (
            <ChatPreview lines={preview} caption={`Con un cliente llamado ${SAMPLE_NAME}.`} />
          ) : (
            <p className="quick-editor__preview-empty">Escribe un mensaje para ver cómo se verá.</p>
          )}
        </div>
      </form>
      {/* Lo que no se puede mostrar junto a un campo (sin conexión, el máximo de respuestas) va aquí. */}
      {error && !Object.keys(problems).some(placed) && <Alert tone="danger">{error}</Alert>}
    </Dialog>
  );
}
