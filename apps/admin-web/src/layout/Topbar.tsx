import { useAuth } from "../state/auth/useAuth";
import { NotificationBell } from "./NotificationBell";
import { SaveStatus } from "./SaveStatus";
import { UserMenu } from "./UserMenu";

/** Barra superior del área de trabajo: estado de guardado, avisos y, si hay autenticación real, la cuenta. */
export function Topbar() {
  const { verifiesCredentials } = useAuth();
  return (
    <div className="topbar">
      <SaveStatus />
      <div className="topbar__actions">
        <NotificationBell />
        {verifiesCredentials && <UserMenu />}
      </div>
    </div>
  );
}
