import { Icon, type IconName } from "../components/ui/Icon";
import { formatTime } from "../lib/format";
import { useConfig } from "../state/useConfig";

/**
 * Estado del guardado de la configuración. "Guardado" solo aparece cuando el
 * almacenamiento confirmó la operación; un fallo se muestra con opción de reintentar.
 */
export function SaveStatus() {
  const { save, actions } = useConfig();
  const { icon, text, tone } = describe(save.status, save.savedAt);

  return (
    <div className={`save-status save-status--${tone}`}>
      <p className="save-status__text" role="status" aria-live="polite">
        <Icon name={icon} size={16} />
        {text}
      </p>
      {save.status === "error" && (
        <>
          <span className="visually-hidden" role="alert">
            {save.error}
          </span>
          <button type="button" className="save-status__retry" onClick={actions.retrySave} title={save.error ?? undefined}>
            Reintentar
          </button>
        </>
      )}
    </div>
  );
}

function describe(status: "idle" | "saving" | "saved" | "error", savedAt: string | null): { icon: IconName; text: string; tone: string } {
  switch (status) {
    case "saving":
      return { icon: "cloudCheck", text: "Guardando…", tone: "saving" };
    case "error":
      return { icon: "alert", text: "No se pudo guardar", tone: "error" };
    case "saved":
    case "idle":
      return savedAt
        ? { icon: "cloudCheck", text: `Guardado · ${formatTime(savedAt)}`, tone: "saved" }
        : { icon: "cloudCheck", text: "Sin cambios todavía", tone: "idle" };
  }
}
