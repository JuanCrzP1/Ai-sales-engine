import type { ReactNode } from "react";
import { Alert } from "../../components/ui/Feedback";
import { Icon, type IconName } from "../../components/ui/Icon";
import { Card, PageHeader } from "../../components/ui/Layout";

interface ComingSoonProps {
  title: string;
  description: string;
  icon: IconName;
  /** Lo que traerá la sección. */
  highlights: string[];
  children?: ReactNode;
}

/** Una sección de Configuración que todavía no existe: dice qué traerá, para saber hacia dónde va la plataforma. */
function ComingSoon({ title, description, icon, highlights, children }: ComingSoonProps) {
  return (
    <>
      <PageHeader title={title} description={description} actions={<span className="soon-badge soon-badge--large">Próximamente</span>} />
      <Card>
        <div className="upcoming">
          <span className="upcoming__icon">
            <Icon name={icon} size={28} />
          </span>
          <h2 className="upcoming__title">Estamos construyendo esta sección</h2>
          <p className="upcoming__text">Cuando esté lista, aquí podrás:</p>
          <ul className="upcoming__list">
            {highlights.map((item) => (
              <li key={item}>
                <Icon name="check" size={16} /> {item}
              </li>
            ))}
          </ul>
          {children}
        </div>
      </Card>
    </>
  );
}

export function BillingPage() {
  return (
    <ComingSoon
      title="Pagos y suscripciones"
      description="Tu plan en la plataforma, cómo lo pagas y tus facturas."
      icon="card"
      highlights={["Ver tu plan y lo que incluye", "Agregar o cambiar tu medio de pago", "Descargar tus facturas y ver tu historial de cobros"]}
    >
      <Alert tone="info" title="Hoy la plataforma no te cobra nada.">
        Solo pagas a OpenRouter lo que usa tu asistente; lo ves en Configuración → Inteligencia artificial, en Consumo.
      </Alert>
    </ComingSoon>
  );
}
