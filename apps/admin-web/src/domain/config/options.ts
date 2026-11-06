import type { Identity, Location } from "../../contracts/businessConfig.v1";
import { RESPONSE_LENGTH_MAX_WORDS } from "../../contracts/businessConfig.v1";
import type { OfferModel, TransferMethodType } from "./types";

export interface Option<T extends string = string> {
  value: T;
  label: string;
  hint?: string;
}

export const OFFER_MODELS: Option<OfferModel>[] = [
  { value: "plans", label: "Planes o servicios", hint: "Vendes suscripciones, paquetes o servicios con precio definido." },
  { value: "catalog", label: "Catálogo de productos", hint: "Vendes productos o platos que el cliente elige de una lista." },
];

export const CURRENCIES: Option[] = [
  { value: "COP", label: "Pesos colombianos (COP)" },
  { value: "USD", label: "Dólares (USD)" },
];

/** Las monedas conocidas y, si es otra, la que ya tiene el dato: el contrato admite cualquier código ISO. */
export function currencyOptions(current: string): Option[] {
  return CURRENCIES.some((option) => option.value === current) ? CURRENCIES : [...CURRENCIES, { value: current, label: current }];
}

/** Opciones de largo de respuesta; el límite de palabras lo define el contrato del motor. */
export const RESPONSE_LENGTHS: Option<"short" | "medium" | "long">[] = [
  { value: "short", label: "Cortas", hint: `Ideal para chat: hasta ${RESPONSE_LENGTH_MAX_WORDS.short} palabras.` },
  { value: "medium", label: "Equilibradas", hint: `Algo más de explicación: hasta ${RESPONSE_LENGTH_MAX_WORDS.medium} palabras.` },
  { value: "long", label: "Detalladas", hint: `Respuestas más completas: hasta ${RESPONSE_LENGTH_MAX_WORDS.long} palabras.` },
];

export const FORMALITY_OPTIONS: Option<"" | "informal" | "neutral" | "formal">[] = [
  { value: "", label: "Sin indicar" },
  { value: "informal", label: "Informal (tutea)" },
  { value: "neutral", label: "Neutral" },
  { value: "formal", label: "Formal (trata de usted)" },
];

export const EMOJI_OPTIONS: Option<"" | "yes" | "no">[] = [
  { value: "", label: "Sin indicar" },
  { value: "yes", label: "Sí, puede usarlos" },
  { value: "no", label: "No" },
];

/**
 * Acciones que el motor ya reconoce en los negocios existentes (`config.capabilities.actions`). Las primarias generan
 * ingresos directos. El contrato admite otras: las que tenga un negocio se muestran también.
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

export const LOCATION_TYPES: Option<"" | Location["type"]>[] = [
  { value: "", label: "No indicar", hint: "El asistente no hablará de ubicación." },
  { value: "virtual", label: "Solo virtual", hint: "Atiendes por chat, llamada o en línea." },
  { value: "fisico", label: "Local físico", hint: "Los clientes pueden visitarte." },
  { value: "mixto", label: "Local físico y virtual" },
];

export const COVERAGE_TYPES: Option<NonNullable<Location["coverage"]>["type"]>[] = [
  { value: "local", label: "Local (barrios o una ciudad)" },
  { value: "nacional", label: "Nacional" },
  { value: "internacional", label: "Internacional" },
];

export const SERVICE_MODES: Option<NonNullable<Identity["service_modes"]>[number]>[] = [
  { value: "presencial", label: "Presencial" },
  { value: "virtual", label: "Virtual" },
  { value: "domicilio", label: "A domicilio" },
  { value: "recoger", label: "Para recoger" },
  { value: "envio", label: "Con envío" },
];

export const BANK_ACCOUNT_TYPES: Option[] = [
  { value: "ahorros", label: "Ahorros" },
  { value: "corriente", label: "Corriente" },
];

/**
 * Canales que el asistente puede mencionar a los clientes como medios de atención. `connector` indica si el motor tiene
 * hoy un conector para recibir mensajes por ese canal; el panel no conecta ningún canal.
 */
export const SERVICE_CHANNELS: (Option & { connector: boolean })[] = [
  { value: "whatsapp", label: "WhatsApp", connector: true },
  { value: "telegram", label: "Telegram", connector: true },
  { value: "instagram", label: "Instagram", connector: false },
  { value: "web", label: "Sitio web", connector: false },
];

export function labelFor<T extends string>(options: Option<T>[], value: T | string): string {
  return options.find((option) => option.value === value)?.label ?? humanize(value);
}

/** Etiqueta legible de un valor sin nombre propio: `activar_soporte` → `Activar soporte`. */
export function humanize(value: string): string {
  const text = value.replace(/[_-]+/g, " ").trim();
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** Las opciones conocidas y las que el negocio ya usa aunque no sean de la lista: no se pierden al editar. */
export function withCurrentValues<T extends Option>(options: T[], values: string[]): (T | Option)[] {
  const known = new Set(options.map((option) => option.value));
  return [...options, ...values.filter((value) => !known.has(value)).map((value) => ({ value, label: humanize(value) }))];
}
