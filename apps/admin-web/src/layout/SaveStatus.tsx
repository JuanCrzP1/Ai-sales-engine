import { Button } from "../components/ui/Button";
import { ConfirmButton } from "../components/ui/ConfirmButton";
import { Icon, type IconName } from "../components/ui/Icon";
import { formatTime } from "../lib/format";
import { useConfig } from "../state/useConfig";

/**
 * Estado del guardado y acción de guardar. Cada guardado crea una versión, por eso se hace a petición. "Guardado" solo
 * aparece cuando el servidor aceptó el documento; un fallo se muestra con opción de reintentar.
 */
export function SaveStatus() {
  const { save, dirty, actions } = useConfig();
  const { icon, text, tone } = describe(save.status, save.savedAt, dirty);

  return (
    <div className={`save-status save-status--${tone}`}>
      <p className="save-status__text" role="status" aria-live="polite">
        <Icon name={icon} size={16} />
        {text}
      </p>
      {dirty && save.status !== "saving" && (
        <span className="button-row">
          <ConfirmButton variant="ghost" confirmLabel="Sí, descartar" onConfirm={actions.discardChanges}>
            Descartar
          </ConfirmButton>
          <Button size="small" onClick={() => void actions.save()}>
            {save.status === "error" ? "Reintentar" : "Guardar cambios"}
          </Button>
        </span>
      )}
    </div>
  );
}

function describe(status: "idle" | "saving" | "saved" | "error", savedAt: string | null, dirty: boolean): { icon: IconName; text: string; tone: string } {
  if (status === "saving") return { icon: "cloudCheck", text: "Guardando…", tone: "saving" };
  if (status === "error") return { icon: "alert", text: "No se pudo guardar", tone: "error" };
  if (dirty) return { icon: "alert", text: "Cambios sin guardar", tone: "idle" };
  return savedAt ? { icon: "cloudCheck", text: `Guardado · ${formatTime(savedAt)}`, tone: "saved" } : { icon: "cloudCheck", text: "Sin cambios todavía", tone: "idle" };
}
