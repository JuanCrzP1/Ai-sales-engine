import { useId, useState, type KeyboardEvent } from "react";
import { Badge } from "../../components/ui/Feedback";
import { TextField } from "../../components/ui/FormFields";
import { replyCostLabel, searchModels, tokenPriceLabel } from "../../domain/assistant/models";
import { useAIModels, type AIModelOption } from "../../state/useAIModels";

/** Cuántos modelos se muestran sin buscar: la lista completa de OpenRouter tiene cientos. */
const VISIBLE = 40;

interface ModelPickerProps {
  /** El modelo elegido, o "" para usar el del sistema. */
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

/** Elegir el modelo de la lista de OpenRouter, con su costo aproximado. Si la lista no carga, se escribe a mano. */
export function ModelPicker({ value, onChange, error }: ModelPickerProps) {
  const state = useAIModels();
  const name = useId();
  const [query, setQuery] = useState("");

  if (state.status === "loading") {
    return (
      <div className="field">
        <span className="field__label">Modelo</span>
        <p className="field__hint">Cargando los modelos de OpenRouter…</p>
      </div>
    );
  }
  if (state.status === "error") {
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

  const { catalog } = state;
  const byId = new Map(catalog.models.map((model) => [model.id, model]));
  const systemModel = byId.get(catalog.defaultModel);
  const chosen = value ? byId.get(value) : systemModel;
  const searching = query.trim() !== "";
  const matches = searchModels(catalog.models, query);
  const recommended = searching ? [] : matches.filter((model) => model.recommended);
  const rest = searching ? matches : matches.filter((model) => !model.recommended);
  const shown = rest.slice(0, VISIBLE);
  const visible = new Set([...recommended, ...shown].map((model) => model.id));
  const pinned = value && !visible.has(value) ? byId.get(value) : undefined;
  const option = (model: AIModelOption) => <ModelOption key={model.id} model={model} name={name} checked={value === model.id} onChoose={onChange} />;

  const keepFormClosed = (event: KeyboardEvent<HTMLInputElement>) => {
    // Enter en el buscador no debe guardar el formulario.
    if (event.key === "Enter") event.preventDefault();
  };

  return (
    <fieldset className="field model-picker" aria-describedby={`${name}-hint`}>
      <legend className="field__label">Modelo</legend>
      <p className="model-picker__chosen" aria-live="polite">
        {chosen ? (
          <>
            Elegido: <strong>{chosen.name}</strong> · {chosen.provider}
            {!value && " (el del sistema)"} — {replyCostLabel(chosen)}
          </>
        ) : (
          <>
            Elegido: <strong>{value || catalog.defaultModel}</strong>
          </>
        )}
      </p>
      <input
        type="search"
        className="input"
        aria-label="Buscar modelo"
        placeholder="Buscar: gemini, claude, gpt, llama…"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        onKeyDown={keepFormClosed}
      />
      <div className="model-picker__list">
        {!searching && (
          <label className="model-option">
            <input type="radio" name={name} value="" checked={value === ""} onChange={() => onChange("")} />
            <span className="model-option__text">
              <span className="model-option__name">Predeterminado del sistema</span>
              <span className="model-option__cost">
                {systemModel ? `${systemModel.name} · ${systemModel.provider} — ${replyCostLabel(systemModel)}` : catalog.defaultModel}
              </span>
            </span>
          </label>
        )}
        {value && !byId.has(value) && (
          <label className="model-option">
            <input type="radio" name={name} value={value} checked onChange={() => onChange(value)} />
            <span className="model-option__text">
              <span className="model-option__name">{value}</span>
              <span className="model-option__cost">Es el que tienes hoy, pero ya no está en la lista de OpenRouter. Elige otro.</span>
            </span>
          </label>
        )}
        {pinned && option(pinned)}
        {recommended.length > 0 && <p className="model-picker__group">Recomendados para conversar en español</p>}
        {recommended.map(option)}
        <p className="model-picker__group">{searching ? `${matches.length} ${matches.length === 1 ? "resultado" : "resultados"}` : `Todos los modelos (${catalog.models.length})`}</p>
        {shown.map(option)}
        {searching && matches.length === 0 && <p className="field__hint">Ningún modelo coincide con «{query.trim()}».</p>}
        {rest.length > shown.length && <p className="field__hint">Hay {rest.length - shown.length} modelos más. Escribe para buscarlos.</p>}
      </div>
      <p className="field__hint" id={`${name}-hint`}>
        Solo aparecen los modelos que responden en el formato que usa tu asistente. El costo es aproximado; el real lo ves abajo, en
        Consumo.
      </p>
      {error && (
        <p className="field__message field__message--error" role="alert">
          {error}
        </p>
      )}
    </fieldset>
  );
}

function ModelOption({ model, name, checked, onChoose }: { model: AIModelOption; name: string; checked: boolean; onChoose: (id: string) => void }) {
  return (
    <label className="model-option">
      <input type="radio" name={name} value={model.id} checked={checked} onChange={() => onChoose(model.id)} />
      <span className="model-option__text">
        <span className="model-option__name">
          {model.name} <span className="model-option__provider">{model.provider}</span>
          {model.recommended && <Badge tone="success">Recomendado</Badge>}
          {model.free && <Badge tone="warning">Gratis</Badge>}
        </span>
        <span className="model-option__cost">{replyCostLabel(model)}</span>
        <span className="model-option__price">{tokenPriceLabel(model)}</span>
      </span>
    </label>
  );
}
