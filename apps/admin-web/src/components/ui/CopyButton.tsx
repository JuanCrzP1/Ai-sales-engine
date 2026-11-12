import { useEffect, useState } from "react";
import { Icon } from "./Icon";

/** Copia un texto al portapapeles y lo confirma unos segundos («Copiado»). */
export function CopyButton({ text, label = "Copiar" }: { text: string; label?: string }) {
  const [state, setState] = useState<"idle" | "copied" | "failed">("idle");

  useEffect(() => {
    if (state === "idle") return;
    const timer = window.setTimeout(() => setState("idle"), 2000);
    return () => window.clearTimeout(timer);
  }, [state]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setState("copied");
    } catch {
      setState("failed");
    }
  };

  return (
    <button type="button" className={`copy-button${state === "copied" ? " copy-button--done" : ""}`} onClick={() => void copy()} aria-live="polite">
      <Icon name={state === "copied" ? "check" : "file"} size={14} />
      {state === "copied" ? "Copiado" : state === "failed" ? "Cópialo a mano" : label}
    </button>
  );
}

/** Un texto para copiar tal cual (una dirección, un encabezado, un ejemplo), con su botón. */
export function CopyField({ label, value, multiline = false }: { label: string; value: string; multiline?: boolean }) {
  return (
    <div className="copy-field">
      <div className="copy-field__head">
        <span className="field__label">{label}</span>
        <CopyButton text={value} />
      </div>
      {multiline ? <pre className="copy-field__value copy-field__value--block">{value}</pre> : <code className="copy-field__value">{value}</code>}
    </div>
  );
}
