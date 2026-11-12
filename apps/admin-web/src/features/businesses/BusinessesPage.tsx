import { useCallback, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { Alert, EmptyState } from "../../components/ui/Feedback";
import { Card, PageHeader } from "../../components/ui/Layout";
import type { BusinessSummary } from "../../domain/config/types";
import { DeleteBusinessDialog } from "../../layout/DeleteBusinessDialog";
import { StandalonePage } from "../../layout/StandalonePage";
import { useAuth } from "../../state/auth/useAuth";
import { persistenceErrorMessage, useBusinessDirectory } from "../../state/directoryContext";
import { BusinessList } from "./BusinessList";
import { CreateBusinessForm } from "./CreateBusinessForm";

type ListState = { status: "loading" } | { status: "error"; message: string } | { status: "ready"; businesses: BusinessSummary[] };

/** Entrada del panel: los negocios que administra, para abrir uno, crear otro, eliminarlo o importar los de ejemplo. */
export function BusinessesPage() {
  const directory = useBusinessDirectory();
  // Con cuentas (en la nube) no aplica el aviso de "solo en este equipo".
  const { verifiesCredentials: withAccounts } = useAuth();
  const [list, setList] = useState<ListState>({ status: "loading" });
  const [creating, setCreating] = useState(false);
  // Al volver de Configuración → Eliminar negocio, el aviso de que se eliminó.
  const deletedName = (useLocation().state as { deleted?: unknown } | null)?.deleted;
  const [notice, setNotice] = useState<{ tone: "success" | "danger"; text: string } | null>(
    typeof deletedName === "string" ? { tone: "success", text: `Se eliminó «${deletedName}» con todo lo suyo.` } : null,
  );
  const [importing, setImporting] = useState(false);

  const refresh = useCallback(() => {
    directory.list().then(
      (businesses) => setList({ status: "ready", businesses }),
      (error: unknown) => setList({ status: "error", message: persistenceErrorMessage(error) }),
    );
  }, [directory]);

  useEffect(refresh, [refresh]);

  const importExisting = async () => {
    setImporting(true);
    setNotice(null);
    try {
      const { created } = await directory.importExisting();
      const text = created.length === 0 ? "No había nada nuevo: todos los negocios ya estaban importados." : created.length === 1 ? "Se importó 1 negocio." : `Se importaron ${created.length} negocios.`;
      setNotice({ tone: "success", text });
      refresh();
    } catch (error) {
      setNotice({ tone: "danger", text: persistenceErrorMessage(error) });
    } finally {
      setImporting(false);
    }
  };

  const [deleting, setDeleting] = useState<BusinessSummary | null>(null);

  return (
    <StandalonePage>
      <PageHeader
        eyebrow={withAccounts ? "Tu cuenta" : "Administración local"}
        title="Tus negocios"
        description="Cada negocio tiene su propia configuración. Elige uno para editarlo o crea uno nuevo."
        actions={!creating ? <Button onClick={() => setCreating(true)}>Crear negocio</Button> : undefined}
      />

      {!withAccounts && (
        <Alert tone="info" title="Solo en este equipo">
          <p>Este panel no tiene inicio de sesión: funciona únicamente en este equipo. En la nube cada persona entra con su cuenta.</p>
        </Alert>
      )}

      {notice && <Alert tone={notice.tone}>{notice.text}</Alert>}
      {creating && <CreateBusinessForm existing={list.status === "ready" ? list.businesses : []} onCancel={() => setCreating(false)} />}

      {list.status === "loading" && (
        <p className="field__hint" role="status">
          Cargando negocios…
        </p>
      )}

      {list.status === "error" && (
        <Alert tone="danger" title="No se pudieron cargar los negocios">
          <p>{list.message}</p>
          <div className="button-row">
            <Button size="small" variant="secondary" onClick={refresh}>
              Reintentar
            </Button>
          </div>
        </Alert>
      )}

      {list.status === "ready" && (
        <Card title="Negocios" description={`${list.businesses.length} en total`}>
          {list.businesses.length === 0 ? (
            <EmptyState
              title="Aún no hay negocios"
              description={directory.canImportExisting ? "Crea el primero o importa los que ya existen en la configuración del asistente." : "Crea el primero para configurar su asistente."}
              action={
                !creating ? (
                  <Button onClick={() => setCreating(true)}>Crear negocio</Button>
                ) : undefined
              }
            />
          ) : (
            <BusinessList
              businesses={list.businesses}
              onRemove={(business) => {
                setNotice(null);
                setDeleting(business);
              }}
            />
          )}
        </Card>
      )}

      {list.status === "ready" && directory.canImportExisting && (
        <Card title="Negocios de ejemplo" description="Agrega al panel los negocios de ejemplo del proyecto, publicados y listos para probar. Lo que ya está aquí no se toca.">
          <div className="button-row">
            <Button variant="secondary" disabled={importing} onClick={() => void importExisting()}>
              {importing ? "Importando…" : "Importar negocios de ejemplo"}
            </Button>
          </div>
        </Card>
      )}
      {deleting && (
        <DeleteBusinessDialog
          business={deleting}
          onClose={() => setDeleting(null)}
          onDeleted={() => {
            setNotice({ tone: "success", text: `Se eliminó «${deleting.name}» con todo lo suyo.` });
            setDeleting(null);
            refresh();
          }}
        />
      )}
    </StandalonePage>
  );
}
