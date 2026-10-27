import { Icon } from "../../components/ui/Icon";

/**
 * Aviso permanente cuando el servicio de autenticación no verifica credenciales:
 * el acceso no debe presentarse como autenticación real.
 */
export function UnverifiedAccessNotice() {
  return (
    <div className="access-notice" role="note">
      <span className="access-notice__icon">
        <Icon name="alert" size={16} />
      </span>
      <p>
        <strong>Acceso local sin verificación.</strong> Aún no hay un servidor conectado: se entra solo con el correo, sin
        contraseña, y los datos quedan guardados únicamente en este navegador.
      </p>
    </div>
  );
}
