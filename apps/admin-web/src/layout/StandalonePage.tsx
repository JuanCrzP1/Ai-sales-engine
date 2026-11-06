import type { ReactNode } from "react";
import { BrandMark } from "../components/brand/BrandMark";
import { useAuth } from "../state/auth/useAuth";
import { UserMenu } from "./UserMenu";

/** Página fuera del espacio de trabajo de un negocio: la lista de negocios y el perfil. */
export function StandalonePage({ children }: { children: ReactNode }) {
  const { verifiesCredentials } = useAuth();
  return (
    <div className="standalone">
      <header className="standalone__header">
        <span className="mobile-header__brand">
          <BrandMark size={30} />
          <span className="sidebar__brand-name">AI Sales Engine</span>
        </span>
        {verifiesCredentials && <UserMenu />}
      </header>
      <main className="standalone__main" id="contenido" tabIndex={-1}>
        {children}
      </main>
    </div>
  );
}
