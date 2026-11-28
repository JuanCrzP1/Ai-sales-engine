import { Outlet } from "react-router-dom";
import { BrandLogo } from "../../components/brand/BrandLogo";
import { BrandMark } from "../../components/brand/BrandMark";
import { Icon, type IconName } from "../../components/ui/Icon";
import { BRAND_NAME } from "../../lib/brand";

/** Un chat de ejemplo (datos ficticios): el asistente atiende, el cliente paga y el equipo recibe el aviso. */
const CHAT: { from: "customer" | "assistant"; text: string; time: string }[] = [
  { from: "customer", text: "Hola, ¿cuánto cuesta el plan Básico?", time: "10:58" },
  { from: "assistant", text: "¡Hola, Sofía! Vale $210.000 al mes e incluye WhatsApp y reportes. ¿Te lo activo?", time: "IA · 10:58" },
  { from: "customer", text: "Sí, ya te hice la transferencia 👍", time: "11:00" },
  { from: "assistant", text: "¡Gracias! Le paso tu comprobante al equipo para confirmarlo.", time: "IA · 11:00" },
];

const FACTS: { icon: IconName; text: string }[] = [
  { icon: "chat", text: "WhatsApp y Telegram" },
  { icon: "clock", text: "Atiende a toda hora" },
  { icon: "headset", text: "Tu equipo toma el chat" },
];

/**
 * Pantalla dividida de las páginas de cuenta: a la izquierda, la marca y el producto en acción; a la derecha, solo el formulario.
 * La marca va una sola vez: a la izquierda y, cuando esa mitad se oculta (celular), encima del formulario. `wide`, para un formulario
 * más amplio (autorizar a un agente, con su tabla de permisos).
 */
export function AuthLayout({ wide = false }: { wide?: boolean }) {
  return (
    <div className="auth">
      <aside className="auth__showcase" aria-hidden="true">
        <div className="auth__orb auth__orb--one" />
        <div className="auth__orb auth__orb--two" />
        <div className="auth__showcase-inner">
          <span className="auth__brand">
            <BrandMark size={40} />
            {BRAND_NAME}
          </span>

          <div className="auth__stage">
            <div>
              <h2 className="auth__headline">Convierte cada conversación en una venta.</h2>
              <p className="auth__lead">
                Tu asistente con IA atiende a tus clientes con la información de tu negocio y te avisa cuando alguien necesita a una persona.
              </p>
            </div>

            <div className="auth__demo">
              <div className="auth__chat">
                <div className="auth__chat-head">
                  <span className="auth__chat-avatar">SR</span>
                  <span className="auth__chat-who">
                    <strong>Sofía Ramírez</strong>
                    <span>WhatsApp</span>
                  </span>
                  <span className="auth__chat-live">En vivo</span>
                </div>
                {CHAT.map((message, index) => (
                  <p key={message.text} className={`auth__bubble auth__bubble--${message.from}`} style={{ animationDelay: `${0.25 + index * 0.3}s` }}>
                    {message.text}
                    <small>{message.time}</small>
                  </p>
                ))}
              </div>
              <div className="auth__float auth__float--sale">
                <span className="auth__float-icon">
                  <Icon name="check" size={18} />
                </span>
                <span>
                  Venta registrada
                  <strong>$ 210.000</strong>
                </span>
              </div>
              <div className="auth__float auth__float--alert">
                <span className="auth__float-icon">
                  <Icon name="bell" size={18} />
                </span>
                <span>
                  Aviso a tu equipo
                  <strong>Pago por confirmar</strong>
                </span>
              </div>
            </div>
          </div>

          <ul className="auth__facts">
            {FACTS.map((fact) => (
              <li key={fact.text}>
                <Icon name={fact.icon} size={16} />
                {fact.text}
              </li>
            ))}
          </ul>
        </div>
      </aside>

      <main className="auth__panel" id="contenido">
        <div className={wide ? "auth__card auth__card--wide" : "auth__card"}>
          <div className="auth__logo">
            <BrandLogo size={40} />
          </div>
          <Outlet />
        </div>
        <p className="auth__legal">
          © {new Date().getFullYear()} {BRAND_NAME}
        </p>
      </main>
    </div>
  );
}
