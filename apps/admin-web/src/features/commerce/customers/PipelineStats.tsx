import { daysText, moneyTotals, percent, type PipelineStats as Stats } from "../../../domain/commerce/pipeline";

const plural = (count: number, one: string, many: string) => `${count} ${count === 1 ? one : many}`;

/**
 * Los números del embudo, dichos como los diría el dueño: cuántos siguen abiertos, cuánto se vendió, de cada 100 cuántos compran y
 * cuánto tardan. Con varias monedas, la principal va en grande y las demás debajo: nunca se suman entre sí.
 */
export function PipelineStats({ stats }: { stats: Stats | null }) {
  const won = stats ? moneyTotals(stats.won) : { main: null, rest: [] };
  const rate = stats ? percent(stats.closeRate) : null;
  const cards: { label: string; value: string; meta: string; tone?: "won" }[] = [
    {
      label: "En el embudo",
      value: stats ? String(stats.openCount) : "—",
      meta: stats ? (stats.openCount === 1 ? "cliente que aún no compra" : "clientes que aún no compran") : "",
    },
    {
      label: "Vendido · 30 días",
      value: won.main ?? "—",
      meta: stats ? [plural(stats.wonCount, "venta", "ventas"), ...won.rest.map((money) => `+ ${money}`)].join(" · ") : "",
      tone: "won",
    },
    {
      label: "De cada 100, compran",
      value: rate ? rate.replace(" %", "") : "—",
      meta: stats ? (stats.lostCount > 0 ? `${plural(stats.lostCount, "no compró", "no compraron")}` : "Nadie se ha perdido") : "",
    },
    {
      label: "Tardan en comprar",
      value: stats?.daysToBuy === null || stats?.daysToBuy === undefined ? "—" : daysText(stats.daysToBuy),
      meta: "desde que escriben (últimos 90 días)",
    },
  ];
  return (
    <section className="pipeline-stats" aria-label="Resumen del embudo">
      {cards.map((card) => (
        <div key={card.label} className="pipeline-stats__card">
          <span className="pipeline-stats__label">{card.label}</span>
          <span className={`pipeline-stats__value${card.tone === "won" && stats && stats.wonCount > 0 ? " pipeline-stats__value--won" : ""}`}>{card.value}</span>
          <span className="pipeline-stats__meta">{card.meta}</span>
        </div>
      ))}
    </section>
  );
}
