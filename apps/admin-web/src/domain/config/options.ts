import type {
  BankAccountType,
  BillingType,
  CommunicationTone,
  Currency,
  ResponseLength,
  SalesMode,
  TransferMethodType,
} from "./types";

export interface Option<T extends string = string> {
  value: T;
  label: string;
  hint?: string;
}

export const SALES_MODES: Option<SalesMode>[] = [
  { value: "plans", label: "Planes o servicios", hint: "Vendes suscripciones, paquetes o servicios con precio definido." },
  { value: "catalog", label: "Catálogo de productos", hint: "Vendes productos o platos que el cliente elige de una lista." },
];

export const CURRENCIES: Option<Currency>[] = [
  { value: "COP", label: "Pesos colombianos (COP)" },
  { value: "USD", label: "Dólares (USD)" },
];

export const BILLING_TYPES: Option<BillingType>[] = [
  { value: "one_time", label: "Pago único" },
  { value: "monthly", label: "Mensual" },
];

export const TONES: Option<CommunicationTone>[] = [
  { value: "cercano", label: "Cercano", hint: "Amable y conversacional, como un asesor de confianza." },
  { value: "profesional", label: "Profesional", hint: "Claro y respetuoso, sin exceso de confianza." },
  { value: "formal", label: "Formal", hint: "Trato de usted y lenguaje cuidado." },
  { value: "entusiasta", label: "Entusiasta", hint: "Energético y positivo." },
];

export const RESPONSE_LENGTHS: Option<ResponseLength>[] = [
  { value: "short", label: "Cortas", hint: "Ideal para chat: respuestas breves y directas." },
  { value: "medium", label: "Medianas", hint: "Algo más de explicación en cada respuesta." },
  { value: "long", label: "Detalladas", hint: "Respuestas más completas." },
];

/**
 * Acciones que el motor ya reconoce en los negocios existentes
 * (`config.capabilities.actions`). Las primarias generan ingresos directos.
 */
export const ASSISTANT_ACTIONS: (Option & { primary: boolean })[] = [
  { value: "cerrar_venta", label: "Cerrar ventas", primary: true },
  { value: "tomar_pedido", label: "Tomar pedidos", primary: true },
  { value: "enviar_pago", label: "Enviar datos de pago", primary: true },
  { value: "agendar_cita", label: "Agendar citas", primary: true },
  { value: "agendar_reserva", label: "Agendar reservas", primary: true },
  { value: "agendar_asesoria", label: "Agendar asesorías", primary: true },
  { value: "activar_servicio", label: "Activar el servicio", primary: true },
  { value: "activar_implementacion", label: "Iniciar implementación", primary: true },
  { value: "responder_dudas", label: "Responder dudas", primary: false },
  { value: "seguimiento", label: "Hacer seguimiento", primary: false },
  { value: "enviar_info", label: "Enviar información", primary: false },
  { value: "confirmar_datos", label: "Confirmar datos del cliente", primary: false },
];

const PRIMARY_ACTIONS: ReadonlySet<string> = new Set(ASSISTANT_ACTIONS.filter((action) => action.primary).map((action) => action.value));

/** Si la acción es de venta directa (las demás son de apoyo). */
export function isPrimaryAction(value: string): boolean {
  return PRIMARY_ACTIONS.has(value);
}

export function isKnownAction(value: string): boolean {
  return ASSISTANT_ACTIONS.some((action) => action.value === value);
}

export const CUSTOMER_DATA_FIELDS: Option[] = [
  { value: "nombre", label: "Nombre" },
  { value: "telefono", label: "Teléfono" },
  { value: "direccion", label: "Dirección" },
  { value: "detalles", label: "Detalles del pedido o caso" },
];

export const TRANSFER_METHOD_TYPES: Option<TransferMethodType>[] = [
  { value: "nequi", label: "Nequi" },
  { value: "daviplata", label: "Daviplata" },
  { value: "bank", label: "Cuenta bancaria" },
  { value: "breb", label: "Bre-B" },
];

export const BANK_ACCOUNT_TYPES: Option<BankAccountType>[] = [
  { value: "ahorros", label: "Ahorros" },
  { value: "corriente", label: "Corriente" },
];

/**
 * Canales que el asistente puede mencionar a los clientes como medios de atención.
 * `connector` indica si el motor tiene hoy un conector para recibir mensajes por ese canal;
 * por ahora el panel no conecta ningún canal.
 */
export const SERVICE_CHANNELS: (Option & { connector: boolean })[] = [
  { value: "whatsapp", label: "WhatsApp", connector: true },
  { value: "telegram", label: "Telegram", connector: true },
  { value: "instagram", label: "Instagram", connector: false },
  { value: "web", label: "Sitio web", connector: false },
];

export function labelFor<T extends string>(options: Option<T>[], value: T | string): string {
  return options.find((option) => option.value === value)?.label ?? value;
}
