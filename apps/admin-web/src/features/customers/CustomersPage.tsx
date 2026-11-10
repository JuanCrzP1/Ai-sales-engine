import { UpcomingFeature } from "../../layout/UpcomingFeature";

/** Los contactos que escribieron al negocio, con su historial y su etapa. */
export function CustomersPage() {
  return (
    <UpcomingFeature
      eyebrow="Atención"
      title="Clientes"
      description="Cada persona que le escribe a tu negocio, con su historial y en qué etapa va."
      icon="users"
      highlights={["La ficha de cada cliente, con sus datos y su historial de chats", "Etapas: nuevo, interesado, compró", "Etiquetas para organizarlos y exportarlos"]}
    />
  );
}
