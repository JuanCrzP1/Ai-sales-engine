import { useCallback, useEffect, useState } from "react";
import { Button } from "../../components/ui/Button";
import { Alert, EmptyState } from "../../components/ui/Feedback";
import { Card, PageHeader } from "../../components/ui/Layout";
import type { BusinessSummary } from "../../domain/config/types";
import { StandalonePage } from "../../layout/StandalonePage";
import { persistenceErrorMessage, useBusinessDirectory } from "../../state/directoryContext";
import { BusinessList } from "./BusinessList";
import { CreateBusinessForm } from "./CreateBusinessForm";

type ListState = { status: "loading" } | { status: "error"; message: string } | { status: "ready"; businesses: BusinessSummary[] };

/** Entrada del panel: los negocios que administra, para abrir uno, crear otro o importar los existentes. */
export function BusinessesPage() {
  const directory = useBusinessDirectory();
  const [list, setList] = useState<ListState>({ status: "loading" });
  const [creating, setCreating] = useState(false);
  const [notice, setNotice] = useState<{ tone: "success" | "danger"; text: string } | null>(null);
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

  const remove = async (business: BusinessSummary) => {
    setNotice(null);
    try {
      await directory.remove(business.slug);
      setNotice({ tone: "success", text: `Se eliminó "${business.name}".` });
      refresh();
    } catch (error) {
      setNotice({ tone: "danger", text: persistenceErrorMessage(error) });
    }
  };

  return (
    <StandalonePage>
      <PageHeader
        eyebrow="Administración local"
        title="Tus negocios"
        description="Cada negocio tiene su propia configuración. Elige uno para editarlo o crea uno nuevo."
        actions={!creating ? <Button onClick={() => setCreating(true)}>Crear negocio</Button> : undefined}
      />

      <Alert tone="info" title="Solo en este equipo">
        <p>Este panel no tiene inicio de sesión todavía: funciona únicamente en este equipo. El acceso con usuarios llegará antes de publicarlo en la nube.</p>
      </Alert>

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
              description="Crea el primero o importa los que ya existen en la configuración del asistente."
              action={
                !creating ? (
                  <Button onClick={() => setCreating(true)}>Crear negocio</Button>
                ) : undefined
              }
            />
          ) : (
            <BusinessList businesses={list.businesses} onRemove={(business) => void remove(business)} />
          )}
        </Card>
      )}

      {list.status === "ready" && (
        <Card title="Importar negocios existentes" description="Copia al panel los negocios configurados en archivos YAML. Los archivos no se modifican y lo que ya está aquí no se toca.">
          <div className="button-row">
            <Button variant="secondary" disabled={importing} onClick={() => void importExisting()}>
              {importing ? "Importando…" : "Importar negocios existentes"}
            </Button>
          </div>
        </Card>
      )}
    </StandalonePage>
  );
}
