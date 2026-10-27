import { useState, type ReactNode } from "react";
import { Button } from "./Button";

interface ConfirmButtonProps {
  children: ReactNode;
  confirmLabel: string;
  onConfirm: () => void;
  variant?: "danger" | "secondary" | "ghost";
  size?: "default" | "small";
}

/** Acción destructiva en dos pasos, sin diálogos del navegador. */
export function ConfirmButton({ children, confirmLabel, onConfirm, variant = "danger", size = "small" }: ConfirmButtonProps) {
  const [asking, setAsking] = useState(false);

  if (!asking) {
    return (
      <Button variant={variant} size={size} onClick={() => setAsking(true)}>
        {children}
      </Button>
    );
  }

  return (
    <span className="button-row" role="group" aria-label="Confirmar acción">
      <Button
        variant="danger"
        size={size}
        onClick={() => {
          setAsking(false);
          onConfirm();
        }}
      >
        {confirmLabel}
      </Button>
      <Button variant="ghost" size={size} onClick={() => setAsking(false)}>
        Cancelar
      </Button>
    </span>
  );
}
