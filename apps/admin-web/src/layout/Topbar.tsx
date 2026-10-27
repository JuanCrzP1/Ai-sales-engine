import { SaveStatus } from "./SaveStatus";
import { UserMenu } from "./UserMenu";

/** Barra superior del área de trabajo: estado de guardado y cuenta. */
export function Topbar() {
  return (
    <div className="topbar">
      <SaveStatus />
      <UserMenu />
    </div>
  );
}
