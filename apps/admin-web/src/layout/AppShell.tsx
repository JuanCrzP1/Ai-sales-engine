import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { Icon } from "../components/ui/Icon";
import { BrandMark } from "../components/brand/BrandMark";
import { ErrorBoundary } from "./ErrorBoundary";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

const SIDEBAR_ID = "menu-principal";

/** Estructura general: barra lateral, cabecera móvil y área de trabajo. */
export function AppShell() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setMenuOpen(false);
    window.scrollTo?.({ top: 0 });
  }, [location.pathname]);

  return (
    <div className="app-shell">
      <a className="skip-link" href="#contenido">
        Saltar al contenido
      </a>

      <header className="mobile-header">
        <span className="mobile-header__brand">
          <BrandMark size={30} />
          <span className="sidebar__brand-name">AI Sales Engine</span>
        </span>
        <Button
          variant="secondary"
          size="small"
          aria-expanded={menuOpen}
          aria-controls={SIDEBAR_ID}
          onClick={() => setMenuOpen((open) => !open)}
        >
          <Icon name={menuOpen ? "close" : "menu"} size={16} />
          {menuOpen ? "Cerrar menú" : "Menú"}
        </Button>
      </header>

      <Sidebar id={SIDEBAR_ID} open={menuOpen} />

      <main className="main" id="contenido" tabIndex={-1}>
        <div className="main__top">
          <Topbar />
        </div>
        <div className="main__inner" key={location.pathname}>
          <ErrorBoundary variant="section" resetKey={location.pathname}>
            <Outlet />
          </ErrorBoundary>
        </div>
      </main>
    </div>
  );
}
