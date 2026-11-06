import { useState } from "react";
import { createBrowserRouter, createRoutesFromElements, RouterProvider } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { ErrorBoundary } from "../layout/ErrorBoundary";
import { LoadingScreen, StatusScreen } from "../layout/StatusScreen";
import { AuthProvider } from "../state/auth/AuthProvider";
import { DirectoryContext } from "../state/directoryContext";
import { appRoutes } from "./AppRoutes";
import { createLocalServices, type ApplicationServices } from "./compositionRoot";
import { ServicesContext } from "./servicesContext";

/** Composición de la aplicación: servicios + sesión + enrutador, protegidos ante errores. */
export function App({ services }: { services?: ApplicationServices }) {
  const [resolved] = useState(() => services ?? createLocalServices());
  const [router] = useState(() => createBrowserRouter(createRoutesFromElements(appRoutes)));

  return (
    <ErrorBoundary>
      <ServicesContext.Provider value={resolved}>
        <DirectoryContext.Provider value={resolved.directory}>
          <AuthProvider
            service={resolved.auth}
            renderLoading={() => <LoadingScreen label="Abriendo tu panel…" />}
            renderError={({ message, retry }) => (
              <StatusScreen title="No se pudo abrir tu sesión" message={message}>
                <Button onClick={retry}>Reintentar</Button>
              </StatusScreen>
            )}
          >
            <RouterProvider router={router} />
          </AuthProvider>
        </DirectoryContext.Provider>
      </ServicesContext.Provider>
    </ErrorBoundary>
  );
}
