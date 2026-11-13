import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { TelegramLogo } from "../../components/brand/TelegramLogo";
import { Button } from "../../components/ui/Button";
import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { CopyButton } from "../../components/ui/CopyButton";
import { Dialog } from "../../components/ui/Dialog";
import { Alert, Badge } from "../../components/ui/Feedback";
import { TextField } from "../../components/ui/FormFields";
import { Icon } from "../../components/ui/Icon";
import { BOTFATHER_URL } from "../../domain/channels/types";
import { TELEGRAM_ARTICLE } from "../../domain/help/help";
import { helpArticlePath } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useTelegram, type TelegramState } from "../../state/useTelegram";

/**
 * Telegram del negocio: el negocio crea su bot con @BotFather y pega el código aquí. Es oficial y gratis, sin QR ni riesgo de
 * bloqueo. Los clientes escriben al bot (por su enlace t.me) y sus chats llegan a Conversaciones.
 */
export function TelegramChannelCard() {
  const telegram = useTelegram();
  const { channel, error, busy } = telegram;
  const [dialog, setDialog] = useState<"connect" | "change" | null>(null);
  const hasBot = Boolean(channel?.botUsername);
  const connected = channel?.status === "connected" && hasBot;

  const open = (mode: "connect" | "change") => {
    telegram.clearErrors();
    setDialog(mode);
  };

  return (
    <section className="whatsapp-card telegram-card" aria-labelledby="telegram-title">
      <header className="whatsapp-card__header">
        <span className="whatsapp-card__logo telegram-card__logo">
          <TelegramLogo size={30} />
        </span>
        <div className="whatsapp-card__heading">
          <h2 id="telegram-title" className="whatsapp-card__title">
            Telegram {connected ? <Badge tone="success">Conectado</Badge> : hasBot ? <Badge tone="danger">No recibe mensajes</Badge> : <Badge tone="neutral">No conectado</Badge>}
          </h2>
          <p className="whatsapp-card__description">Tu asistente atiende a quien le escriba al bot de tu negocio en Telegram. Es oficial y gratis: sin código QR ni riesgo de bloqueo.</p>
        </div>
      </header>

      {error && !dialog && <Alert tone="danger">{error}</Alert>}
      {channel === null && !error && (
        <p className="field__hint" role="status">
          Cargando…
        </p>
      )}

      {channel && !channel.available && !hasBot && (
        <Alert tone="info" title="Muy pronto">
          <p>Telegram todavía no está activo en esta plataforma. Cuando lo esté, aquí podrás conectar el bot de tu negocio en un par de minutos.</p>
        </Alert>
      )}

      {channel?.available && !hasBot && (
        <div className="whatsapp-card__start">
          <ol className="whatsapp-card__how telegram-card__how">
            <li>En Telegram, abre @BotFather y envíale /newbot para crear el bot de tu negocio.</li>
            <li>Copia el código que te da y pégalo aquí.</li>
            <li>Listo: comparte el enlace del bot y tu asistente responde.</li>
          </ol>
          <div className="button-row">
            <Button onClick={() => open("connect")}>
              <Icon name="send" size={16} /> Conectar Telegram
            </Button>
          </div>
        </div>
      )}

      {channel && hasBot && !connected && (
        <div className="telegram-card__problem">
          <Alert tone="danger" title={`@${channel.botUsername} no está recibiendo mensajes`}>
            <p>{channel.problem ?? "Tu bot dejó de recibir los mensajes aquí."}</p>
          </Alert>
          <div className="button-row">
            <Button size="small" onClick={() => void telegram.reconnect()} disabled={busy}>
              {busy ? "Conectando…" : "Volver a conectar"}
            </Button>
            <Button size="small" variant="secondary" onClick={() => open("change")} disabled={busy}>
              Pegar un código nuevo
            </Button>
            <ConfirmButton confirmLabel="Sí, desconectar" onConfirm={() => void telegram.disconnect()}>
              Desconectar
            </ConfirmButton>
          </div>
        </div>
      )}

      {channel && connected && (
        <div className="whatsapp-card__connected telegram-card__connected">
          <span className="whatsapp-card__check telegram-card__check">
            <Icon name="check" size={22} />
          </span>
          <div>
            <p className="whatsapp-card__connected-title">
              Conectado como @{channel.botUsername}
              {channel.botName && <> · {channel.botName}</>}
            </p>
            <p className="field__hint">Los mensajes al bot llegan a Conversaciones y tu asistente los responde. Comparte este enlace para que tus clientes te escriban:</p>
            {channel.link && (
              <div className="telegram-card__link">
                <a href={channel.link} target="_blank" rel="noreferrer">
                  {channel.link.replace("https://", "")}
                </a>
                <CopyButton text={channel.link} label="Copiar enlace" />
              </div>
            )}
          </div>
          <div className="button-row">
            <Button size="small" variant="secondary" onClick={() => void telegram.check()} disabled={busy}>
              {busy ? "Revisando…" : "Revisar conexión"}
            </Button>
            <Button size="small" variant="ghost" onClick={() => open("change")} disabled={busy}>
              Cambiar de bot
            </Button>
            <ConfirmButton confirmLabel="Sí, desconectar" onConfirm={() => void telegram.disconnect()}>
              Desconectar
            </ConfirmButton>
          </div>
        </div>
      )}

      {dialog && <ConnectTelegramDialog telegram={telegram} changing={dialog === "change"} onClose={() => setDialog(null)} />}
    </section>
  );
}

/** La ventana para pegar el código de @BotFather, con los pasos ahí mismo. */
function ConnectTelegramDialog({ telegram, changing, onClose }: { telegram: TelegramState; changing: boolean; onClose: () => void }) {
  const pathTo = useWorkspacePath();
  const [token, setToken] = useState("");
  const { busy, error, tokenError } = telegram;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (await telegram.connect(token)) onClose();
  };

  return (
    <Dialog
      title={changing ? "Cambiar el bot de Telegram" : "Conectar Telegram"}
      description={changing ? "Pega el código del bot nuevo (o el código nuevo de tu bot). Los chats que ya tienes se quedan." : "Te toma un par de minutos. Necesitas Telegram en tu celular o computador."}
      onClose={busy ? () => undefined : onClose}
      footer={
        <>
          <Button variant="ghost" disabled={busy} onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" form="telegram-form" disabled={busy}>
            {busy ? "Conectando…" : "Conectar"}
          </Button>
        </>
      }
    >
      <form id="telegram-form" className="form-stack" onSubmit={(event) => void submit(event)} noValidate>
        <ol className="telegram-steps">
          <li>
            <span>
              En Telegram abre <strong>@BotFather</strong> (el de la insignia azul) y toca <strong>Iniciar</strong>.
            </span>
            <a className="button button--secondary button--small telegram-steps__open" href={BOTFATHER_URL} target="_blank" rel="noreferrer">
              Abrir @BotFather <Icon name="link" size={14} />
            </a>
          </li>
          <li>
            <span>Envíale este mensaje:</span>
            <span className="telegram-steps__command">
              <code>/newbot</code>
              <CopyButton text="/newbot" label="Copiar" />
            </span>
          </li>
          <li>
            <span>
              Te pide el <strong>nombre</strong>: escribe el de tu negocio. Por ejemplo: <code>Café Aroma</code>
            </span>
          </li>
          <li>
            <span>
              Te pide el <strong>usuario</strong>: debe terminar en «bot». Por ejemplo: <code>CafeAromaBot</code>
            </span>
          </li>
          <li>
            <span>
              Te responde con un <strong>código</strong> que se ve así: <code>7123456789:AAH…</code> Cópialo completo y pégalo aquí abajo.
            </span>
          </li>
        </ol>
        <TextField label="Código del bot" value={token} placeholder="7123456789:AAH..." required error={tokenError ?? undefined} onChange={setToken} />
        {error && <Alert tone="danger">{error}</Alert>}
        <p className="field__hint">
          El código queda guardado cifrado y nunca se vuelve a mostrar. ¿Dudas?{" "}
          <Link to={pathTo(helpArticlePath(TELEGRAM_ARTICLE))} onClick={onClose}>
            Ver la guía paso a paso
          </Link>
        </p>
      </form>
    </Dialog>
  );
}
