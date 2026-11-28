import { describeEvent, type CustomerEvent } from "../../../../domain/commerce/customerCard";
import { relativeTime } from "../../../../domain/inbox/format";

/** Lo que le ha pasado a este cliente, lo más reciente primero: cada cambio en una frase, con quién lo hizo y cuándo. */
export function HistorySection({ events }: { events: CustomerEvent[] }) {
  return (
    <section className="card-section" aria-label="Historial">
      <header className="card-section__head">
        <h3>Historial</h3>
      </header>
      {events.length === 0 ? (
        <p className="card-section__empty">Aún no hay movimientos.</p>
      ) : (
        <ol className="history">
          {events.map((event) => {
            const line = describeEvent(event);
            return (
              <li key={event.id} className={`history__item history__item--${line.tone} stage-tone--${line.tone}`}>
                <span className="history__dot" aria-hidden="true" />
                <span className="history__text">
                  <strong>{line.title}</strong>
                  <span>
                    {line.by} · <time dateTime={event.createdAt}>{relativeTime(event.createdAt)}</time>
                  </span>
                </span>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
