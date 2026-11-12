import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { ChatPreview } from "../../components/ui/ChatPreview";
import { RadioGroup } from "../../components/ui/ChoiceGroup";
import { Alert } from "../../components/ui/Feedback";
import { SelectField, TextField } from "../../components/ui/FormFields";
import { Card, PageHeader } from "../../components/ui/Layout";
import { Toggle } from "../../components/ui/Toggle";
import { hoursText, waitNotice, waitText, type AttentionSettings, type HoursMode } from "../../domain/attention/types";
import { LoadingScreen } from "../../layout/StatusScreen";
import { sectionPath } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useAttentionSettings } from "../../state/useAttentionSettings";
import { DevicePushPanel } from "./DevicePushPanel";
import { TeamHoursEditor } from "./TeamHoursEditor";

const NEVER = "nunca";

function minutesLabel(minutes: number): string {
  if (minutes < 60) return `${minutes} minutos`;
  return minutes === 60 ? "1 hora" : `${minutes / 60} horas`;
}

/** Las horas terminan en «a. m.»: no se les agrega otro punto. */
function sentence(text: string): string {
  return text.endsWith(".") ? text : `${text}.`;
}

function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** Cuándo vuelve el equipo, en la zona del negocio: «mañana, 8:00 a. m.». */
function nextOpeningText(iso: string, timezone: string): string {
  const moment = new Date(iso);
  const day = (date: Date) => date.toLocaleDateString("en-CA", { timeZone: timezone });
  const today = new Date();
  const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000);
  const time = moment.toLocaleTimeString("es-CO", { timeZone: timezone, hour: "numeric", minute: "2-digit" });
  if (day(moment) === day(today)) return `hoy a las ${time}`;
  if (day(moment) === day(tomorrow)) return `mañana a las ${time}`;
  return `el ${moment.toLocaleDateString("es-CO", { timeZone: timezone, weekday: "long" })} a las ${time}`;
}

/**
 * Configuración → Atención humana: el horario del equipo, lo que ve el cliente cuando su chat pasa a una persona, cuándo retoma la IA un chat
 * que nadie atendió y cómo se avisa al equipo. Se aplica al instante; los mensajes que dice el asistente están en Asistente IA → Mensajes.
 */
export function AttentionSettingsPage() {
  const attention = useAttentionSettings();
  const pathTo = useWorkspacePath();
  const [form, setForm] = useState<AttentionSettings | null>(null);
  const { view, problems } = attention;

  useEffect(() => {
    if (!view) return;
    setForm({
      hoursMode: view.hoursMode,
      teamHours: view.teamHours,
      timezone: view.timezone,
      replyMinutes: view.replyMinutes,
      resumeAfterMinutes: view.resumeAfterMinutes,
      emailEnabled: view.emailEnabled,
      emailTo: view.emailTo,
    });
  }, [view]);

  // Hasta que el formulario tenga los ajustes cargados, sigue «cargando» (sin mostrar un error que no existe).
  if (attention.status === "loading" || (attention.status === "ready" && !form)) return <LoadingScreen label="Cargando la atención humana…" />;

  const header = (
    <PageHeader
      title="Atención humana"
      description="Qué pasa cuando un cliente necesita a una persona de tu equipo. Se aplica al instante: no hace falta publicar."
    />
  );

  if (attention.status === "error" || !view || !form) {
    return (
      <>
        {header}
        <Alert tone="danger" title={attention.error ?? "No se pudo cargar."}>
          <Button variant="secondary" size="small" onClick={attention.reload}>
            Reintentar
          </Button>
        </Alert>
      </>
    );
  }

  const update = (changes: Partial<AttentionSettings>) => setForm((current) => (current ? { ...current, ...changes } : current));
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    await attention.save(form);
  };
  const accountEmail = view.accountEmails[0];
  const notice = waitNotice(form.replyMinutes);
  const businessHours = view.businessHours.length > 0 ? sentence(capitalize(hoursText(view.businessHours))) : "Tu negocio aún no tiene horario, así que por ahora siempre hay alguien. Escríbelo en Asistente IA → Mi negocio.";

  return (
    <>
      {header}

      <Alert tone={view.teamAvailableNow ? "success" : "info"} title={view.teamAvailableNow ? "Ahora hay alguien de tu equipo" : "Ahora estás fuera del horario"}>
        {view.teamAvailableNow
          ? `Si un chat pasa a una persona, la IA se pausa${view.replyMinutes ? ` y el cliente sabe que le responden en ${waitText(view.replyMinutes)}` : ""}.`
          : `Si un chat pasa a una persona, la IA sigue ayudando y le dice al cliente cuándo lo atienden${view.nextOpening ? ` (${nextOpeningText(view.nextOpening, view.timezone)})` : ""}.`}
      </Alert>

      <form className="settings-stack attention-form" onSubmit={submit} noValidate>
        <Card icon="clock" tone="amber" wide title="Horario del equipo" description="Cuándo hay alguien para atender a los clientes que piden una persona.">
          <RadioGroup<HoursMode>
            legend="¿Cuándo hay alguien de tu equipo?"
            name="hours_mode"
            value={form.hoursMode}
            onChange={(hoursMode) => update({ hoursMode, teamHours: hoursMode === "custom" && form.teamHours.length === 0 ? view.businessHours : form.teamHours })}
            issue={problems.hours_mode ? { severity: "error", message: problems.hours_mode } : undefined}
            options={[
              { value: "business", label: "El mismo horario de «Mi negocio»", hint: businessHours },
              { value: "custom", label: "Otro horario para el equipo", hint: "Por ejemplo, si respondes chats en horas distintas a las del local." },
              { value: "always", label: "Siempre hay alguien", hint: "Cuando un chat pasa a una persona, la IA siempre se pausa." },
            ]}
          />
          {form.hoursMode === "custom" && <TeamHoursEditor value={form.teamHours} onChange={(teamHours) => update({ teamHours })} problems={problems} />}
          <SelectField
            label="Zona horaria"
            value={form.timezone}
            onChange={(timezone) => update({ timezone })}
            options={view.options.timezones.map((zone) => ({ value: zone.id, label: zone.label }))}
            error={problems.timezone}
          />
        </Card>

        <Card icon="chat" tone="sky" title="Lo que ve el cliente" description="Cuando su chat pasa a tu equipo dentro del horario.">
          <SelectField
            label="Le decimos que le responden en…"
            value={String(form.replyMinutes)}
            onChange={(value) => update({ replyMinutes: Number(value) })}
            options={view.options.replyMinutes.map((minutes) => ({ value: String(minutes), label: minutes === 0 ? "No decirle cuánto" : capitalize(waitText(minutes)) }))}
            error={problems.reply_minutes}
          />
          {notice && <ChatPreview lines={[{ from: "assistant", text: notice }]} caption="Lo recibe después de «Te paso con alguien del equipo»." />}
          <p className="field__hint">
            Fuera del horario, el asistente le dice tu horario y cuándo lo atienden. Puedes escribir ese mensaje a tu manera en{" "}
            <Link to={pathTo(sectionPath("messages"))}>Asistente IA → Mensajes</Link>.
          </p>
        </Card>

        <Card icon="robot" tone="violet" title="Si nadie responde" description="Para que ningún cliente quede esperando sin respuesta.">
          <SelectField
            label="La IA retoma el chat si el cliente espera más de…"
            value={form.resumeAfterMinutes === null ? NEVER : String(form.resumeAfterMinutes)}
            onChange={(value) => update({ resumeAfterMinutes: value === NEVER ? null : Number(value) })}
            options={[
              ...view.options.resumeAfterMinutes.map((minutes) => ({ value: String(minutes), label: minutesLabel(minutes) })),
              { value: NEVER, label: "Nunca: el chat espera a tu equipo" },
            ]}
            hint="Le pide disculpas al cliente, responde lo que quedó pendiente y te avisa. El chat sigue marcado para que alguien de tu equipo lo atienda."
            error={problems.resume_after_minutes}
          />
        </Card>

        <Card icon="bell" tone="emerald" wide title="Avisos a tu equipo" description="Además de la campana del panel, para que te enteres aunque no lo tengas abierto.">
          <div className="attention-alerts">
            <div className="form-stack">
              <Toggle
                label="Avisarme por correo"
                description="Cuando un chat pasa a una persona, te llega un correo con lo que pidió el cliente y un botón para abrir el chat."
                checked={form.emailEnabled}
                onChange={(emailEnabled) => update({ emailEnabled })}
              />
              {form.emailEnabled && (
                <TextField
                  label="Correo para los avisos"
                  type="email"
                  value={form.emailTo ?? ""}
                  onChange={(emailTo) => update({ emailTo })}
                  placeholder={accountEmail ?? "equipo@tunegocio.com"}
                  autoComplete="email"
                  hint={accountEmail ? `Déjalo vacío para usar el de tu cuenta (${accountEmail}).` : "El correo adonde llegan los avisos de este negocio."}
                  error={problems.email_to}
                />
              )}
              {!view.emailAvailable && (
                <Alert tone="warning" title="El correo de avisos aún no está activado en la plataforma.">
                  Tus ajustes se guardan y los correos empezarán a llegar apenas se active.
                </Alert>
              )}
              {form.emailEnabled && view.emailAvailable && (
                <div>
                  <Button variant="secondary" size="small" onClick={() => void attention.sendTestEmail()} disabled={attention.sendingEmail}>
                    {attention.sendingEmail ? "Enviando…" : "Enviar correo de prueba"}
                  </Button>
                </div>
              )}
              {attention.emailResult && <Alert tone={attention.emailResult.ok ? "success" : "danger"} title={attention.emailResult.message} />}
            </div>
            <DevicePushPanel />
          </div>
        </Card>

        <div className="form-actions">
          {attention.error && Object.keys(problems).length === 0 && <Alert tone="danger" title={attention.error} />}
          {attention.error && Object.keys(problems).length > 0 && <Alert tone="danger" title={attention.error}>Revisa los campos marcados.</Alert>}
          {attention.saved && <Alert tone="success" title="Guardado. Ya se aplica en tus chats." />}
          <Button type="submit" disabled={attention.saving}>
            {attention.saving ? "Guardando…" : "Guardar"}
          </Button>
        </div>
      </form>
    </>
  );
}
