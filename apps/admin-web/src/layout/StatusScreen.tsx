import type { ReactNode } from "react";
import { BrandMark } from "../components/brand/BrandMark";

interface StatusScreenProps {
  title: string;
  message?: string;
  /** "loading" muestra un indicador animado y se anuncia como estado. */
  tone?: "loading" | "error";
  children?: ReactNode;
}

/** Pantalla completa para estados de carga o de error de la aplicación. */
export function StatusScreen({ title, message, tone = "error", children }: StatusScreenProps) {
  return (
    <div className="status-screen">
      <div className="status-screen__card" role={tone === "loading" ? "status" : "alert"}>
        <BrandMark size={44} />
        {tone === "loading" && <span className="status-screen__spinner" aria-hidden="true" />}
        <h1 className="status-screen__title">{title}</h1>
        {message && <p className="status-screen__message">{message}</p>}
        {children && <div className="button-row status-screen__actions">{children}</div>}
      </div>
    </div>
  );
}

export function LoadingScreen({ label = "Cargando…" }: { label?: string }) {
  return <StatusScreen tone="loading" title={label} />;
}
