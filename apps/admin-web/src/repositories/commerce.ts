import type { Customer, CustomerFilter, NewSale, Report, Sale } from "../domain/commerce/types";

/** Clientes, ventas y reportes de un negocio. Los fallos se rechazan con `PersistenceError` (un dato rechazado trae su campo). */
export interface Commerce {
  customers(filter?: CustomerFilter): Promise<Customer[]>;
  sales(days?: number): Promise<Sale[]>;
  recordSale(sale: NewSale): Promise<Sale>;
  cancelSale(saleId: string): Promise<Sale>;
  report(days: number): Promise<Report>;
}
