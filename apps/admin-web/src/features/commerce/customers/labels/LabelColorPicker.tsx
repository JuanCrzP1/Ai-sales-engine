import { LABEL_COLORS, LABEL_COLOR_NAMES, type LabelColor } from "../../../../domain/commerce/labels";

/** Los colores de una etiqueta, para elegir uno. Cada uno se nombra: no depende solo del color para distinguirse. */
export function LabelColorPicker({ value, label = "Color", disabled = false, onChange }: { value: LabelColor; label?: string; disabled?: boolean; onChange: (color: LabelColor) => void }) {
  return (
    <span className="label-colors" role="radiogroup" aria-label={label}>
      {LABEL_COLORS.map((color) => (
        <button
          key={color}
          type="button"
          role="radio"
          aria-checked={value === color}
          aria-label={LABEL_COLOR_NAMES[color]}
          title={LABEL_COLOR_NAMES[color]}
          className={`label-colors__option label-tone--${color}`}
          disabled={disabled}
          onClick={() => onChange(color)}
        />
      ))}
    </span>
  );
}
