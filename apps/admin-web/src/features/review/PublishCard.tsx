import { useCallback, useEffect, useState } from "react";
import { Button } from "../../components/ui/Button";
import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { Alert, Badge } from "../../components/ui/Feedback";
import { Card } from "../../components/ui/Layout";
import type { VersionInfo } from "../../domain/config/types";
import { formatDateTime } from "../../lib/format";
import type { ActionResult, ReviewReport } from "../../state/configContext";
import { persistenceErrorMessage } from "../../state/directoryContext";
import { useConfig } from "../../state/useConfig";

const STATUS_LABELS: Record<VersionInfo["status"], string> = { draft: "Borrador", published: "Publicada", archived: "Anterior" };

/** Publicar, volver a una versión anterior y ver el historial. El servidor comprueba que la versión compila antes de publicarla. */
export function PublishCard() {
  const { dirty, meta, actions, save } = useConfig();
  const [report, setReport] = useState<ReviewReport | null>(null);
  const [history, setHistory] = useState<VersionInfo[]>([]);
  const [message, setMessage] = useState<{ tone: "success" | "danger"; text: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const { loadReview, loadHistory } = actions;
  const current = meta.version;

  const refresh = useCallback(() => {
    if (meta.latestVersion === null) return;
    Promise.all([loadReview(), loadHistory()]).then(
      ([review, versions]) => {
        setReport(review);
        setHistory([...versions].reverse());
      },
      (error: unknown) => setMessage({ tone: "danger", text: persistenceErrorMessage(error) }),
    );
  }, [loadReview, loadHistory, meta.latestVersion]);

  useEffect(refresh, [refresh, meta.version, meta.publishedVersion]);

  const run = async (operation: () => Promise<ActionResult>, success: string) => {
    setBusy(true);
    setMessage(null);
    const result = await operation();
    setBusy(false);
    setMessage(result.ok ? { tone: "success", text: success } : { tone: "danger", text: result.error });
  };

  const canPublish = !dirty && current !== null && current.status !== "published" && report?.compiles === true;
  const canRollback = history.some((version) => version.status === "archived" && version.publishedAt !== null && meta.publishedVersion !== null && version.version < meta.publishedVersion);

  return (
    <Card title="Publicación" description="Publicar deja esta versión como la oficial del negocio.">
      <Alert tone="info" title="Esto es lo que responde el asistente">
        <p>Lo que publiques es lo que el asistente usa con tus clientes desde su siguiente mensaje. Si algo no queda bien, puedes volver a la versión anterior.</p>
      </Alert>

      {message && <Alert tone={message.tone}>{message.text}</Alert>}

      <dl className="summary-list">
        <div className="summary-list__row">
          <dt>Versión que estás editando</dt>
          <dd>{current ? `${current.version} (${STATUS_LABELS[current.status].toLowerCase()})` : "Aún no hay ninguna guardada"}</dd>
        </div>
        <div className="summary-list__row">
          <dt>Versión publicada</dt>
          <dd>{meta.publishedVersion ?? "Ninguna"}</dd>
        </div>
      </dl>

      {dirty && <p className="field__hint">Tienes cambios sin guardar: guárdalos para poder publicarlos.</p>}
      {report && !report.compiles && !dirty && current && (
        <Alert tone="danger" title="Esta versión todavía no se puede publicar">
          <p>{report.compileError}</p>
        </Alert>
      )}
      {report && report.diagnostics.length > 0 && !dirty && (
        <Alert tone="warning" title="Conviene revisar antes de publicar">
          <ul>
            {report.diagnostics.map((item, index) => (
              <li key={`${item.code}-${index}`}>{item.message}</li>
            ))}
          </ul>
        </Alert>
      )}

      <div className="button-row">
        {dirty && <Button disabled={save.status === "saving"} onClick={() => void actions.save()}>Guardar cambios</Button>}
        {current && !dirty && (
          <Button disabled={!canPublish || busy} onClick={() => void run(() => actions.publish(current.version), `Se publicó la versión ${current.version}.`)}>
            {current.status === "published" ? "Esta versión ya está publicada" : `Publicar versión ${current.version}`}
          </Button>
        )}
        {canRollback && !dirty && (
          <ConfirmButton variant="secondary" size="default" confirmLabel="Sí, volver" onConfirm={() => void run(actions.rollback, "Se volvió a publicar la versión anterior.")}>
            Volver a la versión publicada anterior
          </ConfirmButton>
        )}
      </div>

      {history.length > 0 && (
        <ul className="item-list" aria-label="Historial de versiones">
          {history.map((version) => (
            <li key={version.version} className="item-row">
              <div className="item-row__main">
                <span className="item-row__title">
                  Versión {version.version}
                  <Badge tone={version.status === "published" ? "success" : "neutral"}>{STATUS_LABELS[version.status]}</Badge>
                </span>
                <span className="item-row__meta">{version.createdAt ? formatDateTime(version.createdAt) : ""}</span>
              </div>
              {version.version !== current?.version && !dirty && (
                <span className="button-row">
                  <ConfirmButton variant="ghost" confirmLabel="Sí, restaurar" onConfirm={() => void run(() => actions.restore(version.version), `Se creó un borrador con el contenido de la versión ${version.version}.`)}>
                    Restaurar
                  </ConfirmButton>
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
