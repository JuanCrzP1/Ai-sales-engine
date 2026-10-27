import { useState } from "react";
import { BrowserRouter } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { LoadingScreen, StatusScreen } from "../layout/StatusScreen";
import { AuthProvider } from "../state/auth/AuthProvider";
import { AppRoutes } from "./AppRoutes";
import { createLocalServices, type ApplicationServices } from "./compositionRoot";
import { ErrorBoundary } from "../layout/ErrorBoundary";
import { ServicesContext } from "./servicesContext";

/** Composición de la aplicación: servicios + sesión + enrutador, protegidos ante errores. */
export function App({ services }: { services?: ApplicationServices }) {
  const [resolved] = useState(() => services ?? createLocalServices());

  return (
    <ErrorBoundary>
      <ServicesContext.Provider value={resolved}>
        <AuthProvider
          service={resolved.auth}
          renderLoading={() => <LoadingScreen label="Abriendo tu panel…" />}
          renderError={({ message, retry }) => (
            <StatusScreen title="No se pudo abrir tu sesión" message={message}>
              <Button onClick={retry}>Reintentar</Button>
            </StatusScreen>
          )}
        >
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </AuthProvider>
      </ServicesContext.Provider>
    </ErrorBoundary>
  );
}
