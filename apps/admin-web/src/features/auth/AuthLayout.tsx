import { Outlet } from "react-router-dom";
import { BrandLogo } from "../../components/brand/BrandLogo";
import { BrandMark } from "../../components/brand/BrandMark";
import { Icon, type IconName } from "../../components/ui/Icon";

const HIGHLIGHTS: { icon: IconName; title: string; text: string }[] = [
  { icon: "chat", title: "Vende por chat", text: "Tu asistente responde, recomienda y cierra ventas por ti." },
  { icon: "box", title: "Tu catálogo, sin código", text: "Productos, precios y pagos en formularios simples." },
  { icon: "shield", title: "Tu información, en tu cuenta", text: "Cada cuenta tiene su propia configuración." },
];

/** Pantalla dividida de las páginas de cuenta: presentación de la marca y formulario. `wide`, para un formulario más amplio (autorizar
 * a un agente, con su tabla de permisos). */
export function AuthLayout({ wide = false }: { wide?: boolean }) {
  return (
    <div className="auth">
      <aside className="auth__showcase" aria-hidden="true">
        <div className="auth__orb auth__orb--one" />
        <div className="auth__orb auth__orb--two" />
        <div className="auth__showcase-inner">
          <span className="auth__brand">
            <BrandMark size={44} />
            AI Sales Engine
          </span>
          <h2 className="auth__headline">Convierte cada conversación en una venta.</h2>
          <ul className="auth__highlights">
            {HIGHLIGHTS.map((item) => (
              <li key={item.title} className="auth__highlight">
                <span className="auth__highlight-icon">
                  <Icon name={item.icon} size={18} />
                </span>
                <span>
                  <strong>{item.title}</strong>
                  <span>{item.text}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      </aside>

      <main className="auth__panel" id="contenido">
        <div className={wide ? "auth__card auth__card--wide" : "auth__card"}>
          <div className="auth__logo">
            <BrandLogo width={200} />
          </div>
          <Outlet />
        </div>
      </main>
    </div>
  );
}
