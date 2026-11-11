import { useState } from "react";
import { BarChart, KpiTile, SplitBar } from "../../components/ui/Charts";
import { Alert } from "../../components/ui/Feedback";
import { PageHeader } from "../../components/ui/Layout";
import { STAGE_LABELS, STAGES, change, formatMoney, type Report } from "../../domain/commerce/types";
import { HANDOFF_LABELS, type HandoffReason } from "../../domain/inbox/types";
import { useCommerceData } from "../../state/useCommerceData";

const PERIODS = [7, 30, 90] as const;
const DAY = new Intl.DateTimeFormat("es-CO", { day: "numeric", month: "short", timeZone: "UTC" });
const LONG_DAY = new Intl.DateTimeFormat("es-CO", { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" });

const dayLabel = (iso: string) => DAY.format(new Date(`${iso}T00:00:00Z`));
const dayTitle = (iso: string) => LONG_DAY.format(new Date(`${iso}T00:00:00Z`));

/** Cómo le va al negocio: conversaciones, ventas, el embudo, quién responde y cuánto cuesta la IA, frente al periodo anterior. */
export function ReportsPage() {
  const [days, setDays] = useState<(typeof PERIODS)[number]>(30);
  const { state } = useCommerceData((commerce) => commerce.report(days), [days]);
  const report = state.status === "ready" ? state.data : null;

  return (
    <>
      <PageHeader
        eyebrow="Ventas"
        title="Reportes"
        description="Cómo le va a tu negocio: conversaciones, ventas, en qué etapa quedan tus clientes y quién responde. Comparado con el periodo anterior."
        actions={
          <div className="segmented" role="group" aria-label="Periodo">
            {PERIODS.map((option) => (
              <button key={option} type="button" className="segmented__option" aria-pressed={days === option} onClick={() => setDays(option)}>
                {option} días
              </button>
            ))}
          </div>
        }
      />

      {state.status === "error" && <Alert tone="danger" title="No se pudo cargar el reporte">{state.message}</Alert>}
      {state.status === "loading" && <p className="field__hint" role="status">Cargando el reporte…</p>}
      {report && <ReportView report={report} days={days} />}
    </>
  );
}

function ReportView({ report, days }: { report: Report; days: number }) {
  const { totals, previous } = report;
  const revenue = Object.entries(totals.revenue).sort((a, b) => Number(b[1]) - Number(a[1]));
  const mainCurrency = revenue[0]?.[0] ?? "COP";
  const revenueNow = Number(totals.revenue[mainCurrency] ?? 0);
  const revenueBefore = Number(previous.revenue[mainCurrency] ?? 0);
  const answered = totals.assistantMessages + totals.agentMessages;
  const funnelTop = Math.max(1, report.funnel.new);
  const reasons = Object.entries(report.handoffsByReason).sort((a, b) => b[1] - a[1]);

  return (
    <>
      <p className="report-period">
        Del {dayTitle(report.since)} al {dayTitle(report.until)} · frente a los {days} días anteriores
      </p>

      <div className="kpi-grid">
        <KpiTile label="Conversaciones nuevas" icon="inbox" value={totals.conversations} delta={change(totals.conversations, previous.conversations)} />
        <KpiTile label="Ventas" icon="tag" value={totals.sales} delta={change(totals.sales, previous.sales)} />
        <KpiTile
          label="Ingresos"
          icon="wallet"
          value={formatMoney(revenueNow, mainCurrency)}
          delta={change(revenueNow, revenueBefore)}
          hint={revenue.length > 1 ? revenue.slice(1).map(([currency, amount]) => formatMoney(amount, currency)).join(" · ") : undefined}
        />
        <KpiTile label="Pasaron a una persona" icon="headset" value={totals.handoffs} delta={change(totals.handoffs, previous.handoffs)} better="down" />
      </div>

      <div className="report-grid">
        <section className="report-card report-card--wide" aria-labelledby="r-conversaciones">
          <header className="report-card__header">
            <h2 id="r-conversaciones" className="report-card__title">
              Conversaciones nuevas por día
            </h2>
            <span className="report-card__total">{totals.conversations} en total</span>
          </header>
          <BarChart
            label="Conversaciones nuevas por día"
            unit={totals.conversations === 1 ? "conversación" : "conversaciones"}
            data={report.days.map((day) => ({ key: day.day, label: dayLabel(day.day), title: dayTitle(day.day), value: day.newConversations }))}
          />
        </section>

        <section className="report-card" aria-labelledby="r-embudo">
          <header className="report-card__header">
            <h2 id="r-embudo" className="report-card__title">
              Embudo de ventas
            </h2>
            <span className="report-card__total">Clientes que llegaron a cada etapa</span>
          </header>
          <ol className="funnel">
            {STAGES.map((stage) => {
              const value = report.funnel[stage] ?? 0;
              const share = Math.round((value / funnelTop) * 100);
              return (
                <li key={stage} className="funnel__row">
                  <span className="funnel__label">{STAGE_LABELS[stage]}</span>
                  <span className="funnel__track" aria-hidden="true">
                    <span className="funnel__bar" style={{ width: `${Math.max(value ? 3 : 0, share)}%` }} />
                  </span>
                  <span className="funnel__value">
                    <strong>{value}</strong> {stage !== "new" && report.funnel.new > 0 ? <span className="funnel__share">{share} %</span> : null}
                  </span>
                </li>
              );
            })}
          </ol>
        </section>

        <section className="report-card" aria-labelledby="r-respuestas">
          <header className="report-card__header">
            <h2 id="r-respuestas" className="report-card__title">
              Quién respondió
            </h2>
            <span className="report-card__total">{answered} mensajes enviados</span>
          </header>
          <SplitBar
            label="Quién respondió"
            parts={[
              { label: "Asistente IA", value: totals.assistantMessages, tone: "ai" },
              { label: "Tu equipo", value: totals.agentMessages, tone: "team" },
            ]}
          />
          <dl className="report-facts">
            <div>
              <dt>Mensajes de clientes</dt>
              <dd>{totals.customerMessages}</dd>
            </div>
            <div>
              <dt>Costo de la IA</dt>
              <dd>{report.aiCostUsd == null ? "—" : formatMoney(report.aiCostUsd, "USD")}</dd>
            </div>
          </dl>
        </section>

        <section className="report-card" aria-labelledby="r-ventas">
          <header className="report-card__header">
            <h2 id="r-ventas" className="report-card__title">
              Ventas por día
            </h2>
            <span className="report-card__total">{totals.sales} en total</span>
          </header>
          <BarChart
            label="Ventas por día"
            unit={totals.sales === 1 ? "venta" : "ventas"}
            height={140}
            data={report.days.map((day) => ({ key: day.day, label: dayLabel(day.day), title: dayTitle(day.day), value: day.sales }))}
          />
        </section>

        <section className="report-card" aria-labelledby="r-personas">
          <header className="report-card__header">
            <h2 id="r-personas" className="report-card__title">
              Por qué pasaron a una persona
            </h2>
            <span className="report-card__total">{totals.handoffs} en total</span>
          </header>
          {reasons.length === 0 ? (
            <p className="field__hint">Ningún chat pasó a tu equipo en este periodo.</p>
          ) : (
            <ul className="reason-list">
              {reasons.map(([reason, count]) => (
                <li key={reason}>
                  <span>{HANDOFF_LABELS[reason as HandoffReason] ?? reason}</span>
                  <strong>{count}</strong>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </>
  );
}
