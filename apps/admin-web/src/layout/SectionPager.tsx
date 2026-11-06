import { LinkButton } from "../components/ui/Button";
import { neighbours, type NavItem } from "../navigation/navItems";
import { useWorkspacePath } from "../navigation/useWorkspacePath";

/** Botones "Anterior / Siguiente" del recorrido guiado. */
export function SectionPager({ current }: { current: NavItem["key"] }) {
  const { previous, next } = neighbours(current);
  const pathTo = useWorkspacePath();
  return (
    <nav className="page-footer-nav" aria-label="Navegación entre secciones">
      {previous ? (
        <LinkButton to={pathTo(previous.path)} variant="ghost">
          ← {previous.title}
        </LinkButton>
      ) : (
        <span />
      )}
      {next && (
        <LinkButton to={pathTo(next.path)} variant="primary">
          {next.key === "review" ? "Revisar y publicar" : `Siguiente: ${next.title}`} →
        </LinkButton>
      )}
    </nav>
  );
}
