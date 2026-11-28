/**
 * El tablero de Clientes: una columna por etapa y los números del embudo, como los calcula el servidor
 * (`project/app/domain/business_config/pipeline.py`).
 */
import { LOST, formatMoney, type BoardStage, type Customer, type Stage } from "./types";

export interface StageColumn {
  stage: BoardStage;
  /** Cuántos clientes hay en la etapa; `customers` trae solo las tarjetas más recientes. */
  count: number;
  customers: Customer[];
}

export interface PipelineStats {
  /** Clientes que siguen en el embudo sin comprar. */
  openCount: number;
  lostCount: number;
  /** Las ventas de los últimos 30 días: cuántas y cuánto suman por moneda. */
  wonCount: number;
  won: Record<string, string>;
  /** De todos los clientes, qué parte compró (0 a 1). */
  closeRate: number | null;
  /** Días promedio desde el primer mensaje hasta la primera compra. */
  daysToBuy: number | null;
  /** De los que llegaron a cada etapa, qué parte llegó a la siguiente (0 a 1). */
  advance: Partial<Record<Stage, number | null>>;
}

export interface Pipeline {
  columns: StageColumn[];
  stats: PipelineStats;
}

/** Los motivos más comunes de «no compró», para elegir con un toque. */
export const LOST_REASONS = ["Le pareció caro", "No respondió más", "Compró en otro lado", "No era lo que buscaba"];
export const MAX_LOST_REASON = 200;

export function customerName(customer: Pick<Customer, "name" | "contact">): string {
  return customer.name || `+${customer.contact}`;
}

/** Cómo se hace un cambio de etapa: directo, pidiendo el motivo («No compró») o registrando la venta («Cliente»). */
export type MoveKind = "none" | "direct" | "reason" | "sale";

export function moveKind(from: BoardStage, to: BoardStage): MoveKind {
  if (from === to) return "none";
  if (to === "customer") return "sale";
  return to === LOST ? "reason" : "direct";
}

/** «71 %», o null si no hay con qué calcularlo. */
export function percent(rate: number | null | undefined): string | null {
  return rate === null || rate === undefined || !Number.isFinite(rate) ? null : `${Math.round(rate * 100)} %`;
}

/** «3 días», «1 día», «1,5 días», «menos de 1 día». */
export function daysText(days: number): string {
  if (days < 1) return "menos de 1 día";
  const rounded = Math.round(days * 10) / 10;
  return `${rounded.toLocaleString("es-CO")} ${rounded === 1 ? "día" : "días"}`;
}

/** Los totales por moneda, el principal primero (los pesos, si hay) y los demás después. */
export function moneyTotals(values: Record<string, string>): { main: string | null; rest: string[] } {
  const entries = Object.entries(values).sort(([a], [b]) => (a === "COP" ? -1 : b === "COP" ? 1 : a.localeCompare(b)));
  const [main, ...rest] = entries.map(([currency, amount]) => formatMoney(amount, currency));
  return { main: main ?? null, rest };
}

/** «Lleva $ 210.000 · 2 compras», o null si no ha comprado. */
export function boughtText(customer: Pick<Customer, "purchases" | "spent">): string | null {
  if (customer.purchases <= 0) return null;
  const { main, rest } = moneyTotals(customer.spent);
  const money = [main, ...rest].filter(Boolean).join(" + ");
  const count = `${customer.purchases} ${customer.purchases === 1 ? "compra" : "compras"}`;
  return money ? `Lleva ${money} · ${count}` : count;
}
