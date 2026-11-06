import type { ReactNode } from "react";

interface DisclosureProps {
  title: string;
  description?: string;
  children: ReactNode;
}

/** Tarjeta plegable con el elemento nativo del navegador: accesible por teclado y sin estado propio. */
export function Disclosure({ title, description, children }: DisclosureProps) {
  return (
    <details className="card disclosure">
      <summary className="disclosure__summary">
        <span className="card__title">{title}</span>
        {description && <span className="card__description">{description}</span>}
      </summary>
      <div className="disclosure__content">{children}</div>
    </details>
  );
}
