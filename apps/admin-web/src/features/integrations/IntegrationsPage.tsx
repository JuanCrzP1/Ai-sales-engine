import type { ReactNode } from "react";
import { Button, LinkButton } from "../../components/ui/Button";
import { Alert, Badge } from "../../components/ui/Feedback";
import { Icon, type IconName } from "../../components/ui/Icon";
import { PageHeader } from "../../components/ui/Layout";
import { LoadingScreen } from "../../layout/StatusScreen";
import { API_KEYS_ITEM, ASSISTANT_API_ITEM } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useIntegrationsData } from "../../state/useIntegrationsData";

interface Tile {
  id: string;
  icon: IconName;
  name: string;
  description: string;
  badge: ReactNode;
  action?: ReactNode;
}

/** Integraciones: conectar el asistente con otras herramientas. */
export function IntegrationsPage() {
  const data = useIntegrationsData();
  const pathTo = useWorkspacePath();
  const header = <PageHeader title="Integraciones" description="Conecta tu asistente con las herramientas que ya usas: otras plataformas de atención, tu página web o las IAs que te ayudan a administrarlo." />;

  if (data.status === "loading") return <LoadingScreen label="Cargando las integraciones…" />;
  if (data.status === "error" || !data.overview) {
    return (
      <>
        {header}
        <Alert tone="danger" title={data.error ?? "No se pudieron cargar."}>
          <Button variant="secondary" size="small" onClick={data.reload}>
            Reintentar
          </Button>
        </Alert>
      </>
    );
  }
  const { chatKeys, activeKeys } = data.overview;

  const tiles: Tile[] = [
    {
      id: "api",
      icon: "link",
      name: "API del asistente",
      description: "Conecta tu asistente a Leona, a tu página web o a cualquier sistema por HTTP: te mandan el mensaje del cliente y reciben la respuesta.",
      badge: chatKeys > 0 ? <Badge tone="success">Activa</Badge> : <Badge tone="neutral">Sin conectar</Badge>,
      action: <LinkButton to={pathTo(ASSISTANT_API_ITEM.path)} variant={chatKeys > 0 ? "secondary" : "primary"}>{chatKeys > 0 ? "Ver la conexión" : "Conectar"}</LinkButton>,
    },
    {
      id: "mcp",
      icon: "robot",
      name: "IAs conectadas (MCP)",
      description: "Que Claude, ChatGPT, Cursor, Gemini o n8n configuren y consulten tu plataforma hablándoles, con los mismos permisos y reglas del panel.",
      badge: <span className="soon-badge">Próximamente</span>,
    },
    {
      id: "keys",
      icon: "shield",
      name: "Claves de API",
      description: "Todas las claves de este negocio en un lugar: para qué es cada una, cuándo se usó y revocarla.",
      badge: <Badge tone={activeKeys > 0 ? "success" : "neutral"}>{activeKeys === 1 ? "1 activa" : `${activeKeys} activas`}</Badge>,
      action: <LinkButton to={pathTo(API_KEYS_ITEM.path)}>Ver claves</LinkButton>,
    },
  ];

  return (
    <>
      {header}
      <div className="integration-grid">
        {tiles.map((tile) => (
          <article key={tile.id} className={`integration-card${tile.action ? "" : " integration-card--soon"}`}>
            <div className="integration-card__top">
              <span className={`integration-card__icon integration-card__icon--${tile.id}`} aria-hidden="true">
                <Icon name={tile.icon} size={20} />
              </span>
              {tile.badge}
            </div>
            <h2 className="integration-card__name">{tile.name}</h2>
            <p className="integration-card__text">{tile.description}</p>
            {tile.action && <div className="integration-card__action">{tile.action}</div>}
          </article>
        ))}
      </div>
    </>
  );
}
