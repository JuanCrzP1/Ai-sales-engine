import type { ReactNode } from "react";
import type { IconName } from "./Icon";
import { SettingsCard, type CardTone } from "./SettingsCard";

/** Bloques de maquetación de página: cabecera y tarjetas. */

interface PageHeaderProps {
  eyebrow?: string;
  title: string;
  description?: ReactNode;
  actions?: ReactNode;
}

export function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <header className="card__header">
      <div className="page-header">
        {eyebrow && <p className="page-header__eyebrow">{eyebrow}</p>}
        <h1 className="page-header__title">{title}</h1>
        {description && <p className="page-header__description">{description}</p>}
      </div>
      {actions}
    </header>
  );
}

interface CardProps {
  title?: string;
  description?: ReactNode;
  actions?: ReactNode;
  children?: ReactNode;
  as?: "section" | "div";
  /** Con ícono, la tarjeta es de configuración: ícono de color, título y cuerpo (ver `SettingsCard`). */
  icon?: IconName;
  tone?: CardTone;
  badge?: ReactNode;
  /** Ocupa el ancho completo de la cuadrícula de tarjetas. */
  wide?: boolean;
}

export function Card({ title, description, actions, children, as: Tag = "section", icon, tone, badge, wide }: CardProps) {
  if (icon && title) {
    return (
      <SettingsCard icon={icon} tone={tone} title={title} description={description} badge={badge} actions={actions} wide={wide}>
        {children}
      </SettingsCard>
    );
  }
  return (
    <Tag className="card">
      {(title || actions) && (
        <div className="card__header">
          <div>
            {title && <h2 className="card__title">{title}</h2>}
            {description && <p className="card__description">{description}</p>}
          </div>
          {actions}
        </div>
      )}
      {children}
    </Tag>
  );
}
