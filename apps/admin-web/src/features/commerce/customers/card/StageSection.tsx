import { Button } from "../../../../components/ui/Button";
import { nextStage, sinceText } from "../../../../domain/commerce/customerCard";
import { STAGES, STAGE_LABELS, type BoardStage, type Customer } from "../../../../domain/commerce/types";
import { relativeTime } from "../../../../domain/inbox/format";
import { MoveMenu } from "../MoveMenu";

/**
 * Dónde va el cliente: la barra del embudo con su etapa resaltada, hace cuánto está ahí, y el paso siguiente a un toque («Mover a
 * … →», «No compró», o cualquier otra etapa con «Mover a…»).
 */
export function StageSection({ customer, stageSince, busy, onMove }: { customer: Customer; stageSince: string | null; busy: boolean; onMove: (stage: BoardStage) => void }) {
  const index = STAGES.indexOf(customer.stage as (typeof STAGES)[number]);
  const lost = customer.stage === "lost";
  const next = nextStage(customer.stage);
  return (
    <section className="card-section" aria-label="Etapa">
      <header className="card-section__head">
        <h3>Etapa</h3>
        {stageSince && (
          <time className="card-section__aside" dateTime={stageSince}>
            {sinceText(relativeTime(stageSince))}
          </time>
        )}
      </header>
      <ol className="stage-bar" aria-label={`Va en «${STAGE_LABELS[customer.stage]}»`}>
        {STAGES.map((stage, position) => (
          <li
            key={stage}
            className={`stage-bar__step stage-tone--${stage}${index >= 0 && position <= index ? " stage-bar__step--done" : ""}${position === index ? " stage-bar__step--current" : ""}`}
            aria-current={position === index ? "step" : undefined}
          >
            <span className="stage-bar__line" aria-hidden="true" />
            <span className="stage-bar__name">{STAGE_LABELS[stage]}</span>
          </li>
        ))}
      </ol>
      {lost && (
        <p className="stage-lost stage-tone--lost">
          Está en <strong>«No compró»</strong>
          {customer.lostReason ? `: ${customer.lostReason}` : ", sin motivo anotado"}.
        </p>
      )}
      <div className="card-section__actions">
        {next && (
          <Button size="small" disabled={busy} onClick={() => onMove(next)}>
            {next === "customer" ? "Registrar su venta →" : lost ? "Volver al embudo →" : `Mover a ${STAGE_LABELS[next]} →`}
          </Button>
        )}
        {!lost && customer.stage !== "customer" && (
          <Button size="small" variant="secondary" disabled={busy} onClick={() => onMove("lost")}>
            No compró
          </Button>
        )}
        <MoveMenu current={customer.stage} label="Mover a otra etapa" disabled={busy} onMove={onMove} />
      </div>
    </section>
  );
}
