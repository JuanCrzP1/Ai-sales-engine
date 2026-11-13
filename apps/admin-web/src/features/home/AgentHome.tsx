import { LinkButton } from "../../components/ui/Button";
import { Icon } from "../../components/ui/Icon";
import { CONVERSATIONS_ITEM, CUSTOMERS_ITEM, SALES_ITEM } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { ActivityOverview } from "./ActivityOverview";
import { HomeHeader } from "./HomeHero";

/** El inicio de un asesor: lo que pasó hoy y sus atajos de trabajo (atender, clientes y ventas). */
export function AgentHome() {
  const pathTo = useWorkspacePath();
  return (
    <>
      <HomeHeader />
      <ActivityOverview />
      <section className="agent-shortcuts" aria-label="Atajos">
        {[
          { item: CONVERSATIONS_ITEM, text: "Responde a quien espera a una persona.", icon: "inbox" as const },
          { item: CUSTOMERS_ITEM, text: "Mira en qué va cada cliente.", icon: "users" as const },
          { item: SALES_ITEM, text: "Registra lo que vendiste y revisa los pagos por verificar.", icon: "wallet" as const },
        ].map(({ item, text, icon }) => (
          <div key={item.key} className="agent-shortcut">
            <span className="agent-shortcut__icon" aria-hidden="true">
              <Icon name={icon} size={18} />
            </span>
            <span className="agent-shortcut__text">
              <strong>{item.title}</strong>
              <span>{text}</span>
            </span>
            <LinkButton to={pathTo(item.path)} size="small">
              Abrir
            </LinkButton>
          </div>
        ))}
      </section>
    </>
  );
}
