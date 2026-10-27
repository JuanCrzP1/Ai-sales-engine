export interface ChatLine {
  from: "customer" | "assistant";
  text: string;
}

/** Vista previa estática de una conversación. No envía mensajes. */
export function ChatPreview({ lines, caption }: { lines: ChatLine[]; caption?: string }) {
  return (
    <figure className="chat-preview" aria-label="Vista previa de la conversación">
      {lines.map((line, index) => (
        <p key={index} className={`chat-preview__bubble${line.from === "customer" ? " chat-preview__bubble--user" : ""}`}>
          <span className="visually-hidden">{line.from === "customer" ? "Cliente: " : "Asistente: "}</span>
          {line.text}
        </p>
      ))}
      {caption && <figcaption className="chat-preview__caption">{caption}</figcaption>}
    </figure>
  );
}
