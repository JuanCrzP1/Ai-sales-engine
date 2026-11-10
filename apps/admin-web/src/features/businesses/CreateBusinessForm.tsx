import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Feedback";
import { TextField } from "../../components/ui/FormFields";
import { Icon, iconOr } from "../../components/ui/Icon";
import { toIdentifier } from "../../domain/config/factories";
import type { BusinessSummary, BusinessTemplate } from "../../domain/config/types";
import { OVERVIEW_ITEM, workspacePath, type CreatedFromTemplate } from "../../navigation/navItems";
import { PersistenceError, persistenceErrorMessage, useBusinessDirectory } from "../../state/directoryContext";

interface CreateBusinessFormProps {
  existing: BusinessSummary[];
  onCancel: () => void;
}

const FROM_SCRATCH = "";

/**
 * Registra el negocio y abre su espacio de trabajo. Primero se elige cómo empezar: de cero (la primera opción) o con una plantilla de
 * un tipo de negocio, que trae ejemplos para editar. El servidor valida el identificador, que no esté repetido y la plantilla.
 */
export function CreateBusinessForm({ existing, onCancel }: CreateBusinessFormProps) {
  const directory = useBusinessDirectory();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  /** Identificador escrito a mano; mientras no se toque, sale del nombre. */
  const [customSlug, setCustomSlug] = useState<string | null>(null);
  const [templates, setTemplates] = useState<BusinessTemplate[] | null>(null);
  const [templatesFailed, setTemplatesFailed] = useState(false);
  const [template, setTemplate] = useState(FROM_SCRATCH);
  const [errors, setErrors] = useState<{ name?: string; slug?: string; general?: string }>({});
  const [saving, setSaving] = useState(false);
  const slug = customSlug ?? toIdentifier(name);
  const taken = existing.some((business) => business.slug === slug);
  const chosen = templates?.find((item) => item.id === template) ?? null;

  useEffect(() => {
    let active = true;
    directory.templates().then(
      (loaded) => active && setTemplates(loaded),
      () => active && setTemplatesFailed(true),
    );
    return () => {
      active = false;
    };
  }, [directory]);

  const submit = async () => {
    setSaving(true);
    setErrors({});
    try {
      const created = await directory.create({ slug, name, template: chosen?.id ?? null });
      if (chosen) navigate(workspacePath(created.slug, OVERVIEW_ITEM.path), { state: { template: chosen.title } satisfies CreatedFromTemplate });
      else navigate(workspacePath(created.slug));
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

      <fieldset className="template-picker">
        <legend className="field__label">¿Cómo quieres empezar?</legend>
        <p className="field__hint">Una plantilla trae productos, precios y textos de ejemplo para que los cambies por los tuyos.</p>
        <div className="template-picker__grid">
          <TemplateOption
            value={FROM_SCRATCH}
            icon="blank"
            title="Empezar de cero"
            description="Un negocio vacío: tú escribes todo desde el principio."
            checked={template === FROM_SCRATCH}
            onChange={setTemplate}
          />
          {(templates ?? []).map((item) => (
            <TemplateOption
              key={item.id}
              value={item.id}
              icon={iconOr(item.icon, "sparkles")}
              title={item.title}
              description={item.description}
              checked={template === item.id}
              onChange={setTemplate}
            />
          ))}
        </div>
        {templates === null && !templatesFailed && (
          <p className="field__hint" role="status">
            Cargando plantillas…
          </p>
        )}
        {templatesFailed && <p className="field__hint">No se pudieron cargar las plantillas: puedes empezar de cero.</p>}
      </fieldset>

      {chosen && (
        <Alert tone="info">
          <p>
            Tu negocio empezará con los ejemplos de <strong>{chosen.title}</strong>. Cámbialos por los tuyos y agrega tus medios de pago: nada le llega a
            tus clientes hasta que lo publiques.
          </p>
        </Alert>
      )}

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

interface TemplateOptionProps {
  value: string;
  icon: Parameters<typeof Icon>[0]["name"];
  title: string;
  description: string;
  checked: boolean;
  onChange: (value: string) => void;
}

/** Una forma de empezar, como tarjeta: es un botón de opción nativo, accesible por teclado. */
function TemplateOption({ value, icon, title, description, checked, onChange }: TemplateOptionProps) {
  return (
    <label className={`template-option${checked ? " template-option--active" : ""}`}>
      <input type="radio" name="business-template" value={value} checked={checked} onChange={() => onChange(value)} />
      <span className="template-option__icon">
        <Icon name={icon} size={20} />
      </span>
      <span className="template-option__text">
        <span className="template-option__title">{title}</span>
        <span className="template-option__description">{description}</span>
      </span>
      {checked && (
        <span className="template-option__check" aria-hidden="true">
          <Icon name="check" size={18} />
        </span>
      )}
    </label>
  );
}
