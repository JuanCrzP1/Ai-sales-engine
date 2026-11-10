import { Button } from "../../components/ui/Button";
import { SettingsGroup } from "../../components/ui/SettingsCard";
import { Alert, EmptyState } from "../../components/ui/Feedback";
import { Card, PageHeader } from "../../components/ui/Layout";
import { SelectField } from "../../components/ui/FormFields";
import { isAvailable, isCatalog, offerEntries } from "../../domain/config/document";
import { ContractSection } from "../../layout/ContractSection";
import { SectionPager } from "../../layout/SectionPager";
import { stepLabel } from "../../navigation/navItems";
import { useConfig, useFieldIssue } from "../../state/useConfig";
import { CategoriesForm } from "./CategoriesForm";
import { OfferingEditor } from "./OfferingEditor";
import { OfferingList } from "./OfferingList";
import { useOfferingEditor } from "./useOfferingEditor";

export function CatalogPage() {
  const { document, actions } = useConfig();
  const { editor, startNew, startEdit, change, changeCategory, cancel, save } = useOfferingEditor();
  const listIssue = useFieldIssue("offer");
  const catalog = isCatalog(document);
  const entries = offerEntries(document);
  const addLabel = catalog ? "Agregar producto" : "Agregar plan o servicio";
  const categories = document.offer.catalog?.categories ?? [];

  return (
    <>
      <PageHeader
        eyebrow={stepLabel("catalog")}
        title="Productos y servicios"
        description={catalog ? "Tu catálogo: los productos que el cliente puede pedir." : "Tus planes o servicios, con su precio y lo que incluyen."}
        actions={!editor ? <Button onClick={startNew}>{addLabel}</Button> : undefined}
      />

      {editor && (
        <OfferingEditor
          draft={editor.draft}
          categoryName={editor.categoryName}
          isNew={editor.isNew}
          issues={editor.issues}
          catalog={catalog}
          categorySuggestions={categories.map((category) => category.name)}
          profiles={document.payments.map((profile) => profile.id)}
          onChange={change}
          onChangeCategory={changeCategory}
          onSave={save}
          onCancel={cancel}
        />
      )}

      <SettingsGroup title="Tu oferta" description="Lo que el asistente puede ofrecer, con su precio.">
      <Card icon="box" tone="sky" wide title={catalog ? "Catálogo" : "Planes y servicios"} description={`${entries.length} en total · ${entries.filter(isAvailable).length} disponibles`}>
        {listIssue && <Alert tone="warning">{listIssue.message}</Alert>}
        {entries.length === 0 ? (
          <EmptyState title="Aún no has agregado nada" description="Agrega lo que vendes para que el asistente pueda ofrecerlo." action={!editor ? <Button onClick={startNew}>{addLabel}</Button> : undefined} />
        ) : (
          <OfferingList
            document={document}
            onEdit={startEdit}
            onToggleAvailable={(entry) => actions.setEntryAvailability(entry.id, !isAvailable(entry))}
            onRemove={(entry) => actions.removeEntry(entry.id)}
          />
        )}
      </Card>

      {catalog && <CategoriesForm />}

      {catalog && document.payments.length > 1 && (
        <Card icon="wallet" tone="emerald" title="Perfil de pago del catálogo">
          <SelectField
            label="Con qué perfil se cobra"
            value={document.offer.catalog?.payment_profile ?? ""}
            options={[{ value: "", label: "Sin asignar" }, ...document.payments.map((profile) => ({ value: profile.id, label: profile.id }))]}
            onChange={(profile) => {
              const current = document.offer.catalog;
              if (current) actions.setRootValue("offer", { ...document.offer, catalog: { ...current, payment_profile: profile || null } });
            }}
          />
        </Card>
      )}

      </SettingsGroup>

      <SettingsGroup title="Entrega y existencias" description="Cómo recibe el cliente lo que compra. El asistente lo dice cuando le preguntan y no promete lo que no está aquí.">
        <ContractSection title="Domicilio" description="Si llevas los pedidos a domicilio: zonas, costo y tiempo." section="fulfillment" fields={["delivery"]} icon="truck" tone="sky" />
        <ContractSection title="Envíos" description="Envíos a otras ciudades o países, con transportadora." section="fulfillment" fields={["shipping"]} icon="send" tone="indigo" />
        <ContractSection title="Recogida en el local" description="Si el cliente puede pasar a recoger su pedido." section="fulfillment" fields={["pickup"]} icon="store" tone="amber" />
        <ContractSection title="Citas o reservas" description="Si tu servicio requiere agendar una cita o una reserva." section="fulfillment" fields={["scheduling"]} icon="clock" tone="violet" />
        {catalog && (
          <ContractSection
            title="Variantes y existencias"
            description="Tallas, colores y unidades disponibles de cada producto. El asistente dice qué opciones están agotadas, nunca cuántas quedan."
            section="inventory"
            icon="layers"
            tone="rose"
            wide
          />
        )}
      </SettingsGroup>

      <SectionPager current="catalog" />
    </>
  );
}
