import { useEffect, useMemo, useState } from "react";
import { Outlet, useParams } from "react-router-dom";
import { Button, LinkButton } from "../components/ui/Button";
import type { ContractSchema } from "../domain/config/contractSchema";
import { LoadingScreen, StatusScreen } from "../layout/StatusScreen";
import { ENTRY_PATH } from "../navigation/navItems";
import { persistenceErrorMessage } from "../repositories/persistenceError";
import { AssistantLabContext } from "../state/assistantLabContext";
import { AttentionContext } from "../state/attentionContext";
import { IntegrationsContext } from "../state/integrationsContext";
import { ChannelsContext } from "../state/channelsContext";
import { CommerceContext } from "../state/commerceContext";
import { ConfigProvider } from "../state/ConfigProvider";
import { ContractSchemaContext } from "../state/directoryContext";
import { BusinessRoleContext } from "../state/roleContext";
import type { Role } from "../domain/team/team";
import { useApplicationServices } from "./servicesContext";

type SchemaState = { status: "loading" } | { status: "error"; message: string } | { status: "ready"; schema: ContractSchema; role: Role };

/** Espacio de trabajo del negocio de la ruta: cada negocio tiene su propia configuración, y la ruta decide cuál se edita. */
export function BusinessWorkspace() {
  const { slug = "" } = useParams();
  const { createConfigRepository, createAssistantLab, createChannels, createCommerce, createAttention, createIntegrations, directory } = useApplicationServices();
  const repository = useMemo(() => createConfigRepository(slug), [createConfigRepository, slug]);
  const assistantLab = useMemo(() => createAssistantLab(slug), [createAssistantLab, slug]);
  const channels = useMemo(() => createChannels(slug), [createChannels, slug]);
  const commerce = useMemo(() => createCommerce(slug), [createCommerce, slug]);
  const attention = useMemo(() => createAttention(slug), [createAttention, slug]);
  const integrations = useMemo(() => createIntegrations(slug), [createIntegrations, slug]);
  const [schema, setSchema] = useState<SchemaState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    setSchema({ status: "loading" });
    // El rol de quien entra viene con su lista de negocios: decide lo que el panel le muestra (el servidor lo vuelve a revisar).
    Promise.all([directory.contractSchema(), directory.list()]).then(
      ([loaded, businesses]) => {
        if (active) setSchema({ status: "ready", schema: loaded, role: businesses.find((business) => business.slug === slug)?.role ?? "owner" });
      },
      (error: unknown) => {
        if (active) setSchema({ status: "error", message: persistenceErrorMessage(error) });
      },
    );
    return () => {
      active = false;
    };
  }, [directory, slug, attempt]);

  if (schema.status === "loading") return <LoadingScreen label="Cargando tu configuración…" />;
  if (schema.status === "error") {
    return (
      <StatusScreen title="No se pudo cargar tu configuración" message={schema.message}>
        <Button onClick={() => setAttempt((count) => count + 1)}>Reintentar</Button>
      </StatusScreen>
    );
  }

  return (
    <BusinessRoleContext.Provider value={schema.role}>
    <ContractSchemaContext.Provider value={schema.schema}>
      <ConfigProvider
        key={slug}
        slug={slug}
        repository={repository}
        renderLoading={() => <LoadingScreen label="Cargando tu configuración…" />}
        renderError={({ message, notFound, retry }) => (
          <StatusScreen title={notFound ? "Ese negocio no existe" : "No se pudo cargar tu configuración"} message={notFound ? "Puede que el enlace esté incompleto o que se haya eliminado." : `${message} No se ha borrado nada.`}>
            {!notFound && <Button onClick={retry}>Reintentar</Button>}
            <LinkButton to={ENTRY_PATH}>Volver al panel</LinkButton>
          </StatusScreen>
        )}
      >
        <AssistantLabContext.Provider value={assistantLab}>
          <ChannelsContext.Provider value={channels}>
            <CommerceContext.Provider value={commerce}>
              <AttentionContext.Provider value={attention}>
                <IntegrationsContext.Provider value={integrations}>
                  <Outlet />
                </IntegrationsContext.Provider>
              </AttentionContext.Provider>
            </CommerceContext.Provider>
          </ChannelsContext.Provider>
        </AssistantLabContext.Provider>
      </ConfigProvider>
    </ContractSchemaContext.Provider>
    </BusinessRoleContext.Provider>
  );
}
