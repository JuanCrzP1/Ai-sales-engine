import { useCallback, useEffect, useRef, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { COMPACT_SCREEN, useMediaQuery } from "../lib/useMediaQuery";
import { isAssistantPath, isSettingsPath, titleForPath } from "../navigation/navItems";
import { useConfig } from "../state/useConfig";
import { AssistantTabs } from "./AssistantTabs";
import { SettingsTabs } from "./SettingsTabs";
import { ErrorBoundary } from "./ErrorBoundary";
import { NotificationBell } from "./NotificationBell";
import { SaveProblems } from "./SaveProblems";
import { Sidebar } from "./Sidebar";
import { SaveStatus } from "./SaveStatus";
import { UnsavedChangesGuard } from "./UnsavedChangesGuard";

const SIDEBAR_ID = "menu-principal";

/**
 * Estructura general: barra lateral, área de trabajo y, en el celular, una barra superior con ☰, el nombre de la sección y los
 * avisos. El menú se desliza desde la izquierda sobre un fondo oscuro, como en las aplicaciones móviles: se cierra al tocar
 * fuera, con la X, con Escape, deslizándolo o al elegir una opción, y mientras está abierto la página de atrás no se mueve.
 */
export function AppShell() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const { save, document } = useConfig();
  const compact = useMediaQuery(COMPACT_SCREEN);
  const menuButton = useRef<HTMLButtonElement>(null);
  const wasOpen = useRef(false);

  const closeMenu = useCallback(() => setMenuOpen(false), []);

  useEffect(() => {
    setMenuOpen(false);
    window.scrollTo?.({ top: 0 });
  }, [location.pathname]);

  // En una pantalla grande el menú siempre está a la vista: no queda «abierto» al agrandar la ventana.
  useEffect(() => {
    if (!compact) setMenuOpen(false);
  }, [compact]);

  useEffect(() => {
    if (!menuOpen) {
      // Al cerrarlo, el foco vuelve al botón que lo abrió (para quien navega con teclado o lector de pantalla).
      if (wasOpen.current) menuButton.current?.focus();
      wasOpen.current = false;
      return;
    }
    wasOpen.current = true;
    const root = window.document.documentElement;
    const previous = root.style.overflow;
    root.style.overflow = "hidden";
    window.document.querySelector<HTMLElement>(`#${SIDEBAR_ID} a, #${SIDEBAR_ID} button`)?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMenuOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => {
      root.style.overflow = previous;
      window.removeEventListener("keydown", onKey);
    };
  }, [menuOpen]);

  return (
    <div className="app-shell">
      <a className="skip-link" href="#contenido">
        Saltar al contenido
      </a>

      <header className="mobile-header">
        <button
          ref={menuButton}
          type="button"
          className={`hamburger${menuOpen ? " hamburger--open" : ""}`}
          aria-label={menuOpen ? "Cerrar menú" : "Abrir menú"}
          aria-expanded={menuOpen}
          aria-controls={SIDEBAR_ID}
          onClick={() => setMenuOpen((open) => !open)}
        >
          <span className="hamburger__bars" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
        </button>
        <div className="mobile-header__title">
          <span className="mobile-header__section">{titleForPath(location.pathname)}</span>
          <span className="mobile-header__business">{document.identity.name.trim() || "Tu negocio"}</span>
        </div>
        {/* En el celular los avisos van aquí, siempre a mano; en pantalla grande, en la barra lateral. */}
        {compact && <NotificationBell />}
      </header>

      <div className={`drawer-backdrop${menuOpen ? " drawer-backdrop--visible" : ""}`} aria-hidden="true" onClick={closeMenu} />

      <Sidebar id={SIDEBAR_ID} open={menuOpen} compact={compact} onClose={closeMenu} />

      <main className="main" id="contenido" tabIndex={-1}>
        {/* Sin barra superior: la cuenta y los avisos viven en la barra lateral. El estado de guardado solo importa al configurar. */}
        {isAssistantPath(location.pathname) && (
          <div className="main__top">
            <SaveStatus />
          </div>
        )}
        <UnsavedChangesGuard />
        <SaveProblems />
        {/* Mientras se guarda no se puede editar: lo escrito se perdería al recibir la versión del servidor. */}
        <fieldset className="main__edit-area" disabled={save.status === "saving"}>
          <div className="main__inner" key={location.pathname}>
            {isAssistantPath(location.pathname) && <AssistantTabs />}
            {isSettingsPath(location.pathname) && <SettingsTabs />}
            <ErrorBoundary variant="section" resetKey={location.pathname}>
              <Outlet />
            </ErrorBoundary>
          </div>
        </fieldset>
      </main>
    </div>
  );
}
