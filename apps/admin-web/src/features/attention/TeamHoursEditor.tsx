import { Button } from "../../components/ui/Button";
import { Icon } from "../../components/ui/Icon";
import { WEEKDAY_LABELS, WEEKDAY_SHORT, WEEKDAYS, type HoursRange, type Weekday } from "../../domain/attention/types";

interface TeamHoursEditorProps {
  value: HoursRange[];
  onChange: (value: HoursRange[]) => void;
  /** Problemas por campo del servidor (`team_hours[0].closes`). */
  problems: Record<string, string>;
}

const MAX_RANGES = 14;
const NEW_RANGE: HoursRange = { days: ["lunes", "martes", "miercoles", "jueves", "viernes"], opens: "08:00", closes: "18:00" };

/** El horario propio del equipo: franjas con sus días y su hora de entrada y salida. */
export function TeamHoursEditor({ value, onChange, problems }: TeamHoursEditorProps) {
  const change = (index: number, changes: Partial<HoursRange>) => onChange(value.map((range, at) => (at === index ? { ...range, ...changes } : range)));
  const toggleDay = (index: number, day: Weekday) => {
    const days = value[index]!.days;
    change(index, { days: days.includes(day) ? days.filter((item) => item !== day) : WEEKDAYS.filter((item) => item === day || days.includes(item)) });
  };

  return (
    <div className="team-hours" role="group" aria-label="Horario del equipo">
      {value.length === 0 && <p className="field__hint">Agrega al menos una franja con sus días y horas.</p>}
      {problems.team_hours && (
        <p className="field__message field__message--error" role="alert">
          {problems.team_hours}
        </p>
      )}
      {value.map((range, index) => {
        const issue = problems[`team_hours[${index}].days`] ?? problems[`team_hours[${index}].opens`] ?? problems[`team_hours[${index}].closes`] ?? problems[`team_hours[${index}]`];
        return (
          <div className="team-hours__row" key={index}>
            <div className="team-hours__days" role="group" aria-label={`Días de la franja ${index + 1}`}>
              {WEEKDAYS.map((day) => (
                <button
                  key={day}
                  type="button"
                  className={`day-chip${range.days.includes(day) ? " day-chip--on" : ""}`}
                  aria-pressed={range.days.includes(day)}
                  aria-label={WEEKDAY_LABELS[day]}
                  onClick={() => toggleDay(index, day)}
                >
                  {WEEKDAY_SHORT[day]}
                </button>
              ))}
            </div>
            <div className="team-hours__times">
              <label className="team-hours__time">
                <span>Desde</span>
                <input className="input" type="time" value={range.opens} onChange={(event) => change(index, { opens: event.target.value })} aria-label={`Entrada de la franja ${index + 1}`} />
              </label>
              <label className="team-hours__time">
                <span>Hasta</span>
                <input className="input" type="time" value={range.closes} onChange={(event) => change(index, { closes: event.target.value })} aria-label={`Salida de la franja ${index + 1}`} />
              </label>
              <button type="button" className="team-hours__remove" aria-label={`Quitar la franja ${index + 1}`} title="Quitar" onClick={() => onChange(value.filter((_, at) => at !== index))}>
                <Icon name="trash" size={16} />
              </button>
            </div>
            {issue && (
              <p className="field__message field__message--error" role="alert">
                {issue}
              </p>
            )}
          </div>
        );
      })}
      {value.length < MAX_RANGES && (
        <div>
          <Button variant="secondary" size="small" onClick={() => onChange([...value, value.length === 0 ? NEW_RANGE : { days: [], opens: "09:00", closes: "13:00" }])}>
            <Icon name="plus" size={14} /> Agregar franja
          </Button>
        </div>
      )}
    </div>
  );
}
