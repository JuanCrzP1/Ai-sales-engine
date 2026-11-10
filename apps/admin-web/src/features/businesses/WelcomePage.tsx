import { useNavigate } from "react-router-dom";
import { Icon } from "../../components/ui/Icon";
import { PageHeader } from "../../components/ui/Layout";
import { StandalonePage } from "../../layout/StandalonePage";
import { ENTRY_PATH } from "../../navigation/navItems";
import { useAuth } from "../../state/auth/useAuth";
import { CreateBusinessForm } from "./CreateBusinessForm";

const STEPS = ["Elige cómo empezar y ponle nombre", "Entrena a tu asistente con tus productos, precios y forma de pago", "Pruébalo y conéctalo a tus canales"];

/** Bienvenida de quien aún no tiene un negocio (y también para crear otro): el nombre basta para empezar. */
export function WelcomePage() {
  const { session } = useAuth();
  const navigate = useNavigate();
  const firstName = session?.user.name.split(" ")[0] ?? "";

  return (
    <StandalonePage>
      <PageHeader
        eyebrow={firstName ? `Hola, ${firstName}` : "Bienvenido"}
        title="Crea tu negocio"
        description="Tu asistente de ventas atenderá a tus clientes con la información de tu negocio. Empieza de cero o con una plantilla de tu tipo de negocio: lo demás lo ajustas en el panel."
      />
      <ol className="welcome-steps">
        {STEPS.map((step, index) => (
          <li key={step} className="welcome-steps__item">
            <span className="welcome-steps__number">{index === 0 ? <Icon name="sparkles" size={16} /> : index + 1}</span>
            {step}
          </li>
        ))}
      </ol>
      <CreateBusinessForm existing={[]} onCancel={() => navigate(ENTRY_PATH)} />
    </StandalonePage>
  );
}
