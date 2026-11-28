import type { CardChange, CustomerCard, CustomerNote } from "../domain/commerce/customerCard";
import type { CustomerField, FieldChange, FieldRawValue, FieldValue, NewFieldInput } from "../domain/commerce/customerFields";
import type { Label, LabelChange, LabelColor } from "../domain/commerce/labels";
import type { Pipeline } from "../domain/commerce/pipeline";
import type { NewReminderInput, Reminder } from "../domain/commerce/reminders";
import type { BoardStage, Customer, CustomerFilter, NewSale, Report, Sale } from "../domain/commerce/types";

/** Clientes, ventas y reportes de un negocio. Los fallos se rechazan con `PersistenceError` (un dato rechazado trae su campo). */
export interface Commerce {
  customers(filter?: CustomerFilter): Promise<Customer[]>;
  /** El tablero: una columna por etapa (con `query` o `labelId`, solo quienes coinciden) y los números del embudo. */
  pipeline(query?: string, labelId?: string | null): Promise<Pipeline>;
  /** Pasa al cliente a otra etapa; a «No compró», con su motivo. A «Cliente» no: se llega registrando la venta. */
  moveCustomer(conversationId: string, stage: BoardStage, reason?: string): Promise<Customer>;
  /** La ficha de un cliente: su valor, su responsable, sus compras, sus notas y su historial. */
  customerCard(conversationId: string): Promise<CustomerCard>;
  /** Cambia el valor y/o el responsable (solo lo que trae `change`) y devuelve la ficha como quedó. */
  updateCustomerCard(conversationId: string, change: CardChange): Promise<CustomerCard>;
  addCustomerNote(conversationId: string, body: string): Promise<CustomerNote>;
  deleteCustomerNote(conversationId: string, noteId: string): Promise<void>;
  /** El catálogo de etiquetas del negocio, por nombre, con cuántos clientes lleva cada una. */
  labels(): Promise<Label[]>;
  createLabel(name: string, color: LabelColor): Promise<Label>;
  /** Cambia el nombre y/o el color (solo lo que trae `change`). */
  updateLabel(labelId: string, change: LabelChange): Promise<Label>;
  /** Borra la etiqueta: sus clientes solo la pierden. */
  deleteLabel(labelId: string): Promise<void>;
  /** Deja al cliente con esas etiquetas (y solo esas). */
  setCustomerLabels(conversationId: string, labelIds: string[]): Promise<Customer>;
  /** Los campos del cliente del negocio, en el orden en que se crearon, con cuántos clientes tienen lleno cada uno. */
  customerFields(): Promise<CustomerField[]>;
  createCustomerField(input: NewFieldInput): Promise<CustomerField>;
  /** Cambia el nombre y/o las opciones (solo lo que trae `change`): quien tenía una opción que se quita queda sin valor. */
  updateCustomerField(fieldId: string, change: FieldChange): Promise<CustomerField>;
  /** Borra el campo y su valor en todos los clientes. */
  deleteCustomerField(fieldId: string): Promise<void>;
  /** Cambia los valores que trae `values` (por id de campo; null o vacío lo deja vacío), todos o ninguno. */
  setCustomerFieldValues(conversationId: string, values: Record<string, FieldRawValue>): Promise<FieldValue[]>;
  /** Los recordatorios pendientes por fecha (o los hechos, el último primero); con `mine`, solo los de quien mira. */
  reminders(filter?: { done?: boolean; mine?: boolean }): Promise<Reminder[]>;
  createReminder(conversationId: string, input: NewReminderInput): Promise<Reminder>;
  /** Lo marca hecho o lo vuelve a abrir. */
  setReminderDone(reminderId: string, done: boolean): Promise<Reminder>;
  deleteReminder(reminderId: string): Promise<void>;
  sales(days?: number): Promise<Sale[]>;
  recordSale(sale: NewSale): Promise<Sale>;
  cancelSale(saleId: string): Promise<Sale>;
  report(days: number): Promise<Report>;
}
