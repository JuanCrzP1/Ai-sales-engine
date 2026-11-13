import { useCallback, useEffect, useState } from "react";
import type { Invitation, InvitationInput, IssuedInvitation, Role, TeamView } from "../repositories/team";
import { PersistenceError, persistenceErrorMessage } from "../repositories/persistenceError";
import { useTeamService } from "./teamContext";

export interface TeamState {
  status: "loading" | "ready" | "error";
  team: TeamView | null;
  error: string | null;
  reload: () => void;
  /** Rechazan con `PersistenceError` para mostrar el motivo donde corresponde. */
  invite: (input: InvitationInput) => Promise<IssuedInvitation>;
  renew: (invitationId: string) => Promise<IssuedInvitation>;
  revoke: (invitationId: string) => Promise<void>;
  changeRole: (userId: string, role: Role) => Promise<void>;
  remove: (userId: string) => Promise<void>;
}

/** Los problemas por campo de un fallo (`email`, `role`), para mostrarlos junto a su campo. */
export function teamProblems(reason: unknown): { message: string; problems: Record<string, string> } {
  const problems = reason instanceof PersistenceError ? Object.fromEntries(reason.problems.map((problem) => [problem.path, problem.message])) : {};
  return { message: persistenceErrorMessage(reason), problems };
}

/** El equipo del negocio: Configuración → Equipo. Cada cambio vuelve a leer el equipo, para ver lo mismo que el servidor. */
export function useTeam(slug: string): TeamState {
  const service = useTeamService();
  const [status, setStatus] = useState<TeamState["status"]>("loading");
  const [team, setTeam] = useState<TeamView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  const load = useCallback(async () => setTeam(await service.view(slug)), [service, slug]);

  useEffect(() => {
    let active = true;
    setStatus("loading");
    setError(null);
    service.view(slug).then(
      (view) => {
        if (!active) return;
        setTeam(view);
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
  }, [service, slug, attempt]);

  const after = useCallback(
    async <T,>(action: Promise<T>): Promise<T> => {
      const result = await action;
      await load().catch(() => undefined);
      return result;
    },
    [load],
  );

  return {
    status,
    team,
    error,
    reload: useCallback(() => setAttempt((count) => count + 1), []),
    invite: useCallback((input) => after(service.invite(slug, input)), [after, service, slug]),
    renew: useCallback((id) => after(service.renew(slug, id)), [after, service, slug]),
    revoke: useCallback((id) => after(service.revoke(slug, id)), [after, service, slug]),
    changeRole: useCallback(async (userId, role) => void (await after(service.changeRole(slug, userId, role))), [after, service, slug]),
    remove: useCallback((userId) => after(service.remove(slug, userId)), [after, service, slug]),
  };
}

export type InvitationLoad = { status: "loading" } | { status: "ready"; invitation: Invitation } | { status: "error"; message: string };

/** Una invitación abierta por su enlace: de qué negocio es, y aceptarla. */
export function useInvitation(token: string) {
  const service = useTeamService();
  const [state, setState] = useState<InvitationLoad>({ status: "loading" });
  useEffect(() => {
    let active = true;
    service.preview(token).then(
      (invitation) => active && setState({ status: "ready", invitation }),
      (reason: unknown) => active && setState({ status: "error", message: persistenceErrorMessage(reason) }),
    );
    return () => {
      active = false;
    };
  }, [service, token]);
  const accept = useCallback(() => service.accept(token), [service, token]);
  return { state, accept };
}
