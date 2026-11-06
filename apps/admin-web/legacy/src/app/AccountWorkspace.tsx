import { useMemo } from "react";
import { Outlet } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { ConfirmButton } from "../components/ui/ConfirmButton";
import { LoadingScreen, StatusScreen } from "../layout/StatusScreen";
import { ConfigProvider } from "../state/ConfigProvider";
import { useCurrentUser } from "../state/auth/useAuth";
import { useApplicationServices } from "./servicesContext";

/** Espacio de trabajo de la cuenta activa: cada cuenta tiene su propia configuración. */
export function AccountWorkspace() {
  const user = useCurrentUser();
  const { createConfigRepository } = useApplicationServices();
  const repository = useMemo(() => createConfigRepository(user.id), [createConfigRepository, user.id]);

  return (
    <ConfigProvider
      key={user.id}
      repository={repository}
      renderLoading={() => <LoadingScreen label="Cargando tu configuración…" />}
      renderError={({ message, retry, discard }) => (
        <StatusScreen title="No se pudo cargar tu configuración" message={`${message} No se ha borrado nada.`}>
          <Button onClick={retry}>Reintentar</Button>
          <ConfirmButton variant="danger" size="default" confirmLabel="Sí, descartar y empezar de cero" onConfirm={discard}>
            Descartar lo guardado
          </ConfirmButton>
        </StatusScreen>
      )}
    >
      <Outlet />
    </ConfigProvider>
  );
}
