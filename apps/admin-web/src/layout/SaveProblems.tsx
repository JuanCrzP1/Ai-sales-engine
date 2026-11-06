import { IssueList } from "../components/config/IssueList";
import { Alert } from "../components/ui/Feedback";
import { useConfig } from "../state/useConfig";

/** Por qué no se guardó: el motivo y cada campo que señaló el servidor, con acceso a su sección. */
export function SaveProblems() {
  const { save } = useConfig();
  if (save.status !== "error") return null;
  return (
    <div className="main__alerts">
      <Alert tone="danger" title={save.error ?? "No se pudo guardar"}>
        {save.problems.length > 0 && <IssueList issues={save.problems} />}
      </Alert>
    </div>
  );
}
