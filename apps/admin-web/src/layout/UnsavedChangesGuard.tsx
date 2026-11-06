import { useEffect, useState } from "react";
import { useBlocker, useParams } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { Alert } from "../components/ui/Feedback";
import { workspacePath } from "../navigation/navItems";
import { useConfig } from "../state/useConfig";

/** Evita perder cambios sin guardar: al salir del negocio pregunta qué hacer, y al cerrar la pestaña avisa el navegador. */
export function UnsavedChangesGuard() {
  const { dirty, actions } = useConfig();
  const { slug = "" } = useParams();
  const [saving, setSaving] = useState(false);
  const base = workspacePath(slug);
  const blocker = useBlocker(({ nextLocation }) => dirty && nextLocation.pathname !== base && !nextLocation.pathname.startsWith(`${base}/`));

  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  if (blocker.state !== "blocked") return null;

  const saveAndLeave = async () => {
    setSaving(true);
    const saved = await actions.save();
    setSaving(false);
    if (saved) blocker.proceed();
    else blocker.reset();
  };

  return (
    <div className="main__alerts">
      <Alert tone="warning" title="Tienes cambios sin guardar">
        <p>Si sales ahora, se perderán.</p>
        <div className="button-row">
          <Button size="small" disabled={saving} onClick={() => void saveAndLeave()}>
            Guardar y salir
          </Button>
          <Button size="small" variant="danger" disabled={saving} onClick={() => blocker.proceed()}>
            Salir sin guardar
          </Button>
          <Button size="small" variant="ghost" disabled={saving} onClick={() => blocker.reset()}>
            Seguir editando
          </Button>
        </div>
      </Alert>
    </div>
  );
}
