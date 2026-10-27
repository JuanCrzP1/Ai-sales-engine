import { LinkButton } from "../components/ui/Button";
import { neighbours, type NavItem } from "../navigation/navItems";

/** Botones "Anterior / Siguiente" del recorrido guiado. */
export function SectionPager({ current }: { current: NavItem["key"] }) {
  const { previous, next } = neighbours(current);
  return (
    <nav className="page-footer-nav" aria-label="Navegación entre secciones">
      {previous ? (
        <LinkButton to={previous.path} variant="ghost">
          ← {previous.title}
        </LinkButton>
      ) : (
        <span />
      )}
      {next && (
        <LinkButton to={next.path} variant="primary">
          {next.key === "review" ? "Revisar configuración" : `Siguiente: ${next.title}`} →
        </LinkButton>
      )}
    </nav>
  );
}
