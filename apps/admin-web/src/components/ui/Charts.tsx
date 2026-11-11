import { useState, type ReactNode } from "react";
import { Icon, type IconName } from "./Icon";

/** Una cifra principal con su cambio frente al periodo anterior. `better` dice si subir es bueno (las quejas, por ejemplo, no). */
export function KpiTile({
  label,
  value,
  icon,
  delta,
  better = "up",
  hint,
}: {
  label: string;
  value: ReactNode;
  icon: IconName;
  delta?: number | null;
  better?: "up" | "down";
  hint?: ReactNode;
}) {
  const good = delta == null || delta === 0 ? null : (delta > 0) === (better === "up");
  return (
    <div className="kpi">
      <div className="kpi__top">
        <span className="kpi__label">{label}</span>
        <span className="kpi__icon" aria-hidden="true">
          <Icon name={icon} size={16} />
        </span>
      </div>
      <span className="kpi__value">{value}</span>
      <span className="kpi__foot">
        {delta != null && (
          <span className={`kpi__delta${good === null ? "" : good ? " kpi__delta--good" : " kpi__delta--bad"}`}>
            {delta > 0 ? "▲" : delta < 0 ? "▼" : "■"} {Math.abs(delta)} %
          </span>
        )}
        {hint && <span className="kpi__hint">{hint}</span>}
      </span>
    </div>
  );
}

export interface BarDatum {
  key: string;
  /** Lo que se lee bajo la barra (se muestran algunas, no todas). */
  label: string;
  /** Lo que dice el globo al pasar el mouse. */
  title: string;
  value: number;
}

/**
 * Barras verticales de una sola serie (un solo color: la magnitud la dice la altura). Al pasar el mouse por una barra aparece su
 * valor; la tabla con todos los datos queda para lectores de pantalla.
 */
export function BarChart({ data, label, unit, height = 180 }: { data: BarDatum[]; label: string; unit: string; height?: number }) {
  const [active, setActive] = useState<number | null>(null);
  const max = Math.max(1, ...data.map((item) => item.value));
  const step = Math.max(1, Math.ceil(data.length / 7));
  const top = niceMax(max);
  const shown = active === null ? null : data[active];
  return (
    <figure className="bar-chart" aria-label={label}>
      <div className="bar-chart__plot" style={{ height }} role="img" aria-label={`${label}: ${data.reduce((sum, item) => sum + item.value, 0)} ${unit} en total`}>
        <span className="bar-chart__axis" aria-hidden="true">
          <span>{top}</span>
          <span>{Number.isInteger(top / 2) ? top / 2 : ""}</span>
          <span>0</span>
        </span>
        <div className="bar-chart__bars" onMouseLeave={() => setActive(null)}>
          {[0.5, 1].map((line) => (
            <span key={line} className="bar-chart__grid" style={{ bottom: `${line * 100}%` }} aria-hidden="true" />
          ))}
          {data.map((item, index) => (
            <span
              key={item.key}
              className={`bar-chart__slot${active === index ? " bar-chart__slot--active" : ""}`}
              onMouseEnter={() => setActive(index)}
              onFocus={() => setActive(index)}
              onBlur={() => setActive(null)}
              tabIndex={0}
              aria-label={`${item.title}: ${item.value} ${unit}`}
            >
              <span className="bar-chart__bar" style={{ height: `${(item.value / top) * 100}%` }} />
            </span>
          ))}
          {shown && (
            <span className="chart-tooltip" style={{ left: `${((active! + 0.5) / data.length) * 100}%` }} role="status">
              <strong>
                {shown.value} {unit}
              </strong>
              <span>{shown.title}</span>
            </span>
          )}
        </div>
      </div>
      <div className="bar-chart__labels" aria-hidden="true">
        {data.map((item, index) => (
          <span key={item.key}>{showLabel(index, data.length, step) ? item.label : ""}</span>
        ))}
      </div>
      {/* Una tabla no respeta el alto de 1 px que la oculta: se oculta el contenedor, si no estira la página. */}
      <div className="visually-hidden">
        <table>
          <caption>{label}</caption>
          <tbody>
            {data.map((item) => (
              <tr key={item.key}>
                <th scope="row">{item.title}</th>
                <td>{item.value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </figure>
  );
}

/** Algunas fechas bajo las barras, nunca pegadas: la última siempre; una que quede muy cerca de ella, no. */
function showLabel(index: number, total: number, step: number): boolean {
  if (index === total - 1) return true;
  return index % step === 0 && total - 1 - index >= step;
}

/** Un tope «redondo» para el eje: 7 → 8, 13 → 15, 42 → 50. */
function niceMax(value: number): number {
  if (value <= 2) return 2;
  if (value <= 5) return Math.ceil(value / 2) * 2;
  const magnitude = 10 ** Math.floor(Math.log10(value));
  const steps = [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10];
  return (steps.find((candidate) => candidate * magnitude >= value) ?? 10) * magnitude;
}

/** Cómo se reparte un total entre dos partes (p. ej. la IA y el equipo), con leyenda y cada parte rotulada. */
export function SplitBar({ parts, label }: { parts: { label: string; value: number; tone: "ai" | "team" }[]; label: string }) {
  const total = parts.reduce((sum, part) => sum + part.value, 0);
  return (
    <div className="split-bar">
      <div className="split-bar__track" role="img" aria-label={`${label}: ${parts.map((part) => `${part.label} ${part.value}`).join(", ")}`}>
        {total === 0 ? (
          <span className="split-bar__empty" />
        ) : (
          parts.map((part) =>
            part.value > 0 ? <span key={part.label} className={`split-bar__part split-bar__part--${part.tone}`} style={{ flexGrow: part.value }} /> : null,
          )
        )}
      </div>
      <ul className="split-bar__legend">
        {parts.map((part) => (
          <li key={part.label}>
            <span className={`split-bar__swatch split-bar__part--${part.tone}`} aria-hidden="true" />
            <span className="split-bar__name">{part.label}</span>
            <strong>{part.value}</strong>
            <span className="split-bar__share">{total ? `${Math.round((part.value / total) * 100)} %` : "—"}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
