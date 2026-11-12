import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import { Badge } from "../../components/ui/Feedback";
import { TextField } from "../../components/ui/FormFields";
import { Icon } from "../../components/ui/Icon";
import {
  replyCostLabel,
  searchModels,
  tokenPriceLabel,
} from "../../domain/assistant/models";
import { useAIModels, type AIModelOption } from "../../state/useAIModels";

/** Cuántos modelos se muestran sin buscar: la lista completa de OpenRouter tiene cientos. */
const VISIBLE = 40;
const SYSTEM = "";

interface ModelPickerProps {
  /** El modelo elegido, o "" para usar el del sistema. */
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

type Row =
  | { kind: "group"; label: string }
  | {
      kind: "option";
      id: string;
      model?: AIModelOption;
      label?: string;
      detail?: string;
    };

/**
 * Elegir el modelo en una lista desplegable: muestra el elegido con su costo y, al abrirla, un buscador y los modelos agrupados
 * (recomendados primero). Se maneja con el teclado (flechas, Enter, Escape). Si la lista de OpenRouter no carga, se escribe a mano.
 */
export function ModelPicker({ value, onChange, error }: ModelPickerProps) {
  const state = useAIModels();
  const id = useId();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const root = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const search = useRef<HTMLInputElement>(null);
  const list = useRef<HTMLDivElement>(null);
  const catalog = state.status === "ready" ? state.catalog : null;

  const rows = useMemo<Row[]>(() => {
    if (!catalog) return [];
    const searching = query.trim() !== "";
    const matches = searchModels(catalog.models, query);
    const result: Row[] = [];
    if (!searching) {
      const system = catalog.models.find(
        (model) => model.id === catalog.defaultModel,
      );
      result.push({
        kind: "option",
        id: SYSTEM,
        label: "Predeterminado del sistema",
        detail: system
          ? `${system.name} · ${system.provider} — ${replyCostLabel(system)}`
          : catalog.defaultModel,
      });
      const recommended = matches.filter((model) => model.recommended);
      if (recommended.length > 0)
        result.push({
          kind: "group",
          label: "Recomendados para conversar en español",
        });
      recommended.forEach((model) =>
        result.push({ kind: "option", id: model.id, model }),
      );
      result.push({
        kind: "group",
        label: `Todos los modelos (${catalog.models.length})`,
      });
      matches
        .filter((model) => !model.recommended)
        .slice(0, VISIBLE)
        .forEach((model) =>
          result.push({ kind: "option", id: model.id, model }),
        );
    } else {
      result.push({
        kind: "group",
        label: `${matches.length} ${matches.length === 1 ? "resultado" : "resultados"}`,
      });
      matches
        .slice(0, VISIBLE)
        .forEach((model) =>
          result.push({ kind: "option", id: model.id, model }),
        );
    }
    return result;
  }, [catalog, query]);
  const options = rows.filter(
    (row): row is Extract<Row, { kind: "option" }> => row.kind === "option",
  );

  // Al abrir, el elegido queda marcado y a la vista.
  useEffect(() => {
    if (!open) return;
    const chosen = options.findIndex((option) => option.id === value);
    setActive(chosen >= 0 ? chosen : 0);
    search.current?.focus();
  }, [open]); // Solo al abrir: después, las flechas mueven la marca.

  useEffect(() => {
    list.current
      ?.querySelector<HTMLElement>(`[data-index="${active}"]`)
      ?.scrollIntoView?.({ block: "nearest" });
  }, [active, open]);

  useEffect(() => {
    if (!open) return;
    const close = (event: PointerEvent) => {
      if (event.target instanceof Node && !root.current?.contains(event.target))
        setOpen(false);
    };
    document.addEventListener("pointerdown", close);
    return () => document.removeEventListener("pointerdown", close);
  }, [open]);

  if (state.status === "loading") {
    return (
      <div className="field">
        <span className="field__label">Modelo</span>
        <p className="field__hint">Cargando los modelos de OpenRouter…</p>
      </div>
    );
  }
  if (state.status === "error" || !catalog) {
    return (
      <TextField
        label="Modelo"
        value={value}
        onChange={onChange}
        placeholder="openai/gpt-4o-mini"
        hint="No se pudo cargar la lista de OpenRouter. Escribe el modelo como aparece allí, o déjalo vacío para usar el del sistema."
        error={error}
      />
    );
  }

  const byId = new Map(catalog.models.map((model) => [model.id, model]));
  const system = byId.get(catalog.defaultModel);
  const chosen = value ? byId.get(value) : system;

  const choose = (choice: string) => {
    onChange(choice);
    setOpen(false);
    setQuery("");
    trigger.current?.focus();
  };

  const onSearchKey = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      setActive((current) =>
        Math.max(
          0,
          Math.min(
            options.length - 1,
            current + (event.key === "ArrowDown" ? 1 : -1),
          ),
        ),
      );
    } else if (event.key === "Enter") {
      event.preventDefault();
      const option = options[active];
      if (option) choose(option.id);
    } else if (event.key === "Escape") {
      event.preventDefault();
      setOpen(false);
      trigger.current?.focus();
    }
  };

  let index = -1;
  return (
    <div className="field model-select" ref={root}>
      <span className="field__label" id={`${id}-label`}>
        Modelo
      </span>
      <div className="model-select__anchor">
        <button
          ref={trigger}
          type="button"
          className={`model-select__trigger${open ? " model-select__trigger--open" : ""}`}
          aria-haspopup="listbox"
          aria-expanded={open}
          aria-labelledby={`${id}-label ${id}-value`}
          aria-invalid={error ? true : undefined}
          onClick={() => setOpen((current) => !current)}
        >
          <span className="model-select__value" id={`${id}-value`}>
            {chosen ? (
              <>
                <span className="model-select__name">
                  {chosen.name}{" "}
                  <span className="model-option__provider">
                    {chosen.provider}
                  </span>
                  {!value && <Badge tone="neutral">Del sistema</Badge>}
                  {value && chosen.recommended && (
                    <Badge tone="success">Recomendado</Badge>
                  )}
                </span>
                <span className="model-select__cost">
                  {replyCostLabel(chosen)}
                </span>
              </>
            ) : (
              <>
                <span className="model-select__name">
                  {value || catalog.defaultModel}
                </span>
                <span className="model-select__cost">
                  Ya no está en la lista de OpenRouter: elige otro.
                </span>
              </>
            )}
          </span>
          <Icon name="chevronDown" size={18} />
        </button>

        {open && (
          <div className="model-select__panel">
            <div className="model-select__search">
              <input
                ref={search}
                type="search"
                className="input"
                role="combobox"
                aria-label="Buscar modelo"
                aria-expanded="true"
                aria-controls={`${id}-list`}
                aria-activedescendant={
                  options[active] ? `${id}-option-${active}` : undefined
                }
                placeholder="Buscar: gemini, claude, gpt, llama…"
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setActive(0);
                }}
                onKeyDown={onSearchKey}
              />
            </div>
            <div
              className="model-select__list"
              role="listbox"
              id={`${id}-list`}
              aria-label="Modelos"
              ref={list}
            >
              {rows.map((row) => {
                if (row.kind === "group") {
                  return (
                    <p
                      className="model-select__group"
                      key={`group-${row.label}`}
                      role="presentation"
                    >
                      {row.label}
                    </p>
                  );
                }
                index += 1;
                const position = index;
                const selected = row.id === value;
                return (
                  <div
                    key={row.id || "sistema"}
                    id={`${id}-option-${position}`}
                    data-index={position}
                    role="option"
                    aria-selected={selected}
                    className={`model-select__option${position === active ? " model-select__option--active" : ""}`}
                    onPointerMove={() => setActive(position)}
                    onClick={() => choose(row.id)}
                  >
                    <span className="model-select__check" aria-hidden="true">
                      {selected && <Icon name="check" size={16} />}
                    </span>
                    {row.model ? (
                      <ModelLine model={row.model} />
                    ) : (
                      <span className="model-option__text">
                        <span className="model-option__name">{row.label}</span>
                        <span className="model-option__cost">{row.detail}</span>
                      </span>
                    )}
                  </div>
                );
              })}
              {options.length === 0 && (
                <p className="field__hint model-select__empty">
                  Ningún modelo coincide con «{query.trim()}».
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      <p className="field__hint">
        Solo aparecen los modelos que responden en el formato que usa tu
        asistente. El costo es aproximado; el real lo ves abajo, en Consumo.
      </p>
      {error && (
        <p className="field__message field__message--error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

function ModelLine({ model }: { model: AIModelOption }) {
  return (
    <span className="model-option__text">
      <span className="model-option__name">
        {model.name}{" "}
        <span className="model-option__provider">{model.provider}</span>
        {model.recommended && <Badge tone="success">Recomendado</Badge>}
        {model.free && <Badge tone="warning">Gratis</Badge>}
      </span>
      <span className="model-option__cost">{replyCostLabel(model)}</span>
      <span className="model-option__price">{tokenPriceLabel(model)}</span>
    </span>
  );
}
