import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { Dialog } from "../../components/ui/Dialog";
import { Alert } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { PageHeader } from "../../components/ui/Layout";
import {
  categoriesOf,
  copyShortcut,
  groupByCategory,
  matchQuickReplies,
  replySummary,
  type QuickReply,
  type QuickReplyInput,
} from "../../domain/quickReplies/quickReplies";
import { LoadingScreen } from "../../layout/StatusScreen";
import { persistenceErrorMessage } from "../../state/directoryContext";
import { useQuickReplies } from "../../state/useQuickReplies";
import { QuickReplyEditor } from "./QuickReplyEditor";

type Editing = { kind: "edit"; reply: QuickReply | null; initial?: QuickReplyInput } | { kind: "delete"; reply: QuickReply } | null;

function usage(reply: QuickReply): string {
  if (reply.useCount === 0) return "Sin usar aún";
  return reply.useCount === 1 ? "Usada 1 vez" : `Usada ${reply.useCount} veces`;
}

/**
 * Configuración → Respuestas rápidas: los mensajes guardados del negocio, por categoría, con lo que envía cada uno y cuánto los usa
 * el equipo. Quien organiza el negocio los crea, edita, duplica y borra; en el chat se buscan escribiendo «/». Se aplica al instante.
 */
export function QuickRepliesPage() {
  const { slug = "" } = useParams();
  const catalog = useQuickReplies(slug);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<string | null>(null);
  const [editing, setEditing] = useState<Editing>(null);
  const categories = useMemo(() => categoriesOf(catalog.replies), [catalog.replies]);
  const groups = useMemo(() => groupByCategory(matchQuickReplies(catalog.replies, query)), [catalog.replies, query]);
  const visible = category ? groups.filter((group) => group.category === category) : groups;
  const create = () => setEditing({ kind: "edit", reply: null });

  const header = (
    <PageHeader
      title="Respuestas rápidas"
      description="Mensajes que tu equipo envía seguido, guardados para ponerlos en un chat con un atajo. Se aplica al instante: no hace falta publicar."
      actions={
        catalog.canManage && catalog.replies.length > 0 ? (
          <Button onClick={create}>
            <Icon name="plus" size={16} /> Nueva respuesta
          </Button>
        ) : undefined
      }
    />
  );

  if (catalog.status === "loading") return <LoadingScreen label="Cargando las respuestas rápidas…" />;
  if (catalog.status === "error") {
    return (
      <>
        {header}
        <Alert tone="danger" title={catalog.error ?? "No se pudieron cargar las respuestas rápidas."}>
          <Button variant="secondary" size="small" onClick={catalog.reload}>
            Reintentar
          </Button>
        </Alert>
      </>
    );
  }

  return (
    <>
      {header}

      {catalog.replies.length === 0 ? (
        <section className="quick-empty">
          <span className="quick-empty__icon" aria-hidden="true">
            <Icon name="bolt" size={22} />
          </span>
          <h2 className="quick-empty__title">Responde en segundos, sin copiar y pegar</h2>
          <p className="quick-empty__text">
            {catalog.canManage
              ? "Guarda lo que tu equipo responde todos los días: el saludo, los precios, cómo pagar, los envíos. En el chat las buscas escribiendo «/»."
              : "Aún no hay respuestas rápidas. Las crea quien administra el negocio."}
          </p>
          {catalog.canManage && <Button onClick={create}>Crear la primera</Button>}
        </section>
      ) : (
        <div className="quick-list">
          <div className="quick-list__bar">
            <label className="search-field">
              <Icon name="search" size={16} />
              <input
                className="search-field__input"
                type="search"
                value={query}
                placeholder="Buscar por atajo, categoría o texto"
                aria-label="Buscar respuestas rápidas"
                onChange={(event) => setQuery(event.target.value)}
              />
            </label>
            {categories.length > 0 && (
              <div className="quick-list__filters" role="group" aria-label="Filtrar por categoría">
                <button type="button" className="quick-chip" aria-pressed={category === null} onClick={() => setCategory(null)}>
                  Todas · {catalog.replies.length}
                </button>
                {groupByCategory(catalog.replies).map((group) => (
                  <button
                    key={group.category}
                    type="button"
                    className="quick-chip"
                    aria-pressed={category === group.category}
                    onClick={() => setCategory(category === group.category ? null : group.category)}
                  >
                    {group.category} · {group.replies.length}
                  </button>
                ))}
              </div>
            )}
          </div>

          {!catalog.canManage && <p className="quick-list__note">Solo quien administra el negocio las crea y edita. Tú las usas en el chat escribiendo «/».</p>}
          {visible.length === 0 && <p className="quick-list__note">Ninguna coincide con «{query}».</p>}

          {visible.map((group) => (
            <section key={group.category} className="quick-group" aria-label={group.category}>
              <h2 className="quick-group__title">
                {group.category} <span>{group.replies.length}</span>
              </h2>
              <ul className="quick-group__list">
                {group.replies.map((reply) => (
                  <li key={reply.id} className="quick-row">
                    <div className="quick-row__main">
                      <span className="quick-row__shortcut">/{reply.shortcut}</span>
                      <p className="quick-row__text">{replySummary(reply)}</p>
                      <span className="quick-row__meta">
                        {reply.pieces.length > 1 && <span>{reply.pieces.length} mensajes</span>}
                        <span className={reply.useCount === 0 ? "quick-row__unused" : undefined}>{usage(reply)}</span>
                      </span>
                    </div>
                    {catalog.canManage && (
                      <div className="quick-row__actions">
                        <Button variant="ghost" size="small" onClick={() => setEditing({ kind: "edit", reply })} aria-label={`Editar /${reply.shortcut}`}>
                          Editar
                        </Button>
                        <Button
                          variant="ghost"
                          size="small"
                          aria-label={`Duplicar /${reply.shortcut}`}
                          onClick={() =>
                            setEditing({
                              kind: "edit",
                              reply: null,
                              initial: {
                                shortcut: copyShortcut(reply.shortcut, catalog.replies.map((item) => item.shortcut)),
                                category: reply.category,
                                pieces: reply.pieces,
                              },
                            })
                          }
                        >
                          Duplicar
                        </Button>
                        <Button
                          variant="danger"
                          size="small"
                          className="button--danger-outline"
                          aria-label={`Borrar /${reply.shortcut}`}
                          onClick={() => setEditing({ kind: "delete", reply })}
                        >
                          Borrar
                        </Button>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}

      {editing?.kind === "edit" && (
        <QuickReplyEditor
          reply={editing.reply}
          initial={editing.initial}
          categories={categories}
          onSave={(input) => catalog.save(input, editing.reply?.id)}
          onUpload={catalog.uploadFile}
          onClose={() => setEditing(null)}
        />
      )}
      {editing?.kind === "delete" && <DeleteQuickReplyDialog reply={editing.reply} onDelete={catalog.remove} onClose={() => setEditing(null)} />}
    </>
  );
}

function DeleteQuickReplyDialog({ reply, onDelete, onClose }: { reply: QuickReply; onDelete: (id: string) => Promise<void>; onClose: () => void }) {
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const confirm = async () => {
    setBusy(true);
    setProblem(null);
    try {
      await onDelete(reply.id);
      onClose();
    } catch (reason) {
      setProblem(persistenceErrorMessage(reason));
      setBusy(false);
    }
  };
  return (
    <Dialog
      title={`¿Borrar /${reply.shortcut}?`}
      description="Nadie del equipo podrá volver a usarla en el chat. Los mensajes que ya se enviaron no cambian."
      onClose={busy ? () => undefined : onClose}
      footer={
        <>
          <Button variant="ghost" disabled={busy} onClick={onClose}>
            Cancelar
          </Button>
          <Button variant="danger" className="button--danger-solid" disabled={busy} onClick={() => void confirm()}>
            {busy ? "Borrando…" : "Sí, borrar"}
          </Button>
        </>
      }
    >
      {problem ? <Alert tone="danger">{problem}</Alert> : <p className="quick-row__text">{replySummary(reply)}</p>}
    </Dialog>
  );
}
