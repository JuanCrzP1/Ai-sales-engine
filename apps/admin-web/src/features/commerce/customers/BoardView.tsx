import { useState } from "react";
import { customerName, moneyTotals, percent, type PipelineStats, type StageColumn } from "../../../domain/commerce/pipeline";
import { STAGES, STAGE_HINTS, STAGE_LABELS, type BoardStage, type Customer } from "../../../domain/commerce/types";
import { CustomerCard } from "./CustomerCard";

/** Lo que dice cada columna bajo su nombre (corto) y al pasar el cursor (completo): qué parte avanza a la siguiente etapa. */
function columnNote(stage: BoardStage, advance: PipelineStats["advance"]): { text: string; title: string } {
  if (stage === "customer") return { text: "Ya compraron", title: STAGE_HINTS[stage] };
  if (stage === "lost") return { text: "Fuera del embudo", title: STAGE_HINTS[stage] };
  const next = STAGES[STAGES.indexOf(stage) + 1];
  const rate = percent(advance[stage]);
  if (!rate || !next) return { text: "Sin datos todavía", title: STAGE_HINTS[stage] };
  return { text: `${rate} avanza`, title: `De los que llegaron a «${STAGE_LABELS[stage]}», ${rate} llegó a «${STAGE_LABELS[next]}».` };
}

/**
 * El tablero: una columna por etapa del embudo y, al final, «No compró». Una tarjeta se arrastra a otra columna (la que la recibe se
 * ilumina) o se mueve con «Mover a…». Cada columna dice cuánto suman los valores de sus clientes y trae los más recientes; si hay
 * más, lleva a verlos en la lista.
 */
export function BoardView({
  columns,
  advance,
  busyId,
  onOpen,
  onMove,
  onShowStage,
}: {
  columns: StageColumn[];
  advance: PipelineStats["advance"];
  busyId: string | null;
  onOpen: (customer: Customer) => void;
  onMove: (customer: Customer, stage: BoardStage) => void;
  onShowStage: (stage: BoardStage) => void;
}) {
  const [dragged, setDragged] = useState<Customer | null>(null);
  const [over, setOver] = useState<BoardStage | null>(null);
  const release = () => {
    setDragged(null);
    setOver(null);
  };

  return (
    <div className="board" role="group" aria-label="Tablero de clientes por etapa">
      {columns.map((column) => {
        const receiving = dragged !== null && over === column.stage && dragged.stage !== column.stage;
        const hidden = column.count - column.customers.length;
        const note = columnNote(column.stage, advance);
        const worth = moneyTotals(column.value);
        return (
          <section
            key={column.stage}
            className={`board__column stage-tone--${column.stage}${receiving ? " board__column--over" : ""}${column.stage === "lost" ? " board__column--lost" : ""}`}
            aria-label={`${STAGE_LABELS[column.stage]}: ${column.count}`}
            onDragOver={(event) => {
              if (!dragged) return;
              event.preventDefault();
              setOver(column.stage);
            }}
            onDragLeave={() => setOver((current) => (current === column.stage ? null : current))}
            onDrop={(event) => {
              event.preventDefault();
              if (dragged && dragged.stage !== column.stage) onMove(dragged, column.stage);
              release();
            }}
          >
            <header className="board__header">
              <span className="board__title">
                <span className="board__dot" aria-hidden="true" />
                <h2>{STAGE_LABELS[column.stage]}</h2>
                <span className="board__count">{column.count}</span>
              </span>
              <span className="board__note" title={note.title}>
                {note.text}
              </span>
              {worth.main && <span className="board__worth">{[worth.main, ...worth.rest].join(" + ")}</span>}
            </header>
            {receiving && <p className="board__drop">Suelta aquí para pasar a {customerName(dragged)} a «{STAGE_LABELS[column.stage]}»</p>}
            {column.customers.map((customer) => (
              <CustomerCard
                key={customer.conversationId}
                customer={customer}
                onOpen={() => onOpen(customer)}
                dragging={dragged?.conversationId === customer.conversationId}
                busy={busyId === customer.conversationId}
                onMove={(stage) => onMove(customer, stage)}
                onDragStart={() => setDragged(customer)}
                onDragEnd={release}
              />
            ))}
            {column.count === 0 && !receiving && <p className="board__empty">Nadie aquí</p>}
            {hidden > 0 && (
              <button type="button" className="board__more" onClick={() => onShowStage(column.stage)}>
                + {hidden} más · ver en lista
              </button>
            )}
          </section>
        );
      })}
    </div>
  );
}
