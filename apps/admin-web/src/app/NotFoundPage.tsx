import { LinkButton } from "../components/ui/Button";
import { EmptyState } from "../components/ui/Feedback";
import { BUSINESSES_PATH } from "../navigation/navItems";

export function NotFoundPage() {
  return (
    <EmptyState
      title="Esta página no existe"
      description="Puede que el enlace esté incompleto."
      action={
        <LinkButton to={BUSINESSES_PATH} variant="primary">
          Ver todos los negocios
        </LinkButton>
      }
    />
  );
}
