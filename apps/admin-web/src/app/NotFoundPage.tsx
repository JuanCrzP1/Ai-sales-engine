import { LinkButton } from "../components/ui/Button";
import { EmptyState } from "../components/ui/Feedback";
import { HOME_ITEM } from "../navigation/navItems";

export function NotFoundPage() {
  return (
    <EmptyState
      title="Esta página no existe"
      description="Puede que el enlace esté incompleto."
      action={
        <LinkButton to={HOME_ITEM.path} variant="primary">
          Volver al inicio
        </LinkButton>
      }
    />
  );
}
