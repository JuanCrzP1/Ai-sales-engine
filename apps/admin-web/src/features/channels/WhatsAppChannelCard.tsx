import { useCallback, useEffect, useState } from "react";
import { WhatsAppLogo } from "../../components/brand/WhatsAppLogo";
import { Button } from "../../components/ui/Button";
import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { Alert, Badge } from "../../components/ui/Feedback";
import { Icon, type IconName } from "../../components/ui/Icon";
import type { WhatsAppChannel } from "../../domain/channels/types";
import { useChannels } from "../../state/channelsContext";
import { persistenceErrorMessage } from "../../state/directoryContext";

/** Cada cuánto se pregunta por el estado mientras se espera el escaneo, y cuánto se espera antes de pedir un código nuevo. */
const POLL_MS = 3000;
const QR_TIMEOUT_MS = 120_000;

type Method = "qr" | "official";

function formatPhone(digits: string | null): string {
  return digits ? `+${digits}` : "";
}

/**
 * WhatsApp del negocio: conectar por código QR o, más adelante, con la API oficial de Meta. El negocio no configura servidores ni
 * tokens (son de la plataforma): toca «Conectar WhatsApp», escanea el código y listo.
 */
export function WhatsAppChannelCard() {
  const channels = useChannels();
  const [channel, setChannel] = useState<WhatsAppChannel | null>(null);
  const [method, setMethod] = useState<Method>("qr");
  const [problem, setProblem] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [expired, setExpired] = useState(false);

  const run = useCallback(async (action: () => Promise<WhatsAppChannel>) => {
    setBusy(true);
    setProblem(null);
    try {
      setChannel(await action());
    } catch (error) {
      setProblem(persistenceErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    channels.whatsapp().then(
      (loaded) => active && setChannel(loaded),
      (error: unknown) => active && setProblem(persistenceErrorMessage(error)),
    );
    return () => {
      active = false;
    };
  }, [channels]);

  // Mientras se muestra el QR: pregunta por el estado hasta que el negocio lo escanee (el QR vigente cambia cada pocos segundos).
  const connecting = channel?.status === "connecting";
  useEffect(() => {
    if (!connecting) return;
    setExpired(false);
    const started = Date.now();
    const timer = window.setInterval(() => {
      if (Date.now() - started > QR_TIMEOUT_MS) {
        window.clearInterval(timer);
        setExpired(true);
        return;
      }
      channels.whatsAppStatus().then(setChannel, () => undefined);
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [channels, connecting]);

  const status = channel?.status ?? "disconnected";
  const badge = {
    connected: <Badge tone="success">Conectado</Badge>,
    connecting: <Badge tone="warning">Esperando el escaneo</Badge>,
    disconnected: <Badge tone="neutral">No conectado</Badge>,
  }[status];

  return (
    <section className="whatsapp-card" aria-labelledby="whatsapp-title">
      <header className="whatsapp-card__header">
        <span className="whatsapp-card__logo">
          <WhatsAppLogo size={30} />
        </span>
        <div className="whatsapp-card__heading">
          <h2 id="whatsapp-title" className="whatsapp-card__title">
            WhatsApp {badge}
          </h2>
          <p className="whatsapp-card__description">Tu asistente atiende los chats de tu número de WhatsApp, con la versión publicada de tu negocio.</p>
        </div>
      </header>

      {status !== "connected" && (
        <div className="method-picker" role="radiogroup" aria-label="Cómo conectar WhatsApp">
          <MethodOption
            icon="qr"
            title="Código QR"
            description="Escaneas un código desde el teléfono del negocio y listo."
            checked={method === "qr"}
            onSelect={() => setMethod("qr")}
          />
          <MethodOption icon="building" title="API oficial de Meta" description="Para empresas verificadas por Meta, con número propio." soon checked={method === "official"} onSelect={() => undefined} />
        </div>
      )}

      {problem && <Alert tone="danger">{problem}</Alert>}
      {channel === null && !problem && (
        <p className="field__hint" role="status">
          Cargando…
        </p>
      )}

      {channel && !channel.available && status === "disconnected" && (
        <Alert tone="info" title="Muy pronto">
          <p>La conexión de WhatsApp por código QR todavía no está activa. Cuando lo esté, aquí podrás conectar tu número en un minuto.</p>
        </Alert>
      )}

      {channel?.available && status === "disconnected" && method === "qr" && (
        <div className="whatsapp-card__start">
          <ol className="whatsapp-card__how">
            <li>Toca «Conectar WhatsApp» y aparece un código QR.</li>
            <li>Escanéalo desde el WhatsApp del negocio, en Dispositivos vinculados.</li>
            <li>Listo: tu asistente empieza a responder los chats.</li>
          </ol>
          <Alert tone="info">
            <p>Es una conexión no oficial: usa el número de WhatsApp Business de tu negocio y evita los envíos masivos, porque WhatsApp puede bloquear los números que los hacen.</p>
          </Alert>
          <div className="button-row">
            <Button onClick={() => run(() => channels.connectWhatsApp())} disabled={busy}>
              <Icon name="qr" size={16} /> {busy ? "Preparando el código…" : "Conectar WhatsApp"}
            </Button>
          </div>
        </div>
      )}

      {channel && connecting && (
        <div className="qr-panel">
          <div className="qr-panel__code">
            {channel.qrcode && !expired ? <img src={channel.qrcode} alt="Código QR para vincular WhatsApp" width={232} height={232} /> : <span className="qr-panel__placeholder">{expired ? "El código venció" : "Generando el código…"}</span>}
          </div>
          <div className="qr-panel__steps">
            <h3 className="qr-panel__title">Escanéalo con el WhatsApp del negocio</h3>
            <ol>
              <li>Abre WhatsApp en el teléfono del negocio.</li>
              <li>
                Toca <strong>Menú</strong> o <strong>Configuración</strong> y luego <strong>Dispositivos vinculados</strong>.
              </li>
              <li>
                Toca <strong>Vincular un dispositivo</strong> y apunta la cámara a este código.
              </li>
            </ol>
            {channel.paircode && (
              <p className="field__hint">
                O usa el código de vinculación: <strong>{channel.paircode}</strong>
              </p>
            )}
            <p className="field__hint" role="status">
              {expired ? "Pasaron dos minutos sin escanearlo." : "Esperando que lo escanees… esta pantalla se actualiza sola."}
            </p>
            <div className="button-row">
              {expired && (
                <Button size="small" onClick={() => run(() => channels.newWhatsAppCode())} disabled={busy}>
                  Generar otro código
                </Button>
              )}
              <Button size="small" variant="ghost" onClick={() => run(() => channels.disconnectWhatsApp())} disabled={busy}>
                Cancelar
              </Button>
            </div>
          </div>
        </div>
      )}

      {channel && status === "connected" && (
        <div className="whatsapp-card__connected">
          <span className="whatsapp-card__check">
            <Icon name="check" size={22} />
          </span>
          <div>
            <p className="whatsapp-card__connected-title">
              Conectado {channel.phone && <>al {formatPhone(channel.phone)}</>}
              {channel.profileName && <> · {channel.profileName}</>}
            </p>
            <p className="field__hint">Los mensajes de tus clientes llegan a Conversaciones y tu asistente los responde.</p>
          </div>
          <div className="button-row">
            <ConfirmButton confirmLabel="Sí, desconectar" onConfirm={() => run(() => channels.disconnectWhatsApp())}>
              Desconectar
            </ConfirmButton>
          </div>
        </div>
      )}
    </section>
  );
}

function MethodOption({ icon, title, description, checked, soon = false, onSelect }: { icon: IconName; title: string; description: string; checked: boolean; soon?: boolean; onSelect: () => void }) {
  return (
    <label className={`method-option${checked ? " method-option--active" : ""}${soon ? " method-option--soon" : ""}`}>
      <input type="radio" name="whatsapp-method" checked={checked} disabled={soon} onChange={onSelect} />
      <span className="method-option__icon">
        <Icon name={icon} size={20} />
      </span>
      <span className="method-option__text">
        <span className="method-option__title">
          {title} {soon && <Badge tone="neutral">Próximamente</Badge>}
        </span>
        <span className="method-option__description">{description}</span>
      </span>
    </label>
  );
}
