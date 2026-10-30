// ARCHIVO GENERADO por scripts/generate_business_config_types.py. No editar a mano.
// Fuente: project/config/contracts/v1/business-config.schema.json y
// project/app/domain/business_config/engine_policy.py.
// Marcas: `audiencia` (cliente, avanzado, operador, sistema) y `motor` (conectado, pendiente,
// conservado); un campo sin marca toma la de su sección. Ver docs/business-config.md.

export const SCHEMA_VERSION = "1.0";
export const RESPONSE_LENGTH_MAX_WORDS = {"short": 60, "medium": 75, "long": 100} as const;
export const MIN_MAX_WORDS = 20;
export const MAX_FAQS = 30;
export const MAX_FAQ_QUESTION_CHARS = 200;
export const MAX_FAQ_ANSWER_CHARS = 800;
export const RESPONSE_LENGTH_WORD_RANGES = {"short": [20, 60], "medium": [61, 75], "long": [76, null]} as const;
export const MAX_PROFILE_ITEMS = 10;
export const MAX_PROFILE_ITEM_CHARS = 300;
export const MAX_TONE_CHARS = 160;
export const MAX_PROMOTIONS = 10;
export const PROMPT_WORD_LIMITS = {"industry": 8, "value_proposition": 30, "description": 20, "offer_description": 25} as const;
export const PROMPT_MAX_PROBLEMS = 2;
export const PROMPT_MAX_CATEGORIES = 4;

export interface BuyingMotivation {
  primary: string;
  secondary?: string | null;
}

/** Canales, acciones, métodos de cierre y datos que se piden al cliente. */
export interface Capabilities {
  /** Canales de atención al cliente. [motor: conectado] */
  service_channels?: string[];
  /** Canales por los que funciona el producto que se vende. [motor: conectado] */
  product_channels?: string[];
  /** Acciones de venta. [motor: conectado] */
  actions_primary?: string[];
  /** Acciones de apoyo. [motor: conectado] */
  actions_support?: string[];
  /** Cómo puede cerrar el asistente una venta. [motor: conectado] */
  closing_methods: ClosingMethods;
  /** Datos que el asistente pide al cliente. */
  data_collection: DataCollection;
  /** Situaciones en las que el asistente pasa la conversación a una persona. */
  human_handoff_when?: string[] | null;
  /** Lo que el negocio no hace ni promete. */
  restrictions?: Restrictions | null;
}

export interface Catalog {
  /** [motor: conectado] */
  categories: CatalogCategory[];
  items: CatalogItem[];
  /** Perfil de pago con el que se cobra. [motor: conectado] */
  payment_profile?: string | null;
}

export interface CatalogCategory {
  id: string;
  name: string;
}

/** Producto del catálogo. */
export interface CatalogItem {
  id: string;
  name: string;
  /** Id de su categoría; una categoría sin productos disponibles no se ofrece. [motor: conectado] */
  category: string;
  /** Detalle del producto. */
  description?: string | null;
  prices: ItemPrice[];
  /** Características del producto. */
  features?: string[] | null;
  /** Si es false, el producto se conserva pero no se ofrece (ni su categoría, si se queda sin productos). [motor: conectado] */
  available?: boolean;
}

export interface Closing {
  /** Venta directa, captación de datos, reserva o compra con pago (checkout). */
  strategy: "direct_sale" | "lead_capture" | "booking" | "checkout";
  /** Datos que necesita el cierre (name, phone, address...). */
  required_data?: string[] | null;
  /** Frases que indican intención de compra. */
  purchase_signals?: string[] | null;
  /** Qué hacer ante una intención de compra alta. */
  high_intent_actions?: string[] | null;
  /** Siguientes pasos que el asistente propone. */
  next_steps?: string[] | null;
  /** Compromisos pequeños para avanzar. */
  micro_commitments?: string[] | null;
  /** Reglas de cierre del negocio. */
  rules?: string[] | null;
}

export interface ClosingMethods {
  payment_link: boolean;
  human_handoff: boolean;
  data_collection: boolean;
}

export interface ConversationFlow {
  /** Etapas internas del motor, en orden (p. ej. detect_pain, present_solution). */
  steps: string[];
  no_skip_steps?: boolean | null;
  /** Guiar al cliente paso a paso en un proceso (trámites, matrículas). */
  guided_process?: boolean | null;
}

export interface ConversationWindows {
  /** Minutos sin mensajes tras los que la conversación deja de estar activa. */
  active_window_minutes: number;
  /** Horas sin mensajes tras las que la conversación empieza de nuevo. */
  reset_hours: number;
}

export interface Cost {
  type: "fijo" | "variable" | "gratis";
  value: number;
}

export interface Coverage {
  type: "local" | "nacional" | "internacional";
  zones?: string[];
}

export interface CustomerProblem {
  /** [motor: conectado] */
  id: string;
  /** Qué le causa el problema al cliente. [motor: conectado] */
  impacts?: string[] | null;
  /** Frases del cliente que revelan el problema. [audiencia: avanzado] */
  signals?: string[] | null;
  /** Cómo el problema le cuesta dinero al cliente. [audiencia: avanzado] */
  monetization?: string[] | null;
  /** Mensajes según la urgencia. [audiencia: avanzado] */
  urgency_levels?: Record<string, string[]> | null;
  /** Ángulos de venta para este problema. [audiencia: avanzado] */
  recommended_angles?: string[] | null;
}

export interface DataCollection {
  /** [motor: conectado] */
  enabled: boolean;
  /** [motor: conectado] */
  fields?: ("nombre" | "telefono" | "direccion" | "detalles")[];
  /** Aviso de tratamiento de datos personales que el asistente comparte al pedirlos. */
  consent_notice?: string | null;
}

export interface Delivery {
  available: boolean;
  type?: "propio" | "tercero" | null;
  zones?: string[];
  cost?: Cost | null;
  time?: TimeWindow | null;
}

export interface Discovery {
  /** Preguntas para entender al cliente. */
  questions?: string[] | null;
  /** Qué debe averiguar el asistente. [audiencia: avanzado] */
  objectives?: string[] | null;
}

export interface EngineFeatures {
  /** Bandera heredada: el motor solo la consulta si no hay precios ni pagos, y el contrato siempre los exige. */
  pricing_enabled: boolean;
  /** Debe coincidir con `offer.model` (catalog). [motor: conectado] */
  catalog_mode: boolean;
  /** Modelo de negocio con el que el motor decide cuándo mostrar precios. [motor: conectado] */
  business_model?: "saas" | "catalog" | "checkout" | "service_booking" | "process" | null;
}

export interface EngineSettings {
  /** [motor: conectado] */
  conversation?: ConversationWindows | null;
  features: EngineFeatures;
}

export interface Faq {
  question: string;
  answer: string;
}

export interface Financing {
  available: boolean;
  /** Entidades con las que se financia. */
  providers?: string[];
  /** Modalidades (abono, cuotas...). */
  options?: string[];
}

/** Cómo recibe el cliente lo que compra. Los modos que no aplican se omiten. */
export interface Fulfillment {
  delivery?: Delivery | null;
  shipping?: Shipping | null;
  pickup?: Pickup | null;
  scheduling?: Scheduling | null;
}

export interface Identity {
  /** Nombre del negocio. */
  name: string;
  /** Marca con la que el asistente presenta al negocio, si es distinta del nombre. */
  brand_name?: string | null;
  /** Sector o tipo de negocio, en pocas palabras. [motor: conectado] */
  industry: string;
  /** Qué hace el negocio. */
  description: string;
  /** Promesa comercial: qué gana el cliente. [motor: conectado] */
  value_proposition: string;
  /** A quién se dirige y qué problema resuelve. */
  positioning?: string | null;
  /** Por qué elegir este negocio y no otro. */
  differentiators?: string[] | null;
  /** Dónde está y a qué zonas atiende. */
  location?: Location | null;
  /** Cómo recibe el cliente el servicio o producto. */
  service_modes?: ("virtual" | "presencial" | "domicilio" | "recoger" | "envio")[] | null;
  /** Cliente ideal. */
  target_customer?: TargetCustomer | null;
  /** Pruebas de confianza: casos, resultados, trayectoria. */
  credibility?: string[] | null;
  /** Horarios de atención. */
  opening_hours?: OpeningHours[] | null;
}

/** Variantes y existencias de los productos del catálogo. */
export interface Inventory {
  items?: InventoryItem[];
  /** Si el negocio controla existencias. */
  track_stock?: boolean | null;
}

export interface InventoryItem {
  /** Id de un producto del catálogo. */
  product_id: string;
  variants?: Variant[];
}

export interface ItemPrice {
  currency: string;
  amount: number;
}

export interface Knowledge {
  /** Preguntas frecuentes con su respuesta oficial. */
  faqs?: Faq[];
}

export interface Location {
  /** virtual, fisico (local propio) o mixto. */
  type: "virtual" | "fisico" | "mixto";
  address?: string | null;
  city?: string | null;
  coverage?: Coverage | null;
}

export interface Messages {
  /** Primer mensaje de cada conversación nueva, si está activo. [motor: conectado] */
  welcome: WelcomeMessage;
  /** Respuesta exacta cuando el cliente reporta un pago. [motor: conectado] */
  payment_reported?: string | null;
  /** Mensaje cuando el pago queda confirmado. [motor: conectado] */
  payment_confirmed?: string | null;
  /** Mensaje después de una compra. */
  after_sale?: string | null;
  /** Mensaje para pedir los datos del cliente. */
  data_request?: string | null;
  /** Mensaje de seguimiento a un cliente que no respondió. */
  follow_up?: string | null;
  /** Mensaje al pasar la conversación a una persona. */
  human_handoff?: string | null;
}

export interface MotivationDriver {
  /** Motivo de compra (p. ej. tiempo, dinero). */
  motivation: string;
  description: string;
  /** Frases del cliente que revelan este motivo. */
  signals?: string[];
}

export interface ObjectionHandling {
  /** Objeción que se atiende (p. ej. price). */
  topic: string;
  /** Cómo reconocer la objeción. */
  acknowledge?: string[] | null;
  /** Cómo replantearla. */
  reframe?: string[] | null;
  /** Pruebas que la desmienten. */
  proof?: string[] | null;
  /** Cómo volver al siguiente paso. */
  redirect?: string[] | null;
  /** Reglas al responder esta objeción. */
  rules?: string[] | null;
}

export interface Offer {
  /** plans: planes o servicios; catalog: productos de un catálogo. [motor: conectado] */
  model: "plans" | "catalog";
  plans?: Plan[] | null;
  catalog?: Catalog | null;
}

/** Tipos de oferta en texto libre (no son ids de la oferta). */
export interface OfferMix {
  /** Ofertas principales. */
  core?: string[];
  /** Mejoras para vender más. */
  upsell?: string[];
  /** Complementos para vender junto. */
  cross_sell?: string[];
}

export interface OfferPresentation {
  /** Cómo presentar cuando hay una sola opción. */
  single_offer?: string[] | null;
  /** Cómo presentar cuando hay varias opciones. */
  multiple_offers?: string[] | null;
}

export interface OpeningHours {
  days: ("lunes" | "martes" | "miercoles" | "jueves" | "viernes" | "sabado" | "domingo")[];
  /** Hora HH:MM (24 h). */
  opens: string;
  /** Hora HH:MM (24 h). */
  closes: string;
}

/** Cómo se cobra: link de pago y transferencias. El motor entrega los datos al cliente cuando elige el método. */
export interface PaymentProfile {
  /** [motor: conectado] */
  id: string;
  /** [motor: conectado] */
  link?: SecretRef | null;
  /** [motor: conectado] */
  transfer_enabled: boolean;
  /** [motor: conectado] */
  transfer_methods?: TransferMethod[];
  /** Indicaciones para pagar, sin números ni links (esos datos son secretos). */
  instructions?: string | null;
}

export interface Pickup {
  available: boolean;
  instructions?: string;
}

/** Plan o servicio. */
export interface Plan {
  /** [motor: conectado] */
  id: string;
  /** [motor: conectado] */
  name: string;
  /** Detalle del plan. */
  description?: string | null;
  /** [motor: conectado] */
  prices: PlanPrice[];
  /** [motor: conectado] */
  includes?: string[] | null;
  /** [motor: conectado] */
  not_included?: string[] | null;
  /** Perfil de pago con el que se cobra. [motor: conectado] */
  payment_profile?: string | null;
  /** Para quién es este plan. */
  target?: string | null;
  /** Si es false, el plan se conserva pero no se ofrece. [motor: conectado] */
  available?: boolean;
}

/** Importes de un plan en una moneda. Se usan solo los que correspondan al plan. */
export interface PlanPrice {
  currency: string;
  /** Pago único inicial (instalación, implementación, inscripción). */
  implementation?: number | null;
  /** Cobro mensual. */
  monthly?: number | null;
  /** Valor del primer pago cuando difiere del mensual. */
  first_payment?: number | null;
  /** Precio de pago único. */
  price?: number | null;
  /** Cobro anual. [motor: pendiente] */
  annual?: number | null;
}

/** Políticas oficiales que el asistente comunica tal cual cuando el cliente las pregunta. */
export interface Policies {
  /** Garantía: qué cubre y por cuánto tiempo. */
  warranty?: string | null;
  /** Cambios y devoluciones. */
  returns?: string | null;
  /** Cancelaciones y reembolsos (citas, reservas, suscripciones). */
  cancellation?: string | null;
}

export interface Promotion {
  name: string;
  /** Qué incluye la promoción y a qué aplica. */
  details: string;
  /** Último día de vigencia. */
  valid_until?: string | null;
}

export interface Qualification {
  /** Si el asistente debe comprobar que la oferta encaja con el cliente. */
  detect_offer_fit?: boolean | null;
  /** Criterios para considerar a alguien un cliente potencial. */
  criteria?: string[] | null;
}

export interface RecommendationRule {
  /** Situación o necesidad del cliente. */
  when: string;
  /** Id de un plan, producto o categoría de la oferta. */
  recommend: string;
}

/** Cómo se comunica el asistente. Longitud (en el prompt y al recortar la respuesta, en todos los canales): short = cortas, medium = equilibradas, long = detalladas; límites en `engine_policy`. */
export interface ResponseStyle {
  /** Tono del asistente (p. ej. cercano y claro). */
  tone?: string | null;
  /** Personalidad de la marca. */
  voice?: string | null;
  /** informal (tutea), neutral o formal (usted). */
  formality?: "informal" | "neutral" | "formal" | null;
  /** Si el asistente puede usar emojis. */
  emojis?: boolean | null;
  /** Indicaciones de comunicación del negocio. */
  instructions?: string[] | null;
  /** short (cortas), medium (equilibradas) o long (detalladas). [motor: conectado] */
  length?: "short" | "medium" | "long";
  /** Ajuste dentro del rango de la opción elegida. Si falta, el límite de la opción. [audiencia: avanzado; motor: conectado] */
  max_words?: number | null;
}

export interface Restrictions {
  /** Canales por los que el negocio no atiende. */
  disallowed_channels?: string[];
  /** Acciones que el negocio no realiza (p. ej. llamadas). */
  disallowed_actions?: string[];
  /** Promesas o afirmaciones que el asistente nunca debe hacer (resultados garantizados, diagnósticos...). */
  forbidden_claims?: string[] | null;
}

/** Estrategia comercial. Básica (el cliente la escribe en lenguaje natural): motivos de compra, problemas e impactos, beneficios, argumentos, preguntas, recomendaciones e instrucciones. Avanzada (opcional): el resto. */
export interface Sales {
  /** Motivo principal y secundario de compra. [motor: conectado] */
  buying_motivation?: BuyingMotivation | null;
  /** Qué significa cada motivo de compra y cómo reconocerlo. [audiencia: avanzado] */
  motivation_drivers?: MotivationDriver[] | null;
  /** Problemas del cliente que el negocio resuelve. */
  customer_problems?: CustomerProblem[] | null;
  /** Problemas del cliente en sus palabras. */
  pain_points?: string[] | null;
  /** Casos de uso típicos. [audiencia: avanzado] */
  use_cases?: UseCase[] | null;
  /** Resultados que obtiene el cliente. */
  benefits?: string[] | null;
  /** Argumentos de venta. */
  arguments?: string[] | null;
  /** Cómo resuelve el negocio cada problema y qué pasos sigue el cliente. */
  solution?: Solution | null;
  /** Ángulos de venta por motivo de compra. [audiencia: avanzado] */
  angles?: SalesAngle[] | null;
  /** Ofertas principales, mejoras y complementos. [audiencia: avanzado] */
  offer_mix?: OfferMix | null;
  /** Cómo presentar las opciones. [audiencia: avanzado] */
  offer_presentation?: OfferPresentation | null;
  /** Qué recomendar en cada situación. */
  recommendation_rules?: RecommendationRule[] | null;
  discovery?: Discovery | null;
  /** Cómo calificar al cliente. [audiencia: avanzado] */
  qualification?: Qualification | null;
  /** Cómo atender preguntas de información. [audiencia: avanzado] */
  support?: SupportPolicy | null;
  /** Etapas de la conversación (identificadores internos del motor). [audiencia: operador] */
  conversation_flow?: ConversationFlow | null;
  /** Manejo de objeciones (precio y otras). [audiencia: avanzado] */
  objections?: ObjectionHandling[] | null;
  /** Estrategia y reglas de cierre. [audiencia: avanzado] */
  closing?: Closing | null;
  /** Instrucciones de venta del negocio. */
  instructions?: string[] | null;
}

export interface SalesAngle {
  /** Motivo de compra de `motivation_drivers` al que responde. */
  motivation: string;
  /** Cuándo usar el ángulo: frases del cliente. */
  signals?: string[];
  /** Qué decir con este ángulo. */
  messages?: string[];
}

export interface Scheduling {
  /** Si el servicio requiere agendar una cita o reserva. */
  required: boolean;
}

/** Referencia a un dato sensible guardado fuera del contrato (`<origen>:<clave>`). */
export interface SecretRef {
  secret_ref: string;
}

export interface Shipping {
  available: boolean;
  scope?: "local" | "nacional" | "internacional" | null;
  providers?: string[];
  cost?: Cost | null;
  time?: TimeWindow | null;
}

export interface Solution {
  /** Qué parte de la solución atiende cada problema. [audiencia: avanzado] */
  mapping?: SolutionMapping[] | null;
  /** Pasos que sigue el cliente para comprar o recibir el servicio. */
  process_steps?: string[] | null;
  /** Requisitos que debe cumplir el cliente. */
  requirements?: string[] | null;
}

export interface SolutionMapping {
  /** Id de un problema de `customer_problems`. */
  problem: string;
  solutions: string[];
}

export interface SupportPolicy {
  /** Ante una pregunta, explicar antes de vender. */
  explain_first?: boolean | null;
  /** Después de explicar, llevar la conversación a la venta. */
  sell_after?: boolean | null;
  /** Reglas de atención del negocio. */
  rules?: string[] | null;
}

export interface TargetCustomer {
  /** Tipo de cliente al que se dirige el negocio. */
  segment: string;
  company_size?: string | null;
  /** Situación típica del cliente al llegar. */
  maturity?: string | null;
  /** Quién suele escribir o decidir la compra. */
  roles?: string[] | null;
}

/** Condiciones comerciales y políticas del negocio. */
export interface Terms {
  /** Condiciones reales de compra. [motor: conectado] */
  conditions?: string[] | null;
  /** Cómo responder si el cliente duda del precio. [audiencia: avanzado; motor: conectado] */
  price_framing?: "directo" | "comparativo" | null;
  /** Ventas al mes con las que el cliente recupera la inversión. [audiencia: avanzado; motor: conectado] */
  roi_break_even_sales?: number | null;
  /** Reservas con las que el cliente recupera la inversión. [audiencia: avanzado] */
  roi_break_even_bookings?: number | null;
  /** Argumentos de retorno de la inversión. [audiencia: avanzado; motor: conectado] */
  roi_hints?: string[] | null;
  /** Aclaración sobre cómo se confirma el precio. */
  price_note?: string | null;
  /** Si los precios publicados ya incluyen los impuestos (IVA). */
  prices_include_taxes?: boolean | null;
  /** Únicas promociones o descuentos que el asistente puede ofrecer. */
  promotions?: Promotion[] | null;
  /** Financiación disponible. */
  financing?: Financing | null;
  /** Garantía, devoluciones y cancelaciones. */
  policies?: Policies | null;
}

export interface TimeWindow {
  /** Tiempo mínimo, en texto (p. ej. 30 min, 2 dias). */
  min?: string;
  max?: string;
}

export interface TransferMethod {
  type: "nequi" | "daviplata" | "bank" | "breb";
  number?: SecretRef | null;
  bank?: string | null;
  account_type?: string | null;
  account_number?: SecretRef | null;
  reference?: SecretRef | null;
}

export interface UseCase {
  /** [motor: conectado] */
  name: string;
  signals?: string[];
  /** Enfoque de la solución para este caso. */
  approach: string;
}

export interface Variant {
  sku: string;
  /** Talla, color u otras características. */
  attributes?: Record<string, string | number>;
  stock: number;
  /** Precio de la variante, solo si difiere del precio del producto. */
  prices?: ItemPrice[] | null;
}

export interface WelcomeMessage {
  enabled: boolean;
  text?: string;
}

export interface BusinessConfig {
  /** [audiencia: sistema; motor: conectado] */
  schema_version?: "1.0";
  /** [audiencia: sistema; motor: conectado] */
  tenant_slug: string;
  /** [audiencia: cliente] */
  identity: Identity;
  /** [audiencia: cliente] */
  offer: Offer;
  /** [audiencia: cliente] */
  terms?: Terms;
  /** [audiencia: cliente] */
  payments?: PaymentProfile[];
  /** [audiencia: cliente] */
  sales?: Sales;
  /** [audiencia: cliente] */
  capabilities: Capabilities;
  /** [audiencia: cliente] */
  messages: Messages;
  /** [audiencia: cliente] */
  response_style?: ResponseStyle;
  /** [audiencia: cliente] */
  knowledge?: Knowledge;
  /** [audiencia: cliente] */
  fulfillment?: Fulfillment | null;
  /** [audiencia: cliente] */
  inventory?: Inventory;
  /** Ajustes internos del motor. Si falta, se deriva de la oferta (catálogo o planes) con los valores por defecto. [audiencia: operador] */
  engine?: EngineSettings | null;
  /** Datos de los YAML antiguos sin lugar en el contrato, conservados con su ruta original. [audiencia: sistema; motor: conservado] */
  compatibility?: Record<string, unknown>;
}
