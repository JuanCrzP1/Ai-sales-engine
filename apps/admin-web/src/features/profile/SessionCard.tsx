import { Button } from "../../components/ui/Button";
import { Icon } from "../../components/ui/Icon";
import { Card } from "../../components/ui/Layout";
import { useAuth } from "../../state/auth/useAuth";

const DATE_FORMAT: Intl.DateTimeFormatOptions = { dateStyle: "long", timeStyle: "short" };

/** Información de la sesión activa y cierre de sesión. */
export function SessionCard() {
  const { session, signOut } = useAuth();
  if (!session) return null;

  return (
    <Card title="Sesión" description="Cierra sesión cuando termines, sobre todo en equipos compartidos.">
      <dl className="summary-list">
        <div className="summary-list__row">
          <dt>Sesión iniciada</dt>
          <dd>{new Date(session.startedAt).toLocaleString("es-CO", DATE_FORMAT)}</dd>
        </div>
        <div className="summary-list__row">
          <dt>Cuenta creada</dt>
          <dd>{new Date(session.user.createdAt).toLocaleString("es-CO", DATE_FORMAT)}</dd>
        </div>
      </dl>
      <div className="button-row">
        <Button variant="secondary" onClick={() => void signOut()}>
          <Icon name="logout" size={16} />
          Cerrar sesión
        </Button>
      </div>
    </Card>
  );
}
