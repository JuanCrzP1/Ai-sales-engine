import { useCallback, useEffect, useState, type FormEvent } from "react";
import { WhatsAppLogo } from "../../components/brand/WhatsAppLogo";
import { Button } from "../../components/ui/Button";
import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { Alert, Badge } from "../../components/ui/Feedback";
import { TextField } from "../../components/ui/FormFields";
import { Icon, type IconName } from "../../components/ui/Icon";
import { PasswordField } from "../../components/ui/PasswordField";
import type { WhatsAppChannel } from "../../domain/channels/types";
import { useChannels } from "../../state/channelsContext";
import { PersistenceError, persistenceErrorMessage } from "../../state/directoryContext";

/** Cada cuánto se pregunta por el estado mientras se espera el escaneo, y cuánto se espera antes de pedir un código nuevo. */
const POLL_MS = 3000;
const QR_TIMEOUT_MS = 120_000;
const DEFAULT_SERVER = "https://free.uazapi.com";

type Method = "qr" | "official";
type Problem = { general?: string; server_url?: string; token?: string };

function problemsOf(error: unknown): Problem {
  const problems = error instanceof PersistenceError ? error.problems : [];
  const field = (path: string) => problems.find((problem) => problem.path === path)?.message;
  const found = { server_url: field("server_url"), token: field("token") };
  return found.server_url || found.token ? found : { general: persistenceErrorMessage(error) };
}

function formatPhone(digits: string | null): string {
  return digits ? `+${digits}` : "";
}

/** WhatsApp del negocio: conectar por código QR (uazapi) o, más adelante, con la API oficial de Meta. */
export function WhatsAppChannelCard() {
  const channels = useChannels();
  const [channel, setChannel] = useState<WhatsAppChannel | null>(null);
  const [method, setMethod] = useState<Method>("qr");
  const [problem, setProblem] = useState<Problem>({});
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState(false);
  const [expired, setExpired] = useState(false);

  const run = useCallback(async (action: () => Promise<WhatsAppChannel | void>) => {
    setBusy(true);
    setProblem({});
    try {
      const next = await action();
      if (next) setChannel(next);
      return true;
    } catch (error) {
      setProblem(problemsOf(error));
      return false;
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    channels.whatsapp().then(
      (loaded) => active && setChannel(loaded),
      (error: unknown) => active && setProblem(problemsOf(error)),
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
            description="Escaneas un código desde tu teléfono y listo. Usa un servidor de uazapi."
            checked={method === "qr"}
            onSelect={() => setMethod("qr")}
          />
          <MethodOption icon="building" title="API oficial de Meta" description="Para empresas verificadas por Meta, con número propio." soon checked={method === "official"} onSelect={() => undefined} />
        </div>
      )}

      {problem.general && <Alert tone="danger">{problem.general}</Alert>}
      {channel === null && !problem.general && (
        <p className="field__hint" role="status">
          Cargando…
        </p>
      )}

      {channel && channel.configured && !channel.webhookReady && (
        <Alert tone="warning" title="Los mensajes todavía no llegan al asistente">
          <p>Falta la dirección pública del motor para recibirlos. En este equipo, inicia todo con ./run_local.sh (toma la de ngrok); en la nube se configura sola.</p>
        </Alert>
      )}

      {channel && (!channel.configured || editing) && (
        <SetupForm
          initialServer={channel.serverUrl ?? DEFAULT_SERVER}
          busy={busy}
          problem={problem}
          onCancel={editing ? () => setEditing(false) : undefined}
          onSave={async (input) => {
            const saved = await run(() => channels.saveWhatsApp(input));
            if (saved) {
              setEditing(false);
              await run(() => channels.connectWhatsApp());
            }
          }}
        />
      )}

      {channel?.configured && !editing && status === "disconnected" && (
        <div className="whatsapp-card__ready">
          <p className="whatsapp-card__meta">
            Servidor <strong>{channel.serverUrl}</strong> · token <strong>{channel.tokenHint}</strong>
          </p>
          <div className="button-row">
            <Button onClick={() => run(() => channels.connectWhatsApp())} disabled={busy}>
              <Icon name="qr" size={16} /> {busy ? "Generando código…" : "Mostrar código QR"}
            </Button>
            <Button variant="ghost" onClick={() => setEditing(true)} disabled={busy}>
              Cambiar servidor o token
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
                <Button size="small" onClick={() => run(() => channels.connectWhatsApp())} disabled={busy}>
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

      {channel?.configured && !editing && status !== "connecting" && (
        <div className="whatsapp-card__footer">
          <ConfirmButton confirmLabel="Sí, quitar la conexión" onConfirm={() => run(() => channels.removeWhatsApp().then(() => channels.whatsapp()))}>
            Quitar la conexión y sus datos
          </ConfirmButton>
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

function SetupForm({ initialServer, busy, problem, onSave, onCancel }: { initialServer: string; busy: boolean; problem: Problem; onSave: (input: { serverUrl: string; token: string }) => void; onCancel?: () => void }) {
  const [serverUrl, setServerUrl] = useState(initialServer);
  const [token, setToken] = useState("");
  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSave({ serverUrl: serverUrl.trim(), token: token.trim() });
  };
  return (
    <form className="whatsapp-setup" aria-label="Conectar WhatsApp por código QR" noValidate onSubmit={submit}>
      <div className="grid-2">
        <TextField label="Servidor de uazapi" required value={serverUrl} onChange={setServerUrl} placeholder={DEFAULT_SERVER} error={problem.server_url} hint="La dirección de tu servidor, empezando por https://." />
        <PasswordField
          label="Token"
          required
          value={token}
          onChange={setToken}
          autoComplete="new-password"
          error={problem.token}
          hint="El de tu instancia o el de administrador del servidor: con el de administrador creamos la instancia de tu negocio. Se guarda cifrado."
        />
      </div>
      <Alert tone="info">
        <p>
          Es una conexión no oficial: usa el número de WhatsApp Business de tu negocio y evita los envíos masivos, porque WhatsApp puede bloquear los números
          que los hacen.
        </p>
      </Alert>
      <div className="button-row">
        <Button type="submit" disabled={busy || !serverUrl.trim() || !token.trim()}>
          {busy ? "Conectando…" : "Guardar y mostrar el código QR"}
        </Button>
        {onCancel && (
          <Button variant="ghost" onClick={onCancel} disabled={busy}>
            Cancelar
          </Button>
        )}
      </div>
    </form>
  );
}
