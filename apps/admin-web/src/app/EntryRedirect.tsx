import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { Button } from "../components/ui/Button";
import type { BusinessSummary } from "../domain/config/types";
import { LoadingScreen, StatusScreen } from "../layout/StatusScreen";
import { NEW_BUSINESS_PATH, workspacePath } from "../navigation/navItems";
import { persistenceErrorMessage, useBusinessDirectory } from "../state/directoryContext";

type EntryState = { status: "loading" } | { status: "error"; message: string } | { status: "ready"; businesses: BusinessSummary[] };

/** Al entrar: directo al panel del primer negocio del usuario; si todavía no tiene, a crearlo. */
export function EntryRedirect() {
  const directory = useBusinessDirectory();
  const [state, setState] = useState<EntryState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    setState({ status: "loading" });
    directory.list().then(
      (businesses) => active && setState({ status: "ready", businesses }),
      (error: unknown) => active && setState({ status: "error", message: persistenceErrorMessage(error) }),
    );
    return () => {
      active = false;
    };
  }, [directory, attempt]);

  if (state.status === "loading") return <LoadingScreen label="Abriendo tu panel…" />;
  if (state.status === "error") {
    return (
      <StatusScreen title="No se pudo abrir tu panel" message={state.message}>
        <Button onClick={() => setAttempt((count) => count + 1)}>Reintentar</Button>
      </StatusScreen>
    );
  }
  const [first] = state.businesses;
  return <Navigate to={first ? workspacePath(first.slug) : NEW_BUSINESS_PATH} replace />;
}
