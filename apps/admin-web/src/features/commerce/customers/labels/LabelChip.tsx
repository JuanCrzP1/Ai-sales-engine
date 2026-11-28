import type { LabelRef } from "../../../../domain/commerce/labels";

/** Una etiqueta, con su color. */
export function LabelChip({ label }: { label: Pick<LabelRef, "name" | "color"> }) {
  return <span className={`label-chip label-tone--${label.color}`}>{label.name}</span>;
}
