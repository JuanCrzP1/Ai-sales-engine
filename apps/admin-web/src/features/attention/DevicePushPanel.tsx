import { Button } from "../../components/ui/Button";
import { Alert, Badge } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { useDevicePush } from "../../state/useDevicePush";

/** Las notificaciones en este navegador o celular: activarlas, probarlas o quitarlas. Cada persona las activa en cada dispositivo. */
export function DevicePushPanel() {
  const push = useDevicePush();

  return (
    <div className="device-push">
      <div className="device-push__head">
        <span className="device-push__icon" aria-hidden="true">
          <Icon name="bell" size={18} />
        </span>
        <div>
          <p className="device-push__title">Notificaciones en este dispositivo</p>
          <p className="field__hint">Suenan como un mensaje de WhatsApp aunque el panel esté cerrado. Actívalas en cada celular o computador donde atiendes.</p>
        </div>
        {push.subscribed && <Badge tone="success">Activadas</Badge>}
      </div>

      {push.support === "unsupported" && <Alert tone="info" title="Este navegador no puede recibir notificaciones. Usa Chrome, Edge, Firefox o Safari actualizados." />}
      {push.support === "install" && (
        <Alert tone="info" title="En iPhone y iPad, primero instala el panel">
          Toca Compartir → «Agregar a pantalla de inicio» y abre el panel desde ese ícono. Ahí podrás activar las notificaciones.
        </Alert>
      )}
      {push.support === "supported" && push.permission === "denied" && (
        <Alert tone="warning" title="Bloqueaste las notificaciones para este sitio.">
          Permítelas en la configuración del navegador (el candado junto a la dirección) y vuelve a intentarlo.
        </Alert>
      )}
      {push.support === "supported" && push.subscribed === null && <p className="field__hint">Revisando este dispositivo…</p>}
      {push.support === "supported" && push.subscribed === false && push.permission !== "denied" && (
        <div>
          <Button size="small" onClick={() => void push.enable()} disabled={push.busy}>
            {push.busy ? "Activando…" : "Activar notificaciones"}
          </Button>
        </div>
      )}
      {push.subscribed && (
        <div className="device-push__actions">
          <Button variant="secondary" size="small" onClick={() => void push.test()} disabled={push.busy}>
            Enviar una prueba
          </Button>
          <Button variant="secondary" size="small" onClick={() => void push.disable()} disabled={push.busy}>
            Desactivar aquí
          </Button>
        </div>
      )}
      {push.notice && <Alert tone={push.notice.ok ? "success" : "danger"} title={push.notice.message} />}
    </div>
  );
}
