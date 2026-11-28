import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { Alert, EmptyState } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { PageHeader } from "../../components/ui/Layout";
import { customerName } from "../../domain/commerce/pipeline";
import { bucketOf } from "../../domain/commerce/reminders";
import { BOARD_STAGES, type BoardStage, type Customer } from "../../domain/commerce/types";
import { DeleteChatDialog } from "../../layout/DeleteChatDialog";
import { useDebounced } from "../../lib/useDebounced";
import { CONVERSATIONS_ITEM } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useAuth } from "../../state/auth/useAuth";
import { useCan } from "../../state/roleContext";
import { useCommerceData } from "../../state/useCommerceData";
import { useCustomerFields } from "../../state/useCustomerFields";
import { useLabels } from "../../state/useLabels";
import { useReminders } from "../../state/useReminders";
import { BoardView } from "./customers/BoardView";
import { CustomerDrawer } from "./customers/card/CustomerDrawer";
import { CustomersList } from "./customers/CustomersList";
import { FieldsDialog } from "./customers/fields/FieldsDialog";
import { LabelsDialog } from "./customers/labels/LabelsDialog";
import { LostReasonDialog } from "./customers/LostReasonDialog";
import { PipelineStats } from "./customers/PipelineStats";
import { RemindersView } from "./customers/reminders/RemindersView";
import { useCustomerMoves } from "./customers/useCustomerMoves";
import { RecordSaleDialog } from "./RecordSaleDialog";

type View = "board" | "list" | "reminders";
const VIEWS: { view: View; label: string; icon: "layers" | "menu" | "clock"; param: string | null }[] = [
  { view: "board", label: "Tablero", icon: "layers", param: null },
  { view: "list", label: "Lista", icon: "menu", param: "lista" },
  { view: "reminders", label: "Recordatorios", icon: "clock", param: "recordatorios" },
];
const ALL_LABELS = "";

/** Lo que se está viendo en Clientes; viaja en la dirección. */
interface Place {
  view: View;
  stage: BoardStage | null;
  labelId: string | null;
  customerId: string | null;
}

/**
 * Clientes: cada persona que le escribió al negocio, por etapa. Arriba, los números del embudo; debajo, el tablero (una columna por
 * etapa) o la lista, que se filtran por una etiqueta, o los recordatorios del equipo (con cuántos están vencidos); tocar a un cliente
 * abre su ficha. La vista, los filtros y la ficha abierta viajan en la dirección (`?vista=lista&etapa=ready&etiqueta=…&cliente=…`),
 * para poder compartirla.
 */
export function CustomersPage() {
  const pathTo = useWorkspacePath();
  const canManageLabels = useCan("configure");
  const { verifiesCredentials } = useAuth();
  const [params, setParams] = useSearchParams();
  const place: Place = {
    view: VIEWS.find((item) => item.param !== null && item.param === params.get("vista"))?.view ?? "board",
    stage: BOARD_STAGES.find((item) => item === params.get("etapa")) ?? null,
    labelId: params.get("etiqueta"),
    customerId: params.get("cliente"),
  };
  const [query, setQuery] = useState("");
  const search = useDebounced(query.trim());
  const [version, setVersion] = useState(0);
  const refresh = useCallback(() => setVersion((count) => count + 1), []);
  const labels = useLabels(version);
  const { state } = useCommerceData((commerce) => commerce.pipeline(search, place.labelId), [search, place.labelId, version]);
  const moves = useCustomerMoves(refresh);
  const [deleting, setDeleting] = useState<Customer | null>(null);
  const [managingLabels, setManagingLabels] = useState(false);
  const [managingFields, setManagingFields] = useState(false);
  const fields = useCustomerFields(version);
  // «Míos» solo existe con cuentas: sin ellas (este equipo) todos los recordatorios son de todos.
  const [mine, setMine] = useState(verifiesCredentials);
  const reminders = useReminders(version, { mine });
  const overdue = reminders.status === "ready" ? reminders.data.filter((item) => bucketOf(item.dueAt) === "overdue").length : 0;

  const go = (change: Partial<Place>) => {
    const next = { ...place, ...change };
    const target = new URLSearchParams();
    const param = VIEWS.find((item) => item.view === next.view)?.param;
    if (param) target.set("vista", param);
    if (next.view === "list" && next.stage) target.set("etapa", next.stage);
    if (next.labelId) target.set("etiqueta", next.labelId);
    if (next.customerId) target.set("cliente", next.customerId);
    setParams(target, { replace: true });
  };
  const openCard = (customer: Customer | null) => go({ customerId: customer?.conversationId ?? null });
  const chatPath = (customer: Customer) => `${pathTo(CONVERSATIONS_ITEM.path)}?c=${customer.conversationId}`;

  // Si la etiqueta del filtro ya no existe (la borraron), el filtro se suelta.
  const staleLabel = labels.loaded && place.labelId !== null && !labels.list.some((label) => label.id === place.labelId);
  useEffect(() => {
    if (staleLabel) go({ labelId: null });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [staleLabel]);

  const pipeline = state.status === "ready" ? state.data : null;
  const filtering = Boolean(search) || place.labelId !== null;
  const nobody = pipeline !== null && !filtering && pipeline.columns.every((column) => column.count === 0);

  return (
    <>
      <PageHeader
        eyebrow="Atención"
        title="Clientes"
        description="Cada persona que le escribió a tu negocio, por etapa. El asistente la avanza solo con lo que reconoce en el chat, y tú la puedes mover cuando quieras."
      />

      <PipelineStats stats={pipeline?.stats ?? null} />

      <section className="data-panel customers-panel" aria-label="Clientes por etapa">
        <div className="data-panel__toolbar">
          {place.view === "reminders" ? (
            <p className="customers-panel__lead">Lo que tu equipo tiene que hacer con cada cliente, y cuándo.</p>
          ) : (
            <label className="search-field">
              <Icon name="search" size={16} />
              <span className="visually-hidden">Buscar cliente</span>
              <input className="search-field__input" type="search" placeholder="Buscar por nombre o teléfono" value={query} onChange={(event) => setQuery(event.target.value)} />
            </label>
          )}
          <div className="customers-tools">
            {labels.list.length > 0 && place.view !== "reminders" && (
              <label className="label-filter">
                <span className="visually-hidden">Filtrar por etiqueta</span>
                <select className="select label-filter__select" value={place.labelId ?? ALL_LABELS} onChange={(event) => go({ labelId: event.target.value || null })}>
                  <option value={ALL_LABELS}>Todas las etiquetas</option>
                  {labels.list.map((label) => (
                    <option key={label.id} value={label.id}>
                      {label.name} ({label.customers})
                    </option>
                  ))}
                </select>
              </label>
            )}
            <Button size="small" variant="secondary" onClick={() => setManagingLabels(true)}>
              <Icon name="tag" size={14} /> Etiquetas
            </Button>
            {canManageLabels && (
              <Button size="small" variant="secondary" onClick={() => setManagingFields(true)}>
                <Icon name="toggles" size={14} /> Campos
              </Button>
            )}
            <div className="view-switch" role="group" aria-label="Cómo ver los clientes">
              {VIEWS.map((item) => (
                <button key={item.view} type="button" className="view-switch__option" aria-pressed={place.view === item.view} onClick={() => go({ view: item.view, stage: null, customerId: null })}>
                  <Icon name={item.icon} size={15} />
                  {item.label}
                  {item.view === "reminders" && overdue > 0 && (
                    <span className="view-switch__badge" aria-label={`${overdue} ${overdue === 1 ? "vencido" : "vencidos"}`}>
                      {overdue}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>

        {moves.notice && (
          <p className={`move-notice move-notice--${moves.notice.tone}`} role={moves.notice.tone === "danger" ? "alert" : "status"}>
            {moves.notice.text}
          </p>
        )}

        {state.status === "loading" && <p className="data-panel__status" role="status">Cargando clientes…</p>}
        {state.status === "error" && (
          <div className="data-panel__status">
            <Alert tone="danger" title="No se pudieron cargar los clientes">
              <p>{state.message}</p>
              <Button size="small" variant="secondary" onClick={refresh}>
                Reintentar
              </Button>
            </Alert>
          </div>
        )}
        {nobody && place.view !== "reminders" && <EmptyState title="Aún no hay clientes" description="Cuando alguien le escriba a tu negocio por un canal conectado, aparece aquí con su etapa. Las pruebas del panel no cuentan." />}
        {pipeline && !nobody && place.view === "board" && (
          <BoardView
            columns={pipeline.columns}
            advance={pipeline.stats.advance}
            busyId={moves.busyId}
            onOpen={openCard}
            onMove={moves.request}
            onShowStage={(target) => go({ view: "list", stage: target, customerId: null })}
          />
        )}
        {place.view === "reminders" && (
          <RemindersView
            open={reminders}
            version={version}
            mine={mine}
            canChooseMine={verifiesCredentials}
            onMine={setMine}
            onOpenCustomer={(conversationId) => go({ customerId: conversationId })}
            onChanged={refresh}
          />
        )}
        {pipeline && !nobody && place.view === "list" && (
          <CustomersList
            version={version}
            query={query}
            stage={place.stage}
            labelId={place.labelId}
            busyId={moves.busyId}
            chatPath={chatPath}
            onOpen={openCard}
            onStage={(target) => go({ stage: target, customerId: null })}
            onMove={moves.request}
            onSell={moves.sell}
            onDelete={setDeleting}
          />
        )}
      </section>

      {place.customerId && (
        <CustomerDrawer
          conversationId={place.customerId}
          version={version}
          locked={moves.asking !== null || managingLabels || managingFields}
          busy={moves.busyId === place.customerId}
          labels={labels.list}
          chatPath={chatPath}
          onMove={moves.request}
          onSell={moves.sell}
          onManageLabels={() => setManagingLabels(true)}
          canManageFields={canManageLabels}
          onManageFields={() => setManagingFields(true)}
          onChanged={refresh}
          onClose={() => openCard(null)}
        />
      )}

      {managingLabels && <LabelsDialog labels={labels.list} canManage={canManageLabels} onChanged={refresh} onClose={() => setManagingLabels(false)} />}
      {managingFields && <FieldsDialog fields={fields.list} onChanged={refresh} onClose={() => setManagingFields(false)} />}

      {moves.asking?.kind === "reason" && (
        <LostReasonDialog
          customerName={customerName(moves.asking.customer)}
          saving={moves.busyId === moves.asking.customer.conversationId}
          onClose={moves.cancel}
          onConfirm={(reason) => void moves.confirmLost(reason)}
        />
      )}

      {moves.asking?.kind === "sale" && (
        <RecordSaleDialog customerName={moves.asking.customer.name ?? ""} conversationId={moves.asking.customer.conversationId} onClose={moves.cancel} onSaved={() => moves.sold()} />
      )}

      {deleting && (
        <DeleteChatDialog
          conversationId={deleting.conversationId}
          contactName={customerName(deleting)}
          onClose={() => setDeleting(null)}
          onDeleted={() => {
            setDeleting(null);
            refresh();
          }}
        />
      )}
    </>
  );
}
