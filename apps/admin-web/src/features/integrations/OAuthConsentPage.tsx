import { useMemo, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { CheckboxGroup, RadioGroup } from "../../components/ui/ChoiceGroup";
import { Alert, EmptyState } from "../../components/ui/Feedback";
import { SelectField } from "../../components/ui/FormFields";
import type { AccessLevel, KeyReach } from "../../domain/integrations/types";
import { useAgentAuthorization } from "../../state/useAgentAuthorization";
import { useMyBusinesses } from "../../state/useMyBusinesses";
import { PermissionMatrix } from "./PermissionMatrix";

const REACH_OPTIONS: { value: KeyReach; label: string; hint: string }[] = [
  { value: "all", label: "Todos mis negocios", hint: "También los que crees después. Necesario para que cree negocios." },
  { value: "some", label: "Algunos", hint: "Los que elijas ahora." },
  { value: "one", label: "Uno solo", hint: "No verá tus otros negocios." },
];

/** Ir al agente (fuera del panel). Aparte, para poder cambiarlo en las pruebas. */
export const leavePanel = { to: (url: string) => window.location.assign(url) };

/**
 * `/oauth/authorize`: un agente (Claude en la web o en la app, ChatGPT) pide conectarse a la cuenta. La persona ve quién lo pide y a
 * dónde volverá, elige a qué negocios entra y qué puede hacer, y autoriza o cancela. La conexión queda en «Claves de API», donde se
 * revoca. Los parámetros de la dirección los puso el agente: el servidor los revisa todos.
 */
export function OAuthConsentPage() {
  const [search] = useSearchParams();
  const params = useMemo(() => Object.fromEntries(search.entries()), [search]);
  const { state, decide } = useAgentAuthorization(params);
  const businesses = useMyBusinesses();
  const [reach, setReach] = useState<KeyReach>("all");
  const [chosen, setChosen] = useState<string[]>([]);
  const [single, setSingle] = useState("");
  const [permissions, setPermissions] = useState<Record<string, AccessLevel>>({ businesses: "write", assistant: "write" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [problems, setProblems] = useState<Record<string, string>>({});

  const finish = async (approve: boolean) => {
    setBusy(true);
    setError(null);
    const selected = reach === "some" ? chosen : reach === "one" ? [single || businesses[0]?.slug].filter(Boolean) : [];
    const result = await decide(approve ? { approve, permissions, reach, businesses: selected as string[] } : { approve });
    if ("redirectTo" in result) {
      leavePanel.to(result.redirectTo);
      return;
    }
    setBusy(false);
    setError(result.error);
    setProblems(result.problems);
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    void finish(true);
  };

  if (state.status === "loading") return <p className="auth__subtitle">Revisando la solicitud…</p>;
  if (state.status === "error") return <Alert tone="danger" title={state.message} />;
  const { prompt } = state;
  if (!prompt.ready) {
    return (
      <div className="form-stack">
        <header className="auth__header">
          <h1 className="auth__title">No se puede conectar</h1>
        </header>
        <Alert tone="danger" title={prompt.message}>
          Vuelve a conectar el agente desde su programa.
        </Alert>
        {prompt.redirectTo && <Button onClick={() => leavePanel.to(prompt.redirectTo!)}>Volver al agente</Button>}
      </div>
    );
  }

  return (
    <form className="form-stack" onSubmit={submit} noValidate>
      <header className="auth__header">
        <h1 className="auth__title">Conectar «{prompt.clientName}»</h1>
        <p className="auth__subtitle">
          Podrá trabajar en tus negocios con lo que elijas aquí. Después volverás a <strong>{prompt.redirectHost}</strong>.
        </p>
      </header>
      <RadioGroup legend="A qué negocios entra" name="reach" options={REACH_OPTIONS} value={reach} onChange={setReach} />
      {reach === "some" &&
        (businesses.length > 0 ? (
          <CheckboxGroup
            legend="Negocios"
            name="businesses"
            options={businesses.map((item) => ({ value: item.slug, label: item.name }))}
            values={chosen}
            onChange={setChosen}
            issue={problems.businesses ? { severity: "error", message: problems.businesses } : undefined}
          />
        ) : (
          <EmptyState title="Todavía no tienes negocios" description="Elige «Todos mis negocios» para que pueda crearlos." />
        ))}
      {reach === "one" && businesses.length > 0 && (
        <SelectField
          label="Negocio"
          value={single || businesses[0]?.slug || ""}
          onChange={setSingle}
          options={businesses.map((item) => ({ value: item.slug, label: item.name }))}
          error={problems.reach}
        />
      )}
      <PermissionMatrix areas={prompt.areas} value={permissions} reach={reach} onChange={setPermissions} problems={problems} />
      <Alert tone="info" title="Puedes quitarle el acceso cuando quieras">
        La conexión queda en Integraciones → Claves de API, con el nombre «{prompt.clientName}». Revocarla lo desconecta al instante.
      </Alert>
      {error && Object.keys(problems).length === 0 && <Alert tone="danger" title={error} />}
      <div className="form-actions">
        <Button type="submit" disabled={busy || Object.keys(permissions).length === 0}>
          {busy ? "Conectando…" : "Autorizar"}
        </Button>
        <Button variant="secondary" disabled={busy} onClick={() => void finish(false)}>
          Cancelar
        </Button>
      </div>
    </form>
  );
}
