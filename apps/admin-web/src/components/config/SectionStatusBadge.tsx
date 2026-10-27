import type { SectionProgress } from "../../domain/validation/progress";
import { Badge } from "../ui/Feedback";

export function SectionStatusBadge({ progress }: { progress: SectionProgress }) {
  switch (progress.status) {
    case "complete":
      return <Badge tone="success">Completo</Badge>;
    case "warnings":
      return <Badge tone="warning">Con avisos</Badge>;
    case "pending":
      return <Badge tone="danger">{progress.errors === 1 ? "1 pendiente" : `${progress.errors} pendientes`}</Badge>;
  }
}

export function SectionStatusDot({ progress }: { progress: SectionProgress }) {
  const labels = { complete: "completo", warnings: "con avisos", pending: "pendiente" } as const;
  return (
    <>
      <span className={`status-dot status-dot--${progress.status}`} aria-hidden="true" />
      <span className="visually-hidden">({labels[progress.status]})</span>
    </>
  );
}
