import type { ReactNode } from "react";

/** Componentes de retroalimentación visual: insignias, avisos, estados vacíos y progreso. */

type Tone = "neutral" | "success" | "warning" | "danger" | "accent";

export function Badge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return <span className={`badge badge--${tone}`}>{children}</span>;
}

interface AlertProps {
  tone?: "info" | "warning" | "danger" | "success";
  title?: string;
  children?: ReactNode;
}

export function Alert({ tone = "info", title, children }: AlertProps) {
  return (
    <div className={`alert alert--${tone}`} role={tone === "danger" ? "alert" : "status"}>
      {title && <p className="alert__title">{title}</p>}
      {children}
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <p className="empty-state__title">{title}</p>
      {description && <p>{description}</p>}
      {action}
    </div>
  );
}

export function ProgressBar({ value, total, label }: { value: number; total: number; label: string }) {
  const percent = total === 0 ? 0 : Math.round((value / total) * 100);
  return (
    <div className="progress">
      <div className="progress__label">
        <span>{label}</span>
        <span>
          {value} de {total}
        </span>
      </div>
      <div className="progress__track" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={total} aria-valuenow={value}>
        <div className="progress__bar" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
