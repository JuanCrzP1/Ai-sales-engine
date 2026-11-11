import type { ReactNode } from "react";
import { Icon, type IconName } from "./Icon";

/** Color del ícono de una tarjeta: agrupa visualmente los temas (identidad, oferta, dinero, conversación...). */
export type CardTone = "indigo" | "violet" | "emerald" | "amber" | "sky" | "rose" | "slate";

interface SettingsCardProps {
  icon: IconName;
  tone?: CardTone;
  title: string;
  description?: ReactNode;
  /** Etiqueta junto al título: «Opcional», «Recomendado»... */
  badge?: ReactNode;
  actions?: ReactNode;
  /** Ocupa el ancho completo de la cuadrícula. */
  wide?: boolean;
  /** Plegable con el elemento nativo del navegador (accesible por teclado): para opciones que no todos necesitan. */
  collapsible?: boolean;
  defaultOpen?: boolean;
  children?: ReactNode;
}

/** Una tarjeta de configuración: un tema con su ícono, qué es y sus campos. */
export function SettingsCard({ icon, tone = "indigo", title, description, badge, actions, wide = false, collapsible = false, defaultOpen = false, children }: SettingsCardProps) {
  const className = `settings-card${wide ? " settings-card--wide" : ""}${collapsible ? " settings-card--collapsible" : ""}`;
  const header = (
    <div className="settings-card__header">
      <span className={`settings-card__icon settings-card__icon--${tone}`}>
        <Icon name={icon} size={20} />
      </span>
      <div className="settings-card__heading">
        <h2 className="settings-card__title">
          <span>{title}</span>
          {badge}
        </h2>
        {description && <p className="settings-card__description">{description}</p>}
      </div>
      {actions && <div className="settings-card__actions">{actions}</div>}
    </div>
  );

  if (collapsible) {
    return (
      <details className={className} open={defaultOpen}>
        <summary className="settings-card__summary">
          {header}
          <span className="settings-card__chevron">
            <Icon name="chevronDown" />
          </span>
        </summary>
        <div className="settings-card__body">{children}</div>
      </details>
    );
  }
  return (
    <section className={className}>
      {header}
      {children && <div className="settings-card__body">{children}</div>}
    </section>
  );
}

/** Tarjetas una debajo de otra, todas del mismo ancho: se lee de arriba abajo, como un formulario, y nunca quedan huecos. */
export function SettingsGrid({ children }: { children: ReactNode }) {
  return <div className="settings-stack">{children}</div>;
}

interface SettingsGroupProps {
  title: string;
  description?: ReactNode;
  children: ReactNode;
}

/**
 * Una sección de la página («Lo esencial», «Para afinar»), como en los paneles de Stripe o Shopify: a la izquierda su título y para
 * qué sirve (queda a la vista al bajar), a la derecha sus tarjetas en una sola columna. En el celular, el título va arriba.
 */
export function SettingsGroup({ title, description, children }: SettingsGroupProps) {
  return (
    <section className="settings-group">
      <header className="settings-group__header">
        <h2 className="settings-group__title">{title}</h2>
        {description && <p className="settings-group__description">{description}</p>}
      </header>
      <div className="settings-stack">{children}</div>
    </section>
  );
}
