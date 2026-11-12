import { useState, type FormEvent } from "react";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Feedback";
import { Card } from "../../components/ui/Layout";
import { PasswordField } from "../../components/ui/PasswordField";
import { Toggle } from "../../components/ui/Toggle";
import { authErrorMessage } from "../../domain/auth/messages";
import { AuthError } from "../../domain/auth/types";
import { hasErrors, PASSWORD_MIN_LENGTH, validatePasswordChange, type AuthFieldErrors } from "../../domain/auth/validation";
import { useAuth } from "../../state/auth/useAuth";

const EMPTY = { currentPassword: "", password: "", confirmPassword: "" };

/**
 * Cambiar la contraseña: pide la actual (así nadie la cambia con una sesión olvidada abierta) y, por defecto, cierra la sesión en
 * los demás equipos, como hacen los servicios serios cuando se cambia una contraseña. La contraseña solo viaja al servicio de cuentas.
 */
export function PasswordCard() {
  const { changePassword } = useAuth();
  const [form, setForm] = useState(EMPTY);
  const [signOutOthers, setSignOutOthers] = useState(true);
  const [errors, setErrors] = useState<AuthFieldErrors>({});
  const [status, setStatus] = useState<"idle" | "saving" | "saved">("idle");
  const [failure, setFailure] = useState<string | null>(null);

  const set = (field: keyof typeof EMPTY) => (value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
    setStatus("idle");
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const problems = validatePasswordChange(form);
    setErrors(problems);
    setFailure(null);
    if (hasErrors(problems)) return;
    setStatus("saving");
    try {
      await changePassword({ currentPassword: form.currentPassword, newPassword: form.password, signOutOtherDevices: signOutOthers });
      setForm(EMPTY);
      setStatus("saved");
    } catch (caught) {
      setStatus("idle");
      if (caught instanceof AuthError && caught.code === "wrong_password") setErrors({ currentPassword: authErrorMessage(caught) });
      else setFailure(authErrorMessage(caught));
    }
  };

  return (
    <Card icon="shield" tone="emerald" title="Contraseña" description={`Usa al menos ${PASSWORD_MIN_LENGTH} caracteres, con letras y números.`}>
      <form className="form-stack" noValidate onSubmit={(event) => void handleSubmit(event)}>
        <PasswordField label="Contraseña actual" value={form.currentPassword} onChange={set("currentPassword")} autoComplete="current-password" error={errors.currentPassword} />
        <div className="grid-2">
          <PasswordField label="Contraseña nueva" value={form.password} onChange={set("password")} autoComplete="new-password" error={errors.password} />
          <PasswordField label="Repite la contraseña nueva" value={form.confirmPassword} onChange={set("confirmPassword")} autoComplete="new-password" error={errors.confirmPassword} />
        </div>
        <Toggle
          label="Cerrar la sesión en los demás equipos"
          description="Recomendado: si alguien más tenía tu sesión abierta, tendrá que volver a entrar con la contraseña nueva."
          checked={signOutOthers}
          onChange={setSignOutOthers}
        />
        {failure && <Alert tone="danger" title={failure} />}
        {status === "saved" && (
          <Alert tone="success" title="Listo, tu contraseña cambió.">
            {signOutOthers ? "Cerramos la sesión en tus demás equipos." : "Tus demás sesiones siguen abiertas."}
          </Alert>
        )}
        <div>
          <Button type="submit" disabled={status === "saving"}>
            {status === "saving" ? "Cambiando…" : "Cambiar contraseña"}
          </Button>
        </div>
      </form>
    </Card>
  );
}
