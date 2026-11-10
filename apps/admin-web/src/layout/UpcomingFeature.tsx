import type { ReactNode } from "react";
import { LinkButton } from "../components/ui/Button";
import { Icon, type IconName } from "../components/ui/Icon";
import { Card, PageHeader } from "../components/ui/Layout";
import { CHANNELS_ITEM } from "../navigation/navItems";
import { useWorkspacePath } from "../navigation/useWorkspacePath";

interface UpcomingFeatureProps {
  eyebrow: string;
  title: string;
  description: string;
  icon: IconName;
  /** Lo que va a mostrar la sección cuando lleguen los datos de los canales. */
  highlights: string[];
  children?: ReactNode;
}

/** Una sección que se llena con la actividad de los canales: explica qué mostrará y cómo empezar. */
export function UpcomingFeature({ eyebrow, title, description, icon, highlights, children }: UpcomingFeatureProps) {
  const pathTo = useWorkspacePath();
  return (
    <>
      <PageHeader eyebrow={eyebrow} title={title} description={description} />
      <Card>
        <div className="upcoming">
          <span className="upcoming__icon">
            <Icon name={icon} size={28} />
          </span>
          <h2 className="upcoming__title">Se llena con tus conversaciones</h2>
          <p className="upcoming__text">Cuando conectes un canal y tus clientes empiecen a escribir, aquí verás:</p>
          <ul className="upcoming__list">
            {highlights.map((item) => (
              <li key={item}>
                <Icon name="check" size={16} /> {item}
              </li>
            ))}
          </ul>
          <LinkButton to={pathTo(CHANNELS_ITEM.path)} variant="primary">
            Conectar un canal
          </LinkButton>
          {children}
        </div>
      </Card>
    </>
  );
}
