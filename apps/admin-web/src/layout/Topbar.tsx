import { useAuth } from "../state/auth/useAuth";
import { SaveStatus } from "./SaveStatus";
import { UserMenu } from "./UserMenu";

/** Barra superior del área de trabajo: estado de guardado y, si hay autenticación real, la cuenta. */
export function Topbar() {
  const { verifiesCredentials } = useAuth();
  return (
    <div className="topbar">
      <SaveStatus />
      {verifiesCredentials && <UserMenu />}
    </div>
  );
}
