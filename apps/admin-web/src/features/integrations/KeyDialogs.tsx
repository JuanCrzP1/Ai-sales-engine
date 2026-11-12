import { useState, type FormEvent } from "react";
import { Button } from "../../components/ui/Button";
import { CheckboxGroup } from "../../components/ui/ChoiceGroup";
import { CopyField } from "../../components/ui/CopyButton";
import { Dialog } from "../../components/ui/Dialog";
import { Alert } from "../../components/ui/Feedback";
import { TextField } from "../../components/ui/FormFields";
import { SCOPE_ASSISTANT_CHAT, type CreatedApiKey } from "../../domain/integrations/types";
import type { IntegrationsData } from "../../state/useIntegrationsData";

interface CreateKeyDialogProps {
  scopes: { id: string; label: string }[];
  defaultName?: string;
  create: IntegrationsData["createKey"];
  onCreated: (created: CreatedApiKey) => void;
  onClose: () => void;
}

/** Crear una clave: su nombre (para reconocerla) y lo que puede hacer. */
export function CreateKeyDialog({ scopes, defaultName = "", create, onCreated, onClose }: CreateKeyDialogProps) {
  const [name, setName] = useState(defaultName);
  const [chosen, setChosen] = useState<string[]>([SCOPE_ASSISTANT_CHAT]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [problems, setProblems] = useState<Record<string, string>>({});

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const result = await create(name, chosen);
    setBusy(false);
    if ("created" in result) onCreated(result.created);
    else {
      setError(result.error);
      setProblems(result.problems);
    }
  };

  return (
    <Dialog title="Crear una clave de API" description="Úsala en la plataforma que vas a conectar. Cada clave es solo de este negocio." onClose={onClose}>
      <form className="form-stack" onSubmit={submit} noValidate>
        <TextField label="Nombre" value={name} onChange={setName} placeholder="Ej.: Leona" hint="Para reconocerla después: dónde la vas a usar." error={problems.name} required />
        <CheckboxGroup legend="Qué puede hacer" name="scopes" options={scopes.map((scope) => ({ value: scope.id, label: scope.label }))} values={chosen} onChange={setChosen} issue={problems.scopes ? { severity: "error", message: problems.scopes } : undefined} />
        {error && Object.keys(problems).length === 0 && <Alert tone="danger" title={error} />}
        <div className="form-actions">
          <Button type="submit" disabled={busy || !name.trim() || chosen.length === 0}>
            {busy ? "Creando…" : "Crear clave"}
          </Button>
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
        </div>
      </form>
    </Dialog>
  );
}

/** La clave recién creada: la única vez que se ve completa. */
export function NewSecretDialog({ created, onClose }: { created: CreatedApiKey; onClose: () => void }) {
  return (
    <Dialog title={`Clave «${created.key.name}» creada`} onClose={onClose}>
      <div className="form-stack">
        <Alert tone="warning" title="Cópiala ahora: no se volverá a mostrar.">
          Por seguridad solo guardamos una huella de la clave. Si la pierdes, revócala y crea otra.
        </Alert>
        <CopyField label="Tu clave de API" value={created.secret} />
        <div className="form-actions">
          <Button onClick={onClose}>Ya la copié</Button>
        </div>
      </div>
    </Dialog>
  );
}
