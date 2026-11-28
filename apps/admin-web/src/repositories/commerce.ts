import type { Pipeline } from "../domain/commerce/pipeline";
import type { BoardStage, Customer, CustomerFilter, NewSale, Report, Sale } from "../domain/commerce/types";

/** Clientes, ventas y reportes de un negocio. Los fallos se rechazan con `PersistenceError` (un dato rechazado trae su campo). */
export interface Commerce {
  customers(filter?: CustomerFilter): Promise<Customer[]>;
  /** El tablero: una columna por etapa (con `query`, solo quienes coinciden) y los números del embudo. */
  pipeline(query?: string): Promise<Pipeline>;
  /** Pasa al cliente a otra etapa; a «No compró», con su motivo. A «Cliente» no: se llega registrando la venta. */
  moveCustomer(conversationId: string, stage: BoardStage, reason?: string): Promise<Customer>;
  sales(days?: number): Promise<Sale[]>;
  recordSale(sale: NewSale): Promise<Sale>;
  cancelSale(saleId: string): Promise<Sale>;
  report(days: number): Promise<Report>;
}
