import { useState, type FormEvent } from "react";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Feedback";
import { TextField } from "../../components/ui/FormFields";
import { PasswordField } from "../../components/ui/PasswordField";
import { hasErrors, PASSWORD_MIN_LENGTH, validateSignUp, type AuthFieldErrors } from "../../domain/auth/validation";
import { useAuth } from "../../state/auth/useAuth";
import { useAuthSubmit } from "./useAuthSubmit";

/** Creación de cuenta. Los campos de contraseña solo aparecen si el servicio activo la verifica. */
export function SignUpForm() {
  const { signUp, verifiesCredentials } = useAuth();
  const { pending, error, submit } = useAuthSubmit();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirmPassword: "" });
  const [errors, setErrors] = useState<AuthFieldErrors>({});
  const set = (field: keyof typeof form) => (value: string) => setForm((current) => ({ ...current, [field]: value }));

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const found = validateSignUp(form, { requirePassword: verifiesCredentials });
    setErrors(found);
    if (hasErrors(found)) return;
    const identity = { name: form.name, email: form.email };
    void submit(() => signUp(verifiesCredentials ? { ...identity, password: form.password } : identity));
  };

  return (
    <form className="auth__form" noValidate onSubmit={handleSubmit}>
      {error && <Alert tone="danger">{error}</Alert>}
      <TextField label="Tu nombre" autoComplete="name" required value={form.name} onChange={set("name")} error={errors.name} placeholder="Ej.: Laura Gómez" />
      <TextField label="Correo electrónico" type="email" inputMode="email" autoComplete="email" required value={form.email} onChange={set("email")} error={errors.email} placeholder="nombre@empresa.com" />
      {verifiesCredentials && (
        <>
          <PasswordField
            label="Contraseña"
            autoComplete="new-password"
            value={form.password}
            onChange={set("password")}
            error={errors.password}
            hint={`Mínimo ${PASSWORD_MIN_LENGTH} caracteres, con letras y números.`}
          />
          <PasswordField label="Confirmar contraseña" autoComplete="new-password" value={form.confirmPassword} onChange={set("confirmPassword")} error={errors.confirmPassword} />
        </>
      )}
      <Button type="submit" className="button--block" disabled={pending}>
        {pending ? "Creando cuenta…" : "Crear cuenta"}
      </Button>
    </form>
  );
}
