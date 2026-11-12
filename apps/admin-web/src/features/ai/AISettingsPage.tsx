import { useEffect, useState, type FormEvent } from "react";
import { Button, LinkButton } from "../../components/ui/Button";
import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { Alert, Badge } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { IntegrationMark, type IntegrationMarkKind } from "../../components/brand/IntegrationMark";
import { Card, PageHeader } from "../../components/ui/Layout";
import { PasswordField } from "../../components/ui/PasswordField";
import { LoadingScreen } from "../../layout/StatusScreen";
import { PLAYGROUND_ITEM } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useAISettings } from "../../state/useAISettings";
import { AIUsageCard } from "./AIUsageCard";
import { ModelPicker } from "./ModelPicker";

interface Provider {
  id: string;
  name: string;
  description: string;
  mark: IntegrationMarkKind;
  available: boolean;
}

/** Los proveedores de IA. Hoy, OpenRouter (da acceso a los modelos de todos los demás con una sola clave); los otros, pronto. */
const PROVIDERS: Provider[] = [
  { id: "openrouter", name: "OpenRouter", description: "Modelos de OpenAI, Google, Anthropic y más con una sola clave.", mark: "openrouter", available: true },
  { id: "openai", name: "OpenAI", description: "GPT con tu clave de OpenAI.", mark: "openai", available: false },
  { id: "anthropic", name: "Anthropic", description: "Claude con tu clave de Anthropic.", mark: "anthropic", available: false },
  { id: "google", name: "Google Gemini", description: "Gemini con tu clave de Google AI Studio.", mark: "gemini", available: false },
];

/** La clave guardada, oculta: el comienzo de las claves de OpenRouter y sus últimos caracteres. */
function maskedKey(hint: string | null | undefined): string {
  const last = (hint ?? "").replace(/[^A-Za-z0-9]/g, "");
  return `sk-or-v1-${"•".repeat(24)}${last}`;
}

/**
 * Configuración → Inteligencia artificial: con qué proveedor responde el asistente, su clave (cifrada: nunca se vuelve a mostrar
 * completa, como en OpenAI o Stripe) y el modelo. Cada parte se guarda por separado.
 */
export function AISettingsPage() {
  const ai = useAISettings();
  const pathTo = useWorkspacePath();
  const [model, setModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [editingKey, setEditingKey] = useState(false);
  const [lastSaved, setLastSaved] = useState<"key" | "model" | null>(null);
  const configured = ai.settings?.key.configured ?? false;
  const savedModel = ai.settings?.model ?? "";

  useEffect(() => {
    if (ai.settings) setModel(ai.settings.model ?? "");
  }, [ai.settings]);

  if (ai.status === "loading") return <LoadingScreen label="Cargando la inteligencia artificial…" />;

  const saveKey = async (event: FormEvent) => {
    event.preventDefault();
    setLastSaved(null);
    if (await ai.save({ model: savedModel, apiKey })) {
      setApiKey("");
      setEditingKey(false);
      setLastSaved("key");
    }
  };
  const saveModel = async () => {
    setLastSaved(null);
    if (await ai.save({ model, apiKey: "" })) setLastSaved("model");
  };
  const keyProblem = ai.problems.api_key;
  const modelProblem = ai.problems.model;
  const generalError = ai.error && !keyProblem && !modelProblem ? ai.error : null;
  const showKeyForm = !configured || editingKey;

  return (
    <>
      <PageHeader title="Inteligencia artificial" description="Con qué IA responde el asistente de este negocio. El consumo se cobra en tu propia cuenta del proveedor." />

      {ai.status === "error" && (
        <Alert tone="danger" title={ai.error ?? "No se pudo cargar."}>
          <Button variant="secondary" size="small" onClick={ai.reload}>
            Reintentar
          </Button>
        </Alert>
      )}

      {ai.status === "ready" && (
        <div className="settings-stack">
          <Card icon="plug" tone="indigo" title="Proveedor" description="La empresa que da acceso a los modelos de IA.">
            <div className="provider-grid" role="radiogroup" aria-label="Proveedor de IA">
              {PROVIDERS.map((provider) => (
                <div
                  key={provider.id}
                  role="radio"
                  aria-label={provider.available ? provider.name : `${provider.name}, próximamente`}
                  aria-checked={provider.available}
                  aria-disabled={!provider.available}
                  className={`provider-tile${provider.available ? " provider-tile--selected" : " provider-tile--soon"}`}
                >
                  <IntegrationMark kind={provider.mark} size="md" />
                  <span className="provider-tile__text">
                    <span className="provider-tile__name">
                      {provider.name}
                      {provider.available ? (
                        configured ? (
                          <Badge tone="success">Conectado</Badge>
                        ) : (
                          <Badge tone="warning">Falta la clave</Badge>
                        )
                      ) : (
                        <span className="soon-badge">Pronto</span>
                      )}
                    </span>
                    <span className="provider-tile__description">{provider.description}</span>
                  </span>
                  {provider.available && (
                    <span className="provider-tile__check" aria-hidden="true">
                      <Icon name="check" size={16} />
                    </span>
                  )}
                </div>
              ))}
            </div>
          </Card>

          <Card
            icon="shield"
            tone="emerald"
            title="Clave de API de OpenRouter"
            description="Se guarda cifrada. Sin clave, el asistente de este negocio no puede responder."
            badge={configured ? <Badge tone="success">Guardada</Badge> : <Badge tone="warning">Sin clave</Badge>}
          >
            {!showKeyForm && (
              <div className="form-stack">
                <div className="key-display" aria-label="Clave guardada">
                  <Icon name="shield" size={16} />
                  <code className="key-display__value">{maskedKey(ai.settings?.key.hint)}</code>
                  <Button variant="secondary" size="small" onClick={() => setEditingKey(true)}>
                    Cambiar clave
                  </Button>
                </div>
                <p className="field__hint">
                  Por seguridad, una clave guardada nunca se vuelve a mostrar completa (así lo hacen OpenAI, Stripe y OpenRouter). Si
                  la necesitas, la ves en openrouter.ai; para cambiarla, pega una nueva.
                </p>
                <div className="form-actions">
                  <Button variant="secondary" onClick={() => void ai.verify()} disabled={ai.checking}>
                    {ai.checking ? "Comprobando…" : "Comprobar la clave"}
                  </Button>
                  <ConfirmButton confirmLabel="Sí, quitar la clave" onConfirm={() => void ai.save({ model: savedModel, apiKey: "", clearKey: true })}>
                    Quitar la clave
                  </ConfirmButton>
                </div>
              </div>
            )}

            {showKeyForm && (
              <form className="form-stack" onSubmit={saveKey} noValidate>
                <PasswordField
                  label={configured ? "Nueva clave de OpenRouter" : "Clave de OpenRouter"}
                  value={apiKey}
                  onChange={setApiKey}
                  autoComplete="new-password"
                  required={!configured}
                  hint="Empieza por sk-or-. La creas en openrouter.ai → Keys. Con el ojo ves lo que pegaste antes de guardar."
                  error={keyProblem}
                />
                <div className="form-actions">
                  <Button type="submit" disabled={ai.saving || !apiKey.trim()}>
                    {ai.saving ? "Guardando…" : "Guardar clave"}
                  </Button>
                  {configured && (
                    <Button
                      variant="secondary"
                      onClick={() => {
                        setEditingKey(false);
                        setApiKey("");
                      }}
                    >
                      Cancelar
                    </Button>
                  )}
                </div>
              </form>
            )}

            {ai.check && <Alert tone={ai.check.valid ? "success" : "danger"} title={ai.check.message} />}
            {lastSaved === "key" && ai.saved && <Alert tone="success" title="Clave guardada. El asistente de este negocio ya la usa." />}
          </Card>

          <Card icon="robot" tone="violet" title="Modelo" description="El cerebro del asistente: cada uno responde distinto y cuesta distinto.">
            <div className="form-stack">
              <ModelPicker value={model} onChange={setModel} error={modelProblem} />
              <div className="form-actions">
                <Button onClick={() => void saveModel()} disabled={ai.saving || model === savedModel}>
                  {ai.saving ? "Guardando…" : "Guardar modelo"}
                </Button>
                {model !== savedModel && (
                  <Button variant="secondary" onClick={() => setModel(savedModel)}>
                    Deshacer
                  </Button>
                )}
              </div>
              {lastSaved === "model" && ai.saved && <Alert tone="success" title="Guardado. El asistente de este negocio ya usa este modelo." />}
            </div>
          </Card>

          {generalError && <Alert tone="danger" title={generalError} />}

          <AIUsageCard />

          {configured && (
            <Card icon="flask" tone="sky" title="Pruébalo" description="Conversa con tu asistente como si fueras un cliente, antes de que lo hagan tus clientes.">
              <LinkButton to={pathTo(PLAYGROUND_ITEM.path)}>Probar asistente</LinkButton>
            </Card>
          )}
        </div>
      )}
    </>
  );
}
