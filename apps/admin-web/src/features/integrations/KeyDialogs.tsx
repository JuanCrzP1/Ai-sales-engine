import { useState, type FormEvent } from "react";
import { Button } from "../../components/ui/Button";
import { CheckboxGroup, RadioGroup } from "../../components/ui/ChoiceGroup";
import { CopyField } from "../../components/ui/CopyButton";
import { Dialog } from "../../components/ui/Dialog";
import { Alert } from "../../components/ui/Feedback";
import { SelectField, TextField } from "../../components/ui/FormFields";
import { Tabs } from "../../components/ui/Tabs";
import {
  CHAT_AREA,
  EXPIRY_OPTIONS,
  isAgentKey,
  mcpSnippets,
  type AccessLevel,
  type CreatedApiKey,
  type KeyArea,
  type KeyReach,
} from "../../domain/integrations/types";
import type { IntegrationsData } from "../../state/useIntegrationsData";
import { useMyBusinesses } from "../../state/useMyBusinesses";
import { PermissionMatrix } from "./PermissionMatrix";

/** Para qué se crea: conversar con el asistente (API del asistente), un agente de IA (MCP) o cualquiera (Claves de API). */
export type KeyPurpose = "chat" | "agent" | "any";

interface CreateKeyDialogProps {
  purpose: KeyPurpose;
  areas: KeyArea[];
  /** El negocio desde el que se crea. */
  business: string;
  create: IntegrationsData["createKey"];
  onCreated: (created: CreatedApiKey) => void;
  onClose: () => void;
}

const REACH_OPTIONS: { value: KeyReach; label: string; hint: string }[] = [
  { value: "one", label: "Solo este negocio", hint: "La clave no ve tus otros negocios." },
  { value: "all", label: "Todos mis negocios", hint: "También los que crees después. Necesaria para crear negocios." },
  { value: "some", label: "Algunos", hint: "Los que elijas ahora." },
];

/**
 * Crear una clave: su nombre, qué puede hacer por área, a qué negocios entra y cuándo vence. Para conversar con el asistente basta
 * el nombre: es de este negocio. La clave completa se muestra una sola vez, al crearla.
 */
export function CreateKeyDialog({ purpose, areas, business, create, onCreated, onClose }: CreateKeyDialogProps) {
  const businesses = useMyBusinesses();
  const chatOnly = purpose === "chat";
  const [name, setName] = useState("");
  const [permissions, setPermissions] = useState<Record<string, AccessLevel>>(
    chatOnly ? { [CHAT_AREA]: "write" } : purpose === "agent" ? { businesses: "write", assistant: "write" } : {},
  );
  const [reach, setReach] = useState<KeyReach>(purpose === "agent" ? "all" : "one");
  const [chosen, setChosen] = useState<string[]>([business]);
  const [expiry, setExpiry] = useState<string>(purpose === "agent" ? "90" : "never");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [problems, setProblems] = useState<Record<string, string>>({});

  const changeReach = (next: KeyReach) => {
    setReach(next);
    // Conversar con el asistente es de un solo negocio: con otro alcance, se quita.
    if (next !== "one" && permissions[CHAT_AREA]) {
      const { [CHAT_AREA]: _chat, ...rest } = permissions;
      setPermissions(rest);
    }
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const result = await create({
      name,
      permissions,
      reach,
      ...(reach === "some" ? { businesses: chosen } : {}),
      expiresInDays: expiry === "never" ? null : Number(expiry),
    });
    setBusy(false);
    if ("created" in result) onCreated(result.created);
    else {
      setError(result.error);
      setProblems(result.problems);
    }
  };

  const title = purpose === "agent" ? "Crear una clave para un agente de IA" : "Crear una clave de API";
  return (
    <Dialog title={title} description="Cada clave es tuya: solo entra a tus negocios y solo puede lo que elijas aquí." onClose={onClose}>
      <form className="form-stack" onSubmit={(event) => void submit(event)} noValidate>
        <TextField
          label="Nombre"
          value={name}
          onChange={setName}
          placeholder={purpose === "agent" ? "Ej.: Claude de Juan" : chatOnly ? "Ej.: Mi página web" : "Ej.: n8n de ventas"}
          hint="Para reconocerla después: dónde la vas a usar."
          error={problems.name}
          required
        />
        {!chatOnly && (
          <>
            <RadioGroup legend="A qué negocios entra" name="reach" options={REACH_OPTIONS} value={reach} onChange={changeReach} />
            {reach === "some" && (
              <CheckboxGroup
                legend="Negocios"
                name="businesses"
                options={businesses.map((item) => ({ value: item.slug, label: item.name }))}
                values={chosen}
                onChange={setChosen}
                issue={problems.businesses ? { severity: "error", message: problems.businesses } : undefined}
              />
            )}
            <PermissionMatrix areas={areas} value={permissions} reach={reach} onChange={setPermissions} problems={problems} />
          </>
        )}
        <SelectField
          label="Vence"
          value={expiry}
          onChange={setExpiry}
          options={EXPIRY_OPTIONS.map((option) => ({ value: option.value === null ? "never" : String(option.value), label: option.label }))}
          hint="Al vencer deja de funcionar, como si la revocaras. Para un agente, mejor que venza."
          error={problems.expires_in_days}
        />
        {error && Object.keys(problems).length === 0 && <Alert tone="danger" title={error} />}
        <div className="form-actions">
          <Button type="submit" disabled={busy || !name.trim() || Object.keys(permissions).length === 0}>
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

/** La clave recién creada: la única vez que se ve completa. Si es para un agente, con lo que hay que pegar en cada uno. */
export function NewSecretDialog({ created, mcpUrl, onClose }: { created: CreatedApiKey; mcpUrl?: string | null; onClose: () => void }) {
  const snippets = mcpUrl && isAgentKey(created.key) ? mcpSnippets(mcpUrl, created.secret) : [];
  const [tab, setTab] = useState(snippets[0]?.id ?? "");
  const shown = snippets.find((snippet) => snippet.id === tab);
  return (
    <Dialog title={`Clave «${created.key.name}» creada`} onClose={onClose}>
      <div className="form-stack">
        <Alert tone="warning" title="Cópiala ahora: no se volverá a mostrar.">
          Por seguridad solo guardamos una huella de la clave. Si la pierdes, revócala y crea otra.
        </Alert>
        <CopyField label="Tu clave de API" value={created.secret} />
        {shown && (
          <Tabs label="Conectar tu agente" value={tab} onChange={setTab} tabs={snippets.map((snippet) => ({ value: snippet.id, label: snippet.label }))}>
            <p className="field__hint">{shown.hint}</p>
            <CopyField label="Para pegar" value={shown.code} multiline />
          </Tabs>
        )}
        <div className="form-actions">
          <Button onClick={onClose}>Ya la copié</Button>
        </div>
      </div>
    </Dialog>
  );
}
