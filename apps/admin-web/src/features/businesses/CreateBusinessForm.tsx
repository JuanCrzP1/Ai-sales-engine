import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Feedback";
import { TextField } from "../../components/ui/FormFields";
import { toIdentifier } from "../../domain/config/factories";
import type { BusinessSummary } from "../../domain/config/types";
import { workspacePath } from "../../navigation/navItems";
import { PersistenceError, persistenceErrorMessage, useBusinessDirectory } from "../../state/directoryContext";

interface CreateBusinessFormProps {
  existing: BusinessSummary[];
  onCancel: () => void;
}

/** Registra el negocio y abre su espacio de trabajo. El servidor valida el identificador y que no esté repetido. */
export function CreateBusinessForm({ existing, onCancel }: CreateBusinessFormProps) {
  const directory = useBusinessDirectory();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  /** Identificador escrito a mano; mientras no se toque, sale del nombre. */
  const [customSlug, setCustomSlug] = useState<string | null>(null);
  const [errors, setErrors] = useState<{ name?: string; slug?: string; general?: string }>({});
  const [saving, setSaving] = useState(false);
  const slug = customSlug ?? toIdentifier(name);
  const taken = existing.some((business) => business.slug === slug);

  const submit = async () => {
    setSaving(true);
    setErrors({});
    try {
      const created = await directory.create({ slug, name });
      navigate(workspacePath(created.slug));
    } catch (error) {
      const problems = error instanceof PersistenceError ? error.problems : [];
      const messageFor = (path: string) => problems.find((problem) => problem.path === path)?.message;
      const fieldErrors = { name: messageFor("name"), slug: messageFor("slug") };
      setErrors(fieldErrors.name || fieldErrors.slug ? fieldErrors : { general: persistenceErrorMessage(error) });
      setSaving(false);
    }
  };

  return (
    <form
      className="card"
      aria-label="Crear negocio"
      noValidate
      onSubmit={(event) => {
        event.preventDefault();
        void submit();
      }}
    >
      <h2 className="card__title">Nuevo negocio</h2>
      {errors.general && <Alert tone="danger">{errors.general}</Alert>}
      <div className="grid-2">
        <TextField label="Nombre comercial" required value={name} onChange={setName} placeholder="Ej.: Panadería La Esquina" error={errors.name} />
        <TextField
          label="Identificador"
          required
          value={slug}
          onChange={setCustomSlug}
          error={errors.slug ?? (taken ? "Ya existe un negocio con ese identificador." : undefined)}
          hint="Identifica al negocio dentro del sistema y no se puede cambiar. Minúsculas, números y guion bajo."
        />
      </div>
      <div className="dialog__actions">
        <Button variant="ghost" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" disabled={saving || taken || !slug || !name.trim()}>
          {saving ? "Creando…" : "Crear negocio"}
        </Button>
      </div>
    </form>
  );
}
