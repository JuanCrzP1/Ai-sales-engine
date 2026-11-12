import { useCallback, useEffect, useMemo, useState } from "react";
import type { QuickReply, QuickReplyInput } from "../repositories/quickReplies";
import { PersistenceError, persistenceErrorMessage } from "../repositories/persistenceError";
import { useQuickRepliesService } from "./quickRepliesContext";

export interface QuickRepliesState {
  status: "loading" | "ready" | "error";
  replies: QuickReply[];
  /** Quien mira puede crearlas, editarlas y borrarlas. */
  canManage: boolean;
  error: string | null;
  reload: () => void;
  /** Guardar: crear (sin `id`) o editar. Los fallos se rechazan con `PersistenceError` para mostrarlos en su campo. */
  save: (input: QuickReplyInput, id?: string) => Promise<QuickReply>;
  remove: (id: string) => Promise<void>;
  /** Se usó en un chat: cuenta para que las más usadas salgan primero. Nunca falla hacia afuera: no puede frenar una respuesta. */
  markUsed: (id: string) => void;
}

/** Por qué no se guardó: el mensaje y los problemas por campo (`shortcut`, `pieces[1].text`) para mostrarlos donde van. */
export function saveFailure(reason: unknown): { message: string; problems: Record<string, string> } {
  const problems = reason instanceof PersistenceError ? Object.fromEntries(reason.problems.map((problem) => [problem.path, problem.message])) : {};
  return { message: persistenceErrorMessage(reason), problems };
}

/** Las más usadas primero y, entre iguales, por atajo: el mismo orden que devuelve el servidor. */
function ordered(replies: QuickReply[]): QuickReply[] {
  return [...replies].sort((a, b) => b.useCount - a.useCount || a.shortcut.localeCompare(b.shortcut, "es"));
}

/** Las respuestas rápidas de un negocio: la página de Configuración las organiza y el chat las busca y las usa. */
export function useQuickReplies(slug: string, { enabled = true }: { enabled?: boolean } = {}): QuickRepliesState {
  const createQuickReplies = useQuickRepliesService();
  const service = useMemo(() => createQuickReplies(slug), [createQuickReplies, slug]);
  const [status, setStatus] = useState<QuickRepliesState["status"]>("loading");
  const [replies, setReplies] = useState<QuickReply[]>([]);
  const [canManage, setCanManage] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!enabled) return;
    let active = true;
    setStatus("loading");
    setError(null);
    service.list().then(
      (list) => {
        if (!active) return;
        setReplies(list.replies);
        setCanManage(list.canManage);
        setStatus("ready");
      },
      (reason: unknown) => {
        if (!active) return;
        setError(persistenceErrorMessage(reason));
        setStatus("error");
      },
    );
    return () => {
      active = false;
    };
  }, [service, attempt, enabled]);

  const save = useCallback<QuickRepliesState["save"]>(
    async (input, id) => {
      const saved = id ? await service.update(id, input) : await service.create(input);
      setReplies((current) => ordered([...current.filter((reply) => reply.id !== saved.id), saved]));
      return saved;
    },
    [service],
  );

  const remove = useCallback<QuickRepliesState["remove"]>(
    async (id) => {
      await service.remove(id);
      setReplies((current) => current.filter((reply) => reply.id !== id));
    },
    [service],
  );

  const markUsed = useCallback<QuickRepliesState["markUsed"]>(
    (id) => {
      service.markUsed(id).then(
        (used) => setReplies((current) => ordered(current.map((reply) => (reply.id === used.id ? used : reply)))),
        () => undefined,
      );
    },
    [service],
  );

  const reload = useCallback(() => setAttempt((count) => count + 1), []);

  return { status, replies, canManage, error, reload, save, remove, markUsed };
}
