import { useCallback, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { Alert, EmptyState } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { PageHeader } from "../../components/ui/Layout";
import { customerName } from "../../domain/commerce/pipeline";
import { BOARD_STAGES, type BoardStage, type Customer } from "../../domain/commerce/types";
import { DeleteChatDialog } from "../../layout/DeleteChatDialog";
import { useDebounced } from "../../lib/useDebounced";
import { CONVERSATIONS_ITEM } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useCommerceData } from "../../state/useCommerceData";
import { BoardView } from "./customers/BoardView";
import { CustomersList } from "./customers/CustomersList";
import { LostReasonDialog } from "./customers/LostReasonDialog";
import { PipelineStats } from "./customers/PipelineStats";
import { useCustomerMoves } from "./customers/useCustomerMoves";
import { RecordSaleDialog } from "./RecordSaleDialog";

type View = "board" | "list";
const VIEWS: { view: View; label: string; icon: "layers" | "menu" }[] = [
  { view: "board", label: "Tablero", icon: "layers" },
  { view: "list", label: "Lista", icon: "menu" },
];

/**
 * Clientes: cada persona que le escribió al negocio, por etapa. Arriba, los números del embudo; debajo, el tablero (una columna por
 * etapa) o la lista. La vista y la etapa filtrada viajan en la dirección (`?vista=lista&etapa=ready`), para poder compartirla.
 */
export function CustomersPage() {
  const pathTo = useWorkspacePath();
  const [params, setParams] = useSearchParams();
  const view: View = params.get("vista") === "lista" ? "list" : "board";
  const stage = BOARD_STAGES.find((item) => item === params.get("etapa")) ?? null;
  const [query, setQuery] = useState("");
  const search = useDebounced(query.trim());
  const [version, setVersion] = useState(0);
  const refresh = useCallback(() => setVersion((count) => count + 1), []);
  const { state } = useCommerceData((commerce) => commerce.pipeline(search), [search, version]);
  const moves = useCustomerMoves(refresh);
  const [deleting, setDeleting] = useState<Customer | null>(null);

  const show = (next: View, filter: BoardStage | null = null) => {
    const search = new URLSearchParams();
    if (next === "list") search.set("vista", "lista");
    if (next === "list" && filter) search.set("etapa", filter);
    setParams(search, { replace: true });
  };
  const chatPath = (customer: Customer) => `${pathTo(CONVERSATIONS_ITEM.path)}?c=${customer.conversationId}`;
  const pipeline = state.status === "ready" ? state.data : null;
  const nobody = pipeline !== null && !search && pipeline.columns.every((column) => column.count === 0);

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
          <label className="search-field">
            <Icon name="search" size={16} />
            <span className="visually-hidden">Buscar cliente</span>
            <input className="search-field__input" type="search" placeholder="Buscar por nombre o teléfono" value={query} onChange={(event) => setQuery(event.target.value)} />
          </label>
          <div className="view-switch" role="group" aria-label="Cómo ver los clientes">
            {VIEWS.map((item) => (
              <button key={item.view} type="button" className="view-switch__option" aria-pressed={view === item.view} onClick={() => show(item.view)}>
                <Icon name={item.icon} size={15} />
                {item.label}
              </button>
            ))}
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
        {nobody && <EmptyState title="Aún no hay clientes" description="Cuando alguien le escriba a tu negocio por un canal conectado, aparece aquí con su etapa. Las pruebas del panel no cuentan." />}
        {pipeline && !nobody && view === "board" && (
          <BoardView columns={pipeline.columns} advance={pipeline.stats.advance} busyId={moves.busyId} chatPath={chatPath} onMove={moves.request} onShowStage={(target) => show("list", target)} />
        )}
        {pipeline && !nobody && view === "list" && (
          <CustomersList
            version={version}
            query={query}
            stage={stage}
            busyId={moves.busyId}
            chatPath={chatPath}
            onStage={(target) => show("list", target)}
            onMove={moves.request}
            onSell={moves.sell}
            onDelete={setDeleting}
          />
        )}
      </section>

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
