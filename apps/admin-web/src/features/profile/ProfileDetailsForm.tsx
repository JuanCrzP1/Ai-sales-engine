import { useState, type FormEvent } from "react";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Feedback";
import { Field, TextField } from "../../components/ui/FormFields";
import { Card } from "../../components/ui/Layout";
import { authErrorMessage } from "../../domain/auth/messages";
import { validateName } from "../../domain/auth/validation";
import { useAuth, useCurrentUser } from "../../state/auth/useAuth";

/** Datos personales de la cuenta. El correo identifica la cuenta y no se edita aquí. */
export function ProfileDetailsForm() {
  const user = useCurrentUser();
  const { updateProfile } = useAuth();
  const [name, setName] = useState(user.name);
  const [error, setError] = useState<string | undefined>();
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "failed">("idle");
  const [failure, setFailure] = useState("");
  const changed = name.trim() !== user.name;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const problem = validateName(name);
    setError(problem);
    if (problem) return;
    setStatus("saving");
    try {
      await updateProfile({ name });
      setStatus("saved");
    } catch (caught) {
      setFailure(authErrorMessage(caught));
      setStatus("failed");
    }
  };

  return (
    <Card title="Datos personales" description="Así te verás dentro del panel.">
      <form className="stack" noValidate onSubmit={(event) => void handleSubmit(event)}>
        <div className="grid-2">
          <TextField
            label="Nombre"
            autoComplete="name"
            required
            value={name}
            error={error}
            onChange={(value) => {
              setName(value);
              setStatus("idle");
            }}
          />
          <Field label="Correo electrónico" hint="Es el usuario con el que inicias sesión.">
            {({ id, describedBy }) => <input id={id} className="input" type="email" value={user.email} readOnly aria-describedby={describedBy} />}
          </Field>
        </div>
        {status === "saved" && <Alert tone="success">Tus datos se guardaron.</Alert>}
        {status === "failed" && <Alert tone="danger">{failure}</Alert>}
        <div className="button-row">
          <Button type="submit" disabled={!changed || status === "saving"}>
            {status === "saving" ? "Guardando…" : "Guardar cambios"}
          </Button>
        </div>
      </form>
    </Card>
  );
}
