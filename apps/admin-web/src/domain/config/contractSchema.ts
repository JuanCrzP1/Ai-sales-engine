/**
 * Lectura del JSON Schema del contrato (BusinessConfig v1), que publica el servidor. Con él se generan los formularios
 * de los campos sin pantalla propia: un campo nuevo del contrato queda editable sin duplicar su definición aquí.
 */
export interface SchemaNode {
  $ref?: string;
  anyOf?: SchemaNode[];
  type?: string;
  const?: unknown;
  enum?: string[];
  format?: string;
  description?: string;
  title?: string;
  properties?: Record<string, SchemaNode>;
  required?: string[];
  items?: SchemaNode;
  additionalProperties?: SchemaNode | boolean;
  propertyNames?: SchemaNode;
  default?: unknown;
  maxLength?: number;
  "x-audience"?: string;
}

export interface ContractSchema extends SchemaNode {
  $defs?: Record<string, SchemaNode>;
}

export type FieldKind = "text" | "longText" | "number" | "boolean" | "choice" | "date" | "list" | "choiceList" | "objectList" | "object" | "keyedLists" | "pairs";

export interface FieldShape {
  kind: FieldKind;
  node: SchemaNode;
  /** Si admite quedar sin valor (`null` en el contrato). */
  nullable: boolean;
}

function resolveRef(root: ContractSchema, node: SchemaNode): SchemaNode {
  if (!node.$ref) return node;
  const name = node.$ref.split("/").pop() ?? "";
  const target = root.$defs?.[name];
  if (!target) throw new Error(`El esquema del contrato no define ${name}.`);
  const { $ref: _ref, ...own } = node;
  return { ...target, ...own };
}

/** Quita las referencias y la alternativa `null`, y agrupa `entero | decimal` como número. */
export function fieldShape(root: ContractSchema, raw: SchemaNode): FieldShape {
  const { anyOf, ...own } = raw;
  let node = resolveRef(root, raw);
  let nullable = false;
  if (anyOf) {
    const options = anyOf.filter((option) => option.type !== "null");
    nullable = options.length < anyOf.length;
    const numeric = options.length > 0 && options.every((option) => option.type === "integer" || option.type === "number");
    const textual = options.length > 0 && options.every((option) => option.type === "string" || option.type === "integer");
    if (numeric) node = { ...own, type: "number" };
    else if (textual && options.length > 1) node = { ...own, type: "string" };
    else node = { ...resolveRef(root, options[0] ?? {}), ...own };
  }
  return { kind: kindOf(root, node), node, nullable };
}

function kindOf(root: ContractSchema, node: SchemaNode): FieldKind {
  if (node.enum) return "choice";
  switch (node.type) {
    case "string":
      if (node.format === "date") return "date";
      return (node.maxLength ?? 0) > 300 ? "longText" : "text";
    case "integer":
    case "number":
      return "number";
    case "boolean":
      return "boolean";
    case "array": {
      const items = fieldShape(root, node.items ?? {});
      if (items.kind === "object") return "objectList";
      return items.kind === "choice" ? "choiceList" : "list";
    }
    case "object":
      if (node.properties) return "object";
      return node.propertyNames?.enum ? "keyedLists" : "pairs";
    default:
      return "text";
  }
}

/** Valor inicial al agregar un elemento: solo lo obligatorio, vacío, para que el formulario lo pida. */
export function emptyValue(root: ContractSchema, raw: SchemaNode): unknown {
  const { kind, node } = fieldShape(root, raw);
  switch (kind) {
    case "object": {
      const value: Record<string, unknown> = {};
      for (const key of node.required ?? []) {
        const property = node.properties?.[key];
        if (property) value[key] = emptyValue(root, property);
      }
      return value;
    }
    case "boolean":
      return false;
    case "number":
      return 0;
    case "list":
    case "objectList":
    case "choiceList":
      return [];
    case "keyedLists":
    case "pairs":
      return {};
    case "choice":
      return node.enum?.[0] ?? "";
    default:
      return "";
  }
}

/** Etiquetas de los campos del contrato; los que no están aquí usan la descripción del propio contrato. */
const FIELD_LABELS: Record<string, string> = {
  industry: "A qué se dedica",
  value_proposition: "Propuesta de valor",
  brand_name: "Marca",
  positioning: "Posicionamiento",
  plans: "Planes",
  categories: "Categorías",
  question: "Pregunta",
  answer: "Respuesta",
  text: "Mensaje",
  tone: "Tono",
  voice: "Personalidad",
  after_sale: "Mensaje después de una compra",
  payment_reported: "Mensaje al reportar un pago",
  payment_confirmed: "Mensaje al confirmar un pago",
  data_request: "Mensaje al pedir datos",
  follow_up: "Mensaje de seguimiento",
  warranty: "Garantía",
  returns: "Cambios y devoluciones",
  cancellation: "Cancelaciones y reembolsos",
  details: "Detalle",
  valid_until: "Vigente hasta",
  motivations: "Motivos de compra",
  motivation: "Motivo",
  description: "Descripción",
  signals: "Frases del cliente que lo revelan",
  angle: "Ángulo de venta",
  messages: "Qué decir",
  use_cases: "Casos de uso",
  name: "Nombre",
  approach: "Enfoque",
  solution: "Solución",
  process_steps: "Pasos del proceso",
  requirements: "Requisitos",
  offer_mix: "Mezcla de la oferta",
  core: "Ofertas principales",
  upsell: "Mejoras para vender más",
  cross_sell: "Complementos para vender junto",
  offer_presentation: "Cómo presentar las opciones",
  single_offer: "Cuando hay una sola opción",
  multiple_offers: "Cuando hay varias opciones",
  qualification: "Calificación del cliente",
  detect_offer_fit: "Validar si la oferta encaja antes de cerrar",
  support: "Atención de preguntas",
  explain_first: "Primero aclara la duda",
  sell_after: "Después de explicar, invita a avanzar",
  rules: "Reglas",
  conversation_flow: "Flujo de la conversación",
  steps: "Pasos",
  required_flow: "Secuencia mínima",
  forbid: "Lo que no debe hacer",
  no_skip_steps: "No saltarse pasos",
  guided_process: "Guiar paso a paso",
  objections: "Objeciones",
  topic: "Objeción",
  acknowledge: "Cómo reconocerla",
  reframe: "Cómo replantearla",
  proof: "Pruebas",
  redirect: "Cómo volver al siguiente paso",
  closing: "Cierre",
  strategy: "Tipo de cierre",
  required_data: "Datos que necesita el cierre",
  purchase_signals: "Frases de intención de compra",
  high_intent_actions: "Ante una intención de compra alta",
  next_steps: "Siguientes pasos",
  micro_commitments: "Compromisos pequeños",
  customer_problems: "Problemas del cliente, en detalle",
  id: "Identificador",
  impacts: "Qué le causa",
  monetization: "Cómo le cuesta dinero",
  urgency_levels: "Mensajes según la urgencia",
  alto: "Urgencia alta",
  medio: "Urgencia media",
  bajo: "Urgencia baja",
  recommended_angles: "Ángulos recomendados",
  solutions: "Qué parte de la solución lo atiende",
  pain_points: "Problemas en palabras del cliente",
  objectives: "Qué debe averiguar",
  delivery: "Domicilio",
  shipping: "Envío",
  pickup: "Recogida",
  scheduling: "Agenda",
  available: "Disponible",
  type: "Tipo",
  zones: "Zonas",
  cost: "Costo",
  value: "Valor",
  time: "Tiempo de entrega",
  min: "Mínimo",
  max: "Máximo",
  scope: "Alcance",
  providers: "Proveedores",
  options: "Modalidades",
  instructions: "Indicaciones",
  required: "Requiere agendar",
  track_stock: "Controlar existencias",
  items: "Productos con variantes",
  product_id: "Producto",
  variants: "Variantes",
  sku: "Referencia (SKU)",
  attributes: "Características",
  stock: "Existencias",
  prices: "Precio",
  currency: "Moneda",
  amount: "Precio",
  pricing_enabled: "Puede usar precios en la conversación",
  catalog_mode: "Vende opciones de catálogo",
  multi_currency: "Maneja varias monedas",
  multi_plan: "Ofrece varios planes",
  business_model: "Tipo de negocio",
  segment: "Tipo de cliente",
  company_size: "Tamaño de la empresa",
  maturity: "Situación al llegar",
  roles: "Quién escribe o decide",
  days: "Días",
  opens: "Abre",
  closes: "Cierra",
  price_framing: "Si duda del precio",
  roi_break_even_sales: "Ventas para recuperar la inversión",
  roi_break_even_bookings: "Reservas para recuperar la inversión",
  roi_hints: "Argumentos de retorno de la inversión",
  disallowed_channels: "Canales por los que no atiende",
  disallowed_actions: "Acciones que no realiza",
};

/** Etiquetas de los valores de las listas cerradas del contrato. */
const VALUE_LABELS: Record<string, string> = {
  direct_sale: "Confirmar la compra",
  lead_capture: "Capturar datos",
  booking: "Agendar",
  checkout: "Enviar el pago",
  directo: "Directo",
  comparativo: "Comparativo",
  propio: "Propio",
  tercero: "De un tercero",
  fijo: "Fijo",
  variable: "Variable",
  gratis: "Gratis",
  local: "Local",
  nacional: "Nacional",
  internacional: "Internacional",
  saas: "Software por suscripción",
  catalog: "Catálogo",
  service_booking: "Servicio con reserva",
  process: "Proceso guiado",
  miercoles: "Miércoles",
  sabado: "Sábado",
};

export function fieldLabel(key: string, node: SchemaNode): string {
  return FIELD_LABELS[key] ?? node.description ?? key.replace(/_/g, " ");
}

/** Nombre del campo de una ruta del documento (`knowledge.faqs.0.answer` → Respuesta), si tiene uno en lenguaje del negocio. */
export function pathLabel(path: string): string | null {
  const key = path.split(".").reverse().find((segment) => !/^\d+$/.test(segment));
  return (key && FIELD_LABELS[key]) || null;
}

/** La descripción del contrato como ayuda, cuando no es ya la etiqueta. */
export function fieldHint(key: string, node: SchemaNode): string | undefined {
  return FIELD_LABELS[key] ? node.description : undefined;
}

export function valueLabel(value: string): string {
  if (VALUE_LABELS[value]) return VALUE_LABELS[value];
  const text = value.replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** El nodo de un campo de primer nivel del documento, o de una sección dentro de él. */
export function nodeAt(root: ContractSchema, path: string[]): SchemaNode {
  let node: SchemaNode = root;
  for (const key of path) {
    const shape = fieldShape(root, node).node;
    const next = shape.properties?.[key];
    if (!next) throw new Error(`El contrato no define ${path.join(".")}.`);
    node = next;
  }
  return node;
}
