import { LinkButton } from "../components/ui/Button";
import { EmptyState } from "../components/ui/Feedback";
import { ENTRY_PATH } from "../navigation/navItems";

export function NotFoundPage() {
  return (
    <EmptyState
      title="Esta página no existe"
      description="Puede que el enlace esté incompleto."
      action={
        <LinkButton to={ENTRY_PATH} variant="primary">
          Volver al panel
        </LinkButton>
      }
    />
  );
}
