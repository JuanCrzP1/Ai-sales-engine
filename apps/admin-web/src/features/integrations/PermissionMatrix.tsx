import { useId } from "react";
import { CHAT_AREA, type AccessLevel, type KeyArea, type KeyReach } from "../../domain/integrations/types";

type Level = AccessLevel | "none";

interface PermissionMatrixProps {
  areas: KeyArea[];
  value: Record<string, AccessLevel>;
  reach: KeyReach;
  onChange: (value: Record<string, AccessLevel>) => void;
  problems?: Record<string, string>;
}

function levelsOf(area: KeyArea): { value: Level; label: string }[] {
  const levels: { value: Level; label: string }[] = [{ value: "none", label: "Sin acceso" }];
  if (area.read) levels.push({ value: "read", label: "Ver" });
  if (area.write) levels.push({ value: "write", label: area.read ? "Ver y editar" : "Permitir" });
  return levels;
}

/**
 * Qué puede hacer una clave, por área: sin acceso, ver o ver y editar (las áreas y lo que deja cada nivel las define el motor). Un
 * área que es de un solo negocio (conversar con el asistente) no se puede dar a una clave de varios negocios, y crear negocios
 * necesita entrar a todos: la tabla lo dice en lugar de dejar elegirlo.
 */
export function PermissionMatrix({ areas, value, reach, onChange, problems = {} }: PermissionMatrixProps) {
  const name = useId();
  const set = (area: string, level: Level) => {
    const next = { ...value };
    if (level === "none") delete next[area];
    else next[area] = level;
    onChange(next);
  };

  return (
    <fieldset className="permission-matrix">
      <legend className="field__label">Qué puede hacer</legend>
      <div className="permission-matrix__shortcuts">
        <button
          type="button"
          className="link-button"
          onClick={() => onChange(Object.fromEntries(areas.filter((area) => area.id !== CHAT_AREA && area.read).map((area) => [area.id, "read" as const])))}
        >
          Solo ver
        </button>
        <button
          type="button"
          className="link-button"
          onClick={() => onChange(Object.fromEntries(areas.filter((area) => area.id !== CHAT_AREA && area.write).map((area) => [area.id, "write" as const])))}
        >
          Acceso completo
        </button>
      </div>
      {areas.map((area) => {
        const blocked = area.oneBusinessOnly && reach !== "one" ? "Solo con una clave de este negocio." : null;
        const current: Level = value[area.id] ?? "none";
        const description = current === "write" ? area.write : current === "read" ? area.read : (area.read ?? area.write);
        const createsBusinesses = area.id === "businesses" && current === "write" && reach !== "all";
        return (
          <div key={area.id} className={`permission-matrix__row${blocked ? " permission-matrix__row--blocked" : ""}`} role="radiogroup" aria-label={area.label}>
            <div className="permission-matrix__text">
              <span className="permission-matrix__label">{area.label}</span>
              <span className="permission-matrix__description">{blocked ?? description}</span>
              {createsBusinesses && <span className="field__message field__message--warning">Para crear negocios, la clave debe entrar a todos tus negocios.</span>}
              {problems[`permissions.${area.id}`] && <span className="field__message field__message--error">{problems[`permissions.${area.id}`]}</span>}
            </div>
            <div className="segmented permission-matrix__levels">
              {levelsOf(area).map((level) => (
                <label key={level.value} className={`segmented__option${level.value === current ? " segmented__option--active" : ""}`}>
                  <input
                    type="radio"
                    name={`${name}-${area.id}`}
                    value={level.value}
                    checked={level.value === current}
                    disabled={Boolean(blocked) && level.value !== "none"}
                    onChange={() => set(area.id, level.value)}
                  />
                  <span>{level.label}</span>
                </label>
              ))}
            </div>
          </div>
        );
      })}
      {problems.permissions && <p className="field__message field__message--error">{problems.permissions}</p>}
    </fieldset>
  );
}
