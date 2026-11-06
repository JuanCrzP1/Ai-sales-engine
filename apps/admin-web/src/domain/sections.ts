/** Secciones configurables del asistente. Las usan la navegación, la validación y el progreso. */
export type ConfigSectionId = "business" | "catalog" | "payments" | "assistant" | "messages";

export interface ConfigSection {
  id: ConfigSectionId;
  title: string;
  summary: string;
}

export const CONFIG_SECTIONS: ConfigSection[] = [
  { id: "business", title: "Mi negocio", summary: "Quién eres, a qué te dedicas y qué prometes." },
  { id: "catalog", title: "Productos y servicios", summary: "Lo que vendes, con precios y detalles." },
  { id: "payments", title: "Pagos y cierre", summary: "Cómo te pagan, promociones, políticas y cierre de ventas." },
  { id: "assistant", title: "Cómo atiende", summary: "Personalidad, instrucciones y preguntas frecuentes." },
  { id: "messages", title: "Mensajes y canales", summary: "Bienvenida, mensajes de pago y canales." },
];

export function sectionTitle(id: ConfigSectionId): string {
  return CONFIG_SECTIONS.find((section) => section.id === id)?.title ?? id;
}

/** Sección en la que se edita un campo del contrato, para enlazar los errores del servidor. */
export function sectionForPath(path: string): ConfigSectionId {
  const [root, child] = path.split(".");
  switch (root) {
    case "offer":
    case "inventory":
    case "fulfillment":
      return "catalog";
    case "payments":
    case "terms":
      return "payments";
    case "sales":
    case "response_style":
    case "knowledge":
    case "features":
      return "assistant";
    case "messages":
      return "messages";
    case "capabilities":
      return child === "service_channels" || child === "product_channels" || child === "restrictions" ? "messages" : "payments";
    default:
      return "business";
  }
}
