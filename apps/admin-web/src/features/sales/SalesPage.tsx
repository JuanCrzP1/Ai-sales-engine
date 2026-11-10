import { UpcomingFeature } from "../../layout/UpcomingFeature";

/** Las ventas que cerró el asistente y sus pagos. */
export function SalesPage() {
  return (
    <UpcomingFeature
      eyebrow="Ventas"
      title="Ventas"
      description="Lo que cerró tu asistente: qué se vendió, a quién y si ya pagó."
      icon="wallet"
      highlights={["Cada venta con su producto, su valor y su cliente", "Pagos pendientes y confirmados", "El chat donde se cerró cada venta"]}
    />
  );
}
