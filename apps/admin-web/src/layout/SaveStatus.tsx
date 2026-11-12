import { useLocation } from "react-router-dom";
import { Button, LinkButton } from "../components/ui/Button";
import { ConfirmButton } from "../components/ui/ConfirmButton";
import { Icon, type IconName } from "../components/ui/Icon";
import { formatTime } from "../lib/format";
import { REVIEW_ITEM } from "../navigation/navItems";
import { useWorkspacePath } from "../navigation/useWorkspacePath";
import type { PublicationState, SaveState } from "../state/configContext";
import { useConfig } from "../state/useConfig";

/**
 * Arriba del editor del asistente: el guardado y si lo guardado ya es lo que responde a los clientes. Guardar no es publicar:
 * mientras lo guardado no se publique, aquí se ve «Cambios sin publicar» con el camino para publicarlo.
 */
export function SaveStatus() {
  const { save, dirty, publication, actions } = useConfig();
  const pathTo = useWorkspacePath();
  const { pathname } = useLocation();
  const { icon, text, tone } = describe(save, dirty, publication);
  const reviewPath = pathTo(REVIEW_ITEM.path);
  const onReview = pathname === reviewPath;
  const needsPublishing = !dirty && save.status !== "saving" && save.status !== "error" && (publication === "pending" || publication === "never");

  return (
    <div className={`save-status save-status--${tone}`}>
      <p className="save-status__text" role="status" aria-live="polite" aria-label="Estado del guardado y la publicación">
        {tone === "pending" ? <span className="save-status__dot" aria-hidden="true" /> : <Icon name={icon} size={16} />}
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
      {needsPublishing && !onReview && (
        <LinkButton size="small" variant="primary" to={reviewPath}>
          Revisar y publicar
        </LinkButton>
      )}
    </div>
  );
}

function describe(save: SaveState, dirty: boolean, publication: PublicationState): { icon: IconName; text: string; tone: string } {
  if (save.status === "saving") return { icon: "cloudCheck", text: "Guardando…", tone: "saving" };
  if (save.status === "error") return { icon: "alert", text: "No se pudo guardar", tone: "error" };
  if (dirty) return { icon: "alert", text: "Cambios sin guardar", tone: "idle" };
  // Primero confirma el guardado; después, si falta publicarlo para que los clientes lo vean.
  const saved = save.savedAt ? `Guardado · ${formatTime(save.savedAt)} · ` : "";
  if (publication === "pending") return { icon: "alert", text: `${saved}Cambios sin publicar`, tone: "pending" };
  if (publication === "never" && save.savedAt) return { icon: "alert", text: `${saved}Sin publicar todavía`, tone: "pending" };
  if (publication === "published") return { icon: "check", text: "Publicado · es lo que responde a tus clientes", tone: "saved" };
  return save.savedAt ? { icon: "cloudCheck", text: `Guardado · ${formatTime(save.savedAt)}`, tone: "saved" } : { icon: "cloudCheck", text: "Sin cambios todavía", tone: "idle" };
}
