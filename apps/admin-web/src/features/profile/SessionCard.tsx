import { useState } from "react";
import { Button } from "../../components/ui/Button";
import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { Alert } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { Card } from "../../components/ui/Layout";
import { authErrorMessage } from "../../domain/auth/messages";
import { useAuth } from "../../state/auth/useAuth";

const DATE_FORMAT: Intl.DateTimeFormatOptions = { dateStyle: "long", timeStyle: "short" };

/** La sesión de este equipo, cerrarla, y cerrar la de todos los demás (por si se quedó abierta en un equipo ajeno o perdido). */
export function SessionCard() {
  const { session, signOut, signOutOtherDevices } = useAuth();
  const [result, setResult] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);
  if (!session) return null;

  const closeOthers = async () => {
    setBusy(true);
    setResult(null);
    try {
      await signOutOtherDevices();
      setResult({ ok: true, text: "Listo: cerramos tu sesión en los demás equipos. Este sigue abierto." });
    } catch (caught) {
      setResult({ ok: false, text: authErrorMessage(caught) });
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card icon="user" tone="sky" title="Sesiones" description="Cierra sesión cuando termines, sobre todo en equipos compartidos.">
      <dl className="summary-list">
        <div className="summary-list__row">
          <dt>Sesión en este equipo</dt>
          <dd>Desde el {new Date(session.startedAt).toLocaleString("es-CO", DATE_FORMAT)}</dd>
        </div>
        <div className="summary-list__row">
          <dt>Cuenta creada</dt>
          <dd>{new Date(session.user.createdAt).toLocaleString("es-CO", DATE_FORMAT)}</dd>
        </div>
      </dl>
      {result && <Alert tone={result.ok ? "success" : "danger"} title={result.text} />}
      <div className="button-row">
        <ConfirmButton variant="secondary" size="default" confirmLabel="Sí, cerrarlas" onConfirm={() => { if (!busy) void closeOthers(); }}>
          Cerrar sesión en los demás equipos
        </ConfirmButton>
        <Button variant="secondary" onClick={() => void signOut()}>
          <Icon name="logout" size={16} />
          Cerrar sesión aquí
        </Button>
      </div>
    </Card>
  );
}
