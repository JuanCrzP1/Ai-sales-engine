import { UpcomingFeature } from "../../layout/UpcomingFeature";

/** Cómo le va al negocio: ventas, conversión y lo que más preguntan. */
export function ReportsPage() {
  return (
    <UpcomingFeature
      eyebrow="Ventas"
      title="Reportes"
      description="Cómo le va a tu negocio en el chat, día a día."
      icon="chart"
      highlights={["Conversaciones y ventas por día", "Qué porcentaje de chats termina en venta", "Lo que más preguntan tus clientes"]}
    />
  );
}
