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
  { id: "payments", title: "Pagos y cierre", summary: "Cómo te pagan y cómo se cierra una venta." },
  { id: "assistant", title: "Cómo atiende", summary: "Largo de respuestas, motivos de compra y preguntas frecuentes." },
  { id: "messages", title: "Mensajes y canales", summary: "Bienvenida, mensajes de pago y canales." },
];

export function sectionTitle(id: ConfigSectionId): string {
  return CONFIG_SECTIONS.find((section) => section.id === id)?.title ?? id;
}
