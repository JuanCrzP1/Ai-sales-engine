import { Button } from "../../components/ui/Button";
import { Alert, EmptyState } from "../../components/ui/Feedback";
import { Card, PageHeader } from "../../components/ui/Layout";
import { SectionPager } from "../../layout/SectionPager";
import { stepLabel } from "../../navigation/navItems";
import { useConfig, useFieldIssue } from "../../state/useConfig";
import { OfferingEditor } from "./OfferingEditor";
import { OfferingList } from "./OfferingList";
import { useOfferingEditor } from "./useOfferingEditor";

export function CatalogPage() {
  const { config, actions } = useConfig();
  const { editor, startNew, startEdit, change, cancel, save } = useOfferingEditor();
  const listIssue = useFieldIssue("offerings");
  const salesMode = config.business.salesMode;
  const isCatalog = salesMode === "catalog";
  const categories = [...new Set(config.offerings.map((offering) => offering.category.trim()).filter(Boolean))];
  const addLabel = isCatalog ? "Agregar producto" : "Agregar plan o servicio";

  return (
    <>
      <PageHeader
        eyebrow={stepLabel("catalog")}
        title="Productos y servicios"
        description={
          isCatalog
            ? "Tu catálogo: los productos que el cliente puede pedir."
            : "Tus planes o servicios, con su precio y lo que incluyen."
        }
        actions={!editor ? <Button onClick={startNew}>{addLabel}</Button> : undefined}
      />

      {isCatalog && (
        <Alert tone="info">
          <p>
            En modo catálogo, la versión actual del asistente presenta tus <strong>categorías</strong>. Los nombres y precios
            de cada producto se guardan para una próxima versión.
          </p>
        </Alert>
      )}

      {editor && (
        <OfferingEditor
          draft={editor.draft}
          isNew={editor.isNew}
          issues={editor.issues}
          salesMode={salesMode}
          categorySuggestions={categories}
          onChange={change}
          onSave={save}
          onCancel={cancel}
        />
      )}

      <Card
        title={isCatalog ? "Catálogo" : "Planes y servicios"}
        description={`${config.offerings.length} en total · ${config.offerings.filter((offering) => offering.available).length} disponibles`}
      >
        {listIssue && <Alert tone="warning">{listIssue.message}</Alert>}
        {config.offerings.length === 0 ? (
          <EmptyState
            title="Aún no has agregado nada"
            description="Agrega lo que vendes para que el asistente pueda ofrecerlo."
            action={!editor ? <Button onClick={startNew}>{addLabel}</Button> : undefined}
          />
        ) : (
          <OfferingList
            offerings={config.offerings}
            salesMode={salesMode}
            onEdit={startEdit}
            onToggleAvailable={(offering) => actions.setOfferingAvailability(offering.id, !offering.available)}
            onRemove={(offering) => actions.removeOffering(offering.id)}
          />
        )}
      </Card>

      <SectionPager current="catalog" />
    </>
  );
}
