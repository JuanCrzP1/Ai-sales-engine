import { useState, type FormEvent } from "react";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Feedback";
import { TextField } from "../../components/ui/FormFields";
import { PasswordField } from "../../components/ui/PasswordField";
import { hasErrors, validateSignIn, type AuthFieldErrors } from "../../domain/auth/validation";
import { useAuth } from "../../state/auth/useAuth";
import { useAuthSubmit } from "./useAuthSubmit";

/** Entrada al panel. Solo pide contraseña si el servicio activo la verifica. */
export function SignInForm() {
  const { signIn, verifiesCredentials } = useAuth();
  const { pending, error, submit } = useAuthSubmit();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<AuthFieldErrors>({});

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const found = validateSignIn({ email, password }, { requirePassword: verifiesCredentials });
    setErrors(found);
    if (!hasErrors(found)) void submit(() => signIn(verifiesCredentials ? { email, password } : { email }));
  };

  return (
    <form className="auth__form" noValidate onSubmit={handleSubmit}>
      {error && <Alert tone="danger">{error}</Alert>}
      <TextField
        label="Correo electrónico"
        type={verifiesCredentials ? "email" : "text"}
        inputMode="email"
        autoComplete="email"
        required
        value={email}
        onChange={setEmail}
        error={errors.email}
        placeholder="nombre@empresa.com"
      />
      {verifiesCredentials && (
        <PasswordField label="Contraseña" autoComplete="current-password" value={password} onChange={setPassword} error={errors.password} />
      )}
      <Button type="submit" className="button--block" disabled={pending}>
        {pending ? "Entrando…" : verifiesCredentials ? "Iniciar sesión" : "Entrar"}
      </Button>
    </form>
  );
}
