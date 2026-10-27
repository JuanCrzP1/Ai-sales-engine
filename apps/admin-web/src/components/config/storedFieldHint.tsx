import type { ReactNode } from "react";
import { engineUsage, STORED_FIELD_NOTE, type ConfigField } from "../../domain/config/engineUsage";
import type { SalesMode } from "../../domain/config/types";

/**
 * Aviso honesto para los datos que el asistente actual todavía no utiliza.
 * Devuelve `undefined` cuando el dato sí se usa, para no dejar ayudas vacías.
 */
export function storedFieldHint(field: ConfigField, salesMode: SalesMode, otherHint?: ReactNode): ReactNode | undefined {
  if (engineUsage(field, salesMode) !== "stored") return otherHint;
  const note = <span className="stored-note">{STORED_FIELD_NOTE}</span>;
  return otherHint ? (
    <>
      {otherHint} {note}
    </>
  ) : (
    note
  );
}
