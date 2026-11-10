import { useEffect, useState, type FormEvent } from "react";
import { Button, LinkButton } from "../../components/ui/Button";
import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { Alert, Badge } from "../../components/ui/Feedback";
import { TextField } from "../../components/ui/FormFields";
import { Card, PageHeader } from "../../components/ui/Layout";
import { PasswordField } from "../../components/ui/PasswordField";
import { LoadingScreen } from "../../layout/StatusScreen";
import { PLAYGROUND_ITEM } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useAISettings } from "../../state/useAISettings";

/** La clave de OpenRouter de este negocio y el modelo de su asistente. La clave nunca se vuelve a mostrar completa. */
export function AISettingsPage() {
  const ai = useAISettings();
  const pathTo = useWorkspacePath();
  const [model, setModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const configured = ai.settings?.key.configured ?? false;

  useEffect(() => {
    if (ai.settings) setModel(ai.settings.model ?? "");
  }, [ai.settings]);

  if (ai.status === "loading") return <LoadingScreen label="Cargando la inteligencia artificial…" />;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (await ai.save({ model, apiKey })) setApiKey("");
  };

  return (
    <>
      <PageHeader
        eyebrow="Asistente"
        title="Inteligencia artificial"
        description="Cada negocio responde con su propia clave de OpenRouter: el consumo de su asistente se cobra en esa cuenta."
      />

      {ai.status === "error" && (
        <Alert tone="danger" title={ai.error ?? "No se pudo cargar."}>
          <Button variant="secondary" size="small" onClick={ai.reload}>
            Reintentar
          </Button>
        </Alert>
      )}

      {ai.status === "ready" && (
        <Card
          title="Clave de OpenRouter"
          description="Se guarda cifrada y nunca se vuelve a mostrar completa. Sin clave, el asistente de este negocio no puede responder."
          actions={
            configured ? <Badge tone="success">Configurada {ai.settings?.key.hint}</Badge> : <Badge tone="warning">Sin clave</Badge>
          }
        >
          <form className="form-stack" onSubmit={submit} noValidate>
            <PasswordField
              label={configured ? "Nueva clave (solo si quieres cambiarla)" : "Clave de OpenRouter"}
              value={apiKey}
              onChange={setApiKey}
              autoComplete="new-password"
              required={!configured}
              hint="Empieza por sk-or-. La encuentras en openrouter.ai, en Keys."
              error={ai.problems.api_key}
            />
            <TextField
              label="Modelo"
              value={model}
              onChange={setModel}
              placeholder="openai/gpt-4o-mini"
              hint="Como aparece en OpenRouter. Déjalo vacío para usar el modelo predeterminado del sistema."
              error={ai.problems.model}
            />
            {ai.error && Object.keys(ai.problems).length === 0 && <Alert tone="danger" title={ai.error} />}
            {ai.saved && <Alert tone="success" title="Guardado. El asistente de este negocio ya usa esta configuración." />}
            {ai.check && <Alert tone={ai.check.valid ? "success" : "danger"} title={ai.check.message} />}
            <div className="form-actions">
              <Button type="submit" disabled={ai.saving || (!configured && !apiKey.trim())}>
                {ai.saving ? "Guardando…" : "Guardar"}
              </Button>
              <Button variant="secondary" onClick={() => void ai.verify()} disabled={!configured || ai.checking}>
                {ai.checking ? "Comprobando…" : "Comprobar la clave"}
              </Button>
              {configured && (
                <ConfirmButton confirmLabel="Sí, quitar la clave" onConfirm={() => void ai.save({ model, apiKey: "", clearKey: true })}>
                  Quitar la clave
                </ConfirmButton>
              )}
            </div>
          </form>
        </Card>
      )}

      {configured && (
        <Card title="Pruébalo" description="Conversa con tu asistente como si fueras un cliente, antes de que lo hagan tus clientes.">
          <LinkButton to={pathTo(PLAYGROUND_ITEM.path)}>Probar asistente</LinkButton>
        </Card>
      )}
    </>
  );
}
