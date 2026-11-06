import { useEffect, useMemo, useState } from "react";
import { Outlet, useParams } from "react-router-dom";
import { Button, LinkButton } from "../components/ui/Button";
import type { ContractSchema } from "../domain/config/contractSchema";
import { LoadingScreen, StatusScreen } from "../layout/StatusScreen";
import { BUSINESSES_PATH } from "../navigation/navItems";
import { persistenceErrorMessage } from "../repositories/persistenceError";
import { ConfigProvider } from "../state/ConfigProvider";
import { ContractSchemaContext } from "../state/directoryContext";
import { useApplicationServices } from "./servicesContext";

type SchemaState = { status: "loading" } | { status: "error"; message: string } | { status: "ready"; schema: ContractSchema };

/** Espacio de trabajo del negocio de la ruta: cada negocio tiene su propia configuración, y la ruta decide cuál se edita. */
export function BusinessWorkspace() {
  const { slug = "" } = useParams();
  const { createConfigRepository, directory } = useApplicationServices();
  const repository = useMemo(() => createConfigRepository(slug), [createConfigRepository, slug]);
  const [schema, setSchema] = useState<SchemaState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    setSchema({ status: "loading" });
    directory.contractSchema().then(
      (loaded) => {
        if (active) setSchema({ status: "ready", schema: loaded });
      },
      (error: unknown) => {
        if (active) setSchema({ status: "error", message: persistenceErrorMessage(error) });
      },
    );
    return () => {
      active = false;
    };
  }, [directory, attempt]);

  if (schema.status === "loading") return <LoadingScreen label="Cargando tu configuración…" />;
  if (schema.status === "error") {
    return (
      <StatusScreen title="No se pudo cargar tu configuración" message={schema.message}>
        <Button onClick={() => setAttempt((count) => count + 1)}>Reintentar</Button>
      </StatusScreen>
    );
  }

  return (
    <ContractSchemaContext.Provider value={schema.schema}>
      <ConfigProvider
        key={slug}
        slug={slug}
        repository={repository}
        renderLoading={() => <LoadingScreen label="Cargando tu configuración…" />}
        renderError={({ message, notFound, retry }) => (
          <StatusScreen title={notFound ? "Ese negocio no existe" : "No se pudo cargar tu configuración"} message={notFound ? "Puede que el enlace esté incompleto o que se haya eliminado." : `${message} No se ha borrado nada.`}>
            {!notFound && <Button onClick={retry}>Reintentar</Button>}
            <LinkButton to={BUSINESSES_PATH}>Ver todos los negocios</LinkButton>
          </StatusScreen>
        )}
      >
        <Outlet />
      </ConfigProvider>
    </ContractSchemaContext.Provider>
  );
}
