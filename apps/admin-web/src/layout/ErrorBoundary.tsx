import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button } from "../components/ui/Button";
import { StatusScreen } from "./StatusScreen";

interface ErrorBoundaryProps {
  children: ReactNode;
  /** Al cambiar (por ejemplo, la ruta), se reintenta mostrar el contenido. */
  resetKey?: string;
  /** "page" ocupa la pantalla; "section" se muestra dentro del área de trabajo. */
  variant?: "page" | "section";
}

interface ErrorBoundaryState {
  error: Error | null;
  resetKey?: string;
}

/** Evita que un fallo de renderizado deje la pantalla en blanco. */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null, resetKey: this.props.resetKey };

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { error };
  }

  static getDerivedStateFromProps(props: ErrorBoundaryProps, state: ErrorBoundaryState): Partial<ErrorBoundaryState> | null {
    return props.resetKey !== state.resetKey ? { error: null, resetKey: props.resetKey } : null;
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Error de renderizado capturado:", error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;

    const actions = (
      <>
        <Button onClick={() => this.setState({ error: null })}>Reintentar</Button>
        <Button variant="secondary" onClick={() => window.location.reload()}>
          Recargar la página
        </Button>
      </>
    );
    if (this.props.variant === "section") {
      return (
        <div className="card" role="alert">
          <h1 className="card__title">Esta sección no se pudo mostrar</h1>
          <p className="card__description">Tus datos guardados no se han perdido. Prueba de nuevo o vuelve a otra sección.</p>
          <div className="button-row">{actions}</div>
        </div>
      );
    }
    return (
      <StatusScreen title="Algo salió mal" message="La aplicación encontró un error inesperado. Tus datos guardados no se han perdido.">
        {actions}
      </StatusScreen>
    );
  }
}
