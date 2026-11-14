// ARCHIVO GENERADO por scripts/generate_business_config_types.py. No editar a mano.
// Fuente: project/config/contracts/v1/business-config.schema.json y
// project/app/domain/business_config/engine_policy.py y payment_catalog.py.
// Marcas: `audiencia` (cliente, avanzado, sistema) y `motor` (conectado, pendiente); un campo sin
// marca toma la de su sección. Ver docs/business-config.md.

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
export const MAX_POLICY_CHARS = 800;
export const MAX_MESSAGE_CHARS = 800;
export const MAX_INDUSTRY_CHARS = 80;
export const MAX_DESCRIPTION_CHARS = 500;
export const MAX_VALUE_PROPOSITION_CHARS = 300;
export const MAX_OFFER_DESCRIPTION_CHARS = 300;
export const MAX_CATEGORIES = 20;
export const MAX_CUSTOMER_PROBLEMS = 10;
export const MAX_ESCALATION_TOPICS = 15;
export const MAX_ESCALATION_TOPIC_CHARS = 120;
export const MAX_PAYMENT_INSTRUCTIONS_CHARS = 300;
/** Los medios de pago que un negocio puede configurar, de cualquier país (`project/app/domain/business_config/payment_catalog.py`). */
export const PAYMENT_METHOD_GROUPS = ["Colombia", "México", "Perú", "Argentina", "España", "Estados Unidos", "Todos los países"] as const;
export const PAYMENT_METHOD_CATALOG = [{"id": "nequi", "name": "Nequi", "group": "Colombia", "data": {"slot": "number", "label": "Número de celular", "format": "mobile", "placeholder": "3001234567", "shownAs": "{value}"}, "needsBank": false, "custom": false}, {"id": "daviplata", "name": "Daviplata", "group": "Colombia", "data": {"slot": "number", "label": "Número de celular", "format": "mobile", "placeholder": "3001234567", "shownAs": "{value}"}, "needsBank": false, "custom": false}, {"id": "bank", "name": "Cuenta bancaria", "group": "Todos los países", "data": {"slot": "account_number", "label": "Número de cuenta", "format": "account", "placeholder": "1234567890", "shownAs": "{value}"}, "needsBank": true, "custom": false}, {"id": "breb", "name": "Bre-B", "group": "Colombia", "data": {"slot": "reference", "label": "Llave o referencia Bre-B", "format": "reference", "placeholder": "@tunegocio", "shownAs": "Llave: {value}"}, "needsBank": false, "custom": false}, {"id": "spei", "name": "Transferencia SPEI", "group": "México", "data": {"slot": "reference", "label": "CLABE interbancaria", "format": "clabe", "placeholder": "032180000118359719", "shownAs": "CLABE: {value}"}, "needsBank": false, "custom": false}, {"id": "oxxo", "name": "Depósito en OXXO", "group": "México", "data": {"slot": "reference", "label": "Número de tarjeta para depositar", "format": "account", "placeholder": "4152313412345678", "shownAs": "Tarjeta: {value}"}, "needsBank": false, "custom": false}, {"id": "yape", "name": "Yape", "group": "Perú", "data": {"slot": "number", "label": "Número de celular", "format": "phone", "placeholder": "987654321", "shownAs": "{value}"}, "needsBank": false, "custom": false}, {"id": "plin", "name": "Plin", "group": "Perú", "data": {"slot": "number", "label": "Número de celular", "format": "phone", "placeholder": "987654321", "shownAs": "{value}"}, "needsBank": false, "custom": false}, {"id": "mercadopago", "name": "Mercado Pago", "group": "Argentina", "data": {"slot": "reference", "label": "Alias o CVU", "format": "reference", "placeholder": "tunegocio.mp", "shownAs": "Alias/CVU: {value}"}, "needsBank": false, "custom": false}, {"id": "bizum", "name": "Bizum", "group": "España", "data": {"slot": "number", "label": "Número de móvil", "format": "phone", "placeholder": "612345678", "shownAs": "{value}"}, "needsBank": false, "custom": false}, {"id": "iban", "name": "Transferencia (IBAN)", "group": "España", "data": {"slot": "account_number", "label": "IBAN", "format": "iban", "placeholder": "ES91 2100 0418 4502 0005 1332", "shownAs": "IBAN: {value}"}, "needsBank": false, "custom": false}, {"id": "zelle", "name": "Zelle", "group": "Estados Unidos", "data": {"slot": "reference", "label": "Correo o celular de Zelle", "format": "reference", "placeholder": "pagos@tunegocio.com", "shownAs": "{value}"}, "needsBank": false, "custom": false}, {"id": "paypal", "name": "PayPal", "group": "Todos los países", "data": {"slot": "reference", "label": "Correo de PayPal", "format": "email", "placeholder": "pagos@tunegocio.com", "shownAs": "{value}"}, "needsBank": false, "custom": false}, {"id": "cash", "name": "Efectivo o contraentrega", "group": "Todos los países", "data": null, "needsBank": false, "custom": false}, {"id": "custom", "name": "Otro medio", "group": "Todos los países", "data": {"slot": "reference", "label": "Dato para pagar", "format": "reference", "placeholder": "", "shownAs": "{value}"}, "needsBank": false, "custom": true}] as const;

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
  /** Lo que el negocio no hace. [motor: conectado] */
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
  /** [motor: conectado] */
  id: string;
  /** [motor: conectado] */
  name: string;
  /** Id de su categoría; una categoría sin productos disponibles no se ofrece. [motor: conectado] */
  category: string;
  /** Detalle del producto. [motor: conectado] */
  description?: string | null;
  /** [motor: conectado] */
  prices: ItemPrice[];
  /** Características del producto. [motor: conectado] */
  features?: string[] | null;
  /** Si es false, el producto se conserva pero no se ofrece (ni su categoría, si se queda sin productos). [motor: conectado] */
  available?: boolean;
}

export interface Closing {
  /** Tipo de cierre: direct_sale (confirmar la compra), lead_capture (capturar datos), booking (agendar) o checkout (enviar el pago). */
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

/** Cómo avanza la conversación comercial. */
export interface ConversationFlow {
  /** Pasos que idealmente sigue la conversación, en orden. */
  steps?: string[] | null;
  /** Secuencia mínima que debe respetar la conversación. */
  required_flow?: string[] | null;
  /** Lo que el asistente no debe hacer en este negocio (p. ej. responder_sin_solucion). */
  forbid?: string[] | null;
  /** true: no se saltan pasos de la conversación. */
  no_skip_steps?: boolean | null;
  /** true: guía al cliente paso a paso en un proceso (trámites, matrículas). */
  guided_process?: boolean | null;
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
  /** Qué parte de la solución atiende este problema. [audiencia: avanzado] */
  solutions?: string[] | null;
}

export interface DataCollection {
  /** [motor: conectado] */
  enabled: boolean;
  /** Datos que el asistente puede pedir al cliente: solo esos y los que necesita el cierre (`sales.closing.required_data`). [motor: conectado] */
  fields?: string[];
}

export interface Delivery {
  available: boolean;
  type?: "propio" | "tercero" | null;
  zones?: string[];
  cost?: Cost | null;
  time?: TimeWindow | null;
}

export interface Discovery {
  /** Preguntas para entender al cliente. [motor: conectado] */
  questions?: string[] | null;
  /** Qué debe averiguar el asistente. [audiencia: avanzado; motor: conectado] */
  objectives?: string[] | null;
}

export interface Escalation {
  /** Si el cliente pide hablar con una persona: always (lo pasa) u offer_help_first (primero le ofrece resolverlo una vez; si insiste, lo pasa). [motor: conectado] */
  on_request?: "always" | "offer_help_first";
  /** Temas que siempre van al equipo (p. ej. reembolsos, garantías). [motor: conectado] */
  always_topics?: string[];
  /** Temas que resuelve el asistente sin pasar el chat, salvo que el cliente pida una persona (p. ej. precios, horarios). [motor: conectado] */
  never_topics?: string[];
  /** Pasar el chat si la conversación se estanca: el cliente repite lo mismo o está frustrado y no se le puede ayudar. [motor: conectado] */
  when_stuck?: boolean;
  /** Otras indicaciones del negocio sobre cuándo pasar el chat a una persona. [motor: conectado] */
  instructions?: string | null;
}

export interface Faq {
  /** Pregunta tal como la haría el cliente. */
  question: string;
  /** Respuesta oficial del negocio. */
  answer: string;
}

/** Cómo vende el negocio. Los valores se conservan tal cual; las contradicciones con la oferta las señala el diagnóstico. El antiguo «modo catálogo» (`catalog_mode`) ya no se escribe: el motor lo recibe deducido de lo que vende el negocio y de su oferta. */
export interface Features {
  /** true: permite usar precios en la conversación. false: el asistente no da valores. [motor: conectado] */
  pricing_enabled: boolean;
  /** true: da los precios en todas sus monedas. false: solo en la primera de cada precio. [motor: conectado] */
  multi_currency?: boolean | null;
  /** true: puede ofrecer varios planes. false: recomienda uno solo, el que mejor encaje. [motor: conectado] */
  multi_plan?: boolean | null;
  /** Qué vende el negocio: catalog (productos), saas (planes o suscripción), services (servicios) o service_booking (servicios con cita). El asistente usa el manual de venta de ese tipo; sin indicar, se deduce de la oferta. [motor: conectado] */
  business_model?: "catalog" | "saas" | "services" | "service_booking" | null;
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
  /** Nombre del negocio. [motor: conectado] */
  name: string;
  /** Marca con la que el asistente presenta al negocio, si es distinta del nombre. [motor: conectado] */
  brand_name?: string | null;
  /** Sector o tipo de negocio, en pocas palabras. [motor: conectado] */
  industry: string;
  /** Qué hace el negocio. [motor: conectado] */
  description: string;
  /** Promesa comercial: qué gana el cliente. [motor: conectado] */
  value_proposition: string;
  /** A quién se dirige y qué problema resuelve. [motor: conectado] */
  positioning?: string | null;
  /** Por qué elegir este negocio y no otro. [motor: conectado] */
  differentiators?: string[] | null;
  /** Dónde está y a qué zonas atiende. [motor: conectado] */
  location?: Location | null;
  /** Cómo recibe el cliente el servicio o producto. [motor: conectado] */
  service_modes?: ("virtual" | "presencial" | "domicilio" | "recoger" | "envio")[] | null;
  /** Cliente ideal. [motor: conectado] */
  target_customer?: TargetCustomer | null;
  /** Pruebas de confianza: casos, resultados, trayectoria. [motor: conectado] */
  credibility?: string[] | null;
  /** Horarios de atención. [motor: conectado] */
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
  /** Moneda (código ISO de tres letras). */
  currency: string;
  /** Precio en esa moneda. */
  amount: number;
}

export interface Knowledge {
  /** Preguntas frecuentes con su respuesta oficial. [motor: conectado] */
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
  /** Saludo de cada conversación nueva: mensaje fijo o respuesta de la IA. [motor: conectado] */
  welcome: WelcomeMessage;
  /** Plantilla del mensaje con los datos de pago que el sistema (nunca la IA) envía cuando el cliente elige cómo pagar. Marcadores: {medio}, {datos} (obligatorio) y {titular}. Si falta, la de la plataforma. [motor: conectado] */
  payment_details?: string | null;
  /** Respuesta exacta cuando el cliente reporta un pago. [motor: conectado] */
  payment_reported?: string | null;
  /** Mensaje cuando el equipo confirma el pago. Se guarda; lo enviará la plataforma cuando el equipo pueda confirmar pagos desde el panel. [motor: programado] */
  payment_confirmed?: string | null;
  /** Mensaje después de una compra: la IA lo usa cuando el cliente escribe después de pagar. [motor: conectado] */
  after_sale?: string | null;
  /** Mensaje para pedir los datos del cliente. [motor: conectado] */
  data_request?: string | null;
  /** Mensaje de seguimiento a un cliente que no respondió. Se guarda; lo enviará la plataforma cuando los canales puedan escribir primero. [motor: programado] */
  follow_up?: string | null;
  /** Mensaje al pasar la conversación a una persona. [motor: conectado] */
  human_handoff?: string | null;
  /** Mensaje cuando un chat pasa a una persona fuera del horario del equipo. Si falta, uno con el horario y cuándo lo atienden. [motor: conectado] */
  after_hours?: string | null;
  /** Mensaje cuando la IA retoma un chat que nadie del equipo respondió a tiempo. Si falta, uno de la plataforma. [motor: conectado] */
  ai_resumed?: string | null;
  /** Mensaje exacto cuando la IA no puede responder (sin clave, sin saldo o con el proveedor caído). Si falta, uno neutro de la plataforma. [motor: conectado] */
  fallback?: string | null;
}

/** Un motivo de compra: qué significa, cómo reconocerlo y cómo venderle a quien lo tiene. */
export interface Motivation {
  /** Motivo de compra (p. ej. tiempo, dinero). */
  motivation: string;
  /** Qué significa este motivo para el cliente. */
  description?: string | null;
  /** Frases del cliente que revelan este motivo. */
  signals?: string[] | null;
  /** Ángulo de venta para este motivo. */
  angle?: SalesAngle | null;
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
  /** Días en los que aplica este horario. */
  days: ("lunes" | "martes" | "miercoles" | "jueves" | "viernes" | "sabado" | "domingo")[];
  /** Hora de apertura (HH:MM, 24 h). */
  opens: string;
  /** Hora de cierre (HH:MM, 24 h). */
  closes: string;
}

/** Cómo se cobra: link de pago y transferencias. El motor entrega los datos al cliente cuando elige el método. */
export interface PaymentProfile {
  /** [motor: conectado] */
  id: string;
  /** [motor: conectado] */
  link?: SecretRef | null;
  /** Si es false, el enlace se conserva pero no se ofrece. [motor: conectado] */
  link_enabled?: boolean | null;
  /** [motor: conectado] */
  transfer_enabled: boolean;
  /** [motor: conectado] */
  transfer_methods?: TransferMethod[];
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
  /** Detalle del plan. [motor: conectado] */
  description?: string | null;
  /** [motor: conectado] */
  prices: PlanPrice[];
  /** [motor: conectado] */
  includes?: string[] | null;
  /** [motor: conectado] */
  not_included?: string[] | null;
  /** Perfil de pago con el que se cobra. [motor: conectado] */
  payment_profile?: string | null;
  /** Para quién es este plan. [motor: conectado] */
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
  /** Valor del primer pago, si difiere de los siguientes. */
  first_payment?: number | null;
  /** Precio de pago único. */
  price?: number | null;
  /** Cobro anual. [motor: conectado] */
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
  /** Nombre con el que se presenta la promoción. */
  name: string;
  /** Qué incluye la promoción y a qué aplica. */
  details: string;
  /** Último día de vigencia. */
  valid_until?: string | null;
}

export interface Qualification {
  /** true: valida si la oferta encaja antes de empujar el cierre. */
  detect_offer_fit?: boolean | null;
}

export interface RecommendationRule {
  /** Situación o necesidad del cliente. */
  when: string;
  /** Plan, producto o categoría que se recomienda. Si no está en la oferta, el diagnóstico lo señala. */
  recommend: string;
}

/** Cómo se comunica el asistente. Longitud (en el prompt y al recortar la respuesta, en todos los canales): short = cortas, medium = equilibradas, long = detalladas; límites en `engine_policy`. */
export interface ResponseStyle {
  /** Tono del asistente (p. ej. cercano y claro). [motor: conectado] */
  tone?: string | null;
  /** Personalidad de la marca. [motor: conectado] */
  voice?: string | null;
  /** informal (tutea), neutral o formal (usted). [motor: conectado] */
  formality?: "informal" | "neutral" | "formal" | null;
  /** Si el asistente puede usar emojis. [motor: conectado] */
  emojis?: boolean | null;
  /** Cómo debe expresarse el asistente en este negocio. [motor: conectado] */
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
}

/** Estrategia comercial. Básica (el cliente la escribe en lenguaje natural): motivos de compra, problemas e impactos, beneficios, argumentos, preguntas, recomendaciones e instrucciones. Avanzada (opcional): el resto. */
export interface Sales {
  /** Motivo principal y secundario de compra. [motor: conectado] */
  buying_motivation?: BuyingMotivation | null;
  /** Cada motivo de compra: qué significa, cómo reconocerlo y con qué ángulo venderle. [audiencia: avanzado; motor: conectado] */
  motivations?: Motivation[] | null;
  /** Problemas del cliente que el negocio resuelve. [motor: conectado] */
  customer_problems?: CustomerProblem[] | null;
  /** Problemas del cliente en sus palabras. [motor: conectado] */
  pain_points?: string[] | null;
  /** Casos de uso típicos. [audiencia: avanzado; motor: conectado] */
  use_cases?: UseCase[] | null;
  /** Resultados que obtiene el cliente. [motor: conectado] */
  benefits?: string[] | null;
  /** Argumentos de venta. [motor: conectado] */
  arguments?: string[] | null;
  /** Qué pasos sigue el cliente y qué requisitos debe cumplir. [motor: conectado] */
  solution?: Solution | null;
  /** Ofertas principales, mejoras y complementos. [audiencia: avanzado; motor: conectado] */
  offer_mix?: OfferMix | null;
  /** Cómo presentar las opciones. [audiencia: avanzado; motor: conectado] */
  offer_presentation?: OfferPresentation | null;
  /** Qué recomendar en cada situación. [motor: conectado] */
  recommendation_rules?: RecommendationRule[] | null;
  discovery?: Discovery | null;
  /** Cómo calificar al cliente. [audiencia: avanzado; motor: conectado] */
  qualification?: Qualification | null;
  /** Cómo atender preguntas de información. [audiencia: avanzado; motor: conectado] */
  support?: SupportPolicy | null;
  /** Pasos de la conversación y reglas para avanzar. [audiencia: avanzado; motor: conectado] */
  conversation_flow?: ConversationFlow | null;
  /** Manejo de objeciones (precio y otras). [audiencia: avanzado; motor: conectado] */
  objections?: ObjectionHandling[] | null;
  /** Estrategia y reglas de cierre. [audiencia: avanzado; motor: conectado] */
  closing?: Closing | null;
  /** Cómo debe vender el asistente en este negocio. [motor: conectado] */
  instructions?: string[] | null;
}

export interface SalesAngle {
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
  /** Pasos que sigue el cliente para comprar o recibir el servicio. */
  process_steps?: string[] | null;
  /** Requisitos que debe cumplir el cliente. */
  requirements?: string[] | null;
}

export interface SupportPolicy {
  /** true: primero aclara la duda. false: vende directo. */
  explain_first?: boolean | null;
  /** true: después de explicar, vuelve a llevar al cliente a avanzar. */
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
  /** Reservas con las que el cliente recupera la inversión. [audiencia: avanzado; motor: conectado] */
  roi_break_even_bookings?: number | null;
  /** Argumentos de retorno de la inversión. [audiencia: avanzado; motor: conectado] */
  roi_hints?: string[] | null;
  /** Aclaración sobre cómo se confirma el precio. [motor: conectado] */
  price_note?: string | null;
  /** Únicas promociones o descuentos que el asistente puede ofrecer. [motor: conectado] */
  promotions?: Promotion[] | null;
  /** Financiación disponible. [motor: conectado] */
  financing?: Financing | null;
  /** Garantía, devoluciones y cancelaciones. [motor: conectado] */
  policies?: Policies | null;
}

export interface TimeWindow {
  /** Tiempo mínimo, en texto (p. ej. 30 min, 2 dias). */
  min?: string;
  max?: string;
}

/** Un medio para pagar: Nequi, una cuenta bancaria, Yape, PayPal, efectivo u «otro medio» (`payment_catalog.py`). Lo que se paga va cifrado en `number`, `account_number` o `reference`, según el medio. */
export interface TransferMethod {
  /** El medio, del catálogo de medios de pago (`payment_catalog.py`). */
  type: "nequi" | "daviplata" | "bank" | "breb" | "spei" | "oxxo" | "yape" | "plin" | "mercadopago" | "bizum" | "iban" | "zelle" | "paypal" | "cash" | "custom";
  number?: SecretRef | null;
  bank?: string | null;
  account_type?: string | null;
  account_number?: SecretRef | null;
  reference?: SecretRef | null;
  /** «Otro medio»: su nombre, como lo verá el cliente (por ejemplo, «Nu»). */
  name?: string | null;
  /** «Otro medio»: cómo se llama su dato (por ejemplo, «Alias» o «Número»). */
  data_label?: string | null;
  /** Lo que el cliente debe saber al pagar por este medio (por ejemplo, «envía el comprobante con tu nombre»). Sale con los datos; la IA no lo ve. */
  instructions?: string | null;
  /** Etiqueta para reconocer la cuenta en el panel. No se comparte con el cliente. [motor: solo panel] */
  label?: string | null;
  /** A nombre de quién está la cuenta. Se le muestra al cliente con los datos de pago, para que sepa que paga al negocio correcto. [motor: conectado] */
  holder?: string | null;
  /** Si es false, la cuenta se conserva pero no se ofrece. */
  enabled?: boolean | null;
}

export interface UseCase {
  /** [motor: conectado] */
  name: string;
  signals?: string[];
  /** Enfoque de la solución para este caso. */
  approach: string;
}

export interface Variant {
  /** Código interno de la variante, para el equipo. [motor: solo panel] */
  sku: string;
  /** Talla, color u otras características. */
  attributes?: Record<string, string | number>;
  stock: number;
  /** Precio de la variante, solo si difiere del precio del producto. */
  prices?: ItemPrice[] | null;
}

/** Las dos modalidades de saludo, según `enabled`. - `true`: ante un saludo sin más en una conversación nueva, el sistema envía `text` tal cual, sin IA. - `false`: no envía el mensaje fijo y responde la IA. El texto se conserva para cuando se reactive. Un saludo con una intención ("hola, ¿qué precio tiene?") siempre lo responde la IA. */
export interface WelcomeMessage {
  /** true: envía el mensaje inicial fijo, sin IA. false: no lo envía y responde la IA. */
  enabled: boolean;
  /** Mensaje de apertura que recibe el cliente. */
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
  escalation?: Escalation;
  /** [audiencia: cliente; motor: conectado] */
  fulfillment?: Fulfillment | null;
  /** [audiencia: cliente; motor: conectado] */
  inventory?: Inventory;
  /** Interruptores comerciales. Si faltan, se derivan de la oferta (catálogo o planes). [audiencia: avanzado] */
  features?: Features | null;
}
